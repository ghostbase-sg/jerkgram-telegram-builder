#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

SOURCE_ENV = "GHOSTBASE_SOURCE_ROOT"

# STEP7 is intentionally audit-first. Do not mutate Telegram source here.
# InstalledIdentity is the only layer that may later receive the Jerkgram main-app IDs.
# TelegramClientIdentity and AppleSharedIdentity are report-only until an exact owner is proven.

PROD_BUNDLE_ID = "com.jerkgram.ios"
TEST_BUNDLE_ID = "com.pixidev.jerkgram.test"

# Bounded build/signing roots only. Missing roots are skipped; no repository-wide scan.
CANDIDATE_ROOTS = (
    "build-system",
    "Telegram",
    "TelegramShare",
    "TelegramNotificationServiceExtension",
    "TelegramIntents",
    "TelegramWidget",
)

TEXT_SUFFIXES = {
    ".bzl", ".bazel", ".build", ".entitlements", ".json", ".plist", ".py",
    ".sh", ".swift", ".xcconfig", ".xcodeproj", ".yml", ".yaml",
}

INSTALLED_MARKERS = (
    "PRODUCT_BUNDLE_IDENTIFIER",
    "CFBundleIdentifier",
    "bundle_id",
    "bundleId",
    "bundleIdentifier",
)

TELEGRAM_CLIENT_MARKERS = (
    "api_id",
    "apiId",
    "api_hash",
    "apiHash",
    "telegramClient",
    "clientIdentifier",
)

APPLE_SHARED_MARKERS = (
    "application-identifier",
    "keychain-access-groups",
    "com.apple.security.application-groups",
    "group.",
    "aps-environment",
)

BUNDLE_LITERAL_RE = re.compile(r"\b(?:com|org|net)\.[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)+\b")


def source_root() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    value = os.environ.get(SOURCE_ENV)
    if not value:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} <telegram-source-root> (or set {SOURCE_ENV})")
    return Path(value).resolve()


def classify(path: Path, text: str) -> set[str]:
    categories: set[str] = set()
    lowered_path = str(path).lower()

    if any(marker in text for marker in INSTALLED_MARKERS):
        categories.add("InstalledIdentity")
    if any(marker in text for marker in TELEGRAM_CLIENT_MARKERS):
        categories.add("TelegramClientIdentity")
    if any(marker in text for marker in APPLE_SHARED_MARKERS):
        categories.add("AppleSharedIdentity")

    if "entitlement" in lowered_path or path.suffix == ".entitlements":
        categories.add("AppleSharedIdentity")
    if any(token in lowered_path for token in ("extension", "widget", "share", "intent")):
        # Extension IDs are Apple signing/shared identity unless proven otherwise.
        categories.add("AppleSharedIdentity")

    return categories


def relevant_lines(text: str) -> list[str]:
    markers = INSTALLED_MARKERS + TELEGRAM_CLIENT_MARKERS + APPLE_SHARED_MARKERS
    lines: list[str] = []
    for line in text.splitlines():
        if any(marker in line for marker in markers) or BUNDLE_LITERAL_RE.search(line):
            compact = line.strip()
            if compact and compact not in lines:
                lines.append(compact[:320])
    return lines[:24]


def main() -> int:
    root = source_root()
    if not root.is_dir():
        raise SystemExit(f"[build132-bundle-audit] source root does not exist: {root}")

    findings: list[tuple[str, str, list[str]]] = []
    scanned = 0

    for relative_root in CANDIDATE_ROOTS:
        base = root / relative_root
        if not base.exists():
            continue
        paths = [base] if base.is_file() else base.rglob("*")
        for path in paths:
            if not path.is_file():
                continue
            if path.suffix and path.suffix.lower() not in TEXT_SUFFIXES and path.name not in ("BUILD", "WORKSPACE"):
                continue
            if path.stat().st_size > 2_000_000:
                continue
            scanned += 1
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            categories = classify(path.relative_to(root), text)
            if not categories:
                continue
            lines = relevant_lines(text)
            if not lines:
                continue
            findings.append((str(path.relative_to(root)), ",".join(sorted(categories)), lines))

    installed = [item for item in findings if "InstalledIdentity" in item[1]]

    print(f"[build132-bundle-audit] scanned_text_files={scanned}")
    print(f"[build132-bundle-audit] prod_target={PROD_BUNDLE_ID}")
    print(f"[build132-bundle-audit] test_target={TEST_BUNDLE_ID}")

    for path, categories, lines in findings:
        print(f"\npath={path}\n  categories={categories}")
        for line in lines:
            print(f"  {line}")

    if not installed:
        print("[build132-bundle-audit] FAIL: no bounded InstalledIdentity owner found", file=sys.stderr)
        return 2

    print("\n[build132-bundle-audit] PASS: InstalledIdentity owner(s) found; TelegramClientIdentity and AppleSharedIdentity remain audit-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
