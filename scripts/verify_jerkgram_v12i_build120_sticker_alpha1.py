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


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build120 sticker alpha verify] " + message)


def main() -> None:
    require(STICKER.is_file(), "sticker renderer missing: " + str(STICKER))
    text = STICKER.read_text(encoding="utf-8")

    require(text.count(MARK) == 1, "marker count != 1")
    require(text.count(SETUP) == 1, "setupItem owner count != 1")

    setup_start = text.index(SETUP)
    setup_end = text.find("\n    private var absoluteRect:", setup_start)
    require(setup_end > setup_start, "setupItem boundaries missing")
    setup = text[setup_start:setup_end]

    for token in (
        MARK,
        "GhostBaseMessageAttribute",
        ".isDeleted",
        "? 0.55 : 1.0",
        "self.contextSourceNode.contentNode.alpha = ghostBaseDeletedStickerAlpha",
    ):
        require(token in setup, "missing deleted-sticker alpha token: " + token)

    mark_start = setup.index(MARK)
    next_owner = setup.find("        if item.message.id.namespace", mark_start)
    require(next_owner > mark_start, "alpha patch boundary missing")
    patch = setup[mark_start:next_owner]

    for forbidden in (
        "mediaBox",
        "resourceData",
        "storeResourceData",
        "fetchResource",
        "TelegramMediaFile",
        "message.media",
    ):
        require(forbidden not in patch, "alpha patch unexpectedly changes media/cache behavior: " + forbidden)

    print("[Build120 sticker alpha verify] GREEN")
    print("[Build120 sticker alpha verify] dedicated sticker renderer mirrors deleted alpha 0.55")
    print("[Build120 sticker alpha verify] every setupItem explicitly restores live alpha 1.0")
    print("[Build120 sticker alpha verify] no media recovery/cache path added")


if __name__ == "__main__":
    main()
