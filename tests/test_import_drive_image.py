import unittest
from pathlib import Path

from scripts.import_drive_image import detected_image_type, destination_for, response_content_type


class ImportDriveImageTests(unittest.TestCase):
    def test_valid_destination(self):
        self.assertEqual(
            destination_for("forum-20260910", "banner.png"),
            Path("campaigns/forum-20260910/images/banner.png"),
        )

    def test_rejects_unsafe_slugs(self):
        for slug in ("", "../outside", "one/two", "..", "campaign..backup", "/tmp"):
            with self.subTest(slug=slug), self.assertRaises(ValueError):
                destination_for(slug, "banner.png")

    def test_rejects_unsafe_or_unsupported_filenames(self):
        for filename in ("", "../x.png", "a/b.png", "a\\b.png", "a..png", "image.svg"):
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                destination_for("campaign", filename)

    def test_supported_extensions_are_case_insensitive(self):
        for extension in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".PNG"):
            destination_for("campaign", "image" + extension)

    def test_reads_final_redirect_response_content_type(self):
        headers = (
            b"HTTP/1.1 302 Found\r\nContent-Type: text/html\r\n\r\n"
            b"HTTP/2 200\r\nContent-Type: image/png; charset=binary\r\n\r\n"
        )
        self.assertEqual(response_content_type(headers), "image/png")

    def test_image_signatures(self):
        samples = {
            b"\x89PNG\r\n\x1a\nrest": ".png",
            b"\xff\xd8\xffrest": ".jpg",
            b"GIF89arest": ".gif",
            b"RIFF1234WEBPrest": ".webp",
            b"<html>Drive error</html>": None,
        }
        for data, expected in samples.items():
            with self.subTest(expected=expected):
                self.assertEqual(detected_image_type(data), expected)


if __name__ == "__main__":
    unittest.main()
