#!/usr/bin/env python3

from pathlib import Path
import importlib.util


# Keep the already-tested media/remote implementation byte-for-byte in the
# internal base. This adapter owns only the final voice UI shape that differs
# after GhostBase v1.1A TRANSCRIPTION1 removed its now-dead isConsumed local.
_BASE_PATH = Path(__file__).with_name("apply_jerkgram_v12m_build124_onetime_persistence_base1.py")
_spec = importlib.util.spec_from_file_location("build124_onetime_persistence_base1", _BASE_PATH)
_base = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_base)

for _name in dir(_base):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_base, _name)

# Canonical materialized Official owners (kept explicit for the Build124
# source-contract tests):
# submodules/TelegramCore/Sources/State/ManagedAutoremoveMessageOperations.swift
# submodules/TelegramCore/Sources/TelegramEngine/Messages/MarkMessageContentAsConsumedInteractively.swift
# submodules/TelegramUI/Components/Chat/ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift

VOICE_VISUAL_ANCHOR = '''                var consumableContentIcon: UIImage?
                for attribute in arguments.message.attributes {
                    if let attribute = attribute as? ConsumableContentMessageAttribute {
                        if !attribute.consumed {
'''

VOICE_VISUAL_REPLACEMENT = '''                var consumableContentIcon: UIImage?
                for attribute in arguments.message.attributes {
                    if let attribute = attribute as? ConsumableContentMessageAttribute {
                        // MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_VOICE_VISUAL1
                        // Read Telegram's real consumed bit directly. TRANSCRIPTION1 intentionally
                        // removed the old isConsumed local because its previous UI consumer vanished.
                        let jerkgramKeepConsumedOneTimeVisual = (
                            ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true)
                            && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false)
                            && arguments.message.id.peerId.namespace != Namespaces.Peer.SecretChat
                            && arguments.message.minAutoremoveOrClearTimeout == viewOnceTimeout
                        )
                        if !attribute.consumed || jerkgramKeepConsumedOneTimeVisual {
'''


def patch_voice_file_text(text: str) -> str:
    if VOICE_MARKER in text:
        return text

    require(
        text.count(VOICE_VISUAL_ANCHOR) == 1,
        f"expected one consumable voice visual loop owner, found {text.count(VOICE_VISUAL_ANCHOR)}",
    )
    updated = text.replace(VOICE_VISUAL_ANCHOR, VOICE_VISUAL_REPLACEMENT, 1)

    require(VOICE_MARKER in updated, "persistent one-time voice visual marker missing after patch")
    require(
        "if !attribute.consumed || jerkgramKeepConsumedOneTimeVisual" in updated,
        "real consumed state is not the voice visual source of truth",
    )
    require(
        "ConsumableContentMessageAttribute(consumed: false)" not in updated,
        "voice visual patch must never falsify consumed state",
    )
    return updated


def main() -> None:
    require(AUTOREMOVE_TARGET.is_file(), f"target missing: {AUTOREMOVE_TARGET}")
    require(REMOTE_TARGET.is_file(), f"target missing: {REMOTE_TARGET}")
    require(VOICE_TARGET.is_file(), f"target missing: {VOICE_TARGET}")

    autoremove_original = AUTOREMOVE_TARGET.read_text(encoding="utf-8")
    remote_original = REMOTE_TARGET.read_text(encoding="utf-8")
    voice_original = VOICE_TARGET.read_text(encoding="utf-8")

    autoremove_updated = patch_autoremove_text(autoremove_original)
    remote_updated = patch_remote_consumed_text(remote_original)
    voice_updated = patch_voice_file_text(voice_original)

    AUTOREMOVE_TARGET.write_text(autoremove_updated, encoding="utf-8")
    REMOTE_TARGET.write_text(remote_updated, encoding="utf-8")
    VOICE_TARGET.write_text(voice_updated, encoding="utf-8")

    print("[Build124 one-time persistence] GREEN")
    print("[Build124 one-time persistence] retained one-time media stays real across remote consumption and managed autoremove")
    print("[Build124 one-time persistence] post-TRANSCRIPTION1 voice UI reads Telegram consumed state directly")


if __name__ == "__main__":
    main()
