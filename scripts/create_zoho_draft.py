#!/usr/bin/env python3
"""Create a Zoho Campaigns draft using only the createCampaign API."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
SECRET_NAMES = ("ZOHO_CLIENT_ID", "ZOHO_CLIENT_SECRET", "ZOHO_REFRESH_TOKEN")
CREATE_CAMPAIGN_PATH = "/api/v1.1/createCampaign"
TIMEOUT_SECONDS = 30
SAFE_PROVIDER_CODE_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


class DraftError(Exception):
    """A safe, user-facing validation or API error."""


class JsonResponse(dict):
    """Parsed JSON plus transport metadata that never includes the raw body."""

    def __init__(self, value: dict, http_status: int | None) -> None:
        super().__init__(value)
        self.http_status = http_status


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DraftError(f"設定JSONを読み込めません: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DraftError("設定JSONのルートはobjectである必要があります")
    return value


def load_dotenv(path: Path) -> dict[str, str]:
    """Read a deliberately small .env subset without adding a dependency."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise DraftError(f".envを読み込めません: {path}: {exc}") from exc
    values: dict[str, str] = {}
    for number, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise DraftError(f".envの{number}行目が KEY=VALUE 形式ではありません")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values


def load_secrets(env_file: Path) -> dict[str, str]:
    """Load OAuth values from the environment, falling back to .env locally."""
    secrets = {name: os.environ.get(name, "") for name in SECRET_NAMES}
    if any(not value for value in secrets.values()):
        dotenv_values = load_dotenv(env_file) if env_file.is_file() else {}
        secrets = {
            name: value or dotenv_values.get(name, "")
            for name, value in secrets.items()
        }
    missing = [name for name, value in secrets.items() if not value]
    if missing:
        raise DraftError("環境変数または.envに必要な値がありません: " + ", ".join(missing))
    return secrets


def require_text(data: dict, key: str, context: str = "設定") -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise DraftError(f"{context}.{key} は空でない文字列で指定してください")
    return value.strip()


def reject_placeholder(value: str, label: str) -> None:
    if value.startswith("REPLACE_"):
        raise DraftError(f"{label} を実運用値へ置き換えてください")


def validate_config(config: dict) -> None:
    token_url = require_text(config, "accounts_token_url")
    base_url = require_text(config, "campaigns_base_url")
    pages_url = require_text(config, "github_pages_base_url")
    if token_url != "https://accounts.zoho.jp/oauth/v2/token":
        raise DraftError("accounts_token_url は https://accounts.zoho.jp/oauth/v2/token に固定してください")
    if base_url.rstrip("/") != "https://campaigns.zoho.jp":
        raise DraftError("campaigns_base_url は https://campaigns.zoho.jp に固定してください")
    parsed_pages = urlparse(pages_url)
    if parsed_pages.scheme != "https" or not parsed_pages.netloc.endswith("github.io"):
        raise DraftError("github_pages_base_url は github.io のHTTPS URLで指定してください")

    sender = config.get("from")
    topic = config.get("topic")
    lists = config.get("mailing_lists")
    if not isinstance(sender, dict) or not isinstance(topic, dict):
        raise DraftError("from と topic はobjectで指定してください")
    require_text(sender, "name", "from")
    from_email = require_text(sender, "email", "from")
    reply_to = require_text(config, "reply_to")
    if not EMAIL_RE.fullmatch(from_email) or not EMAIL_RE.fullmatch(reply_to):
        raise DraftError("from.email または reply_to のメールアドレス形式が不正です")
    require_text(topic, "name", "topic")
    topic_id = require_text(topic, "id", "topic")
    reject_placeholder(topic_id, "topic.id")
    if not isinstance(lists, dict) or not lists:
        raise DraftError("mailing_lists は「リスト名: listkey」の空でないobjectで指定してください")
    for name, listkey in lists.items():
        if not isinstance(name, str) or not name.strip() or not isinstance(listkey, str) or not listkey.strip():
            raise DraftError("mailing_lists のリスト名とlistkeyは空でない文字列にしてください")
        reject_placeholder(listkey.strip(), f"mailing_lists.{name}")


