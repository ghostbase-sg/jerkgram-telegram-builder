#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

SOURCE_ENV = "GHOSTBASE_SOURCE_ROOT"
TARGET = Path("submodules/BuildConfig/Sources/BuildConfig.m")
MARKER = "// JERKGRAM_BUILD132_TELEGRAM_CLIENT_IDENTITY1"
COMPAT_BUNDLE_ID = "ph.telegra.Telegraph"

OLD = '''        if (baseAppBundleId != nil) {
            _dataDict[@"bundleId"] = baseAppBundleId;
        }'''

NEW = f'''        if (baseAppBundleId != nil) {{
            {MARKER}
            // Keep Telegram's client/network bundle identity independent from the
            // iOS InstalledIdentity. Local app-group/keychain/extension plumbing
            // continues to receive the real installed baseAppBundleId at call sites.
            _dataDict[@"bundleId"] = @"{COMPAT_BUNDLE_ID}";
        }}'''


def source_root() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    value = os.environ.get(SOURCE_ENV)
    if not value:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} <telegram-source-root> (or set {SOURCE_ENV})")
    return Path(value).resolve()


def main() -> int:
    root = source_root()
    path = root / TARGET
    if not path.is_file():
        raise SystemExit(f"[build132-telegram-client-identity] missing owner: {TARGET}")

    text = path.read_text(encoding="utf-8")

    if NEW in text:
        if text.count(MARKER) != 1:
            raise SystemExit("[build132-telegram-client-identity] duplicate STEP7 client marker")
        print(f"[build132-telegram-client-identity] already applied: client bundleId={COMPAT_BUNDLE_ID}")
        return 0

    if MARKER in text:
        raise SystemExit("[build132-telegram-client-identity] marker exists without canonical patched block")

    count = text.count(OLD)
    if count != 1:
        raise SystemExit(
            f"[build132-telegram-client-identity] expected exactly one BuildConfig bundleData identity anchor, found {count}"
        )

    updated = text.replace(OLD, NEW, 1)

    # Strict bounded scope: only the BuildConfig dataDict bundleId assignment may differ.
    def normalize(value: str) -> str:
        value = value.replace(NEW, "<JERKGRAM_TELEGRAM_CLIENT_IDENTITY>")
        value = value.replace(OLD, "<JERKGRAM_TELEGRAM_CLIENT_IDENTITY>")
        return value

    if normalize(text) != normalize(updated):
        raise SystemExit("[build132-telegram-client-identity] internal scope check failed")

    path.write_text(updated, encoding="utf-8")
    print(
        "[build132-telegram-client-identity] patched network/client bundleId only: "
        f"installed baseAppBundleId remains caller-owned; client bundleId={COMPAT_BUNDLE_ID}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
