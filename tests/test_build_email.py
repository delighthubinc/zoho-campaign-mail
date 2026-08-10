"""HTML email template selection and large seminar regression tests."""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import tempfile
import unittest
from html import escape as html_escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_email", ROOT / "scripts" / "build_email.py")
assert SPEC and SPEC.loader
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


class LargeSeminarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.content = build.load_json(ROOT / "campaigns/forum-20260910/campaign.json")
        cls.rendered = build.render_large_seminar(
            cls.content,
            build.BASE_TEMPLATE.read_text(encoding="utf-8"),
            build.TEMPLATE_FILES["large_seminar"].read_text(encoding="utf-8"),
        )

    def test_template_type_selects_large_seminar(self) -> None:
        self.assertEqual(self.content["template_type"], "large_seminar")
        self.assertIn("large_seminar", build.TEMPLATE_FILES)

    def test_required_copy_and_links_are_rendered(self) -> None:
        for value in (
            self.content["subject"], *self.content["intro"],
            self.content["speakers"][0]["name"], self.content["speakers"][1]["name"],
            html_escape(build.build_cta_url(self.content["cta"])), self.content["cta"]["label"],
        ):
            self.assertIn(value, self.rendered)
        for image in (self.content["banner"], *(s["image"] for s in self.content["speakers"])):
            self.assertIn(image["url"], self.rendered)

    def test_email_contains_no_forbidden_active_or_external_content(self) -> None:
        self.assertIsNone(re.search(r"<\s*(script|form)\b", self.rendered, re.IGNORECASE))
        self.assertIsNone(re.search(r"<link\b[^>]*rel=[\"']?stylesheet", self.rendered, re.IGNORECASE))
        self.assertNotIn("javascript:", self.rendered.lower())

    def test_every_image_has_nonempty_alt(self) -> None:
        tags = re.findall(r"<img\b[^>]*>", self.rendered, re.IGNORECASE)
        self.assertEqual(len(tags), 5)
        self.assertTrue(all(re.search(r'alt="[^"]+"', tag) for tag in tags))

    def test_seminar_common_branding_and_recipient_copy(self) -> None:
        defaults = build.load_json(build.EMAIL_DEFAULTS)
        self.assertEqual(self.rendered.count(defaults["logo_url"]), 1)
        self.assertEqual(self.rendered.count(defaults["contact_image_url"]), 1)
        self.assertIn("$[UD:COMPANY_NAME||]$　$[UD:LAST_NAME||]$様", self.rendered)
        self.assertNotIn("$[UD:COMPANY_NAME&#x27;", self.rendered)
        for line in defaults["recipient_notice"].splitlines():
            self.assertIn(line, self.rendered)
        self.assertIn('href="mailto:contact@delight-hub.jp"', self.rendered)
        self.assertIn('href="https://delight-hub.jp/"', self.rendered)
        self.assertIn("企画部 天野 晴香", self.rendered)

    def test_banner_links_to_the_exact_same_url_as_ctas(self) -> None:
        self.assertEqual(
            build.build_cta_url(self.content["cta"]),
            "https://realestate-future-forum.studio.site/"
            "?utm_source=delighthub&utm_medium=email&utm_campaign=20260910",
        )
        expected_href = html_escape(build.build_cta_url(self.content["cta"]))
        raw_banner_url = self.content["banner"]["url"]
        banner_url = re.escape(raw_banner_url)
        self.assertEqual(self.rendered.count(raw_banner_url), 1)
        self.assertRegex(
            self.rendered,
            rf'<a href="{re.escape(expected_href)}"[^>]*>\s*<img src="{banner_url}"',
        )
        self.assertEqual(self.rendered.count(f'href="{expected_href}"'), 3)
        self.assertIn("※バナーをクリックすると、イベントページに遷移します。", self.rendered)

    def test_common_blocks_are_unique_and_in_the_required_order(self) -> None:
        defaults = build.load_json(build.EMAIL_DEFAULTS)
        recipient = defaults["zoho_recipient"]
        banner_url = self.content["banner"]["url"]
        banner_notice = defaults["banner_notice"]
        signature_start = "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="

        self.assertEqual(self.rendered.count(defaults["logo_url"]), 1)
        self.assertEqual(self.rendered.count(recipient), 1)
        self.assertEqual(self.rendered.count(banner_url), 1)
        self.assertEqual(self.rendered.count(defaults["contact_image_url"]), 1)
        self.assertEqual(self.rendered.count(defaults["company_name"]), 1)
        self.assertEqual(self.rendered.count(signature_start), 2)
        self.assertNotIn("お問い合わせ：", self.rendered)
        self.assertNotIn("{{FOOTER}}", self.rendered)

        positions = [
            self.rendered.index(defaults["logo_url"]),
            self.rendered.index(recipient),
            self.rendered.index(defaults["recipient_notice"].splitlines()[1]),
            self.rendered.index(banner_url),
            self.rendered.index(banner_notice),
            self.rendered.index(self.content["intro"][0]),
            self.rendered.index(defaults["contact_image_url"]),
        ]
        self.assertEqual(positions, sorted(positions))

    def test_seminar_templates_have_no_legacy_banner_or_footer_placeholder(self) -> None:
        base = build.BASE_TEMPLATE.read_text(encoding="utf-8")
        layout = build.TEMPLATE_FILES["large_seminar"].read_text(encoding="utf-8")
        self.assertNotIn("{{BANNER}}", base + layout)
        self.assertNotIn("{{FOOTER}}", base + layout)
        self.assertNotIn("お問い合わせ：", base + layout)

    def test_checked_in_forum_html_matches_current_generator(self) -> None:
        checked_in = (ROOT / "campaigns/forum-20260910/mail.html").read_text(encoding="utf-8")
        self.assertEqual(checked_in, self.rendered)

    def test_common_information_is_not_duplicated_in_campaign_data(self) -> None:
        for key in ("company_name", "department", "contact_name", "postal_code",
                    "address", "logo_url", "contact_image_url", "zoho_recipient",
                    "recipient_notice"):
            self.assertNotIn(key, self.content)

    def test_campaign_json_is_serializable_without_html_fragments(self) -> None:
        serialized = json.dumps(self.content, ensure_ascii=False)
        self.assertNotIn("<table", serialized.lower())

    def test_template_option_is_registered_once(self) -> None:
        template_actions = [
            action for action in build.build_parser()._actions
            if "--template" in action.option_strings
        ]
        self.assertEqual(len(template_actions), 1)

    def test_large_seminar_renders_structured_cta_with_utm(self) -> None:
        content = copy.deepcopy(self.content)
        content["cta"] = {
            "label": "無料で参加申し込み",
            "base_url": "https://events.example.jp/forum?plan=free#apply",
            "utm": {"source": "zoho", "medium": "email", "campaign": "forum_20260910"},
        }
        rendered = build.render_large_seminar(
            content,
            build.BASE_TEMPLATE.read_text(encoding="utf-8"),
            build.TEMPLATE_FILES["large_seminar"].read_text(encoding="utf-8"),
        )
        expected = "https://events.example.jp/forum?plan=free&amp;utm_source=zoho&amp;utm_medium=email&amp;utm_campaign=forum_20260910#apply"
        self.assertEqual(rendered.count(expected), 3)


class SeminarBlockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.content = {
            "campaign_slug": "generic-seminar",
            "zoho_campaign_name": "汎用セミナー管理名",
            "template_type": "seminar",
            "preset": "standard",
            "subject": "汎用セミナー",
            "preheader": "セミナーのご案内",
            "cta": {
                "label": "申し込む",
                "base_url": "https://events.example.jp/apply",
                "utm": {"source": "zoho", "medium": "email", "campaign": "generic_seminar"},
            },
            "blocks": [
                {"type": "hero", "image": {"url": "https://example.github.io/repo/campaigns/generic-seminar/images/hero.png", "alt": "セミナーバナー"}},
                {"type": "text", "heading": "ご案内", "paragraphs": ["最初の本文"]},
                {"type": "event_date", "date": "2026年10月1日", "note": "オンライン"},
                {"type": "benefits", "items": ["実務に役立つ"]},
                {"type": "speaker", "name": "講師 太郎", "company": "講師株式会社", "title": "最新講演", "image": {"url": "https://example.github.io/repo/speaker.jpg", "alt": "講師太郎"}},
                {"type": "cta", "label": "無料で申し込む"},
                {"type": "event_info", "items": {"日時": "2026年10月1日", "形式": "オンライン"}},
            ],
        }

    def render(self, content=None):
        return build.render_seminar(
            content or self.content,
            build.BASE_TEMPLATE.read_text(encoding="utf-8"),
            build.TEMPLATE_FILES["seminar"].read_text(encoding="utf-8"),
        )

    def keynote_block(self):
        return {"type": "keynote_speakers", "heading": "注目の基調講演", "speakers": [{
            "name": "基調 花子", "company": "未来株式会社", "title": "未来の展望",
            "image": {"url": "https://example.github.io/repo/keynote.jpg", "alt": "基調花子"},
        }]}

    def test_standard_and_large_presets_generate(self):
        for preset in ("standard", "large"):
            with self.subTest(preset=preset):
                content = copy.deepcopy(self.content); content["preset"] = preset
                self.assertIn("汎用セミナー", self.render(content))
        without_preset = copy.deepcopy(self.content); without_preset.pop("preset")
        self.assertIn("汎用セミナー", self.render(without_preset))

    def test_blocks_render_in_array_order(self):
        rendered = self.render()
        markers = ["セミナーバナー", "最初の本文", "2026年10月1日", "実務に役立つ", "講師 太郎", "無料で申し込む", "開催概要"]
        positions = [rendered.index(marker) for marker in markers]
        self.assertEqual(positions, sorted(positions))

    def test_removing_block_removes_its_output(self):
        content = copy.deepcopy(self.content)
        content["blocks"] = [b for b in content["blocks"] if b["type"] != "benefits"]
        self.assertNotIn("実務に役立つ", self.render(content))

    def test_large_does_not_force_keynotes(self):
        content = copy.deepcopy(self.content); content["preset"] = "large"
        self.assertNotIn("KEYNOTE SPEAKERS", self.render(content))
        self.assertNotIn("基調講演", self.render(content))

    def test_standard_can_add_keynotes(self):
        content = copy.deepcopy(self.content); content["blocks"].insert(2, self.keynote_block())
        self.assertIn("基調 花子", self.render(content))

    def test_session_cards_and_optional_keynote_badge(self):
        content = copy.deepcopy(self.content)
        content["blocks"] = [{"type": "session_cards", "sessions": [
            {"time": "10:00", "company": "A社", "title": "基調セッション", "keynote": True},
            {"time": "11:00", "company": "B社", "title": "通常セッション"},
        ]}]
        rendered = self.render(content)
        self.assertIn('<table role="presentation"', rendered)
        self.assertLess(rendered.index("10:00"), rendered.index("A社"))
        self.assertLess(rendered.index("A社"), rendered.index("基調セッション"))
        self.assertEqual(rendered.count(">基調講演</span>"), 1)

    def test_text_is_escaped_and_arbitrary_html_field_is_rejected(self):
        content = copy.deepcopy(self.content)
        content["blocks"] = [{"type": "text", "paragraphs": ["<script>alert('x')</script> & 本文"]}]
        rendered = self.render(content)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn("<script>", rendered)
        content["blocks"][0]["html"] = "<b>自由HTML</b>"
        with self.assertRaisesRegex(ValueError, "未対応のfield"):
            self.render(content)

    def test_invalid_block_type_and_missing_required_field_fail(self):
        for block, message in (({"type": "free_html"}, "未対応"), ({"type": "session_cards", "sessions": [{"time": "10:00", "company": "A社"}]}, "title")):
            with self.subTest(block=block):
                content = copy.deepcopy(self.content); content["blocks"] = [block]
                with self.assertRaisesRegex(ValueError, message):
                    self.render(content)

    def test_utm_builder_is_shared_by_hero_and_cta_blocks(self):
        rendered = self.render()
        expected = html_escape(build.build_cta_url(self.content["cta"]))
        self.assertEqual(rendered.count(f'href="{expected}"'), 2)


