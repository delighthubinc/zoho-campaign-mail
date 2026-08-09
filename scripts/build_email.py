#!/usr/bin/env python3
"""Build a table-based HTML email without contacting external services."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlencode, urljoin, urlparse, urlunparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT / "templates" / "email_template.html"
BASE_TEMPLATE = ROOT / "templates" / "base" / "email.html"
EMAIL_DEFAULTS = ROOT / "config" / "email_defaults.json"
TEMPLATE_FILES = {
    "large_seminar": ROOT / "templates" / "seminar" / "large_seminar.html",
}
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


def validate_cta_url(value: str, label: str = "cta URL") -> str:
    """Validate a CTA URL without making an external request."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} は空でない文字列で指定してください")
    value = value.strip()
    if any(character.isspace() or ord(character) < 32 for character in value):
        raise ValueError(f"{label} は有効なHTTP(S) URLで指定してください")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not parsed.hostname:
        raise ValueError(f"{label} は有効なHTTP(S) URLで指定してください")
    if parsed.username or parsed.password:
        raise ValueError(f"{label} に認証情報を含めないでください")
    return value


def build_cta_url(cta: dict, utm_content: str | None = None) -> str:
    """Resolve legacy or structured CTA data and safely add UTM parameters."""
    if not isinstance(cta, dict):
        raise ValueError("cta はobjectで指定してください")

    has_url = "url" in cta
    has_base_url = "base_url" in cta
    if has_url == has_base_url:
        raise ValueError("cta は url（従来形式）または base_url のどちらか一方を指定してください")
    key = "url" if has_url else "base_url"
    base_url = validate_cta_url(require_text(cta, key), f"cta.{key}")

    utm = cta.get("utm")
    if utm is None:
        if utm_content is not None:
            raise ValueError("utm_content を使用する場合は cta.utm を指定してください")
        return base_url
    if not isinstance(utm, dict):
        raise ValueError("cta.utm はobjectで指定してください")
    allowed = {"source", "medium", "campaign", "content"}
    unknown = sorted(set(utm) - allowed)
    if unknown:
        raise ValueError(f"cta.utm に未対応の項目があります: {', '.join(unknown)}")
    required = {name: require_text(utm, name) for name in ("source", "medium", "campaign")}
    content = utm_content if utm_content is not None else utm.get("content")
    if content is not None and (not isinstance(content, str) or not content.strip()):
        raise ValueError("cta.utm.content は空でない文字列で指定してください")

    parameters = {
        "utm_source": required["source"],
        "utm_medium": required["medium"],
        "utm_campaign": required["campaign"],
    }
    if content is not None:
        parameters["utm_content"] = content.strip()
    parsed = urlparse(base_url)
    query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True)
             if key not in parameters]
    query.extend(parameters.items())
    result = urlunparse(parsed._replace(query=urlencode(query, doseq=True)))
    return validate_cta_url(result)


def require_list(data: dict, key: str) -> list:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{key} は空でない配列で指定してください")
    return value


def image_tag(image: dict, width: int, label: str) -> str:
    if not isinstance(image, dict):
        raise ValueError(f"{label} はobjectで指定してください")
    url = validate_https_url(require_text(image, "url"), f"{label}.url")
    alt = require_text(image, "alt")
    return (f'<img src="{html.escape(url, quote=True)}" width="{width}" alt="{html.escape(alt, quote=True)}" '
            f'style="display:block;width:100%;max-width:{width}px;height:auto;border:0;">')


def cta_table(cta: dict) -> str:
    if not isinstance(cta, dict):
        raise ValueError("cta はobjectで指定してください")
    label = require_text(cta, "label")
    url = build_cta_url(cta)
    return ('<table role="presentation" align="center" cellpadding="0" cellspacing="0" border="0" '
            'style="margin:0 auto;border-collapse:collapse;"><tr><td align="center" bgcolor="#c5a253" '
            'style="border-radius:4px;background-color:#c5a253;">'
            f'<a href="{html.escape(url, quote=True)}" style="display:inline-block;padding:16px 42px;'
            'font-size:16px;line-height:1.2;font-weight:700;color:#ffffff;text-decoration:none;'
            f'border:1px solid #c5a253;border-radius:4px;">{html.escape(label)}</a></td></tr></table>')


