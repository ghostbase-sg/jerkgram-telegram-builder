#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

EXPECTED = {
    "version": "1.0.2-beta.1",
    "displayVersion": "1.0.2 Beta 1",
    "build": "132",
    "telegramBase": "12.9.2",
}

ABOUT_OWNER = Path("submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift")
IDENTITY_OWNER = Path("submodules/SettingsUI/Sources/GhostBase/JerkgramReleaseIdentity.swift")
IDENTITY_MARKER = "// BUILD132_RELEASE_IDENTITY1"

VALUE_PATTERN = re.compile(
    r'(?m)(\b(?:label|value|rightLabel)\s*:\s*)'
    r'(?P<expr>JerkgramReleaseIdentity\.[A-Za-z_][A-Za-z0-9_]*|"[^"\n]*"|[A-Za-z_][A-Za-z0-9_\.]*)'
)


def fail(message: str) -> None:
    print(f"[build132-release-identity] FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def require_file(root: Path, relative_path: Path, label: str) -> tuple[Path, str]:
    path = root / relative_path
    if not path.is_file():
        fail(f"{label} not found at expected path: {relative_path}")
    return path, path.read_text(encoding="utf-8")


def require_identity(root: Path) -> Path:
    path, text = require_file(root, IDENTITY_OWNER, "JerkgramReleaseIdentity")
    if text.count("enum JerkgramReleaseIdentity") != 1:
        fail(f"{IDENTITY_OWNER}: expected exactly one JerkgramReleaseIdentity enum")
    if IDENTITY_MARKER not in text:
        fail(f"{IDENTITY_OWNER}: missing {IDENTITY_MARKER}")

    for name, value in EXPECTED.items():
        pattern = rf'static\s+let\s+{re.escape(name)}\s*=\s*"{re.escape(value)}"'
        if re.search(pattern, text) is None:
            fail(f"{IDENTITY_OWNER}: missing {name} = {value!r}")

    return path


def about_region(text: str) -> str:
    if text.count('"Jerkgram Version"') != 1:
        fail(f'{ABOUT_OWNER}: expected exactly one "Jerkgram Version" label')

    start = text.find('"Jerkgram Version"')
    base = text.find('"Telegram Base"', start)
    if base < 0:
        fail(f'{ABOUT_OWNER}: missing canonical "Telegram Base" label')

    region_start = max(0, start - 600)
    region_end = min(len(text), base + 1400)
    region = text[region_start:region_end]

    if '"Telegram Version"' in region:
        fail(f'{ABOUT_OWNER}: legacy "Telegram Version" label remains in About')
    return region


def extract_row_value(region: str, label: str) -> str:
    token = f'"{label}"'
    if region.count(token) != 1:
        fail(f"{ABOUT_OWNER}: expected exactly one About row {label!r}, found {region.count(token)}")

    label_match = re.search(re.escape(token), region)
    assert label_match is not None
    window = region[label_match.end() : min(len(region), label_match.end() + 900)]
    match = VALUE_PATTERN.search(window)
    if match is None:
        fail(f"{ABOUT_OWNER}: missing simple value field for About row {label!r}")
    return match.group("expr")


def require_about_uses_identity(root: Path) -> Path:
    path, text = require_file(root, ABOUT_OWNER, "About owner")
    region = about_region(text)

    expected_rows = {
        "Jerkgram Version": "JerkgramReleaseIdentity.displayVersion",
        "Build": "JerkgramReleaseIdentity.build",
        "Telegram Base": "JerkgramReleaseIdentity.telegramBase",
    }
    for label, expected_expression in expected_rows.items():
        actual = extract_row_value(region, label)
        if actual != expected_expression:
            fail(f"{ABOUT_OWNER}: {label} uses {actual!r}, expected {expected_expression!r}")

    if "1.0.0" in region:
        fail(f"{ABOUT_OWNER}: stale Jerkgram-visible 1.0.0 remains in About")
    if extract_row_value(region, "Jerkgram Version") == "JerkgramReleaseIdentity.telegramBase":
        fail(f"{ABOUT_OWNER}: Telegram Base must never be used as Jerkgram Version")

    return path


def require_bounded_patcher() -> None:
    patcher_path = Path(__file__).with_name("apply_build132_release_identity_about.py")
    if not patcher_path.is_file():
        fail(f"patcher not found next to verifier: {patcher_path.name}")

    text = patcher_path.read_text(encoding="utf-8")
    if "rglob(" in text:
        fail("release identity patcher must not recursively scan the Swift source tree")
    if "CFBundleShortVersionString" in text:
        fail("release identity patcher must not rewrite Telegram CFBundleShortVersionString")

    for token in (
        str(ABOUT_OWNER),
        str(IDENTITY_OWNER),
        "JerkgramReleaseIdentity.displayVersion",
        "JerkgramReleaseIdentity.build",
        "JerkgramReleaseIdentity.telegramBase",
    ):
        if token not in text:
            fail(f"patcher missing bounded invariant token: {token!r}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify_build132_release_identity_about.py <materialized-source-root>")

    root = Path(sys.argv[1]).expanduser().resolve()
    if not root.is_dir():
        fail(f"not a directory: {root}")

    require_bounded_patcher()
    identity_path = require_identity(root)
    about_path = require_about_uses_identity(root)

    print("[build132-release-identity] OK")
    print(f"  identity:  {identity_path.relative_to(root)}")
    print(f"  about:     {about_path.relative_to(root)}")
    print("  display:   1.0.2 Beta 1")
    print("  technical: 1.0.2-beta.1")
    print("  build:     132")
    print("  base:      12.9.2")


if __name__ == "__main__":
    main()
