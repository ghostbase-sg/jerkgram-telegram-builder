#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SOURCE_ENV = "GHOSTBASE_SOURCE_ROOT"
VARIANT_ENV = "JERKGRAM_BUNDLE_VARIANT"

PROD_BUNDLE_ID = "com.jerkgram.ios"
TEST_BUNDLE_ID = "com.pixidev.jerkgram.test"

CONFIG_PATHS = (
    Path("build-system/appcenter-configuration.json"),
    Path("build-system/appstore-configuration.json"),
)

# STEP7 scope guard: these values are outside InstalledIdentity and must not be
# rewritten by the bundle-id patcher. The verifier records them before/after
# through a sidecar created by the patcher.
PROTECTED_KEYS = (
    "api_id",
    "api_hash",
    "team_id",
    "app_center_id",
    "appstore_id",
    "app_specific_url_scheme",
    "premium_iap_product_id",
    "enable_siri",
    "enable_icloud",
)

SIDECAR = Path(".jerkgram-build132-bundle-identity.json")


def source_root() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    value = os.environ.get(SOURCE_ENV)
    if not value:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} <telegram-source-root> (or set {SOURCE_ENV})")
    return Path(value).resolve()


def fail(message: str) -> None:
    raise SystemExit(f"[Build132 bundle identity verify] FAIL: {message}")


def expected_bundle_id() -> tuple[str, str]:
    variant = os.environ.get(VARIANT_ENV, "prod").strip().lower()
    if variant == "prod":
        return variant, PROD_BUNDLE_ID
    if variant == "test":
        return variant, TEST_BUNDLE_ID
    fail(f"{VARIANT_ENV} must be 'prod' or 'test', got {variant!r}")
    raise AssertionError


def main() -> int:
    root = source_root()
    variant, expected = expected_bundle_id()

    sidecar_path = root / SIDECAR
    if not sidecar_path.is_file():
        fail("STEP7 sidecar missing; bundle-id patcher did not run")
    try:
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid STEP7 sidecar: {exc}")

    if sidecar.get("schema") != 1:
        fail("unexpected STEP7 sidecar schema")
    if sidecar.get("variant") != variant or sidecar.get("bundle_id") != expected:
        fail("sidecar variant/bundle_id does not match requested build variant")

    seen = 0
    snapshots = sidecar.get("protected", {})
    for relative in CONFIG_PATHS:
        path = root / relative
        if not path.is_file():
            continue
        seen += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(f"invalid JSON at {relative}: {exc}")

        if data.get("bundle_id") != expected:
            fail(f"{relative}: expected bundle_id {expected!r}, got {data.get('bundle_id')!r}")

        before = snapshots.get(str(relative))
        if not isinstance(before, dict):
            fail(f"missing protected-key snapshot for {relative}")
        for key in PROTECTED_KEYS:
            if key in before and data.get(key) != before[key]:
                fail(f"{relative}: protected key changed during STEP7: {key}")

    if seen == 0:
        fail("no known build-system configuration JSON found")

    # The patch is intentionally limited to configuration bundle_id. App groups,
    # keychain groups, extension IDs and Telegram client identity remain generated/
    # signing-owned and are not hardcoded by STEP7.
    forbidden_sidecar_keys = {
        "application-identifier",
        "keychain-access-groups",
        "com.apple.security.application-groups",
        "extension_bundle_id",
        "telegram_client_identity",
    }
    if forbidden_sidecar_keys.intersection(sidecar):
        fail("STEP7 sidecar indicates forbidden shared/client identity mutation")

    print(
        f"[Build132 bundle identity verify] PASS: variant={variant} main bundle_id={expected}; "
        "client credentials and Apple shared identity preserved"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
