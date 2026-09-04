#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

DISPLAY_VERSION = "1.0.2 Beta 1"
TECHNICAL_VERSION = "1.0.2-beta.1"
BUILD_NUMBER = "132"
TELEGRAM_BASE = "12.9.2"

ABOUT_OWNER = Path("submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift")
IDENTITY_OWNER = Path("submodules/SettingsUI/Sources/GhostBase/JerkgramReleaseIdentity.swift")
IDENTITY_MARKER = "// BUILD132_RELEASE_IDENTITY1"

IDENTITY_SOURCE = f'''{IDENTITY_MARKER}
enum JerkgramReleaseIdentity {{
    static let version = "{TECHNICAL_VERSION}"
    static let displayVersion = "{DISPLAY_VERSION}"
    static let build = "{BUILD_NUMBER}"
    static let telegramBase = "{TELEGRAM_BASE}"
}}
'''


def fail(message: str) -> None:
    print(f"[build132-release-identity] FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def require_owner(root: Path, relative_path: Path, label: str) -> Path:
    path = root / relative_path
    if not path.is_file():
        fail(f"{label} not found at expected path: {relative_path}")
    return path


def write_identity(root: Path) -> tuple[Path, bool]:
    path = root / IDENTITY_OWNER
    if path.exists():
        current = path.read_text(encoding="utf-8")
        if IDENTITY_MARKER not in current:
            fail(f"refusing to overwrite non-Build132 identity owner: {IDENTITY_OWNER}")
        if current == IDENTITY_SOURCE:
            return path, False
    else:
        if not path.parent.is_dir():
            fail(f"identity parent directory not found: {IDENTITY_OWNER.parent}")

    path.write_text(IDENTITY_SOURCE, encoding="utf-8")
    return path, True


def about_region(text: str) -> tuple[int, int]:
    jerkgram_label = '"Jerkgram Version"'
    count = text.count(jerkgram_label)
    if count != 1:
        fail(f"expected exactly one Jerkgram Version label, found {count}")

    start = text.find(jerkgram_label)
    base_positions = [
        pos
        for token in ('"Telegram Base"', '"Telegram Version"')
        for pos in [text.find(token, start)]
        if pos >= 0
    ]
    if len(base_positions) != 1:
        fail(f"expected exactly one Telegram Base/Telegram Version label after Jerkgram Version, found {len(base_positions)}")

    region_start = max(0, start - 600)
    region_end = min(len(text), base_positions[0] + 1400)
    return region_start, region_end


VALUE_PATTERN = re.compile(
    r'(?m)(\b(?:label|value|rightLabel)\s*:\s*)'
    r'(?P<expr>JerkgramReleaseIdentity\.[A-Za-z_][A-Za-z0-9_]*|"[^"\n]*"|[A-Za-z_][A-Za-z0-9_\.]*)'
)


def replace_row_value(region: str, label: str, replacement: str) -> str:
    token = f'"{label}"'
    if region.count(token) != 1:
        fail(f"expected exactly one About row label {label!r} in bounded region, found {region.count(token)}")

    label_match = re.search(re.escape(token), region)
    assert label_match is not None
    window_start = label_match.end()
    window_end = min(len(region), window_start + 900)
    window = region[window_start:window_end]

    value_matches = list(VALUE_PATTERN.finditer(window))
    if not value_matches:
        fail(f"could not find a simple value field for About row {label!r}")

    match = value_matches[0]
    absolute_start = window_start + match.start("expr")
    absolute_end = window_start + match.end("expr")
    return region[:absolute_start] + replacement + region[absolute_end:]


def extract_row_value(region: str, label: str) -> str:
    token = f'"{label}"'
    label_match = re.search(re.escape(token), region)
    if label_match is None:
        fail(f"missing About row {label!r} after patch")

    window = region[label_match.end() : min(len(region), label_match.end() + 900)]
    match = VALUE_PATTERN.search(window)
    if match is None:
        fail(f"missing value field for About row {label!r} after patch")
    return match.group("expr")


def patch_about(text: str) -> str:
    start, end = about_region(text)
    region = text[start:end]

    base_count = region.count('"Telegram Base"')
    legacy_count = region.count('"Telegram Version"')
    if base_count == 0 and legacy_count == 1:
        region = region.replace('"Telegram Version"', '"Telegram Base"', 1)
    elif not (base_count == 1 and legacy_count == 0):
        fail(
            "bounded About region must contain exactly one Telegram Base label "
            "or exactly one legacy Telegram Version label"
        )

    region = replace_row_value(region, "Jerkgram Version", "JerkgramReleaseIdentity.displayVersion")
    region = replace_row_value(region, "Build", "JerkgramReleaseIdentity.build")
    region = replace_row_value(region, "Telegram Base", "JerkgramReleaseIdentity.telegramBase")

    expected = {
        "Jerkgram Version": "JerkgramReleaseIdentity.displayVersion",
        "Build": "JerkgramReleaseIdentity.build",
        "Telegram Base": "JerkgramReleaseIdentity.telegramBase",
    }
    for label, expression in expected.items():
        actual = extract_row_value(region, label)
        if actual != expression:
            fail(f"{label} uses {actual!r}, expected {expression!r}")

    if "1.0.0" in region:
        fail("stale 1.0.0 remains in Jerkgram-visible About region")

    return text[:start] + region + text[end:]


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: apply_build132_release_identity_about.py <materialized-source-root>")

    root = Path(sys.argv[1]).expanduser().resolve()
    if not root.is_dir():
        fail(f"not a directory: {root}")

    about_path = require_owner(root, ABOUT_OWNER, "About owner")
    original_about = about_path.read_text(encoding="utf-8")
    patched_about = patch_about(original_about)

    identity_path, identity_changed = write_identity(root)
    about_changed = patched_about != original_about
    if about_changed:
        about_path.write_text(patched_about, encoding="utf-8")

    if not identity_changed and not about_changed:
        print("[build132-release-identity] already applied")
    else:
        print("[build132-release-identity] patched")

    print(f"  identity:         {identity_path.relative_to(root)}")
    print(f"  about:            {about_path.relative_to(root)}")
    print(f"  Jerkgram Version: {DISPLAY_VERSION}")
    print(f"  Build:            {BUILD_NUMBER}")
    print(f"  Telegram Base:    {TELEGRAM_BASE}")


if __name__ == "__main__":
    main()
