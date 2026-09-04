#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

DISPLAY_VERSION = "1.0.2 Beta 1"
TECHNICAL_VERSION = "1.0.2-beta.1"
BUILD_NUMBER = "132"
TELEGRAM_BASE = "12.9.2"

IDENTITY_BLOCK = f'''enum JerkgramReleaseIdentity {{
    static let version = "{TECHNICAL_VERSION}"
    static let displayVersion = "{DISPLAY_VERSION}"
    static let build = "{BUILD_NUMBER}"
    static let telegramBase = "{TELEGRAM_BASE}"
}}
'''


def fail(message: str) -> None:
    print(f"[build132-release-identity] FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def find_about_owner(root: Path) -> Path:
    matches: list[Path] = []
    for path in root.rglob("*.swift"):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "Jerkgram Version" in text and ("Telegram Base" in text or "Telegram Version" in text):
            matches.append(path)

    if len(matches) != 1:
        rendered = ", ".join(str(path.relative_to(root)) for path in matches[:8]) or "none"
        fail(f"expected exactly one About owner, found {len(matches)}: {rendered}")
    return matches[0]


def ensure_identity(text: str) -> tuple[str, bool]:
    if "enum JerkgramReleaseIdentity" in text:
        changed = False
        values = {
            "version": TECHNICAL_VERSION,
            "displayVersion": DISPLAY_VERSION,
            "build": BUILD_NUMBER,
            "telegramBase": TELEGRAM_BASE,
        }
        for name, value in values.items():
            pattern = re.compile(rf'(static\s+let\s+{re.escape(name)}\s*=\s*)"[^"]*"')
            text, count = pattern.subn(rf'\1"{value}"', text, count=1)
            if count != 1:
                fail(f"existing JerkgramReleaseIdentity is missing static let {name}")
            changed = True
        return text, changed

    declaration = re.search(r"(?m)^(?:public\s+|internal\s+|private\s+|fileprivate\s+)?(?:final\s+)?(?:class|struct|enum)\s+", text)
    if declaration is None:
        fail("could not find a Swift declaration anchor for JerkgramReleaseIdentity")

    insertion = IDENTITY_BLOCK + "\n"
    return text[: declaration.start()] + insertion + text[declaration.start() :], True


def about_region(text: str) -> tuple[int, int]:
    start = text.find("Jerkgram Version")
    if start < 0:
        fail("About owner has no Jerkgram Version label")

    end_candidates = [
        pos for pos in (
            text.find("Telegram Base", start),
            text.find("Telegram Version", start),
        ) if pos >= 0
    ]
    if not end_candidates:
        fail("About owner has no Telegram Base/Telegram Version label")

    # Keep replacements tightly around the About rows rather than touching the file globally.
    region_start = max(0, start - 600)
    region_end = min(len(text), min(end_candidates) + 1400)
    return region_start, region_end


def replace_row_value(region: str, label: str, replacement: str) -> tuple[str, bool]:
    label_match = re.search(rf'"{re.escape(label)}"', region)
    if label_match is None:
        return region, False

    # Telegram Settings rows normally expose the right-hand text as label:/value:.
    # Restrict the search to this row-sized window so we never rewrite another setting.
    window_start = label_match.end()
    window_end = min(len(region), window_start + 900)
    window = region[window_start:window_end]
    value_match = re.search(
        r'(?m)(\b(?:label|value|rightLabel)\s*:\s*)(?:"[^"]*"|[^,\n\)]+)',
        window,
    )
    if value_match is None:
        fail(f"could not find value field for About row {label!r}")

    absolute_start = window_start + value_match.start()
    absolute_end = window_start + value_match.end()
    replacement_expr = value_match.group(1) + replacement
    return region[:absolute_start] + replacement_expr + region[absolute_end:], True


def patch_about(text: str) -> tuple[str, bool]:
    start, end = about_region(text)
    region = text[start:end]

    changed = False
    for labels, replacement in (
        (("Jerkgram Version",), "JerkgramReleaseIdentity.displayVersion"),
        (("Build",), "JerkgramReleaseIdentity.build"),
        (("Telegram Base", "Telegram Version"), "JerkgramReleaseIdentity.telegramBase"),
    ):
        replaced = False
        for label in labels:
            if f'"{label}"' not in region:
                continue
            region, did_replace = replace_row_value(region, label, replacement)
            replaced = replaced or did_replace
            if did_replace:
                break
        if not replaced:
            fail(f"could not patch About row: {' / '.join(labels)}")
        changed = True

    return text[:start] + region + text[end:], changed


def verify_result(text: str) -> None:
    required = (
        f'static let version = "{TECHNICAL_VERSION}"',
        f'static let displayVersion = "{DISPLAY_VERSION}"',
        f'static let build = "{BUILD_NUMBER}"',
        f'static let telegramBase = "{TELEGRAM_BASE}"',
        "JerkgramReleaseIdentity.displayVersion",
        "JerkgramReleaseIdentity.build",
        "JerkgramReleaseIdentity.telegramBase",
    )
    for token in required:
        if token not in text:
            fail(f"post-patch verification missing {token!r}")

    start, end = about_region(text)
    about = text[start:end]
    if "1.0.0" in about:
        fail("stale 1.0.0 remains in About region")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: apply_build132_release_identity_about.py <materialized-source-root>")

    root = Path(sys.argv[1]).expanduser().resolve()
    if not root.is_dir():
        fail(f"not a directory: {root}")

    owner = find_about_owner(root)
    original = owner.read_text(encoding="utf-8")

    patched, _ = ensure_identity(original)
    patched, _ = patch_about(patched)
    verify_result(patched)

    if patched == original:
        print(f"[build132-release-identity] already applied: {owner.relative_to(root)}")
        return

    owner.write_text(patched, encoding="utf-8")
    print(f"[build132-release-identity] patched: {owner.relative_to(root)}")
    print(f"  Jerkgram Version: {DISPLAY_VERSION}")
    print(f"  Build:            {BUILD_NUMBER}")
    print(f"  Telegram Base:    {TELEGRAM_BASE}")


if __name__ == "__main__":
    main()
