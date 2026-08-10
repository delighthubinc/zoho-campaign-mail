#!/usr/bin/env python3
"""Validate a generated campaign locally or after GitHub Pages deployment."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from build_email import (EMAIL_DEFAULTS, PLACEHOLDER_RE, build_cta_url, load_json,
                         validate_seminar_data)

ROOT = Path(__file__).resolve().parents[1]
TEMP_URL_RE = re.compile(r"(?:example\.(?:com|org|jp)|localhost|127\.0\.0\.1|REPLACE_|TODO|TBD)", re.I)
SECRET_RE = re.compile(
    r"(?:ZOHO_(?:CLIENT_ID|CLIENT_SECRET|REFRESH_TOKEN|ACCESS_TOKEN)\s*[:=]|"
    r"(?:1000\.[A-Za-z0-9_-]{20,}|Zoho-oauthtoken\s+[A-Za-z0-9._-]{20,}))",
    re.I,
)
ZOHO_TAG = "$[UD:COMPANY_NAME||]$　$[UD:LAST_NAME||]$様"


class ValidationError(Exception):
    pass


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.images: list[tuple[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a" and values.get("href"):
            self.hrefs.append(html.unescape(values["href"] or ""))
        if tag == "img" and values.get("src"):
            self.images.append((html.unescape(values["src"] or ""), values.get("alt")))


def fetch(url: str, method: str = "GET") -> bytes:
    try:
        with urlopen(Request(url, method=method, headers={"User-Agent": "zoho-campaign-mail-validator/2"}), timeout=30) as response:
            if response.status != 200:
                raise ValidationError(f"HTTP {response.status}: {url}")
            return response.read()
    except (HTTPError, URLError) as exc:
        raise ValidationError(f"URLを取得できません: {url}: {exc}") from exc


def campaign_images(data: dict) -> list[str]:
    """Return all structured campaign image URLs used by either schema."""
    images: list[str] = []
    if data.get("template_type") == "seminar":
        for block in data.get("blocks", []):
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type in {"hero", "speaker", "image_text"}:
                image = block.get("image")
                if isinstance(image, dict) and isinstance(image.get("url"), str):
                    images.append(image["url"])
            if block_type == "keynote_speakers":
                for speaker in block.get("speakers", []):
                    image = speaker.get("image") if isinstance(speaker, dict) else None
                    if isinstance(image, dict) and isinstance(image.get("url"), str):
                        images.append(image["url"])
            if block_type == "company_logos":
                for image in block.get("logos", []):
                    if isinstance(image, dict) and isinstance(image.get("url"), str):
                        images.append(image["url"])
    else:
        banner = data.get("banner")
        if isinstance(banner, dict) and isinstance(banner.get("url"), str):
            images.append(banner["url"])
        images.extend(speaker.get("image", {}).get("url") for speaker in data.get("speakers", [])
                      if isinstance(speaker, dict) and isinstance(speaker.get("image", {}).get("url"), str))
    return images


def validate(data: dict, document: str, check_urls: bool = False) -> list[str]:
    errors: list[str] = []
    slug = data.get("campaign_slug")
    subject = data.get("subject")
    campaign_name = data.get("zoho_campaign_name")
    for key, value in (("campaign_slug", slug), ("subject", subject), ("zoho_campaign_name", campaign_name)):
        if not isinstance(value, str) or not value.strip():
            errors.append(f"campaign.jsonの{key}が未設定です")
    if data.get("template_type") == "seminar":
        try:
            validate_seminar_data(data)
        except (ValueError, TypeError) as exc:
            errors.append(f"seminar schemaが不正です: {exc}")
    if PLACEHOLDER_RE.search(document):
        errors.append("未解決の{{PLACEHOLDER}}があります")
    if TEMP_URL_RE.search(document):
        errors.append("仮URLまたはTODO文字列があります")
    if SECRET_RE.search(document):
        errors.append("OAuth/Secretらしき値があります")
    if ZOHO_TAG not in document:
        errors.append("Zoho宛名差し込みタグが完全な形で存在しません")
    if isinstance(subject, str) and html.escape(subject) not in document:
        errors.append("件名がHTMLに存在しません")

    parser = Links()
    parser.feed(document)
    try:
        cta_url = build_cta_url(data.get("cta"))
    except (ValueError, TypeError) as exc:
        errors.append(f"CTA/UTMが不正です: {exc}")
        cta_url = ""
    if data.get("template_type") == "seminar":
        blocks = data.get("blocks", [])
        expected_ctas = sum(block.get("type") in {"hero", "cta"}
                            for block in blocks if isinstance(block, dict))
        if cta_url and parser.hrefs.count(cta_url) != expected_ctas:
            errors.append("CTA URLがheroとCTA blockに正しい回数設定されていません")
    elif cta_url and parser.hrefs.count(cta_url) < 2:
        errors.append("CTA URLがボタンとバナーに同一URLで設定されていません")

    image_urls = [url for url, _ in parser.images]
    expected_images = campaign_images(data)
    for url in expected_images:
        if url not in image_urls:
            errors.append(f"campaign画像URLがHTMLに存在しません: {url}")
    defaults = load_json(EMAIL_DEFAULTS)
    for label in ("logo_url", "contact_image_url"):
        if defaults[label] not in image_urls:
            errors.append(f"共通画像 {label} がHTMLに存在しません")
    expected_images += [defaults["logo_url"], defaults["contact_image_url"]]

    if check_urls and not errors:
        for url in dict.fromkeys(expected_images):
            try:
                fetch(url)
            except ValidationError as exc:
                errors.append(str(exc))
        if cta_url:
            try:
                fetch(cta_url, "HEAD")
            except ValidationError:
                try:
                    fetch(cta_url)
                except ValidationError as exc:
                    errors.append(f"CTA遷移先を確認できません: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign-slug", required=True)
    parser.add_argument("--public-url")
    parser.add_argument("--check-urls", action="store_true")
    args = parser.parse_args()
    campaign_dir = ROOT / "campaigns" / args.campaign_slug
    data = load_json(campaign_dir / "campaign.json")
    if data.get("campaign_slug") != args.campaign_slug:
        print("error: campaign_slugとディレクトリ名が一致しません", file=sys.stderr)
        return 1
    try:
        document = (fetch(args.public_url).decode("utf-8") if args.public_url else
                    (campaign_dir / "mail.html").read_text(encoding="utf-8"))
        errors = validate(data, document, args.check_urls)
    except (OSError, UnicodeDecodeError, ValidationError, ValueError) as exc:
        errors = [str(exc)]
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if not errors:
        print(f"campaign validation passed: {args.campaign_slug}")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
