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

MARKER = "Jerkgram v1.2K BUILD122_REPLY_NO_REUPLOAD1"
STATIC_MARKER = "Jerkgram v1.2K BUILD122_STATIC_STICKER_ALPHA_OWNER1"
ANIMATED_MARKER = "Jerkgram v1.2K BUILD122_ANIMATED_STICKER_ALPHA1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build122] " + message)


def balanced_block(text: str, token: str, start_at: int = 0) -> tuple[int, int]:
    start = text.find(token, start_at)
    require(start >= 0, "block token missing: " + token)
    brace = text.find("{", start)
    require(brace >= 0, "opening brace missing: " + token)
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
                return start, index + 1
    raise RuntimeError("[Build122] unbalanced block: " + token)


def patch_enqueue(text: str) -> str:
    if MARKER in text:
        return text
    for proof in (
        "GhostBase v1.1U BUILD106_FINAL1",
        "BUILD106_ALBUM_RECOVERY1",
        "Jerkgram v1.2J BUILD121_NATIVE_STICKER_RECOVERY1",
        "private func ghostBaseResolveDeletedReplies(",
        "private func ghostBaseBuildPortableDeletedReply(",
    ):
        require(proof in text, "enqueue prerequisite missing: " + proof)

    resolver = text.find("private func ghostBaseResolveDeletedReplies(")
    loop_start, loop_end = balanced_block(text, "                for plan in plans {", resolver)
    old_loop = text[loop_start:loop_end]
    for proof in (
        "ghostBaseReconstructedMedia(",
        "recoveredGroup",
        "ghostBaseBuildRecoveredAlbumTail(",
        "recoveredMedia: recovered",
    ):
        require(proof in old_loop, "expected Build106/121 outgoing recovery owner missing: " + proof)

    new_loop = r'''                // MARK: Jerkgram v1.2K BUILD122_REPLY_NO_REUPLOAD1
                // A reply to a locally deleted/recovered message is a reply/quote only.
                // Never turn the source message's cached media into outgoing media.
                // This must be identical for cached, uncached, partially loaded and album sources.
                for plan in plans {
                    guard
                        let source = plan.source,
                        let authorName = plan.authorName
                    else {
                        result.append(plan.outgoing)
                        continue
                    }

                    let candidate =
                        ghostBaseBuildPortableDeletedReply(
                            outgoing: plan.outgoing,
                            source: source,
                            authorName: authorName,
                            authorUsername: plan.authorUsername,
                            mentionPeerId: plan.mentionPeerId,
                            recoveredMedia: nil
                        )

                    result.append(candidate)
                }'''

    text = text[:loop_start] + new_loop + text[loop_end:]

    patched_start, patched_end = balanced_block(
        text, "                // MARK: Jerkgram v1.2K BUILD122_REPLY_NO_REUPLOAD1"
    )
    patched_loop = text[patched_start:patched_end]
    require("recoveredMedia: nil" in patched_loop, "nil-media reply contract missing")
    for forbidden in (
        "ghostBaseReconstructedMedia(",
        "recoveredGroup",
        "ghostBaseBuildRecoveredAlbumTail(",
        "recoveredMedia: recovered",
    ):
        require(forbidden not in patched_loop, "outgoing recovery survived: " + forbidden)
    return text


def patch_static_sticker(text: str) -> str:
    if STATIC_MARKER in text:
        return text
    require(
        "Jerkgram v1.2I BUILD120_STICKER_DELETED_ALPHA1" in text,
        "Build120 static sticker alpha prerequisite missing",
    )
    old = "        self.contextSourceNode.contentNode.alpha = ghostBaseDeletedStickerAlpha\n"
    require(text.count(old) == 1, "Build120 static alpha owner count != 1")
    new = (
        "        // MARK: Jerkgram v1.2K BUILD122_STATIC_STICKER_ALPHA_OWNER1\n"
        "        // Keep the deleted state on the extracted-content container too, so\n"
        "        // child image/placeholder animation alpha cannot cancel it.\n"
        "        self.contextSourceNode.alpha = ghostBaseDeletedStickerAlpha\n"
        "        self.contextSourceNode.contentNode.alpha = ghostBaseDeletedStickerAlpha\n"
    )
    return text.replace(old, new, 1)


def patch_animated_sticker(text: str) -> str:
    if ANIMATED_MARKER in text:
        return text
    require("public class ChatMessageAnimatedStickerItemNode" in text, "animated sticker renderer missing")
    setup = "    override public func setupItem(_ item: ChatMessageItem, synchronousLoad: Bool) {\n"
    super_call = "        super.setupItem(item, synchronousLoad: synchronousLoad)\n"
    require(text.count(setup) == 1, "animated setupItem owner count != 1")
    start = text.index(setup)
    end = text.find("\n    private ", start + len(setup))
    if end < 0:
        end = len(text)
    block = text[start:end]
    require(block.count(super_call) == 1, "animated setupItem super owner count != 1")
    patch = (
        super_call
        + "        // MARK: Jerkgram v1.2K BUILD122_ANIMATED_STICKER_ALPHA1\n"
        + "        let ghostBaseDeletedAnimatedStickerAlpha: CGFloat = (((item.message.attributes.first(where: { $0 is GhostBaseMessageAttribute }) as? GhostBaseMessageAttribute)?.isDeleted) ?? false) ? 0.55 : 1.0\n"
        + "        self.contextSourceNode.alpha = ghostBaseDeletedAnimatedStickerAlpha\n"
        + "        self.contextSourceNode.contentNode.alpha = ghostBaseDeletedAnimatedStickerAlpha\n"
    )
    block = block.replace(super_call, patch, 1)
    return text[:start] + block + text[end:]


def main() -> None:
    for path in (ENQUEUE, STATIC_STICKER, ANIMATED_STICKER):
        require(path.is_file(), "missing source: " + str(path))

    enqueue = patch_enqueue(ENQUEUE.read_text(encoding="utf-8"))
    static = patch_static_sticker(STATIC_STICKER.read_text(encoding="utf-8"))
    animated = patch_animated_sticker(ANIMATED_STICKER.read_text(encoding="utf-8"))

    ENQUEUE.write_text(enqueue, encoding="utf-8")
    STATIC_STICKER.write_text(static, encoding="utf-8")
    ANIMATED_STICKER.write_text(animated, encoding="utf-8")

    print("[Build122] reply source media hard-disabled for deleted/recovered replies")
    print("[Build122] static + animated/video sticker deleted alpha owners materialized")


if __name__ == "__main__":
    main()
