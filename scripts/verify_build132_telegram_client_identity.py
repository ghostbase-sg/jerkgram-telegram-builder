#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

SOURCE_ENV = "GHOSTBASE_SOURCE_ROOT"
TARGET = Path("submodules/BuildConfig/Sources/BuildConfig.m")
MARKER = "// JERKGRAM_BUILD132_TELEGRAM_CLIENT_IDENTITY1"
COMPAT_BUNDLE_ID = "ph.telegra.Telegraph"

PATCHED_ASSIGNMENT = f'_dataDict[@"bundleId"] = @"{COMPAT_BUNDLE_ID}";'
UPSTREAM_ASSIGNMENT = '_dataDict[@"bundleId"] = baseAppBundleId;'
INIT_SIGNATURE = '- (instancetype _Nonnull)initWithBaseAppBundleId:(NSString * _Nonnull)baseAppBundleId {'
SERIALIZE_ANCHOR = 'NSData *data = [NSJSONSerialization dataWithJSONObject:dataDict options:0 error:nil];'


def source_root() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    value = os.environ.get(SOURCE_ENV)
    if not value:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} <telegram-source-root> (or set {SOURCE_ENV})")
    return Path(value).resolve()


def fail(message: str) -> None:
    raise SystemExit(f"[Build132 Telegram client identity verify] FAIL: {message}")


def main() -> int:
    path = source_root() / TARGET
    if not path.is_file():
        fail(f"missing owner: {TARGET}")

    text = path.read_text(encoding="utf-8")

    if text.count(MARKER) != 1:
        fail("missing or duplicate STEP7 TelegramClientIdentity marker")
    if text.count(PATCHED_ASSIGNMENT) != 1:
        fail("compatibility client bundleId assignment missing or duplicated")
    if UPSTREAM_ASSIGNMENT in text:
        fail("runtime client payload still inherits InstalledIdentity")
    if text.count(INIT_SIGNATURE) != 1:
        fail("BuildConfig baseAppBundleId initializer contract changed unexpectedly")
    if text.count(SERIALIZE_ANCHOR) != 1:
        fail("BuildConfig bundleData JSON serialization contract changed unexpectedly")

    marker_index = text.index(MARKER)
    assignment_index = text.index(PATCHED_ASSIGNMENT)
    init_index = text.index(INIT_SIGNATURE)
    serialize_index = text.index(SERIALIZE_ANCHOR)
    if not (init_index < marker_index < assignment_index < serialize_index):
        fail("client identity marker escaped BuildConfig init/bundleData path")
    if assignment_index - marker_index > 420:
        fail("compatibility assignment escaped bounded marker window")

    # Installed identities must never be hardcoded into Telegram client payload.
    for installed_id in ("com.jerkgram.ios", "com.pixidev.jerkgram.test"):
        if installed_id in text:
            fail(f"InstalledIdentity leaked into BuildConfig client owner: {installed_id}")

    print(
        "[Build132 Telegram client identity verify] PASS: network appData bundleId="
        f"{COMPAT_BUNDLE_ID}; InstalledIdentity remains separate"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
