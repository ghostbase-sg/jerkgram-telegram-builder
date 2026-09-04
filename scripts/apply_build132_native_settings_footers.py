#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

OWNER = Path("submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift")
MARKER = "BUILD132_NATIVE_SETTINGS_FOOTERS1"
TARGETS = ("About", "Appearance", "Messages")


def fail(message: str) -> None:
    print(f"[build132-native-footers] FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: apply_build132_native_settings_footers.py <materialized-source-root>")

    root = Path(sys.argv[1]).expanduser().resolve()
    owner = root / OWNER
    if not owner.is_file():
        fail(f"missing exact owner: {OWNER}")

    source = owner.read_text(encoding="utf-8")
    if MARKER in source:
        print("[build132-native-footers] already applied")
        return

    # Fail closed until the exact native ItemList footer constructor used by
    # this generated controller is matched.  Do not guess Swift UI types and
    # do not broaden the search outside OWNER.
    for target in TARGETS:
        if target not in source:
            fail(f"missing bounded settings anchor: {target}")

    fail("exact native footer constructor anchor not materialized in this bounded scaffold")


if __name__ == "__main__":
    main()
