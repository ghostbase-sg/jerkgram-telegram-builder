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
    r'(?m)^[ \t]*telegram_bundle_id[ \t]*=[ \t]*[\"\'](?P<value>[^\"\']+)[\"\'][ \t]*$'
)

# These are adjacent build identities but are deliberately outside STEP7 InstalledIdentity.
PROTECTED_ASSIGNMENTS = (
    "telegram_api_id",
    "telegram_api_hash",
    "telegram_team_id",
    "telegram_app_center_id",
    "telegram_appstore_id",
    "telegram_app_specific_url_scheme",
    "telegram_premium_iap_product_id",
    "telegram_aps_environment",
    "telegram_enable_siri",
    "telegram_enable_icloud",
    "telegram_enable_watch",
)


def source_root() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    value = os.environ.get(SOURCE_ENV)
    if not value:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} <telegram-source-root> (or set {SOURCE_ENV})")
    return Path(value).resolve()


def fail(message: str) -> None:
    raise SystemExit(f"[Build132 active bundle identity verify] FAIL: {message}")


def requested_identity() -> tuple[str, str]:
    variant = os.environ.get(VARIANT_ENV, "prod").strip().lower()
    if variant == "prod":
        return variant, PROD_BUNDLE_ID
    if variant == "test":
        return variant, TEST_BUNDLE_ID
    fail(f"{VARIANT_ENV} must be 'prod' or 'test', got {variant!r}")
    raise AssertionError


def assignment_count(text: str, name: str) -> int:
    pattern = re.compile(rf"(?m)^[ \t]*{re.escape(name)}[ \t]*=")
    return len(pattern.findall(text))


def main() -> int:
    root = source_root()
    path = root / TARGET
    if not path.is_file():
        fail(f"active Bazel configuration missing: {TARGET}")

    variant, expected = requested_identity()
    text = path.read_text(encoding="utf-8")

    if text.count(MARKER) != 1:
        fail("missing or duplicate STEP7 InstalledIdentity marker")

    matches = list(ASSIGNMENT_RE.finditer(text))
    if len(matches) != 1:
        fail(f"expected exactly one telegram_bundle_id assignment, found {len(matches)}")
    actual = matches[0].group("value")
    if actual != expected:
        fail(f"variant={variant} expects {expected!r}, got {actual!r}")

    marker_index = text.index(MARKER)
    assignment_index = matches[0].start()
    if marker_index > assignment_index or text[marker_index + len(MARKER):assignment_index].strip():
        fail("STEP7 marker is not immediately attached to telegram_bundle_id")

    # Presence/count checks catch accidental deletion or duplicate injection. Values are
    # intentionally NOT hardcoded here: API credentials/team/signing ownership belong to
    # their existing builder stages, not to STEP7.
    for name in PROTECTED_ASSIGNMENTS:
        count = assignment_count(text, name)
        if count > 1:
            fail(f"protected assignment duplicated: {name}")

    # Never encode Jerkgram's main bundle ID into adjacent credentials/shared-signing vars.
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("telegram_bundle_id") or stripped.startswith(MARKER):
            continue
        if PROD_BUNDLE_ID in line or TEST_BUNDLE_ID in line:
            fail(f"main InstalledIdentity leaked into non-bundle configuration: {stripped[:160]}")

    print(
        f"[Build132 active bundle identity verify] PASS: variant={variant} "
        f"InstalledIdentity={expected}; client/signing/shared variables not rewritten by STEP7"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
