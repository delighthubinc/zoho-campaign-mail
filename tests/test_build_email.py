"""HTML email template selection and large seminar regression tests."""

from __future__ import annotations

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
            self.content["cta"]["url"], self.content["cta"]["label"],
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


if __name__ == "__main__":
    unittest.main()
