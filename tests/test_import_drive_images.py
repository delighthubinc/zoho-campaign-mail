import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.import_drive_images import MAX_IMAGES, install_batch, parse_images_json


class ImportDriveImagesTests(unittest.TestCase):
    def parse(self, value, slug="forum-20260910"):
        return parse_images_json(json.dumps(value), slug)

    def test_valid_multiple_images(self):
        images = [
            {"drive_file_id": "id_one-1", "filename": "banner.png"},
            {"drive_file_id": "id_two-2", "filename": "speaker01.jpg"},
        ]
        self.assertEqual(self.parse(images), images)

    def test_rejects_empty_array(self):
        with self.assertRaisesRegex(ValueError, "between 1 and 20"):
            self.parse([])

    def test_rejects_more_than_twenty_images(self):
        images = [
            {"drive_file_id": f"id_{index}", "filename": f"image-{index}.png"}
            for index in range(MAX_IMAGES + 1)
        ]
        with self.assertRaisesRegex(ValueError, "between 1 and 20"):
            self.parse(images)

    def test_rejects_invalid_json(self):
        with self.assertRaisesRegex(ValueError, "not valid JSON"):
            parse_images_json("[{", "campaign")

    def test_rejects_missing_required_key(self):
        with self.assertRaisesRegex(ValueError, "missing required key: filename"):
            self.parse([{"drive_file_id": "id"}])

    def test_rejects_duplicate_filename(self):
        images = [
            {"drive_file_id": "first", "filename": "same.png"},
            {"drive_file_id": "second", "filename": "same.png"},
        ]
        with self.assertRaisesRegex(ValueError, "duplicate filename"):
            self.parse(images)

    def test_rejects_invalid_campaign_slug(self):
        with self.assertRaisesRegex(ValueError, "campaign_slug"):
            self.parse([{"drive_file_id": "id", "filename": "image.png"}], "../bad")

    def test_rejects_invalid_filename(self):
        with self.assertRaisesRegex(ValueError, "single file name"):
            self.parse([{"drive_file_id": "id", "filename": "../image.png"}])

    def test_rejects_unsupported_extension(self):
        with self.assertRaisesRegex(ValueError, "filename extension"):
            self.parse([{"drive_file_id": "id", "filename": "image.svg"}])

    def test_rejects_invalid_drive_file_id(self):
        with self.assertRaisesRegex(ValueError, "drive_file_id"):
            self.parse([{"drive_file_id": "bad id", "filename": "image.png"}])

    def test_batch_validation_finishes_before_any_install(self):
        png = b"\x89PNG\r\n\x1a\ncontent"
        images = [
            {"drive_file_id": "first", "filename": "first.png"},
            {"drive_file_id": "second", "filename": "second.png"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            downloads = root / "downloads"
            downloads.mkdir()
            (downloads / "0.download").write_bytes(png)
            (downloads / "0.headers").write_bytes(b"HTTP/2 200\r\nContent-Type: image/png\r\n")
            (downloads / "1.download").write_bytes(b"<html>error</html>")
            (downloads / "1.headers").write_bytes(b"HTTP/2 200\r\nContent-Type: text/html\r\n")

            previous = Path.cwd()
            try:
                # install_image resolves destinations relative to the repository cwd.
                os.chdir(root)
                with self.assertRaisesRegex(ValueError, "Content-Type"):
                    install_batch(images, "campaign", downloads)
            finally:
                os.chdir(previous)
            self.assertFalse((root / "campaigns").exists())


if __name__ == "__main__":
    unittest.main()
