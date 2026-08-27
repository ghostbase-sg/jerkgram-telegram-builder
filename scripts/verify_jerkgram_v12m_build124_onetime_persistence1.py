#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
AUTOREMOVE_TARGET = ROOT / "submodules/TelegramCore/Sources/State/ManagedAutoremoveMessageOperations.swift"
VOICE_TARGET = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift"

AUTOREMOVE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_MARKER1"
VOICE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_VOICE_VISUAL1"


def fail(message: str) -> None:
    raise SystemExit("[verify Build124 one-time persistence] ERROR: " + message)


def require(value: bool, message: str) -> None:
    if not value:
        fail(message)


def main() -> None:
    require(AUTOREMOVE_TARGET.is_file(), f"target missing: {AUTOREMOVE_TARGET}")
    require(VOICE_TARGET.is_file(), f"target missing: {VOICE_TARGET}")

    autoremove = AUTOREMOVE_TARGET.read_text(encoding="utf-8")
    voice = VOICE_TARGET.read_text(encoding="utf-8")

    require(autoremove.count(AUTOREMOVE_MARKER) == 1, "persistent one-time marker must exist exactly once")
    require(voice.count(VOICE_MARKER) == 1, "persistent one-time voice marker must exist exactly once")

    require("currentMessage.minAutoremoveOrClearTimeout == viewOnceTimeout" in autoremove, "managed autoremove is not restricted to genuine view-once messages")
    require("currentMessage.id.peerId.namespace != Namespaces.Peer.SecretChat" in autoremove, "secret chats must stay on Telegram stock semantics")
    require("AutoclearTimeoutMessageAttribute(timeout: viewOnceTimeout, countdownBeginTime: nil)" in autoremove, "persistent one-time identity is not disarmed")
    require("updatedAttributes.remove(at: i)" in autoremove, "stock autoclear removal fallback was lost")

    require("arguments.message.minAutoremoveOrClearTimeout == viewOnceTimeout" in voice, "voice visual is not restricted to genuine view-once messages")
    require("arguments.message.id.peerId.namespace != Namespaces.Peer.SecretChat" in voice, "voice override must not affect secret chats")
    require("if !attribute.consumed || jerkgramKeepConsumedOneTimeVisual" in voice, "consumed one-time voice visual is not retained")
    require("isConsumed = attribute.consumed" in voice, "real consumed state must remain authoritative")

    combined = autoremove + "\n" + voice
    require("ConsumableContentMessageAttribute(consumed: false)" not in combined, "consumed/read state must never be falsified")

    print("[verify Build124 one-time persistence] SOURCE VERIFIED")
    print("[verify Build124 one-time persistence] view-once marker persists with countdownBeginTime=nil; voice visual persists while consumed state remains real")


if __name__ == "__main__":
    main()
