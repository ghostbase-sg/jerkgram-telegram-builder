#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
AUTOREMOVE_TARGET = ROOT / "submodules/TelegramCore/Sources/State/ManagedAutoremoveMessageOperations.swift"
REMOTE_TARGET = ROOT / "submodules/TelegramCore/Sources/TelegramEngine/Messages/MarkMessageContentAsConsumedInteractively.swift"
VOICE_TARGET = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift"

MEDIA_MARKER = "// MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_MEDIA1"
AUTOREMOVE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_MARKER1"
REMOTE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_REMOTE1"
VOICE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_VOICE_VISUAL1"


def fail(message: str) -> None:
    raise SystemExit("[verify Build124 one-time persistence] ERROR: " + message)


def require(value: bool, message: str) -> None:
    if not value:
        fail(message)


def main() -> None:
    require(AUTOREMOVE_TARGET.is_file(), f"target missing: {AUTOREMOVE_TARGET}")
    require(REMOTE_TARGET.is_file(), f"target missing: {REMOTE_TARGET}")
    require(VOICE_TARGET.is_file(), f"target missing: {VOICE_TARGET}")

    autoremove = AUTOREMOVE_TARGET.read_text(encoding="utf-8")
    remote = REMOTE_TARGET.read_text(encoding="utf-8")
    voice = VOICE_TARGET.read_text(encoding="utf-8")

    require(autoremove.count(MEDIA_MARKER) == 1, "persistent one-time media marker must exist exactly once")
    require(autoremove.count(AUTOREMOVE_MARKER) == 1, "persistent one-time marker must exist exactly once")
    require(remote.count(REMOTE_MARKER) == 1, "remote one-time persistence marker must exist exactly once")
    require(voice.count(VOICE_MARKER) == 1, "persistent one-time voice marker must exist exactly once")

    require("currentMessage.minAutoremoveOrClearTimeout == viewOnceTimeout" in autoremove, "managed autoremove is not limited to view-once media")
    require("currentMessage.attributes.contains(where: { $0 is ConsumableContentMessageAttribute })" in autoremove, "managed autoremove does not require consumable one-time media")
    require("currentMessage.id.peerId.namespace != Namespaces.Peer.SecretChat" in autoremove, "secret chats must stay on Telegram stock semantics")
    require("if !jerkgramKeepOneTimeIdentity {" in autoremove, "retained one-time media is still replaced by ExpiredContent")
    require(autoremove.count("let jerkgramKeepOneTimeIdentity = (") == 1, "one-time persistence decision must have exactly one owner")
    require("var updatedMedia = currentMessage.media" in autoremove, "Telegram media owner is missing")
    require("var updatedAttributes = currentMessage.attributes" in autoremove, "Telegram attribute owner is missing")
    require(
        autoremove.index("let jerkgramKeepOneTimeIdentity = (") < autoremove.index("var updatedMedia = currentMessage.media"),
        "one-time persistence decision runs after Telegram media expiration",
    )
    require(
        autoremove.index("var updatedMedia = currentMessage.media") < autoremove.index("var updatedAttributes = currentMessage.attributes"),
        "one-time media/attribute owner order changed unexpectedly",
    )
    require("TelegramMediaExpiredContent(data: .image)" in autoremove, "stock image expiration fallback was lost")
    require("TelegramMediaExpiredContent(data: .videoMessage)" in autoremove, "stock instant-video expiration fallback was lost")
    require("TelegramMediaExpiredContent(data: .voiceMessage)" in autoremove, "stock voice expiration fallback was lost")
    require("TelegramMediaExpiredContent(data: .file)" in autoremove, "stock file expiration fallback was lost")
    require("AutoclearTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: nil)" in autoremove, "persistent timed identity is not disarmed")
    require("updatedAttributes.remove(at: i)" in autoremove, "stock autoclear removal fallback was lost")
    require("ghostBaseOT1KeepOutgoingTimerLocal" not in autoremove, "legacy OT1 managed-autoremove owner survived Build124")
    require("GhostBase.OT1.AutoremoveKeepBlocked.Count" not in autoremove, "legacy OT1 managed-autoremove diagnostics survived Build124")

    require("message.minAutoremoveOrClearTimeout == viewOnceTimeout" in remote, "remote persistence is not limited to view-once media")
    require("message.attributes.contains(where: { $0 is ConsumableContentMessageAttribute })" in remote, "remote persistence does not require consumable one-time media")
    require("message.id.peerId.namespace != Namespaces.Peer.SecretChat" in remote, "remote persistence must not affect Secret Chats")
    require(remote.count("let jerkgramKeepOneTimeRemoteMedia = (") == 1, "remote one-time persistence decision must have exactly one owner")
    require(remote.count("if !jerkgramKeepOneTimeRemoteMedia && (attribute.timeout == viewOnceTimeout") == 2, "both remote media-expiration owners must be guarded")
    require("AutoremoveTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: nil)" in remote, "remote autoremove view-once countdown is still armed")
    require("AutoclearTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: nil)" in remote, "remote autoclear view-once countdown is still armed")
    require("AutoremoveTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: countdownBeginTime)" in remote, "stock remote autoremove countdown fallback was lost")
    require("AutoclearTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: countdownBeginTime)" in remote, "stock remote autoclear countdown fallback was lost")
    require("ConsumableContentMessageAttribute(consumed: true)" in remote, "remote consumed=true source of truth was lost")
    require("UserDefaults.standard.object(forKey: \"jerkgram.ProtectedContent.Enabled\")" in remote, "remote decision is not bound to the active protected-content setting")
    require("UserDefaults.standard.object(forKey: \"jerkgram.ProtectedContent.OneTimeSave\")" in remote, "remote decision is not bound to the active one-time persistence setting")

    require("arguments.message.minAutoremoveOrClearTimeout == viewOnceTimeout" in voice, "voice visual is not limited to view-once media")
    require("UserDefaults.standard.object(forKey: \"jerkgram.ProtectedContent.Enabled\")" in voice, "voice visual is not bound to the active protected-content setting")
    require("arguments.message.id.peerId.namespace != Namespaces.Peer.SecretChat" in voice, "voice override must not affect secret chats")
    require("if !attribute.consumed || jerkgramKeepConsumedOneTimeVisual" in voice, "consumed one-time voice visual is not retained")
    require("attribute.consumed" in voice, "real consumed state owner must remain authoritative")

    combined = autoremove + "\n" + remote + "\n" + voice
    require("ConsumableContentMessageAttribute(consumed: false)" not in combined, "consumed/read state must never be falsified")

    print("[verify Build124 one-time persistence] SOURCE VERIFIED")
    print("[verify Build124 one-time persistence] only consumable view-once media persist across remote consumption and managed autoremove; ordinary timed media keep Telegram behavior")


if __name__ == "__main__":
    main()
