#!/usr/bin/env python3
"""Classify a PR; fail closed unless it changes one campaign directory only."""
import argparse
import re
import subprocess

SLUG = re.compile(r"^campaigns/([a-z0-9][a-z0-9-]{0,79})/(campaign\.json|mail\.html|images/[^/]+)$")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    output = subprocess.check_output(
        ["git", "diff", "--name-only", "--diff-filter=ACMRD", args.base, args.head], text=True
    )
    files = [line for line in output.splitlines() if line]
    matches = [SLUG.fullmatch(path) for path in files]
    slugs = {match.group(1) for match in matches if match}
    eligible = bool(files) and all(matches) and len(slugs) == 1
    print(f"eligible={'true' if eligible else 'false'}")
    print(f"slug={next(iter(slugs)) if len(slugs) == 1 else ''}")
    if not eligible:
        # System/template PRs remain reviewable, but can never enter auto-merge.
        return 0
    required = {f"campaigns/{next(iter(slugs))}/campaign.json", f"campaigns/{next(iter(slugs))}/mail.html"}
    if not required.issubset(files):
        raise SystemExit("campaign.json and mail.html must both be present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
