"""Regression tests for safe Zoho Campaign draft payload generation."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

        summary = draft.redacted_summary(
            self.config, payload, self.args.campaign_slug, self.args.mailing_list
        )
        self.assertEqual(summary["campaign_slug"], "2026-example")
        for secret_name in (*draft.SECRET_NAMES, "access_token"):
            self.assertNotIn(secret_name, json.dumps(summary))

    def test_environment_secrets_take_priority_over_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text(
                "ZOHO_CLIENT_ID=file-id\n"
                "ZOHO_CLIENT_SECRET=file-secret\n"
                "ZOHO_REFRESH_TOKEN=file-token\n",
                encoding="utf-8",
            )
            environment = {
                "ZOHO_CLIENT_ID": "environment-id",
                "ZOHO_CLIENT_SECRET": "environment-secret",
                "ZOHO_REFRESH_TOKEN": "environment-token",
            }
            with patch.dict(os.environ, environment, clear=True):
                self.assertEqual(draft.load_secrets(env_file), environment)

    def test_dotenv_is_used_when_secret_environment_variables_are_absent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            expected = {
                "ZOHO_CLIENT_ID": "file-id",
                "ZOHO_CLIENT_SECRET": "file-secret",
                "ZOHO_REFRESH_TOKEN": "file-token",
            }
            env_file.write_text(
                "\n".join(f"{key}={value}" for key, value in expected.items()) + "\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(draft.load_secrets(env_file), expected)

    def test_script_contains_only_create_campaign_operation(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertEqual(draft.CREATE_CAMPAIGN_PATH, "/api/v1.1/createCampaign")
        for forbidden in ("sendCampaign", "scheduleCampaign", "campaign.UPDATE"):
            self.assertNotIn(forbidden, source)

    def test_secret_loading_and_summary_have_no_duplicate_legacy_paths(self) -> None:
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        }

        self.assertEqual(
            sum(
                isinstance(node, ast.FunctionDef) and node.name == "redacted_summary"
                for node in tree.body
            ),
            1,
        )
        main_calls = [
            node.func.id
            for node in ast.walk(functions["main"])
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        self.assertEqual(main_calls.count("redacted_summary"), 1)
        self.assertEqual(main_calls.count("load_secrets"), 1)
        self.assertNotIn("load_dotenv", main_calls)


if __name__ == "__main__":
    unittest.main()
