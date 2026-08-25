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
BLUR_MARK = "Jerkgram v1.2B BUILD113_STATIC_AVATAR_BLUR_OWNER1"
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

    # Bound this overlay to the exact final owners proven by the Build105 ->
    # Build106 -> Build113 chain. Do not adapt silently to a different profile
    # implementation.
    for token in (PIPELINE_MARK, BLUR_MARK, CACHE_MARK):
        require(token in text, "required final owner missing: " + token)

    start = text.find("    // MARK: " + PIPELINE_MARK + "\n")
    end = text.find("    private func resourceEntrySignal(\n", start)
    require(start >= 0 and end > start, "static avatar pipeline boundaries missing")

    region = text[start:end]
    require("blurred: false" in region, "Telegram avatar pipeline no longer owns unblurred decode")
    require(region.count("synchronousLoad: false") == 1, "expected one async static-avatar load owner")
    require("synchronousLoad: true" not in region, "unexpected pre-existing synchronous static-avatar load")

    # BUILD120_PROFILE_COLDSTART1
    # The native circular avatar has normally already populated Telegram's
    # avatar cache when PeerInfo opens. Ask the same peerAvatarImage pipeline
    # for its cached presentation synchronously so the fullscreen background
    # does not spend its first rendered frame on itemBlocksBackgroundColor.
    # If Telegram still needs network/media work, the existing signal remains
    # live and completes normally; this does not add raw MediaBox decoding,
    # disk scans, image processing, observers, or a second blur stage.
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
    print("[Build120 profile blur lifecycle] Build113 systemMaterial owner preserved")
    print("[Build120 profile blur lifecycle] Build105 bounded RAM/disk reopen cache preserved")


if __name__ == "__main__":
    main()
