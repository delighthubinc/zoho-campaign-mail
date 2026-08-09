#!/usr/bin/env python3
"""Validate and install an image downloaded by the Drive import workflow."""

from __future__ import annotations

import argparse
import os
import re
import shutil
from pathlib import Path


SLUG_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
GENERIC_BINARY_TYPES = {"application/octet-stream", "binary/octet-stream"}


def destination_for(campaign_slug: str, filename: str) -> Path:
    if not campaign_slug or not SLUG_RE.fullmatch(campaign_slug) or ".." in campaign_slug:
        raise ValueError(
            "campaign_slug must contain only letters, numbers, '.', '_' or '-' and must not contain '..'"
        )
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
    return Path("campaigns") / campaign_slug / "images" / filename


def response_content_type(headers: bytes) -> str:
    """Return Content-Type from the final response in a curl header dump."""
    content_type = ""
    for raw_line in headers.decode("iso-8859-1").splitlines():
        if raw_line.upper().startswith("HTTP/"):
            content_type = ""
        elif raw_line.lower().startswith("content-type:"):
            content_type = raw_line.split(":", 1)[1].split(";", 1)[0].strip().lower()
    return content_type


def detected_image_type(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


def install_image(download: Path, headers: Path, campaign_slug: str, filename: str) -> Path:
    destination = destination_for(campaign_slug, filename)
    content_type = response_content_type(headers.read_bytes())
    if not content_type or not (
        content_type.startswith("image/") or content_type in GENERIC_BINARY_TYPES
    ):
        raise ValueError(f"unexpected HTTP Content-Type: {content_type or '(missing)'}")

    data = download.read_bytes()
    actual_type = detected_image_type(data)
    expected_type = Path(filename).suffix.lower()
    if expected_type == ".jpeg":
        expected_type = ".jpg"
    if actual_type != expected_type:
        raise ValueError(
            f"downloaded content is not the requested image format "
            f"(expected {expected_type}, detected {actual_type or 'unknown'})"
        )

    repository = Path.cwd().resolve()
    current = repository
    for component in destination.parent.parts:
        current /= component
        if current.is_symlink():
            raise ValueError("destination must not traverse symbolic links")
        current.mkdir(exist_ok=True)
    campaigns_root = repository / "campaigns"
    resolved_destination = destination.resolve()
    if campaigns_root not in resolved_destination.parents:
        raise ValueError("destination resolves outside the campaigns directory")

    temporary_destination = destination.with_name(f".{destination.name}.tmp")
    shutil.copyfile(download, temporary_destination)
    os.replace(temporary_destination, destination)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign-slug", required=True)
    parser.add_argument("--filename", required=True)
    parser.add_argument("--download")
    parser.add_argument("--headers")
    parser.add_argument("--print-destination", action="store_true")
    args = parser.parse_args()

    destination = destination_for(args.campaign_slug, args.filename)
    if args.print_destination:
        print(destination.as_posix())
        return
    if not args.download or not args.headers:
        parser.error("--download and --headers are required when installing an image")
    installed = install_image(
        Path(args.download), Path(args.headers), args.campaign_slug, args.filename
    )
    print(f"Image validation OK: {installed} ({installed.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
