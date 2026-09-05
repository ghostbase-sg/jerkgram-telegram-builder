#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

SOURCE_ENV = "GHOSTBASE_SOURCE_ROOT"
TARGET = Path("submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderNode.swift")
MARKER = "// JERKGRAM_BUILD132_SETTINGS_AVATAR_VIDEO_PERF1"
PATCHED_CONDITION = "if self.avatarListNode.listContainerNode.isCollapsing && !self.ignoreCollapse && !self.isSettings {"
UPSTREAM_CONDITION = "if self.avatarListNode.listContainerNode.isCollapsing && !self.ignoreCollapse {"
DISABLE_LINE = "self.avatarListNode.avatarContainerNode.canAttachVideo = false"
REENABLE_LINE = "strongSelf.avatarListNode.avatarContainerNode.canAttachVideo = true"


def source_root() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    value = os.environ.get(SOURCE_ENV)
    if not value:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} <telegram-source-root> (or set {SOURCE_ENV})")
    return Path(value).resolve()


def fail(message: str) -> None:
    raise SystemExit(f"[Build132 settings avatar perf verify] FAIL: {message}")


def main() -> int:
    path = source_root() / TARGET
    if not path.is_file():
        fail(f"missing owner: {TARGET}")

    text = path.read_text(encoding="utf-8")

    if text.count(MARKER) != 1:
        fail("missing or duplicate STEP6 marker")
    if text.count(PATCHED_CONDITION) != 1:
        fail("Settings-only collapse guard is missing or duplicated")
    if UPSTREAM_CONDITION in text:
        fail("unguarded upstream collapse video-detach condition still present")
    if text.count(DISABLE_LINE) < 1:
        fail("non-Settings PeerInfo video-detach behavior was removed")
    if text.count(REENABLE_LINE) < 1:
        fail("upstream video re-enable completion was removed")

    marker_index = text.index(MARKER)
    condition_index = text.index(PATCHED_CONDITION)
    disable_index = text.index(DISABLE_LINE, condition_index)
    if not (marker_index < condition_index < disable_index):
        fail("STEP6 marker/guard/detach order is invalid")
    if disable_index - condition_index > 240:
        fail("video-detach assignment escaped the bounded Settings guard")

    # The fix must stay in the header lifecycle owner. Do not rewrite the media pipeline.
    forbidden = (
        "videoNode?.canAttachContent = true // JERKGRAM_BUILD132",
        "videoNode.canAttachContent = true // JERKGRAM_BUILD132",
        "UniversalVideoNode(context: // JERKGRAM_BUILD132",
    )
    for token in forbidden:
        if token in text:
            fail(f"unexpected media-pipeline override: {token}")

    print("[Build132 settings avatar perf verify] PASS: Settings collapse keeps animated avatar video attached; non-Settings PeerInfo behavior preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
