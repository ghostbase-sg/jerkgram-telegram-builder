#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

SOURCE_ENV = "GHOSTBASE_SOURCE_ROOT"
TARGET = Path("submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderNode.swift")
MARKER = "// JERKGRAM_BUILD132_SETTINGS_AVATAR_VIDEO_PERF1"

OLD = """        if self.avatarListNode.listContainerNode.isCollapsing && !self.ignoreCollapse {\n            self.avatarListNode.avatarContainerNode.canAttachVideo = false\n        }"""
NEW = """        // JERKGRAM_BUILD132_SETTINGS_AVATAR_VIDEO_PERF1\n        // Settings uses an animated account avatar in the stretch/morph header. Keep its\n        // video content attached during the short collapse transition to avoid a costly\n        // detach -> reattach media-pipeline cycle. Non-Settings PeerInfo keeps upstream behavior.\n        if self.avatarListNode.listContainerNode.isCollapsing && !self.ignoreCollapse && !self.isSettings {\n            self.avatarListNode.avatarContainerNode.canAttachVideo = false\n        }"""


def source_root() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    value = os.environ.get(SOURCE_ENV)
    if not value:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} <telegram-source-root> (or set {SOURCE_ENV})")
    return Path(value).resolve()


def main() -> int:
    path = source_root() / TARGET
    if not path.is_file():
        raise SystemExit(f"[build132-settings-avatar-perf] missing owner: {TARGET}")

    text = path.read_text(encoding="utf-8")

    if NEW in text:
        if text.count(MARKER) != 1:
            raise SystemExit("[build132-settings-avatar-perf] invalid duplicate marker")
        print("[build132-settings-avatar-perf] already applied")
        return 0

    old_count = text.count(OLD)
    if old_count != 1:
        raise SystemExit(f"[build132-settings-avatar-perf] expected exactly one upstream collapse anchor, found {old_count}")
    if MARKER in text:
        raise SystemExit("[build132-settings-avatar-perf] marker exists without canonical patched block")

    updated = text.replace(OLD, NEW, 1)
    path.write_text(updated, encoding="utf-8")
    print("[build132-settings-avatar-perf] patched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
