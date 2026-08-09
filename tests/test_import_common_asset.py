import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.import_common_asset import (
    destination_for,
    install_common_asset,
    validate_drive_file_id,
)


PNG = b"\x89PNG\r\n\x1a\ncontent"
JPG = b"\xff\xd8\xffcontent"


class ImportCommonAssetTests(unittest.TestCase):
    def test_valid_destination_is_fixed_under_common_assets(self):
        self.assertEqual(destination_for("delight-hub-logo.png"), Path("assets/common/delight-hub-logo.png"))
        for extension in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".PNG"):
            destination = destination_for("image" + extension)
            self.assertEqual(destination.parent, Path("assets/common"))

    def test_rejects_unsafe_filename_and_path_traversal(self):
        for filename in ("", ".", "..", "../x.png", "a/b.png", "a\\b.png", "a..png", "/tmp/x.png"):
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                destination_for(filename)

    def test_rejects_unsupported_extension(self):
        with self.assertRaisesRegex(ValueError, "filename extension"):
            destination_for("logo.svg")

    def test_rejects_invalid_drive_file_id(self):
        for file_id in ("", "has a space", "id&confirm=x", "../id"):
            with self.subTest(file_id=file_id), self.assertRaises(ValueError):
                validate_drive_file_id(file_id)

    def install(self, root: Path, data: bytes, content_type: str, filename: str) -> Path:
        download = root / "download"
        headers = root / "headers"
        download.write_bytes(data)
        headers.write_bytes(f"HTTP/2 200\r\nContent-Type: {content_type}\r\n".encode())
        return install_common_asset(download, headers, filename)

    def test_installs_valid_png_and_jpg(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = Path.cwd()
            try:
                os.chdir(root)
                self.assertEqual(self.install(root, PNG, "image/png", "logo.png").read_bytes(), PNG)
                self.assertEqual(self.install(root, JPG, "image/jpeg", "profile.jpg").read_bytes(), JPG)
            finally:
                os.chdir(previous)

    def test_rejects_content_type_and_magic_byte_mismatches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = Path.cwd()
            try:
                os.chdir(root)
                with self.assertRaisesRegex(ValueError, "Content-Type"):
                    self.install(root, PNG, "text/html", "logo.png")
                with self.assertRaisesRegex(ValueError, "Content-Type"):
                    self.install(root, PNG, "image/jpeg", "logo.png")
                with self.assertRaisesRegex(ValueError, "requested image format"):
                    self.install(root, JPG, "application/octet-stream", "logo.png")
            finally:
                os.chdir(previous)

    def test_rejects_symlinked_common_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.mkdir()
            (root / "assets").mkdir()
            (root / "assets/common").symlink_to(outside, target_is_directory=True)
            previous = Path.cwd()
            try:
                os.chdir(root)
                with self.assertRaisesRegex(ValueError, "symbolic links"):
                    self.install(root, PNG, "image/png", "logo.png")
            finally:
                os.chdir(previous)
            self.assertFalse((outside / "logo.png").exists())

    def test_identical_content_does_not_replace_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = Path.cwd()
            try:
                os.chdir(root)
                destination = self.install(root, PNG, "image/png", "logo.png")
                with mock.patch("scripts.import_common_asset.os.replace") as replace:
                    self.install(root, PNG, "image/png", "logo.png")
                replace.assert_not_called()
                self.assertEqual(destination.read_bytes(), PNG)
            finally:
                os.chdir(previous)

    def test_changed_content_updates_existing_file(self):
        updated_png = b"\x89PNG\r\n\x1a\nupdated"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = Path.cwd()
            try:
                os.chdir(root)
                destination = self.install(root, PNG, "image/png", "logo.png")
                self.assertEqual(destination.read_bytes(), PNG)
                self.assertEqual(
                    self.install(root, updated_png, "image/png", "logo.png").read_bytes(),
                    updated_png,
                )
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