def content_url(config: dict, slug: str) -> str:
    base = require_text(config, "github_pages_base_url").rstrip("/") + "/"
    result = urljoin(base, f"campaigns/{slug}/mail.html")
    base_parsed, result_parsed = urlparse(base), urlparse(result)
    if result_parsed.netloc != base_parsed.netloc or not result_parsed.path.startswith(base_parsed.path):
        raise DraftError("content_url がGitHub Pagesの設定パス外です")
    return result


def build_payload(config: dict, args: argparse.Namespace) -> dict[str, str]:
    selected_names = args.mailing_list
    if len(selected_names) != len(set(selected_names)):
        raise DraftError("--mailing-list が重複しています")
    configured_lists: dict = config["mailing_lists"]
    unknown = [name for name in selected_names if name not in configured_lists]
    if unknown:
        raise DraftError("未設定の配信リストです: " + ", ".join(unknown))
    # Zoho expects each listkey as a property whose value is an empty array.
    # It does not accept {"listkey": ["key1", "key2"]} for this endpoint.
    list_details = {configured_lists[name]: [] for name in selected_names}
    return {
        "resfmt": "json",
        "campaignname": args.campaign_name.strip(),
        "subject": args.subject.strip(),
        "from_name": config["from"]["name"],
        "from_email": config["from"]["email"],
        "reply_to": config["reply_to"],
        "content_url": content_url(config, args.campaign_slug),
        "topicId": config["topic"]["id"],
        "list_details": json.dumps(list_details, ensure_ascii=False, separators=(",", ":")),
    }


