#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src",
)).resolve()

BG = ROOT / (
    "submodules/TelegramUI/Components/PeerInfo/"
    "PeerInfoScreen/Sources/"
    "GhostBaseProfileFullscreenBackground.swift"
)

PIPELINE_MARK = "GhostBase v1.1T BUILD97_STATIC_AVATAR_PIPELINE1"
BUILD120_MARK = "Jerkgram v1.2I BUILD120_PROFILE_COLDSTART1"
BUILD113_MARK = "Jerkgram v1.2B BUILD113_STATIC_AVATAR_BLUR_OWNER1"
CACHE_MARK = "GhostBase v1.1T AVATAR_REOPEN_NO_GREY1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build120 profile blur verify] " + message)


def main() -> None:
    require(BG.is_file(), "profile background source missing: " + str(BG))
    text = BG.read_text(encoding="utf-8")

    for token in (PIPELINE_MARK, BUILD120_MARK, BUILD113_MARK, CACHE_MARK):
        require(token in text, "owner missing: " + token)

    start = text.find("    // MARK: " + PIPELINE_MARK + "\n")
    end = text.find("    private func resourceEntrySignal(\n", start)
    require(start >= 0 and end > start, "static avatar pipeline boundaries missing")
    avatar = text[start:end]

    require("blurred: false" in avatar, "static avatar decode unexpectedly requests pre-blurred pixels")
    require("synchronousLoad: true" in avatar, "Build120 synchronous cold-start load missing")
    require("synchronousLoad: false" not in avatar, "synchronousLoad false survived in static avatar owner")
    require(avatar.count(BUILD120_MARK) == 1, "Build120 cold-start owner count != 1")

    blur_start = text.find("            // MARK: " + BUILD113_MARK + "\n")
    blur_end = text.find("\n        case .telegramTheme:", blur_start)
    require(blur_start >= 0, "Build113 static blur owner start missing")
    if blur_end < 0:
        blur_end = min(len(text), blur_start + 5000)
    blur = text[blur_start:blur_end]

    require("systemMaterialDark" in blur, "Build113 dark systemMaterial owner missing")
    require("systemMaterialLight" in blur, "Build113 light systemMaterial owner missing")
    require("self.blurView.alpha = 1.0" in blur, "persistent blur owner is not fully opaque")

    cache_start = text.find("            // MARK: " + CACHE_MARK + "\n")
    cache_end = text.find("            self.applyAnimatedMedia(", cache_start)
    require(cache_start >= 0, "Build105 reopen cache owner missing")
    if cache_end < 0:
        cache_end = min(len(text), cache_start + 5000)
    cache = text[cache_start:cache_end]
    require("Self.imageCache.object" in cache, "RAM reopen cache missing")
    require("ghostBaseLoadAvatarDiskCache" in cache, "bounded disk reopen cache missing")

    print("[Build120 profile blur verify] GREEN")
    print("[Build120 profile blur verify] static avatar cold load is synchronous through Telegram peerAvatarImage")
    print("[Build120 profile blur verify] decoded source remains unblurred before the single Build113 material owner")
    print("[Build120 profile blur verify] RAM/disk reopen cache remains intact")


if __name__ == "__main__":
    main()
