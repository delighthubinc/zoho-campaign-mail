#!/usr/bin/env python3
"""Build a table-based HTML email without contacting external services."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT / "templates" / "email_template.html"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
IMAGE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
PLACEHOLDER_RE = re.compile(r"{{[A-Z_]+}}")


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"JSONを読み込めません: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSONのルートはobjectである必要があります: {path}")
    return value


def require_text(data: dict, key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} は空でない文字列で指定してください")
    return value.strip()


def escaped_multiline(value: str) -> str:
    return html.escape(value, quote=True).replace("\n", "<br>")


def validate_https_url(value: str, label: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{label} は有効なHTTPS URLで指定してください")
    return value


def render(content: dict, template: str, image_base_url: str) -> str:
    heading = require_text(content, "heading")
    preheader = content.get("preheader", "")
    footer = content.get("footer", "")
    paragraphs = content.get("paragraphs")
    if not isinstance(preheader, str) or not isinstance(footer, str):
        raise ValueError("preheader と footer は文字列で指定してください")
    if not isinstance(paragraphs, list) or not paragraphs or not all(
        isinstance(item, str) and item.strip() for item in paragraphs
    ):
        raise ValueError("paragraphs は空でない文字列の配列で指定してください")

    paragraph_html = "\n              ".join(
        f'<p style="margin:0 0 20px;font-size:16px;line-height:1.8;color:#374151;">{escaped_multiline(item.strip())}</p>'
        for item in paragraphs
    )

    hero_row = ""
    hero = content.get("hero_image")
    if hero is not None:
        if not isinstance(hero, dict):
            raise ValueError("hero_image はobjectで指定してください")
        filename = require_text(hero, "filename")
        alt = require_text(hero, "alt")
        if not IMAGE_NAME_RE.fullmatch(filename) or filename in {".", ".."}:
            raise ValueError("hero_image.filename が安全なファイル名ではありません")
        image_url = urljoin(image_base_url, quote(filename))
        hero_row = (
            '<tr><td style="padding:0;">'
            f'<img src="{html.escape(image_url, quote=True)}" width="600" '
            f'alt="{html.escape(alt, quote=True)}" style="display:block;width:100%;max-width:600px;height:auto;border:0;">'
            "</td></tr>"
        )

    cta_row = ""
    cta = content.get("cta")
    if cta is not None:
        if not isinstance(cta, dict):
            raise ValueError("cta はobjectで指定してください")
        label = require_text(cta, "label")
        url = validate_https_url(require_text(cta, "url"), "cta.url")
        cta_row = (
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;margin-top:28px;">'
            '<tr><td style="border-radius:4px;background-color:#155eef;">'
            f'<a href="{html.escape(url, quote=True)}" style="display:inline-block;padding:14px 24px;font-size:16px;'
            f'line-height:1.2;font-weight:700;color:#ffffff;text-decoration:none;">{html.escape(label)}</a>'
            "</td></tr></table>"
        )

    replacements = {
        "{{TITLE}}": html.escape(heading),
        "{{PREHEADER}}": html.escape(preheader.strip()),
        "{{HEADING}}": html.escape(heading),
        "{{PARAGRAPHS}}": paragraph_html,
        "{{HERO_ROW}}": hero_row,
        "{{CTA_ROW}}": cta_row,
        "{{FOOTER}}": escaped_multiline(footer.strip()),
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    leftovers = sorted(set(PLACEHOLDER_RE.findall(template)))
    if leftovers:
        raise ValueError(f"テンプレートに未解決のプレースホルダーがあります: {', '.join(leftovers)}")
    return template.rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FIX済み原稿からHTMLメールを生成します（外部通信なし）")
    parser.add_argument("--campaign-slug", required=True)
    parser.add_argument("--content", required=True, type=Path, help="原稿JSON")
    parser.add_argument("--config", default=ROOT / "config" / "zoho.json", type=Path)
    parser.add_argument("--template", default=DEFAULT_TEMPLATE, type=Path)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if not SLUG_RE.fullmatch(args.campaign_slug):
            raise ValueError("campaign-slug は小文字英数字とハイフン（最大80文字）で指定してください")
        config = load_json(args.config)
        content = load_json(args.content)
        pages_base = validate_https_url(require_text(config, "github_pages_base_url"), "github_pages_base_url")
        repo_path = urlparse(pages_base).path.rstrip("/") + "/"
        if not urlparse(pages_base).netloc.endswith("github.io"):
            raise ValueError("github_pages_base_url は github.io のURLで指定してください")
        image_base = urljoin(pages_base.rstrip("/") + "/", f"campaigns/{args.campaign_slug}/images/")
        if not urlparse(image_base).path.startswith(repo_path):
            raise ValueError("画像URLがGitHub Pagesの公開パス外です")
        template = args.template.read_text(encoding="utf-8")
        output = ROOT / "campaigns" / args.campaign_slug / "mail.html"
        if output.exists() and not args.overwrite:
            raise ValueError(f"出力先が既に存在します（置換する場合は --overwrite）: {output}")
        built = render(content, template, image_base)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(built, encoding="utf-8")
        print(f"生成しました: {output.relative_to(ROOT)}")
        print(f"公開予定URL: {urljoin(pages_base.rstrip('/') + '/', f'campaigns/{args.campaign_slug}/mail.html')}")
        return 0
    except (ValueError, OSError) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
