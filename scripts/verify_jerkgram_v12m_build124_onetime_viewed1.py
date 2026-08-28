#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
MEDIA_TARGET = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveMediaNode/Sources/ChatMessageInteractiveMediaNode.swift"
VOICE_TARGET = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift"
INSTANT_VIDEO_TARGET = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveInstantVideoNode/Sources/ChatMessageInteractiveInstantVideoNode.swift"

MEDIA_MARKER = "// MARK: Jerkgram v1.2M BUILD124_OUTGOING_ONETIME_VIEWED_MEDIA1"
VOICE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_OUTGOING_ONETIME_VIEWED_VOICE1"


def fail(message: str) -> None:
    raise SystemExit("[verify Build124 one-time viewed] ERROR: " + message)


def require(value: bool, message: str) -> None:
    if not value:
        fail(message)


def main() -> None:
    require(MEDIA_TARGET.is_file(), f"target missing: {MEDIA_TARGET}")
    require(VOICE_TARGET.is_file(), f"target missing: {VOICE_TARGET}")
    require(INSTANT_VIDEO_TARGET.is_file(), f"target missing: {INSTANT_VIDEO_TARGET}")

    media = MEDIA_TARGET.read_text(encoding="utf-8")
    voice = VOICE_TARGET.read_text(encoding="utf-8")
    instant_video = INSTANT_VIDEO_TARGET.read_text(encoding="utf-8")

    require(media.count(MEDIA_MARKER) == 1, "outgoing photo/video viewed marker must exist exactly once")
    require(voice.count(VOICE_MARKER) == 1, "outgoing voice viewed marker must exist exactly once")

    require("ConsumableContentMessageAttribute" in media, "photo/video viewed state must come from consumable-content state")
    require("return attribute.consumed" in media, "photo/video viewed state is not tied to consumed=true")
    require("!message.effectivelyIncoming(context.account.peerId)" in media, "photo/video viewed badge must use Telegram effective outgoing semantics")
    require("!message.flags.contains(.Incoming)" not in media, "raw incoming flag must not own outgoing viewed semantics")
    require('jerkgramOneTimeBadgeText = jerkgramOutgoingOneTimeViewed ? "1 ✓" : "1"' in media, "photo/video viewed badge state missing")
    require('iconName: "Chat/Message/SecretMediaOnce"' in media, "photo/video one-time effect icon was removed")

    require("jerkgramKeepConsumedOneTimeVisual && attribute.consumed" in voice, "voice viewed state must come from the real consumed bit")
    require("context.fillEllipse" in voice, "voice one-time dot was removed from combined viewed icon")
    require("context.strokePath()" in voice, "voice viewed check is missing")
    require("if !attribute.consumed || jerkgramKeepConsumedOneTimeVisual" in voice, "persistent voice owner no longer follows Telegram consumed state")
    require("ConsumableContentMessageAttribute(consumed: false)" not in voice, "voice consumed state must never be falsified")

    # Official 12.9.2 already maps ConsumableContentMessageAttribute to durationNode.isSeen.
    # Build124 intentionally leaves this owner stock instead of layering another indicator.
    require("durationNode.isSeen = !notConsumed" in instant_video, "native circle viewed/seen owner missing")
    require(MEDIA_MARKER not in instant_video and VOICE_MARKER not in instant_video, "Build124 viewed overlay must not patch the native circle seen owner")

    print("[verify Build124 one-time viewed] SOURCE VERIFIED")
    print("[verify Build124 one-time viewed] outgoing photo/video: SecretMediaOnce + 1 ✓ after consumed=true using Telegram effective direction")
    print("[verify Build124 one-time viewed] outgoing voice: one-time dot + viewed check after consumed=true on post-transcription owner")
    print("[verify Build124 one-time viewed] circle: Telegram native isSeen state preserved")


if __name__ == "__main__":
    main()
