#!/usr/bin/env python3
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src",
)).resolve()
ENQUEUE = ROOT / "submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift"
MARK = "Jerkgram v1.2J BUILD121_NATIVE_STICKER_RECOVERY1"
OLD = "GhostBase v1.1V BUILD107_STICKER_TEXT_FALLBACK1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build121 sticker recovery verify] " + message)


def main() -> None:
    require(ENQUEUE.is_file(), "EnqueueMessage.swift missing")
    text = ENQUEUE.read_text(encoding="utf-8")

    require(text.count(MARK) == 1, "Build121 marker count != 1")
    require(OLD not in text, "Build107 sticker hard-rejection marker survived")
    require(
        re.search(
            r"if let file = media as\? TelegramMediaFile,\s*"
            r"file\.isSticker\s*\{\s*return nil",
            text,
            re.S,
        ) is None,
        "sticker hard rejection survived",
    )
    for mime in ("video/webm", "application/x-tgsticker", "image/webp"):
        require(text.count(f'case "{mime}":') == 1, mime + " cache case count != 1")

    require("mimeType: file.mimeType" in text, "TelegramMediaFile mimeType is not preserved")
    require("attributes: file.attributes" in text, "TelegramMediaFile attributes are not preserved")
    require("BUILD106_ALBUM_RECOVERY1" in text, "album recovery regression")
    require("BUILD106_PORTABLE_AUTHOR1" in text, "portable author regression")
    require(
        ('return "Sticker"' in text) or ('return "Стикер"' in text),
        "textual missing-media sticker fallback disappeared",
    )

    print("[Build121 sticker recovery verify] GREEN")
    print("[Build121 sticker recovery verify] native WebP/TGS/WebM path restored")
    print("[Build121 sticker recovery verify] Build107 hard rejection absent")


if __name__ == "__main__":
    main()
