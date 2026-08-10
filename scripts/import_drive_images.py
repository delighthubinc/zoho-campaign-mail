#!/usr/bin/env python3
"""Validate a batch import request and install its downloaded Drive images."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Support both ``python scripts/import_drive_images.py`` and package-style test imports.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.import_drive_image import destination_for, install_image, validate_download


DRIVE_FILE_ID_RE = re.compile(r"[A-Za-z0-9_-]+\Z")
MAX_IMAGES = 20


def parse_issue_body(raw: str) -> tuple[str, list[dict[str, str]]]:
    """Parse the strict JSON contract used by the ChatGPT Issue bridge."""
    try:
        value: Any = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(f"Issue body is not valid JSON: {error.msg}") from error
    if not isinstance(value, dict):
        raise ValueError("Issue body must be a JSON object")
    if set(value) != {"campaign_slug", "images"}:
        raise ValueError("Issue body must contain exactly campaign_slug and images")
    if not isinstance(value["campaign_slug"], str):
        raise ValueError("campaign_slug must be a string")
    return value["campaign_slug"], parse_images_json(
        json.dumps(value["images"], ensure_ascii=False), value["campaign_slug"]
    )


def parse_images_json(raw: str, campaign_slug: str) -> list[dict[str, str]]:
    """Parse and validate workflow input, including every destination path."""
    try:
        value: Any = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(f"images_json is not valid JSON: {error.msg}") from error
    if not isinstance(value, list):
        raise ValueError("images_json must be a JSON array")
    if not 1 <= len(value) <= MAX_IMAGES:
        raise ValueError(f"images_json must contain between 1 and {MAX_IMAGES} images")

    images: list[dict[str, str]] = []
    filenames: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"images_json[{index}] must be an object")
        for key in ("drive_file_id", "filename"):
            if key not in item:
                raise ValueError(f"images_json[{index}] is missing required key: {key}")
            if not isinstance(item[key], str) or not item[key]:
                raise ValueError(f"images_json[{index}].{key} must be a non-empty string")
        if set(item) != {"drive_file_id", "filename"}:
            raise ValueError(
                f"images_json[{index}] must contain exactly drive_file_id and filename"
            )
        drive_file_id = item["drive_file_id"]
        filename = item["filename"]
        if not DRIVE_FILE_ID_RE.fullmatch(drive_file_id):
            raise ValueError(f"images_json[{index}].drive_file_id contains invalid characters")
        destination_for(campaign_slug, filename)
        if filename in filenames:
            raise ValueError(f"duplicate filename in images_json: {filename}")
        filenames.add(filename)
        images.append({"drive_file_id": drive_file_id, "filename": filename})
    return images


def write_manifest(images: list[dict[str, str]], path: Path) -> None:
    path.write_text(json.dumps(images, ensure_ascii=False), encoding="utf-8")


def validate_destinations_available(images: list[dict[str, str]], campaign_slug: str) -> None:
    """Refuse replacement of any repository image in the requested batch."""
    for image in images:
        destination = destination_for(campaign_slug, image["filename"])
        if destination.exists() or destination.is_symlink():
            raise ValueError(f"destination already exists: {destination}")


def install_batch(images: list[dict[str, str]], campaign_slug: str, download_dir: Path) -> None:
    """Validate the complete batch before installing any image."""
    validate_destinations_available(images, campaign_slug)
    downloads: list[tuple[Path, Path, str]] = []
    for index, image in enumerate(images):
        download = download_dir / f"{index}.download"
        headers = download_dir / f"{index}.headers"
        validate_download(download, headers, image["filename"])
        downloads.append((download, headers, image["filename"]))

    # No working-tree destination is touched until every response passes validation.
    for download, headers, filename in downloads:
        installed = install_image(download, headers, campaign_slug, filename)
        print(f"Image validation OK: {installed} ({installed.stat().st_size} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign-slug")
    parser.add_argument("--images-json")
    parser.add_argument("--issue-body")
    parser.add_argument("--manifest")
    parser.add_argument("--download-dir")
    args = parser.parse_args()

    if args.issue_body:
        issue_slug, images = parse_issue_body(Path(args.issue_body).read_text(encoding="utf-8"))
        if args.campaign_slug and args.campaign_slug != issue_slug:
            parser.error("--campaign-slug does not match the Issue body")
        args.campaign_slug = issue_slug
    else:
        if not args.campaign_slug or args.images_json is None:
            parser.error("--campaign-slug and --images-json are required")
        images = parse_images_json(args.images_json, args.campaign_slug)
    validate_destinations_available(images, args.campaign_slug)
    if args.manifest:
        write_manifest(images, Path(args.manifest))
    elif args.download_dir:
        install_batch(images, args.campaign_slug, Path(args.download_dir))
    else:
        parser.error("one of --manifest or --download-dir is required")


if __name__ == "__main__":
    main()
