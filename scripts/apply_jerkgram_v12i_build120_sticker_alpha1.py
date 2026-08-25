#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src",
)).resolve()

STICKER = ROOT / (
    "submodules/TelegramUI/Components/Chat/"
    "ChatMessageStickerItemNode/Sources/"
    "ChatMessageStickerItemNode.swift"
)

MARK = "Jerkgram v1.2I BUILD120_STICKER_DELETED_ALPHA1"
SETUP = "    override public func setupItem(_ item: ChatMessageItem, synchronousLoad: Bool) {\n"
SUPER = "        super.setupItem(item, synchronousLoad: synchronousLoad)\n"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build120 sticker alpha] " + message)


def main() -> None:
    require(STICKER.is_file(), "sticker renderer missing: " + str(STICKER))
    text = STICKER.read_text(encoding="utf-8")

    if MARK in text:
        print("[Build120 sticker alpha] already materialized")
        return

    require("import TelegramCore" in text, "TelegramCore import missing")
    require(text.count(SETUP) == 1, "setupItem owner count != 1")

    setup_start = text.index(SETUP)
    setup_end = text.find("\n    private var absoluteRect:", setup_start)
    require(setup_end > setup_start, "setupItem boundaries missing")
    setup = text[setup_start:setup_end]
    require(setup.count(SUPER) == 1, "setupItem super call count != 1")

    patch = (
        SUPER
        + "        // MARK: Jerkgram v1.2I BUILD120_STICKER_DELETED_ALPHA1\n"
        + "        // Stickers use a dedicated renderer and therefore bypass the\n"
        + "        // bubble deleted-content alpha owner. Mirror the same visual\n"
        + "        // contract here without changing recovery/cache behaviour.\n"
        + "        // Reassign on every setupItem so reused live nodes return to 1.0.\n"
        + "        let ghostBaseDeletedStickerAlpha: CGFloat = (((item.message.attributes.first(where: { $0 is GhostBaseMessageAttribute }) as? GhostBaseMessageAttribute)?.isDeleted) ?? false) ? 0.55 : 1.0\n"
        + "        self.contextSourceNode.contentNode.alpha = ghostBaseDeletedStickerAlpha\n"
    )

    setup = setup.replace(SUPER, patch, 1)
    text = text[:setup_start] + setup + text[setup_end:]
    STICKER.write_text(text, encoding="utf-8")

    print("[Build120 sticker alpha] GREEN")
    print("[Build120 sticker alpha] deleted stickers use alpha 0.55; live/reused stickers reset to 1.0")
    print("[Build120 sticker alpha] recovery/cache policy unchanged")


if __name__ == "__main__":
    main()
