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

ROW_SPECS = (
    (1, "strings.jerkgramVersion", "JerkgramReleaseIdentity.displayVersion"),
    (2, "strings.build", "JerkgramReleaseIdentity.build"),
    (3, "strings.telegramBase", "JerkgramReleaseIdentity.telegramBase"),
)
ABOUT_START = "if page == .about {"
ABOUT_END = "if page == .debugResearch {"


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
    if text.count(ABOUT_START) != 1:
        fail(f"expected exactly one semantic About block, found {text.count(ABOUT_START)}")
    start = text.index(ABOUT_START)
    end = text.find(ABOUT_END, start)
    if end < 0:
        fail("semantic About block has no bounded Debug/Research successor")
    if end <= start:
        fail("invalid semantic About block bounds")
    return start, end


def row_pattern(index: int, title: str) -> re.Pattern[str]:
    return re.compile(
        rf'(?m)^(?P<prefix>[ \t]*\.aboutValue\(1,[ \t]*{index},[ \t]*{re.escape(title)},[ \t]*)(?P<value>.+)(?P<suffix>\),[ \t]*)$'
    )


def patch_about(text: str) -> str:
    start, end = about_region(text)
    region = text[start:end]

    for index, title, replacement in ROW_SPECS:
        pattern = row_pattern(index, title)
        matches = list(pattern.finditer(region))
        if len(matches) != 1:
            fail(f"expected exactly one About row {title} at index {index}, found {len(matches)}")
        match = matches[0]
        current = match.group("value").strip()
        if current == replacement:
            continue
        new_line = f'{match.group("prefix")}{replacement}{match.group("suffix")}'
        region = region[:match.start()] + new_line + region[match.end():]

    for index, title, expected in ROW_SPECS:
        matches = list(row_pattern(index, title).finditer(region))
        if len(matches) != 1 or matches[0].group("value").strip() != expected:
            fail(f"About row {title} did not converge to {expected}")

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
