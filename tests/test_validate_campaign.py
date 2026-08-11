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

    def test_unknown_content_source_is_rejected_fail_closed(self):
        self.data["content_source"] = "generated"
        self.assertIn("fixed_html", "\n".join(module.validate(self.data, self.document)))

    def test_broken_zoho_tag_and_cta_are_rejected(self):
        bad = self.document.replace(module.ZOHO_TAG, "COMPANY LAST NAME").replace(
            html.escape(module.build_cta_url(self.data["cta"]), quote=True), "https://invalid.test/"
        )
        errors = "\n".join(module.validate(self.data, bad))
        self.assertIn("Zoho", errors)
        self.assertIn("CTA", errors)

    def test_utm_mismatch_is_rejected(self):
        expected = html.escape(module.build_cta_url(self.data["cta"]), quote=True)
        bad = self.document.replace(expected, expected.replace("utm_campaign=20260910", "utm_campaign=wrong"))
        self.assertIn("UTM", "\n".join(module.validate(self.data, bad)))

    def test_missing_campaign_and_common_images_are_rejected(self):
        campaign_image = self.data["images"][0]["url"]
        defaults = module.load_json(module.EMAIL_DEFAULTS)
        bad = self.document.replace(campaign_image, "https://invalid.test/missing.png")
        bad = bad.replace(defaults["logo_url"], "https://invalid.test/logo.png")
        errors = "\n".join(module.validate(self.data, bad))
        self.assertIn("campaign画像URL", errors)
        self.assertIn("共通画像 logo_url", errors)

    def test_common_footer_must_match_email_defaults(self):
        defaults = module.load_json(module.EMAIL_DEFAULTS)
        bad = self.document.replace(defaults["contact_name"], "立原")
        errors = "\n".join(module.validate(self.data, bad))
        self.assertIn("共通署名 contact_name", errors)

    def test_javascript_and_empty_links_are_rejected(self):
        bad = self.document.replace("</body>", '<script>alert(1)</script><a href="#">bad</a></body>')
        errors = "\n".join(module.validate(self.data, bad))
        self.assertIn("JavaScript", errors)
        self.assertIn("空または#", errors)

    def test_empty_html_is_rejected(self):
        self.assertIn("空", "\n".join(module.validate(self.data, "")))


class GenericSeminarValidationTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "campaign_slug": "generic-seminar", "zoho_campaign_name": "管理名",
            "template_type": "seminar", "preset": "large", "subject": "汎用セミナー",
            "content_source": "fixed_html",
            "preheader": "ご案内",
            "cta": {"label": "申し込む", "base_url": "https://events.delight-hub.jp/apply", "utm": {
                "source": "newsletter", "medium": "email", "campaign": "confirmed_value"}},
            "blocks": [
                {"type": "hero", "image": {"url": "https://delighthubinc.github.io/zoho-campaign-mail/campaigns/generic-seminar/images/hero.png", "alt": "正式バナー"}},
                {"type": "cta", "label": "申し込む"},
            ],
        }
        self.data["images"] = [self.data["blocks"][0]["image"]]
        self.document = __import__("build_email").render_seminar(
            self.data,
            __import__("build_email").BASE_TEMPLATE.read_text(encoding="utf-8"),
            __import__("build_email").TEMPLATE_FILES["seminar"].read_text(encoding="utf-8"),
        )

    def test_generic_seminar_passes_with_confirmed_utm(self):
        self.assertEqual(module.validate(self.data, self.document), [])

    def test_blocks_are_not_treated_as_html_generation_source(self):
        self.data["blocks"][1].pop("label")
        self.assertEqual(module.validate(self.data, self.document), [])


if __name__ == "__main__":
    unittest.main()
