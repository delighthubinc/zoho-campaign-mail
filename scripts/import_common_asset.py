#!/usr/bin/env python3
"""Safely install a public Drive image in the repository's common asset area."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

# Support direct script execution as well as imports from the test suite.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.import_drive_image import ALLOWED_SUFFIXES, validate_download


COMMON_ASSET_DIRECTORY = Path("assets/common")
DRIVE_FILE_ID_RE = re.compile(r"[A-Za-z0-9_-]+\Z")


def validate_drive_file_id(drive_file_id: str) -> None:
    if not drive_file_id or not DRIVE_FILE_ID_RE.fullmatch(drive_file_id):
        raise ValueError("drive_file_id contains invalid characters")


def destination_for(filename: str) -> Path:
    """Return the fixed common-asset destination for a safe image filename."""
    if (
        not filename
        or filename in {".", ".."}
        or "/" in filename
        or "\\" in filename
        or ".." in filename
        or Path(filename).name != filename
    ):
        raise ValueError("filename must be a single file name and must not contain '/', '\\' or '..'")
    if Path(filename).suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValueError("filename extension must be .png, .jpg, .jpeg, .gif or .webp")
    return COMMON_ASSET_DIRECTORY / filename


def install_common_asset(download: Path, headers: Path, filename: str) -> Path:
    """Validate and atomically install an image without following destination symlinks."""
    destination = destination_for(filename)
    validate_download(download, headers, filename)

    repository = Path.cwd().resolve()
    common_root = repository / COMMON_ASSET_DIRECTORY
    current = repository
    for component in COMMON_ASSET_DIRECTORY.parts:
        current /= component
        if current.is_symlink():
            raise ValueError("destination must not traverse symbolic links")
        current.mkdir(exist_ok=True)

    if destination.is_symlink():
        raise ValueError("destination must not be a symbolic link")
    resolved_destination = destination.resolve()
    if common_root.resolve() not in resolved_destination.parents:
        raise ValueError("destination resolves outside assets/common")

    # Preserve the working tree exactly when Drive returned the already tracked bytes.
    if destination.exists() and destination.read_bytes() == download.read_bytes():
        return destination

    temporary_destination = destination.with_name(f".{destination.name}.tmp")
    if temporary_destination.is_symlink():
        raise ValueError("temporary destination must not be a symbolic link")
    shutil.copyfile(download, temporary_destination)
    os.replace(temporary_destination, destination)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--drive-file-id", required=True)
    parser.add_argument("--filename", required=True)
    parser.add_argument("--download")
    parser.add_argument("--headers")
    parser.add_argument("--print-destination", action="store_true")
    args = parser.parse_args()

    validate_drive_file_id(args.drive_file_id)
    destination = destination_for(args.filename)
    if args.print_destination:
        print(destination.as_posix())
        return
    if not args.download or not args.headers:
        parser.error("--download and --headers are required when installing an asset")
    installed = install_common_asset(Path(args.download), Path(args.headers), args.filename)
    print(f"Image validation OK: {installed} ({installed.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
