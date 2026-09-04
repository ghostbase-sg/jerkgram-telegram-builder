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


def fail(message: str) -> None:
    print(f"[build132-release-identity] FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_swift_files(root: Path) -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for path in root.rglob("*.swift"):
        try:
            files.append((path, path.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            continue
    return files


def require_identity(swift_files: list[tuple[Path, str]]) -> Path:
    matches = [(path, text) for path, text in swift_files if "enum JerkgramReleaseIdentity" in text]
    if len(matches) != 1:
        fail(f"expected exactly one JerkgramReleaseIdentity enum, found {len(matches)}")

    path, text = matches[0]
    for name, value in EXPECTED.items():
        pattern = rf"static\s+let\s+{re.escape(name)}\s*=\s*\"{re.escape(value)}\""
        if re.search(pattern, text) is None:
            fail(f"{path}: missing {name} = {value!r}")
    return path


def require_about_uses_identity(swift_files: list[tuple[Path, str]]) -> Path:
    candidates: list[tuple[Path, str]] = []
    for path, text in swift_files:
        if "Jerkgram Version" in text and "Telegram Base" in text:
            candidates.append((path, text))

    if len(candidates) != 1:
        fail(f"expected exactly one About owner with Jerkgram Version + Telegram Base, found {len(candidates)}")

    path, text = candidates[0]
    required_refs = (
        "JerkgramReleaseIdentity.displayVersion",
        "JerkgramReleaseIdentity.build",
        "JerkgramReleaseIdentity.telegramBase",
    )
    for ref in required_refs:
        if ref not in text:
            fail(f"{path}: About does not use {ref}")

    if "1.0.0" in text:
        fail(f"{path}: stale Jerkgram-visible 1.0.0 remains in About owner")

    return path


def reject_global_bundle_version_rewrite(swift_files: list[tuple[Path, str]]) -> None:
    jerkgram_release_tokens = ("1.0.2-beta.1", "1.0.2 Beta 1")
    for path, text in swift_files:
        if "CFBundleShortVersionString" not in text:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if "CFBundleShortVersionString" in line and any(token in line for token in jerkgram_release_tokens):
                fail(f"{path}:{line_number}: Jerkgram release version must not replace Telegram CFBundleShortVersionString")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify_build132_release_identity_about.py <materialized-source-root>")

    root = Path(sys.argv[1]).expanduser().resolve()
    if not root.is_dir():
        fail(f"not a directory: {root}")

    swift_files = read_swift_files(root)
    if not swift_files:
        fail(f"no Swift files found under {root}")

    identity_path = require_identity(swift_files)
    about_path = require_about_uses_identity(swift_files)
    reject_global_bundle_version_rewrite(swift_files)

    print("[build132-release-identity] OK")
    print(f"  identity: {identity_path.relative_to(root)}")
    print(f"  about:    {about_path.relative_to(root)}")
    print("  display:  1.0.2 Beta 1")
    print("  technical:1.0.2-beta.1")
    print("  build:    132")
    print("  base:     12.9.2")


if __name__ == "__main__":
    main()
