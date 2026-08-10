"""Regression tests for safe Zoho Campaign draft payload generation."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
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

        self.assertEqual(payload["resfmt"], "json")
        self.assertEqual(
            set(payload),
            {
                "resfmt", "campaignname", "subject", "from_name", "from_email",
                "reply_to", "content_url", "topicId", "list_details",
            },
        )
        encoded_payload = draft.urlencode(payload)
        self.assertEqual(encoded_payload.count("resfmt="), 1)
        self.assertIn("resfmt=json", encoded_payload)
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
        self.assertEqual(summary["resfmt"], "json")
        for secret_name in (*draft.SECRET_NAMES, "access_token"):
            self.assertNotIn(secret_name, json.dumps(summary))

    def test_dry_run_prints_lowercase_resfmt_without_loading_secrets(self) -> None:
        argv = [
            "create_zoho_draft.py", "--campaign-slug", self.args.campaign_slug,
            "--campaign-name", self.args.campaign_name, "--subject", self.args.subject,
            "--mailing-list", self.args.mailing_list[0], "--dry-run",
        ]
        output = StringIO()
        with patch.object(draft.sys, "argv", argv), patch.object(
            draft, "load_secrets", side_effect=AssertionError("must not load secrets")
        ), redirect_stdout(output):
            self.assertEqual(draft.main(), 0)
        self.assertEqual(output.getvalue().count('"resfmt": "json"'), 1)

    def test_defaults_build_the_same_list_details_as_explicit_selection(self) -> None:
        defaults = self.config["default_mailing_lists"]
        default_args = argparse.Namespace(**vars(self.args))
        default_args.mailing_list = defaults

        self.assertEqual(
            draft.build_payload(self.config, default_args)["list_details"],
            draft.build_payload(self.config, self.args)["list_details"],
        )

    def test_numeric_and_string_success_codes_are_accepted(self) -> None:
        for code in (200, "200"):
            with self.subTest(code=code):
                draft.validate_create_response({"code": code})

    def test_numeric_and_string_business_error_codes_are_rejected(self) -> None:
        for code in (1001, "1001"):
            with self.subTest(code=code):
                with self.assertRaises(draft.DraftError) as caught:
                    draft.validate_create_response(
                        {"code": code, "message": "resfmt pattern doesnot match", "uri": draft.CREATE_CAMPAIGN_PATH}
                    )
                message = str(caught.exception)
                self.assertIn(f"provider_code={code}", message)
                self.assertNotIn("resfmt pattern doesnot match", message)
                self.assertNotIn(draft.CREATE_CAMPAIGN_PATH, message)
                self.assertIn("レスポンス本文は出力しません", message)

    def test_only_bounded_safe_provider_codes_are_diagnostic(self) -> None:
        safe = (0, 1001, "1001", "INVALID_TOPIC", "E-42", "code_7")
        for code in safe:
            with self.subTest(code=code):
                self.assertEqual(draft.safe_provider_code(code), str(code))

        unsafe = (
            True, -1, 10**18, "", "x" * 33, "bad code", "bad/code",
            {"echo": "secret"}, [1001], None,
        )
        for code in unsafe:
            with self.subTest(code=code):
                self.assertEqual(draft.safe_provider_code(code), "unavailable")

    def test_business_error_diagnostic_excludes_all_other_provider_fields(self) -> None:
        response = draft.JsonResponse(
            {
                "code": {"unexpected": "provider-code-sensitive"},
                "message": "provider-message-sensitive",
                "uri": "provider-uri-sensitive",
                "request": "request-payload-sensitive",
            },
            200,
        )
        with self.assertRaises(draft.DraftError) as caught:
            draft.validate_create_response(response)
        message = str(caught.exception)
        self.assertIn("transport_http_status=200", message)
        self.assertIn("provider_code=unavailable", message)
        self.assertIn("provider_outcome=non_success", message)
        for forbidden in (
            "provider-code-sensitive", "provider-message-sensitive",
            "provider-uri-sensitive", "request-payload-sensitive",
        ):
            self.assertNotIn(forbidden, message)

    def test_provider_code_matching_oauth_value_is_not_logged(self) -> None:
        oauth_value = "oauth-token-sensitive"
        with self.assertRaises(draft.DraftError) as caught:
            draft.validate_create_response({"code": oauth_value}, (oauth_value,))
        self.assertIn("provider_code=unavailable", str(caught.exception))
        self.assertNotIn(oauth_value, str(caught.exception))

    def test_api_error_exit_is_one_and_all_oauth_values_are_redacted(self) -> None:
        secrets = {
            "ZOHO_CLIENT_ID": "client-id-sensitive",
            "ZOHO_CLIENT_SECRET": "client-secret-sensitive",
            "ZOHO_REFRESH_TOKEN": "refresh-token-sensitive",
        }
        token = "access-token-sensitive"
        response = {
            "code": 1001,
            "message": " ".join((*secrets.values(), token)),
            "uri": draft.CREATE_CAMPAIGN_PATH,
        }
        argv = [
            "create_zoho_draft.py", "--campaign-slug", self.args.campaign_slug,
            "--campaign-name", self.args.campaign_name, "--subject", self.args.subject,
            "--mailing-list", self.args.mailing_list[0],
        ]
        stdout, stderr = StringIO(), StringIO()
        with patch.object(draft.sys, "argv", argv), patch.object(
            draft, "load_secrets", return_value=secrets
        ), patch.object(draft, "access_token", return_value=token), patch.object(
            draft, "request_json", return_value=response
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(draft.main(), 1)

        combined = stdout.getvalue() + stderr.getvalue()
        for secret in (*secrets.values(), token):
            self.assertNotIn(secret, combined)
        self.assertIn("provider_code=1001", combined)
        self.assertNotIn("access-token-sensitive", combined)
        for payload_value in (
            self.args.campaign_name, self.args.subject,
            self.config["from"]["email"], self.config["topic"]["id"],
        ):
            self.assertNotIn(payload_value, combined)

    def test_oauth_error_body_is_not_logged(self) -> None:
        oauth_value = "oauth-provider-body-sensitive"
        with patch.object(
            draft, "request_json", return_value={"error": oauth_value}
        ):
            with self.assertRaises(draft.DraftError) as caught:
                draft.access_token(self.config, {
                    "ZOHO_CLIENT_ID": "id", "ZOHO_CLIENT_SECRET": "secret",
                    "ZOHO_REFRESH_TOKEN": "refresh",
                })
        self.assertNotIn(oauth_value, str(caught.exception))

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

    def test_response_body_is_never_printed_and_cli_options_are_unique(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("json.dumps(result", source)
        self.assertNotIn("message={safe_value", source)
        tree = ast.parse(source)
        options = [
            node.args[0].value
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_argument"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
            and node.args[0].value.startswith("--")
        ]
        self.assertEqual(len(options), len(set(options)), options)
        self.assertEqual(
            set(options),
            {"--config", "--env-file", "--campaign-file", "--campaign-slug",
             "--campaign-name", "--subject", "--mailing-list", "--dry-run"},
        )


if __name__ == "__main__":
    unittest.main()
