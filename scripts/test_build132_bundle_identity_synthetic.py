#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
APPLY = SCRIPTS / "apply_build132_bundle_identity.py"
VERIFY = SCRIPTS / "verify_build132_active_bundle_identity.py"

VARIABLES = '''telegram_bazel_path = "tools/bazel"
telegram_use_xcode_managed_codesigning = False
telegram_team_id = "C67CF9S4VU"
telegram_bundle_id = "ph.telegra.Telegraph"
telegram_api_id = "123456"
telegram_api_hash = "keep-me-secret"
telegram_app_center_id = "0"
telegram_is_internal_build = False
telegram_is_appstore_build = False
telegram_appstore_id = "0"
telegram_app_specific_url_scheme = ""
telegram_premium_iap_product_id = "org.telegram.telegramPremium.monthly"
telegram_aps_environment = "production"
telegram_enable_siri = True
telegram_enable_icloud = True
'''

PROTECTED_LINES = (
    'telegram_team_id = "C67CF9S4VU"',
    'telegram_api_id = "123456"',
    'telegram_api_hash = "keep-me-secret"',
    'telegram_premium_iap_product_id = "org.telegram.telegramPremium.monthly"',
    'telegram_aps_environment = "production"',
    'telegram_enable_siri = True',
    'telegram_enable_icloud = True',
)


def run(script: Path, root: Path, variant: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["JERKGRAM_BUNDLE_VARIANT"] = variant
    return subprocess.run(
        [sys.executable, str(script), str(root)],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"[Build132 bundle identity synthetic] FAIL: {message}")


def assert_protected(text: str) -> None:
    for line in PROTECTED_LINES:
        require(text.count(line) == 1, f"protected line changed or duplicated: {line}")


def main() -> int:
    for script in (APPLY, VERIFY):
        require(script.is_file(), f"missing script: {script.name}")

    with tempfile.TemporaryDirectory(prefix="jerkgram-build132-bundle-") as temp:
        root = Path(temp)
        variables = root / "build-input/configuration-repository/variables.bzl"
        variables.parent.mkdir(parents=True)
        variables.write_text(VARIABLES, encoding="utf-8")

        # Production is the default/release identity.
        result = run(APPLY, root, "prod")
        require(result.returncode == 0, f"prod apply failed: {result.stderr or result.stdout}")
        prod_text = variables.read_text(encoding="utf-8")
        require('telegram_bundle_id = "com.jerkgram.ios"' in prod_text, "prod bundle id missing")
        assert_protected(prod_text)

        result = run(VERIFY, root, "prod")
        require(result.returncode == 0, f"prod verify failed: {result.stderr or result.stdout}")

        before_second_apply = variables.read_bytes()
        result = run(APPLY, root, "prod")
        require(result.returncode == 0, f"prod second apply failed: {result.stderr or result.stdout}")
        require(variables.read_bytes() == before_second_apply, "prod apply is not idempotent")

        # The exact same materialized config can be switched deliberately to test identity.
        result = run(APPLY, root, "test")
        require(result.returncode == 0, f"test apply failed: {result.stderr or result.stdout}")
        test_text = variables.read_text(encoding="utf-8")
        require('telegram_bundle_id = "com.pixidev.jerkgram.test"' in test_text, "test bundle id missing")
        require("com.jerkgram.ios" not in test_text, "prod id leaked into test config")
        assert_protected(test_text)

        result = run(VERIFY, root, "test")
        require(result.returncode == 0, f"test verify failed: {result.stderr or result.stdout}")

        # Cross-variant verifier must fail closed.
        result = run(VERIFY, root, "prod")
        require(result.returncode != 0, "prod verifier accepted test bundle id")

        # Unknown build variant must fail closed.
        result = run(APPLY, root, "staging")
        require(result.returncode != 0, "unknown variant was accepted")

        # Duplicate InstalledIdentity assignment must fail closed.
        variables.write_text(
            VARIABLES + '\ntelegram_bundle_id = "duplicate.invalid"\n',
            encoding="utf-8",
        )
        result = run(APPLY, root, "prod")
        require(result.returncode != 0, "duplicate telegram_bundle_id assignment was accepted")

    print(
        "[Build132 bundle identity synthetic] PASS: prod/test switch, idempotence, "
        "protected vars, cross-variant and duplicate fail-closed checks"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
