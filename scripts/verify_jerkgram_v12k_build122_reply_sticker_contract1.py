#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    os.environ.get("JERKGRAM_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"),
)).resolve()

ENQUEUE = ROOT / "submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift"
STATIC_STICKER = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageStickerItemNode/Sources/ChatMessageStickerItemNode.swift"
ANIMATED_STICKER = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageAnimatedStickerItemNode/Sources/ChatMessageAnimatedStickerItemNode.swift"

REPLY_MARKER = "BUILD122_REPLY_NO_REUPLOAD1"
STATIC_MARKER = "BUILD122_STATIC_STICKER_ALPHA_OWNER1"
ANIMATED_MARKER = "BUILD122_ANIMATED_STICKER_ALPHA1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build122 verify] " + message)


def balanced_block(text: str, token: str, start_at: int = 0) -> str:
    start = text.find(token, start_at)
    require(start >= 0, "block missing: " + token)
    brace = text.find("{", start)
    require(brace >= 0, "brace missing: " + token)
    depth = 0
    in_string = False
    escaped = False
    for index in range(brace, len(text)):
        ch = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise RuntimeError("[Build122 verify] unbalanced block: " + token)


def main() -> None:
    for path in (ENQUEUE, STATIC_STICKER, ANIMATED_STICKER):
        require(path.is_file(), "missing source: " + str(path))

    enqueue = ENQUEUE.read_text(encoding="utf-8")
    static = STATIC_STICKER.read_text(encoding="utf-8")
    animated = ANIMATED_STICKER.read_text(encoding="utf-8")

    require(REPLY_MARKER in enqueue, "reply marker missing")
    resolver_pos = enqueue.find("private func ghostBaseResolveDeletedReplies(")
    reply_loop = balanced_block(enqueue, "                // MARK: Jerkgram v1.2K BUILD122_REPLY_NO_REUPLOAD1", resolver_pos)
    require("recoveredMedia: nil" in reply_loop, "reply does not force nil source media")
    for forbidden in (
        "ghostBaseReconstructedMedia(",
        "recoveredGroup",
        "ghostBaseBuildRecoveredAlbumTail(",
        "recoveredMedia: recovered",
    ):
        require(forbidden not in reply_loop, "cache/media-dependent outgoing path survived: " + forbidden)

    require(STATIC_MARKER in static, "static sticker alpha marker missing")
    require("self.contextSourceNode.alpha = ghostBaseDeletedStickerAlpha" in static, "static container alpha missing")
    require("self.contextSourceNode.contentNode.alpha = ghostBaseDeletedStickerAlpha" in static, "static content alpha missing")
    require("? 0.55 : 1.0" in static, "static deleted/live alpha values missing")

    require(ANIMATED_MARKER in animated, "animated sticker alpha marker missing")
    require("GhostBaseMessageAttribute" in animated, "animated deleted-state attribute lookup missing")
    require("self.contextSourceNode.alpha = ghostBaseDeletedAnimatedStickerAlpha" in animated, "animated container alpha missing")
    require("self.contextSourceNode.contentNode.alpha = ghostBaseDeletedAnimatedStickerAlpha" in animated, "animated content alpha missing")
    require("? 0.55 : 1.0" in animated, "animated deleted/live alpha values missing")

    print("[Build122 verify] GREEN")
    print("[Build122 verify] deleted/recovered replies cannot reupload source media")
    print("[Build122 verify] static + animated/video sticker alpha owners present")


if __name__ == "__main__":
    main()
