"""HTML email template selection and large seminar regression tests."""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import tempfile
import unittest
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
            build.build_cta_url(self.content["cta"]), self.content["cta"]["label"],
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
        self.assertEqual(len(tags), 3)
        self.assertTrue(all(re.search(r'alt="[^"]+"', tag) for tag in tags))

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
        self.assertEqual(rendered.count(expected), 2)


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
