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

MARK = "Jerkgram v1.2I BUILD120_PROFILE_COLDSTART1"
PIPELINE_MARK = "GhostBase v1.1T BUILD97_STATIC_AVATAR_PIPELINE1"
BLUR_MARK = "GhostBase v1.1U BUILD106_STATIC_AVATAR_BLUR1"
BUILD114_MARK = "Jerkgram v1.2C BUILD114_SOURCE_LUMINANCE1"
REMOVED_BUILD113_MARK = "Jerkgram v1.2B BUILD113_STATIC_AVATAR_BLUR_OWNER1"
CACHE_MARK = "GhostBase v1.1T AVATAR_REOPEN_NO_GREY1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build120 profile blur lifecycle] " + message)


def main() -> None:
    require(BG.is_file(), "profile background source missing: " + str(BG))
    text = BG.read_text(encoding="utf-8")

    if MARK in text:
        print("[Build120 profile blur lifecycle] already materialized")
        return

    # Build114 intentionally removed the Build113 systemMaterial override and
    # restored the Build106 persistent-alpha owner. Bind Build120 to the
    # actually materialized final chain instead of silently reviving Build113.
    for token in (PIPELINE_MARK, BLUR_MARK, BUILD114_MARK, CACHE_MARK):
        require(token in text, "required final owner missing: " + token)
    require(
        REMOVED_BUILD113_MARK not in text,
        "obsolete Build113 blur owner unexpectedly survived Build114",
    )

    start = text.find("    // MARK: " + PIPELINE_MARK + "\n")
    end = text.find("    private func resourceEntrySignal(\n", start)
    require(start >= 0 and end > start, "static avatar pipeline boundaries missing")

    region = text[start:end]
    require("blurred: false" in region, "Telegram avatar pipeline no longer owns unblurred decode")
    require(region.count("synchronousLoad: false") == 1, "expected one async static-avatar load owner")
    require("synchronousLoad: true" not in region, "unexpected pre-existing synchronous static-avatar load")

    # The native circular avatar has normally already populated Telegram's
    # avatar cache when PeerInfo opens. Ask the same peerAvatarImage pipeline
    # for its cached presentation synchronously so the fullscreen background
    # does not spend its first rendered frame on itemBlocksBackgroundColor.
    # If Telegram still needs network/media work, the existing signal remains
    # live and completes normally. No raw MediaBox decode, disk scan, observer,
    # image processing pass, or second blur stage is introduced here.
    region = region.replace(
        "            synchronousLoad: false\n",
        "            // MARK: Jerkgram v1.2I BUILD120_PROFILE_COLDSTART1\n"
        "            synchronousLoad: true\n",
        1,
    )

    text = text[:start] + region + text[end:]
    BG.write_text(text, encoding="utf-8")

    print("[Build120 profile blur lifecycle] GREEN")
    print("[Build120 profile blur lifecycle] cold/open/reopen use Telegram cached avatar synchronously when available")
    print("[Build120 profile blur lifecycle] Build114-restored Build106 persistent blur owner preserved")
    print("[Build120 profile blur lifecycle] Build105 bounded RAM/disk reopen cache preserved")


if __name__ == "__main__":
    main()