def request_json(url: str, data: dict[str, str], headers: dict[str, str] | None = None) -> dict:
    request = Request(
        url,
        data=urlencode(data).encode("utf-8"),
        headers={"Accept": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            http_status = response.status
            raw = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        # Do not print the response body: providers can echo sensitive request data.
        raise DraftError(f"APIがHTTP {exc.code}を返しました: {urlparse(url).netloc}{urlparse(url).path}") from exc
    except URLError as exc:
        raise DraftError(f"APIへ接続できません: {urlparse(url).netloc}: {exc.reason}") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DraftError("APIレスポンスがJSONではありません") from exc
    if not isinstance(value, dict):
        raise DraftError("APIレスポンスの形式が不正です")
    return JsonResponse(value, http_status)


def access_token(config: dict, secrets: dict[str, str]) -> str:
    response = request_json(
        config["accounts_token_url"],
        {
            "grant_type": "refresh_token",
            "client_id": secrets["ZOHO_CLIENT_ID"],
            "client_secret": secrets["ZOHO_CLIENT_SECRET"],
            "refresh_token": secrets["ZOHO_REFRESH_TOKEN"],
        },
    )
    token = response.get("access_token")
    if not isinstance(token, str) or not token:
        # OAuth provider fields are untrusted and can contain echoed secrets.
        raise DraftError("Access Tokenを取得できませんでした: oauth_error=unavailable")
    return token


def redacted_summary(
    config: dict, payload: dict[str, str], campaign_slug: str, selected_lists: list[str]
) -> dict:
    return {
        "operation": "createCampaign (Draft作成のみ)",
        "endpoint": config["campaigns_base_url"].rstrip("/") + CREATE_CAMPAIGN_PATH,
        "resfmt": payload["resfmt"],
        "campaign_slug": campaign_slug,
        "campaignname": payload["campaignname"],
        "subject": payload["subject"],
        "from_name": payload["from_name"],
        "from_email": payload["from_email"],
        "reply_to": payload["reply_to"],
        "topic": config["topic"],
        "mailing_lists": selected_lists,
        "list_details": json.loads(payload["list_details"]),
        "content_url": payload["content_url"],
    }


def safe_provider_code(value: object, sensitive_values: tuple[str, ...] = ()) -> str:
    """Return only a bounded provider code, never arbitrary response content."""
    if isinstance(value, bool):
        return "unavailable"
    if isinstance(value, int):
        candidate = str(value)
        if value < 0 or len(candidate) > 18:
            return "unavailable"
    elif isinstance(value, str) and SAFE_PROVIDER_CODE_RE.fullmatch(value):
        candidate = value
    else:
        return "unavailable"
    if any(candidate == secret for secret in sensitive_values if secret):
        return "unavailable"
    return candidate


def safe_http_status(value: object) -> str:
    """Format a real HTTP status without accepting arbitrary provider content."""
    return str(value) if isinstance(value, int) and not isinstance(value, bool) and 100 <= value <= 599 else "unavailable"


def validate_create_response(response: dict, sensitive_values: tuple[str, ...] = ()) -> None:
    """Reject business errors with only allowlisted, bounded diagnostics."""
    code = response.get("code")
    if code in (200, "200"):
        return
    http_status = safe_http_status(getattr(response, "http_status", None))
    provider_code = safe_provider_code(code, sensitive_values)
    raise DraftError(
        "Zoho Campaigns APIがDraft作成エラーを返しました（レスポンス本文は出力しません）\n"
        f"transport_http_status={http_status}\n"
        f"provider_code={provider_code}\n"
        "provider_outcome=non_success"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="createCampaign APIだけを使ってZoho Campaigns Draftを作成します")
    parser.add_argument("--config", default=ROOT / "config" / "zoho.json", type=Path)
    parser.add_argument("--env-file", default=ROOT / ".env", type=Path)
    parser.add_argument("--campaign-file", type=Path, help="slug/name/subjectを取得するcampaign.json")
    parser.add_argument("--campaign-slug")
    parser.add_argument("--campaign-name")
    parser.add_argument("--subject")
    parser.add_argument("--mailing-list", action="append", help="省略時は設定のdefault_mailing_lists")
    parser.add_argument("--dry-run", action="store_true", help="OAuth通信もDraft作成も行わず設定だけを検証")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_json(args.config)
        validate_config(config)
        if args.campaign_file:
            campaign = load_json(args.campaign_file)
            args.campaign_slug = require_text(campaign, "campaign_slug", "campaign")
            args.campaign_name = require_text(campaign, "zoho_campaign_name", "campaign")
            args.subject = require_text(campaign, "subject", "campaign")
        if not args.mailing_list:
            defaults = config.get("default_mailing_lists")
            if not isinstance(defaults, list) or not defaults or not all(isinstance(x, str) and x for x in defaults):
                raise DraftError("default_mailing_listsを空でない文字列配列で設定してください")
            args.mailing_list = defaults
        if not isinstance(args.campaign_slug, str) or not SLUG_RE.fullmatch(args.campaign_slug):
            raise DraftError("campaign-slug は小文字英数字とハイフン（最大80文字）で指定してください")
        if not isinstance(args.campaign_name, str) or not isinstance(args.subject, str) or not args.campaign_name.strip() or not args.subject.strip():
            raise DraftError("campaign-name と subject は空にできません")
        payload = build_payload(config, args)
        if args.dry_run:
            print(
                json.dumps(
                    redacted_summary(config, payload, args.campaign_slug, args.mailing_list),
                    ensure_ascii=False,
                    indent=2,
                )
            )
            print("dry-run: 外部通信は行っていません。")
            return 0

        print("operation=createCampaign_draft_only")
        secrets = load_secrets(args.env_file)
        token = access_token(config, secrets)
        endpoint = config["campaigns_base_url"].rstrip("/") + CREATE_CAMPAIGN_PATH
        result = request_json(endpoint, payload, {"Authorization": f"Zoho-oauthtoken {token}"})
        validate_create_response(result, tuple(secrets.values()) + (token,))
        print("Zoho Campaigns Draftを作成しました。")
        return 0
    except DraftError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
