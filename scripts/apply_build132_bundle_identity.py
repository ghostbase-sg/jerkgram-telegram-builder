#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

SOURCE_ENV = "GHOSTBASE_SOURCE_ROOT"
VARIANT_ENV = "JERKGRAM_BUNDLE_VARIANT"

PROD_BUNDLE_ID = "com.jerkgram.ios"
TEST_BUNDLE_ID = "com.pixidev.jerkgram.test"
TARGET = Path("build-input/configuration-repository/variables.bzl")
MARKER = "# JERKGRAM_BUILD132_INSTALLED_IDENTITY1"

ASSIGNMENT_RE = re.compile(
    r'(?m)^(?P<prefix>[ \t]*telegram_bundle_id[ \t]*=[ \t]*)(?P<quote>[\"\'])(?P<value>[^\"\']+)(?P=quote)(?P<suffix>[ \t]*)$'
)


def source_root() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    value = os.environ.get(SOURCE_ENV)
    if not value:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} <telegram-source-root> (or set {SOURCE_ENV})")
    return Path(value).resolve()


def requested_identity() -> tuple[str, str]:
    variant = os.environ.get(VARIANT_ENV, "prod").strip().lower()
    if variant == "prod":
        return variant, PROD_BUNDLE_ID
    if variant == "test":
        return variant, TEST_BUNDLE_ID
    raise SystemExit(f"[build132-bundle-identity] {VARIANT_ENV} must be 'prod' or 'test', got {variant!r}")


def main() -> int:
    root = source_root()
    path = root / TARGET
    if not path.is_file():
        raise SystemExit(f"[build132-bundle-identity] active Bazel configuration missing: {TARGET}")

    variant, bundle_id = requested_identity()
    text = path.read_text(encoding="utf-8")
    matches = list(ASSIGNMENT_RE.finditer(text))
    if len(matches) != 1:
        raise SystemExit(
            f"[build132-bundle-identity] expected exactly one telegram_bundle_id assignment in {TARGET}, found {len(matches)}"
        )

    match = matches[0]
    old_bundle_id = match.group("value")

    # Scope invariant: STEP7 mutates only the InstalledIdentity assignment.
    # It must not touch telegram_team_id, telegram_app_group, API credentials,
    # extension bundle ids, keychain groups or entitlements.
    canonical_assignment = f'{match.group("prefix")}\"{bundle_id}\"{match.group("suffix")}'
    replacement = f"{MARKER}\n{canonical_assignment}"

    marker_count = text.count(MARKER)
    if marker_count > 1:
        raise SystemExit("[build132-bundle-identity] duplicate STEP7 marker")

    if marker_count == 1:
        marker_start = text.index(MARKER)
        marker_end = marker_start + len(MARKER)
        if marker_end >= match.start() or text[marker_end:match.start()].strip():
            raise SystemExit("[build132-bundle-identity] STEP7 marker is not attached to telegram_bundle_id")
        updated = text[:marker_start] + replacement + text[match.end():]
    else:
        updated = text[:match.start()] + replacement + text[match.end():]

    # Prove locally that every line except the marker + bundle assignment is unchanged.
    def strip_owned(value: str) -> str:
        value = value.replace(MARKER + "\n", "")
        return ASSIGNMENT_RE.sub("<JERKGRAM_INSTALLED_IDENTITY>", value, count=1)

    if strip_owned(text) != strip_owned(updated):
        raise SystemExit("[build132-bundle-identity] internal scope check failed: non-bundle config changed")

    if updated == text:
        print(f"[build132-bundle-identity] already applied: variant={variant} bundle_id={bundle_id}")
        return 0

    path.write_text(updated, encoding="utf-8")
    print(
        f"[build132-bundle-identity] patched InstalledIdentity only: "
        f"{old_bundle_id} -> {bundle_id} (variant={variant})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
