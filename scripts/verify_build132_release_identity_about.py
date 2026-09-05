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


def require_file(root: Path, relative_path: Path, label: str) -> tuple[Path, str]:
    path = root / relative_path
    if not path.is_file():
        fail(f"{label} not found at expected path: {relative_path}")
    return path, path.read_text(encoding="utf-8")


def require_identity(root: Path) -> Path:
    path, text = require_file(root, IDENTITY_OWNER, "JerkgramReleaseIdentity")
    if text.count("enum JerkgramReleaseIdentity") != 1:
        fail(f"{IDENTITY_OWNER}: expected exactly one JerkgramReleaseIdentity enum")
    if text.count(IDENTITY_MARKER) != 1:
        fail(f"{IDENTITY_OWNER}: missing or duplicate {IDENTITY_MARKER}")

    for name, value in EXPECTED.items():
        pattern = rf'static\s+let\s+{re.escape(name)}\s*=\s*"{re.escape(value)}"'
        if re.search(pattern, text) is None:
            fail(f"{IDENTITY_OWNER}: missing {name} = {value!r}")
    return path


def about_region(text: str) -> str:
    if text.count(ABOUT_START) != 1:
        fail(f"{ABOUT_OWNER}: expected exactly one semantic About block")
    start = text.index(ABOUT_START)
    end = text.find(ABOUT_END, start)
    if end < 0 or end <= start:
        fail(f"{ABOUT_OWNER}: semantic About block is not bounded by Debug/Research")
    return text[start:end]


def row_pattern(index: int, title: str) -> re.Pattern[str]:
    return re.compile(
        rf'(?m)^[ \t]*\.aboutValue\(1,[ \t]*{index},[ \t]*{re.escape(title)},[ \t]*(?P<value>.+)\),[ \t]*$'
    )


def require_about_uses_identity(root: Path) -> Path:
    path, text = require_file(root, ABOUT_OWNER, "About owner")
    region = about_region(text)

    for index, title, expected_expression in ROW_SPECS:
        matches = list(row_pattern(index, title).finditer(region))
        if len(matches) != 1:
            fail(f"{ABOUT_OWNER}: expected exactly one About row {title}, found {len(matches)}")
        actual = matches[0].group("value").strip()
        if actual != expected_expression:
            fail(f"{ABOUT_OWNER}: {title} uses {actual!r}, expected {expected_expression!r}")

    if "1.0.0" in region:
        fail(f"{ABOUT_OWNER}: stale Jerkgram-visible 1.0.0 remains in About")
    if region.count("JerkgramReleaseIdentity.displayVersion") != 1:
        fail(f"{ABOUT_OWNER}: display identity must be used exactly once in About")
    if region.count("JerkgramReleaseIdentity.build") != 1:
        fail(f"{ABOUT_OWNER}: build identity must be used exactly once in About")
    if region.count("JerkgramReleaseIdentity.telegramBase") != 1:
        fail(f"{ABOUT_OWNER}: Telegram base identity must be used exactly once in About")
    return path


def require_bounded_patcher() -> None:
    patcher_path = Path(__file__).with_name("apply_build132_release_identity_about.py")
    if not patcher_path.is_file():
        fail(f"patcher not found next to verifier: {patcher_path.name}")

    text = patcher_path.read_text(encoding="utf-8")
    if "rglob(" in text or "os.walk(" in text:
        fail("release identity patcher must not recursively scan the Swift source tree")
    forbidden_info_key = "CFBundle" + "ShortVersionString"
    if forbidden_info_key in text:
        fail("release identity patcher must not target Telegram's signing/display version key")

    for token in (
        str(ABOUT_OWNER),
        str(IDENTITY_OWNER),
        "strings.jerkgramVersion",
        "strings.build",
        "strings.telegramBase",
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