def fill(template: str, replacements: dict[str, str]) -> str:
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    leftovers = sorted(set(PLACEHOLDER_RE.findall(template)))
    if leftovers:
        raise ValueError(f"テンプレートに未解決のプレースホルダーがあります: {', '.join(leftovers)}")
    return template


def seminar_base_replacements(defaults: dict) -> dict[str, str]:
    """Render public, seminar-wide branding without campaign-level duplication."""
    logo_url = validate_https_url(require_text(defaults, "logo_url"), "logo_url")
    contact_image_url = validate_https_url(
        require_text(defaults, "contact_image_url"), "contact_image_url"
    )
    corporate_site_url = validate_https_url(
        require_text(defaults, "corporate_site_url"), "corporate_site_url"
    )
    email_address = require_text(defaults, "email")
    if "@" not in email_address or any(character.isspace() for character in email_address):
        raise ValueError("email は有効なメールアドレスで指定してください")
    return {
        "{{LOGO_URL}}": html.escape(logo_url, quote=True),
        "{{LOGO_ALT}}": html.escape(require_text(defaults, "logo_alt"), quote=True),
        # html.escape does not alter Zoho's $, [, ], :, | characters or the full-width space.
        "{{ZOHO_RECIPIENT}}": html.escape(require_text(defaults, "zoho_recipient")),
        "{{RECIPIENT_NOTICE}}": escaped_multiline(require_text(defaults, "recipient_notice")),
        "{{CONTACT_IMAGE_URL}}": html.escape(contact_image_url, quote=True),
        "{{CONTACT_IMAGE_ALT}}": html.escape(
            require_text(defaults, "contact_image_alt"), quote=True
        ),
        "{{COMPANY_NAME}}": html.escape(require_text(defaults, "company_name")),
        "{{DEPARTMENT}}": html.escape(require_text(defaults, "department")),
        "{{CONTACT_NAME}}": html.escape(require_text(defaults, "contact_name")),
        "{{POSTAL_CODE}}": html.escape(require_text(defaults, "postal_code")),
        "{{ADDRESS}}": html.escape(require_text(defaults, "address")),
        "{{EMAIL}}": html.escape(email_address),
        "{{EMAIL_HREF}}": html.escape(f"mailto:{email_address}", quote=True),
        "{{CORPORATE_SITE_URL}}": html.escape(corporate_site_url, quote=True),
    }