class LegacyTemplateTests(unittest.TestCase):
    def test_content_without_template_type_uses_legacy_renderer(self) -> None:
        content = {
            "preheader": "従来形式プレビュー",
            "heading": "従来形式セミナー",
            "hero_image": {"filename": "banner.png", "alt": "従来形式バナー"},
            "paragraphs": ["従来形式の本文です。"],
            "cta": {"label": "詳細を見る", "url": "https://example.jp/event"},
            "footer": "株式会社Delight Hub",
        }
        self.assertNotIn("template_type", content)
        rendered = build.render(
            content,
            build.DEFAULT_TEMPLATE.read_text(encoding="utf-8"),
            "https://example.github.io/repo/campaigns/legacy/images/",
        )
        self.assertIn("従来形式セミナー", rendered)
        self.assertIn("https://example.github.io/repo/campaigns/legacy/images/banner.png", rendered)
        self.assertNotRegex(rendered, build.PLACEHOLDER_RE)

    def test_help_can_be_rendered(self) -> None:
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as output:
            build.build_parser().print_help(output)
            output.seek(0)
            help_text = output.read()
        self.assertIn("--template TEMPLATE", help_text)
        self.assertIn("--campaign-slug CAMPAIGN_SLUG", help_text)


class CtaUrlTests(unittest.TestCase):
    def test_url_without_utm_is_unchanged(self) -> None:
        cta = {"label": "詳細", "base_url": "https://events.example.jp/apply"}
        self.assertEqual(build.build_cta_url(cta), cta["base_url"])

    def test_url_with_utm(self) -> None:
        result = build.build_cta_url({
            "label": "詳細",
            "base_url": "https://events.example.jp/apply",
            "utm": {"source": "zoho", "medium": "email", "campaign": "forum_20260910"},
        })
        self.assertEqual(
            result,
            "https://events.example.jp/apply?utm_source=zoho&utm_medium=email&utm_campaign=forum_20260910",
        )

    def test_existing_query_is_preserved(self) -> None:
        result = build.build_cta_url({
            "base_url": "https://events.example.jp/apply?plan=free&lang=ja",
            "utm": {"source": "zoho", "medium": "email", "campaign": "forum_20260910"},
        })
        self.assertIn("plan=free&lang=ja&utm_source=zoho", result)

    def test_values_are_url_encoded(self) -> None:
        result = build.build_cta_url({
            "base_url": "https://events.example.jp/apply",
            "utm": {"source": "ゾーホー", "medium": "メール", "campaign": "秋 フォーラム"},
        })
        self.assertIn("utm_source=%E3%82%BE%E3%83%BC%E3%83%9B%E3%83%BC", result)
        self.assertIn("utm_campaign=%E7%A7%8B+%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A9%E3%83%A0", result)

    def test_query_is_inserted_before_fragment(self) -> None:
        result = build.build_cta_url({
            "base_url": "https://events.example.jp/apply#form",
            "utm": {"source": "zoho", "medium": "email", "campaign": "forum_20260910"},
        })
        self.assertEqual(result.split("#"), [
            "https://events.example.jp/apply?utm_source=zoho&utm_medium=email&utm_campaign=forum_20260910",
            "form",
        ])

    def test_optional_content_can_distinguish_placements(self) -> None:
        cta = {
            "base_url": "https://events.example.jp/apply",
            "utm": {"source": "zoho", "medium": "email", "campaign": "forum_20260910"},
        }
        self.assertIn("utm_content=hero_cta", build.build_cta_url(cta, "hero_cta"))
        self.assertIn("utm_content=bottom_cta", build.build_cta_url(cta, "bottom_cta"))
        self.assertNotIn("utm_content", build.build_cta_url(cta))

    def test_invalid_placeholder_and_empty_urls_are_rejected(self) -> None:
        for url in ("not-a-url", "#", ""):
            with self.subTest(url=url), self.assertRaises(ValueError):
                build.build_cta_url({"url": url})

    def test_legacy_completed_url_remains_supported(self) -> None:
        cta = {"label": "詳細を見る", "url": "https://events.example.jp/apply?ref=legacy"}
        self.assertEqual(build.build_cta_url(cta), cta["url"])
        rendered = build.render(
            {"heading": "従来形式", "paragraphs": ["本文"], "cta": cta},
            build.DEFAULT_TEMPLATE.read_text(encoding="utf-8"),
            "https://example.github.io/repo/campaigns/legacy/images/",
        )
        self.assertIn("https://events.example.jp/apply?ref=legacy", rendered)


if __name__ == "__main__":
    unittest.main()
