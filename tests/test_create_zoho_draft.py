"""Regression tests for safe Zoho Campaign draft payload generation."""

from __future__ import annotations

import argparse
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "create_zoho_draft.py"
SPEC = importlib.util.spec_from_file_location("create_zoho_draft", MODULE_PATH)
assert SPEC and SPEC.loader
draft = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(draft)


class DraftPayloadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = draft.load_json(ROOT / "config" / "zoho.json")
        self.args = argparse.Namespace(
            campaign_slug="2026-example",
            campaign_name="テストDraft",
            subject="テスト件名",
            mailing_list=["過去リスト（新）", "CRMから連携されたリスト"],
        )

    def test_two_lists_are_object_keys_with_empty_array_values(self) -> None:
        draft.validate_config(self.config)
        payload = draft.build_payload(self.config, self.args)

        self.assertEqual(
            json.loads(payload["list_details"]),
            {
                "3zed9d3e291d576c454137d73c7861ad5f164ac0b4207463f0d7d28a805d92174b": [],
                "3zfc1d61d9ab39d57f34714cbbe3a168f99d03784995392a08a00ca40669125b59": [],
            },
        )

    def test_operational_fixed_values_and_content_url(self) -> None:
        payload = draft.build_payload(self.config, self.args)

        self.assertEqual(payload["topicId"], "17155000000008017")
        self.assertEqual(payload["from_name"], "天野晴香／株式会社Delight Hub")
        self.assertEqual(payload["from_email"], "h-amano01@delight-hub.jp")
        self.assertEqual(payload["reply_to"], "h-amano01@delight-hub.jp")
        self.assertEqual(
            payload["content_url"],
            "https://delighthubinc.github.io/zoho-campaign-mail/campaigns/2026-example/mail.html",
        )


if __name__ == "__main__":
    unittest.main()
