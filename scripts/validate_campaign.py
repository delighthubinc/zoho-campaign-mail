#!/usr/bin/env python3
"""Validate fixed campaign HTML locally or after GitHub Pages deployment."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from build_email import EMAIL_DEFAULTS, PLACEHOLDER_RE, build_cta_url, load_json

ROOT = Path(__file__).resolve().parents[1]
TEMP_VALUE_RE = re.compile(
    r"(?:example\.(?:com|org|jp)|localhost|127\.0\.0\.1|REPLACE[_-]?ME|TODO|TBD)", re.I
)
SECRET_RE = re.compile(
    r"(?:ZOHO_(?:CLIENT_ID|CLIENT_SECRET|REFRESH_TOKEN|ACCESS_TOKEN)\s*[:=]|"
    r"(?:client[_ -]?secret|refresh[_ -]?token|access[_ -]?token)\s*[:=]\s*[^\s<]{8,}|"
    r"1000\.[A-Za-z0-9_-]{20,}|Zoho-oauthtoken\s+[A-Za-z0-9._-]{20,})",
    re.I,
)
ZOHO_TAG = "$[UD:COMPANY_NAME||]$　$[UD:LAST_NAME||]$様"
FORBIDDEN_ELEMENTS = {"script", "iframe", "object", "embed", "form"}


class ValidationError(Exception):
    pass


class DocumentInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.images: list[str] = []
        self.anchor_stack: list[dict[str, object]] = []
        self.anchors: list[tuple[str, str, list[str], bool]] = []
        self.unsafe: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        values = {key.lower(): value for key, value in attrs}
        if tag in FORBIDDEN_ELEMENTS:
            self.unsafe.append(f"<{tag}>")
        for key, value in attrs:
            if key.lower().startswith("on"):
                self.unsafe.append(key)
            if isinstance(value, str) and value.lstrip().lower().startswith("javascript:"):
                self.unsafe.append(f"{key}=javascript:")
        if tag == "a":
            href = html.unescape(values.get("href") or "")
            self.hrefs.append(href)
            self.anchor_stack.append({
                "href": href, "text": [], "images": [],
                "formal": values.get("data-cta") == "true",
            })
        if tag == "img":
            src = html.unescape(values.get("src") or "")
            if src:
                self.images.append(src)
                if self.anchor_stack:
                    self.anchor_stack[-1]["images"].append(src)  # type: ignore[union-attr]

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        if self.anchor_stack:
            self.anchor_stack[-1]["text"].append(data)  # type: ignore[union-attr]

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self.anchor_stack:
            anchor = self.anchor_stack.pop()
            self.anchors.append((
                str(anchor["href"]), "".join(anchor["text"]).strip(),  # type: ignore[arg-type]
                list(anchor["images"]), bool(anchor["formal"]),  # type: ignore[arg-type]
            ))


def fetch(url: str, method: str = "GET") -> bytes:
    try:
        request = Request(url, method=method, headers={"User-Agent": "zoho-campaign-mail-validator/3"})
        with urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise ValidationError(f"HTTP {response.status}: {url}")
            return response.read()
    except (HTTPError, URLError) as exc:
        raise ValidationError(f"URLを取得できません: {url}: {exc}") from exc


def campaign_images(data: dict) -> list[str]:
    """Read the authoritative fixed-HTML campaign image manifest."""
    images = data.get("images")
    if not isinstance(images, list) or not images:
        raise ValueError("images は1件以上のcampaign画像object配列で指定してください")
    urls: list[str] = []
    for index, image in enumerate(images):
        if not isinstance(image, dict) or not isinstance(image.get("url"), str) or not image["url"].strip():
            raise ValueError(f"images[{index}].url は空でない文字列で指定してください")
        urls.append(image["url"].strip())
    return urls


def _https_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme == "https" and bool(parsed.netloc) and not parsed.username and not parsed.password


def _without_query(value: str) -> str:
    parsed = urlsplit(value)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def validate(data: dict, document: str, check_urls: bool = False) -> list[str]:
    errors: list[str] = []
    if not document.strip():
        return ["mail.htmlが空です"]

    for key in ("campaign_slug", "subject", "zoho_campaign_name"):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"campaign.jsonの{key}が未設定です")
    if data.get("content_source") != "fixed_html":
        errors.append('content_sourceは"fixed_html"である必要があります')

    serialized = json.dumps(data, ensure_ascii=False)
    combined = serialized + "\n" + document
    if PLACEHOLDER_RE.search(combined):
        errors.append("未解決の{{PLACEHOLDER}}があります")
    if TEMP_VALUE_RE.search(combined):
        errors.append("仮URLまたはTODO/TBD文字列があります")
    if SECRET_RE.search(combined):
        errors.append("OAuth/Secretらしき値があります")
    if ZOHO_TAG not in document:
        errors.append("Zoho宛名差し込みタグが完全な形で存在しません")
    subject = data.get("subject")
    if isinstance(subject, str) and subject not in html.unescape(document):
        errors.append("件名がHTMLに存在しません")

    inspector = DocumentInspector()
    try:
        inspector.feed(document)
        inspector.close()
    except (ValueError, TypeError) as exc:
        errors.append(f"HTMLを解析できません: {exc}")
    if inspector.unsafe:
        errors.append("JavaScriptまたは不要な実行要素があります: " + ", ".join(inspector.unsafe))
    for href in inspector.hrefs:
        if not href.strip() or href.strip() == "#":
            errors.append("空または#のリンクがあります")

    try:
        cta_url = build_cta_url(data.get("cta"))
        label = data.get("cta", {}).get("label")
        if not isinstance(label, str) or not label.strip():
            raise ValueError("cta.label は空でない文字列で指定してください")
    except (ValueError, TypeError) as exc:
        errors.append(f"CTA/UTMが不正です: {exc}")
        cta_url, label = "", ""

    try:
        expected_images = campaign_images(data)
    except ValueError as exc:
        errors.append(f"campaign画像情報が不正です: {exc}")
        expected_images = []
    for url in expected_images:
        if not _https_url(url):
            errors.append(f"campaign画像URLが有効なHTTPS URLではありません: {url}")
        if url not in inspector.images:
            errors.append(f"campaign画像URLがHTMLに存在しません: {url}")

    if cta_url:
        matching_buttons = [a for a in inspector.anchors if a[1] == label]
        linked_campaign_images = [a for a in inspector.anchors if set(a[2]) & set(expected_images)]
        formal_links = [a for a in inspector.anchors if a[3]]
        if not matching_buttons:
            errors.append("CTA labelを持つCTAボタンがHTMLに存在しません")
        if not linked_campaign_images:
            errors.append("campaign画像（hero/banner）がCTAリンク内に存在しません")
        for href, _text, _images, _formal in matching_buttons + linked_campaign_images + formal_links:
            if href != cta_url:
                errors.append(f"正式CTAのURL/UTMがcampaign.jsonと一致しません: {href}")
        # Catch alternate UTM variants of the CTA destination without treating unrelated links as CTA.
        for href in inspector.hrefs:
            if _without_query(href) == _without_query(cta_url) and href != cta_url:
                errors.append(f"CTA遷移先に不一致のURL/UTMがあります: {href}")

    defaults = load_json(EMAIL_DEFAULTS)
    common_images = [defaults["logo_url"], defaults["contact_image_url"]]
    for label_name, url in zip(("logo_url", "contact_image_url"), common_images):
        if url not in inspector.images:
            errors.append(f"共通画像 {label_name} がHTMLに存在しません")
        if not _https_url(url):
            errors.append(f"共通画像 {label_name} が有効なHTTPS URLではありません")

    if check_urls and not errors:
        for url in dict.fromkeys(expected_images + common_images):
            try:
                fetch(url)
            except ValidationError as exc:
                errors.append(str(exc))
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
    try:
        data = load_json(campaign_dir / "campaign.json")
        if data.get("campaign_slug") != args.campaign_slug:
            raise ValidationError("campaign_slugとディレクトリ名が一致しません")
        raw = fetch(args.public_url) if args.public_url else (campaign_dir / "mail.html").read_bytes()
        document = raw.decode("utf-8")
        errors = validate(data, document, args.check_urls)
    except (OSError, UnicodeDecodeError, ValidationError, ValueError) as exc:
        errors = [str(exc)]
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if not errors:
        print(f"campaign validation passed: {args.campaign_slug}")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
