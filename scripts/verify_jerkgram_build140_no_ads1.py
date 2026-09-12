#!/usr/bin/env python3

from pathlib import Path
import os

import apply_jerkgram_build140_no_ads1 as patch


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build140 no ads verifier] " + message)


def verify_chat(text: str) -> None:
    require(text.count(patch.CHAT_MARKER) == 1, "chat marker count != 1")
    require(patch.CHAT_OWNER not in text, "stock chat sponsored-state owner survived")
    marker = text.index(patch.CHAT_MARKER)
    window = text[max(0, marker - 180):marker + 220]
    require("adMessagesState = .single(nil)" in window, "chat sponsored-state signal is not nil")
    require("isPremium" not in window, "chat no-ads patch must not spoof Premium")


def verify_gallery(text: str) -> None:
    require(text.count(patch.GALLERY_MARKER) == 1, "gallery marker count != 1")
    require(patch.GALLERY_START not in text, "gallery still creates an ad context")
    marker = text.index(patch.GALLERY_MARKER)
    window = text[marker:marker + 320]
    for owner in (
        "self.adDisposable.set(nil)",
        "self.adContext = nil",
        "self.adState = nil",
        "self.adSchedule = []",
    ):
        require(owner in window, "gallery reset missing: " + owner)
    require("isPremium" not in window, "gallery no-ads patch must not spoof Premium")


def main() -> None:
    chat_path = ROOT / "submodules/TelegramUI/Sources/ChatHistoryListNode.swift"
    gallery_path = ROOT / "submodules/GalleryUI/Sources/Items/UniversalVideoGalleryItem.swift"
    require(chat_path.is_file(), "missing ChatHistoryListNode.swift")
    require(gallery_path.is_file(), "missing UniversalVideoGalleryItem.swift")

    verify_chat(chat_path.read_text(encoding="utf-8"))
    verify_gallery(gallery_path.read_text(encoding="utf-8"))

    print("[Build140 no ads verifier] GREEN")
    print("[Build140 no ads verifier] chat + video-gallery sponsored UI owners are disabled; no local Premium spoof in patched owners")


if __name__ == "__main__":
    main()