def render_large_seminar(
    content: dict, base: str, layout: str, defaults: dict | None = None
) -> str:
    defaults = defaults or load_json(EMAIL_DEFAULTS)
    subject = require_text(content, "subject")
    preheader = require_text(content, "preheader")
    intro = require_list(content, "intro")
    if not all(isinstance(item, str) and item.strip() for item in intro):
        raise ValueError("intro の各項目は空でない文字列で指定してください")
    intro_html = "".join(
        f'<p style="margin:0 0 18px;font-size:16px;line-height:1.9;color:#26354a;">{escaped_multiline(p.strip())}</p>'
        for p in intro
    )

    speakers = require_list(content, "speakers")
    if len(speakers) != 2 or not all(isinstance(s, dict) for s in speakers):
        raise ValueError("large_seminar の speakers は2名のobject配列で指定してください")
    speaker_cells = []
    for index, speaker in enumerate(speakers):
        name, company = require_text(speaker, "name"), require_text(speaker, "company")
        title, subtitle = require_text(speaker, "title"), require_text(speaker, "subtitle")
        photo = image_tag(speaker.get("image"), 244, f"speakers[{index}].image")
        speaker_cells.append(
            '<td class="speaker-column" width="50%" valign="top" style="width:50%;padding:0 8px 20px;">'
            f'{photo}<p style="margin:16px 0 3px;font-size:20px;line-height:1.4;font-weight:700;color:#102a4c;">{html.escape(name)}</p>'
            f'<p style="margin:0 0 16px;font-size:12px;line-height:1.6;color:#657184;">{html.escape(company)}</p>'
            f'<p style="margin:0 0 8px;font-size:17px;line-height:1.55;font-weight:700;color:#102a4c;">{html.escape(title)}</p>'
            f'<p style="margin:0;font-size:13px;line-height:1.7;color:#4b5563;">{html.escape(subtitle)}</p></td>'
        )

    benefits = require_list(content, "benefits")
    if not all(isinstance(item, str) and item.strip() for item in benefits):
        raise ValueError("benefits の各項目は空でない文字列で指定してください")
    benefits_html = "".join(
        f'<tr><td valign="top" style="padding:0 12px 14px 0;font-size:16px;line-height:1.7;font-weight:700;color:#c5a253;">{i:02d}</td>'
        f'<td style="padding:0 0 14px;font-size:15px;line-height:1.7;color:#26354a;">{html.escape(item.strip())}</td></tr>'
        for i, item in enumerate(benefits, 1)
    )

    event_info = content.get("event_info")
    if not isinstance(event_info, dict) or not event_info:
        raise ValueError("event_info は空でないobjectで指定してください")
    event_rows = "".join(
        f'<tr><th width="88" valign="top" align="left" style="padding:9px 12px 9px 0;border-bottom:1px solid #d8dee8;font-size:14px;line-height:1.6;color:#102a4c;">{html.escape(str(k))}</th>'
        f'<td valign="top" style="padding:9px 0;border-bottom:1px solid #d8dee8;font-size:14px;line-height:1.6;color:#26354a;">{html.escape(str(v))}</td></tr>'
        for k, v in event_info.items()
    )
    event_date = require_text(content, "event_date")
    event_note = require_text(content, "event_note")
    cta_data = content.get("cta")
    cta_url = build_cta_url(cta_data)
    cta = cta_table(cta_data)
    banner = image_tag(content.get("banner"), 640, "banner")
    banner_link = (
        f'<a href="{html.escape(cta_url, quote=True)}" style="display:block;text-decoration:none;">'
        f'{banner}</a>'
    )
    layout = fill(layout, {
        "{{BANNER_LINK}}": banner_link,
        "{{BANNER_NOTICE}}": html.escape(require_text(defaults, "banner_notice")),
        "{{INTRO}}": intro_html, "{{EVENT_DATE}}": html.escape(event_date),
        "{{EVENT_NOTE}}": html.escape(event_note), "{{TOP_CTA}}": cta,
        "{{SPEAKERS}}": "".join(speaker_cells), "{{BENEFITS}}": benefits_html,
        "{{EVENT_INFO}}": event_rows, "{{BOTTOM_CTA}}": cta,
    })
    replacements = seminar_base_replacements(defaults)
    replacements.update({"{{TITLE}}": html.escape(subject),
                         "{{PREHEADER}}": html.escape(preheader), "{{CONTENT}}": layout})
    return fill(base, replacements).rstrip() + "\n"


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
        url = build_cta_url(cta)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FIX済み原稿からHTMLメールを生成します（外部通信なし）")
    parser.add_argument("--campaign-slug", required=True)
    parser.add_argument("--content", required=True, type=Path, help="原稿JSON")
    parser.add_argument("--config", default=ROOT / "config" / "zoho.json", type=Path)
    parser.add_argument("--template", type=Path, help="従来形式テンプレートの上書き指定")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def parse_args() -> argparse.Namespace:
    return build_parser().parse_args()


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
        output = ROOT / "campaigns" / args.campaign_slug / "mail.html"
        if output.exists() and not args.overwrite:
            raise ValueError(f"出力先が既に存在します（置換する場合は --overwrite）: {output}")
        template_type = content.get("template_type")
        if template_type is None:
            template = (args.template or DEFAULT_TEMPLATE).read_text(encoding="utf-8")
            built = render(content, template, image_base)
        else:
            if args.template:
                raise ValueError("template_type 指定時は --template を併用できません")
            if template_type not in TEMPLATE_FILES:
                supported = ", ".join(sorted(TEMPLATE_FILES))
                raise ValueError(f"未対応の template_type です: {template_type}（対応: {supported}）")
            base = BASE_TEMPLATE.read_text(encoding="utf-8")
            layout = TEMPLATE_FILES[template_type].read_text(encoding="utf-8")
            built = render_large_seminar(content, base, layout)
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
