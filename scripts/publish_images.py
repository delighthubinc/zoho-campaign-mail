#!/usr/bin/env python3
"""Place image assets in a campaign's GitHub Pages directory."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
IMAGE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def load_object(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"JSONを読み込めません: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"JSONのルートはobjectである必要があります: {path}")
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="画像をキャンペーン公開ディレクトリへ配置します")
    parser.add_argument("--campaign-slug", required=True)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--config", default=ROOT / "config" / "zoho.json", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if not SLUG_RE.fullmatch(args.campaign_slug):
            raise ValueError("campaign-slug は小文字英数字とハイフン（最大80文字）で指定してください")
        manifest = load_object(args.manifest)
        config = load_object(args.config)
        images = manifest.get("images")
        if not isinstance(images, list) or not images:
            raise ValueError("manifest.images は空でない配列で指定してください")
        pages_base = config.get("github_pages_base_url")
        if not isinstance(pages_base, str) or urlparse(pages_base).scheme != "https" or not urlparse(pages_base).netloc.endswith("github.io"):
            raise ValueError("github_pages_base_url は github.io のHTTPS URLで指定してください")

        destination_dir = ROOT / "campaigns" / args.campaign_slug / "images"
        prepared: list[tuple[Path, Path, str]] = []
        seen: set[str] = set()
        unsupported: list[str] = []
        for index, item in enumerate(images):
            if not isinstance(item, dict):
                raise ValueError(f"images[{index}] はobjectで指定してください")
            name = item.get("name")
            if not isinstance(name, str) or not IMAGE_NAME_RE.fullmatch(name) or name in {".", ".."}:
                raise ValueError(f"images[{index}].name が安全なファイル名ではありません")
            if name in seen:
                raise ValueError(f"画像名が重複しています: {name}")
            seen.add(name)
            source_value = item.get("source")
            if not source_value:
                if item.get("drive_file_id") or item.get("drive_url"):
                    unsupported.append(name)
                    continue
                raise ValueError(f"{name}: source、drive_file_id、drive_url のいずれかが必要です")
            if not isinstance(source_value, str):
                raise ValueError(f"{name}: source は文字列で指定してください")
            source = Path(source_value).expanduser()
            if not source.is_absolute():
                source = (ROOT / source).resolve()
            if not source.is_file():
                raise ValueError(f"画像が見つかりません: {source}")
            destination = destination_dir / name
            if destination.exists() and not args.overwrite:
                raise ValueError(f"出力先が既に存在します（置換する場合は --overwrite）: {destination}")
            public_url = urljoin(pages_base.rstrip("/") + "/", f"campaigns/{args.campaign_slug}/images/{quote(name)}")
            prepared.append((source, destination, public_url))

        if unsupported:
            raise NotImplementedError(
                "Google Drive取得は未実装です。ローカルへ取得して source を指定してください: " + ", ".join(unsupported)
            )
        destination_dir.mkdir(parents=True, exist_ok=True)
        for source, destination, public_url in prepared:
            shutil.copy2(source, destination)
            print(f"配置しました: {destination.relative_to(ROOT)}")
            print(f"公開予定URL: {public_url}")
        return 0
    except (ValueError, OSError, NotImplementedError) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
