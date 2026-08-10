"""Tests for the Ver.2 campaign safety gate."""
import importlib.util
import html
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("validate_campaign", ROOT / "scripts/validate_campaign.py")
module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(module)


class CampaignValidationTests(unittest.TestCase):
    def setUp(self):
        self.data = module.load_json(ROOT / "campaigns/forum-20260910/campaign.json")
        self.document = (ROOT / "campaigns/forum-20260910/mail.html").read_text(encoding="utf-8")

    def test_checked_in_campaign_passes(self):
        self.assertEqual(module.validate(self.data, self.document), [])

    def test_placeholder_temporary_url_and_secret_are_rejected(self):
        bad = self.document + "{{PLACEHOLDER}} https://example.com ZOHO_CLIENT_SECRET=leaked"
        errors = "\n".join(module.validate(self.data, bad))
        self.assertIn("PLACEHOLDER", errors)
        self.assertIn("仮URL", errors)
        self.assertIn("Secret", errors)

    def test_broken_zoho_tag_and_cta_are_rejected(self):
        bad = self.document.replace(module.ZOHO_TAG, "COMPANY LAST NAME").replace(
            html.escape(module.build_cta_url(self.data["cta"]), quote=True), "https://invalid.test/"
        )
        errors = "\n".join(module.validate(self.data, bad))
        self.assertIn("Zoho", errors)
        self.assertIn("CTA URL", errors)


class GenericSeminarValidationTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "campaign_slug": "generic-seminar", "zoho_campaign_name": "管理名",
            "template_type": "seminar", "preset": "large", "subject": "汎用セミナー",
            "preheader": "ご案内",
            "cta": {"base_url": "https://events.delight-hub.jp/apply", "utm": {
                "source": "newsletter", "medium": "email", "campaign": "confirmed_value"}},
            "blocks": [
                {"type": "hero", "image": {"url": "https://delighthubinc.github.io/zoho-campaign-mail/campaigns/generic-seminar/images/hero.png", "alt": "正式バナー"}},
                {"type": "cta", "label": "申し込む"},
            ],
        }
        self.document = module.__dict__["validate_seminar_data"] and __import__("build_email").render_seminar(
            self.data,
            __import__("build_email").BASE_TEMPLATE.read_text(encoding="utf-8"),
            __import__("build_email").TEMPLATE_FILES["seminar"].read_text(encoding="utf-8"),
        )

    def test_generic_seminar_passes_with_confirmed_utm(self):
        self.assertEqual(module.validate(self.data, self.document), [])

    def test_schema_error_is_reported_by_validator(self):
        self.data["blocks"][1].pop("label")
        errors = "\n".join(module.validate(self.data, self.document))
        self.assertIn("seminar schema", errors)
        self.assertIn("label", errors)


if __name__ == "__main__":
    unittest.main()
