#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
AUTOREMOVE_TARGET = ROOT / "submodules/TelegramCore/Sources/State/ManagedAutoremoveMessageOperations.swift"
VOICE_TARGET = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift"

MEDIA_MARKER = "// MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_MEDIA1"
AUTOREMOVE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_MARKER1"
VOICE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_VOICE_VISUAL1"


OLD_MEDIA = '''                                var updatedMedia = currentMessage.media
                                for i in 0 ..< updatedMedia.count {
                                    if let _ = updatedMedia[i] as? TelegramMediaImage {
                                        updatedMedia[i] = TelegramMediaExpiredContent(data: .image)
                                    } else if let file = updatedMedia[i] as? TelegramMediaFile {
                                        if file.isInstantVideo {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .videoMessage)
                                        } else if file.isVoice {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .voiceMessage)
                                        } else {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .file)
                                        }
                                    }
                                }
'''

NEW_MEDIA = '''                                // MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_MEDIA1
                                // Decide before Telegram replaces one-time media with ExpiredContent.
                                // Secret chats deliberately remain on Telegram's native lifecycle.
                                let jerkgramKeepOneTimeIdentity = (
                                    ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true)
                                    && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false)
                                    && currentMessage.id.peerId.namespace != Namespaces.Peer.SecretChat
                                    && currentMessage.minAutoremoveOrClearTimeout == viewOnceTimeout
                                )
                                var updatedMedia = currentMessage.media
                                if !jerkgramKeepOneTimeIdentity {
                                    for i in 0 ..< updatedMedia.count {
                                        if let _ = updatedMedia[i] as? TelegramMediaImage {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .image)
                                        } else if let file = updatedMedia[i] as? TelegramMediaFile {
                                            if file.isInstantVideo {
                                                updatedMedia[i] = TelegramMediaExpiredContent(data: .videoMessage)
                                            } else if file.isVoice {
                                                updatedMedia[i] = TelegramMediaExpiredContent(data: .voiceMessage)
                                            } else {
                                                updatedMedia[i] = TelegramMediaExpiredContent(data: .file)
                                            }
                                        }
                                    }
                                }
'''

OLD_AUTOCLEAR = '''                                var updatedAttributes = currentMessage.attributes
                                for i in 0 ..< updatedAttributes.count {
                                    if let _ = updatedAttributes[i] as? AutoclearTimeoutMessageAttribute {
                                        updatedAttributes.remove(at: i)
                                        break
                                    }
                                }
'''

# Build124's first persistence overlay declared the decision here, after Telegram
# had already expired the media. Keep this migration owner so rerunning the
# installer over an earlier materialized Build124 tree remains safe.
OLD_BUILD124_AUTOCLEAR = '''                                var updatedAttributes = currentMessage.attributes
                                // MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_MARKER1
                                // Keep the cloud view-once identity after Jerkgram retains the media, but
                                // disarm the timestamp operation. countdownBeginTime == nil means the
                                // replacement attribute is not scheduled for another autoremove pass.
                                let jerkgramKeepOneTimeIdentity = (
                                    ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true)
                                    && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false)
                                    && currentMessage.id.peerId.namespace != Namespaces.Peer.SecretChat
                                    && currentMessage.minAutoremoveOrClearTimeout == viewOnceTimeout
                                )
                                for i in 0 ..< updatedAttributes.count {
                                    if let attribute = updatedAttributes[i] as? AutoclearTimeoutMessageAttribute {
                                        if jerkgramKeepOneTimeIdentity && attribute.timeout == viewOnceTimeout {
                                            updatedAttributes[i] = AutoclearTimeoutMessageAttribute(timeout: viewOnceTimeout, countdownBeginTime: nil)
                                        } else {
                                            updatedAttributes.remove(at: i)
                                        }
                                        break
                                    }
                                }
'''

NEW_AUTOCLEAR = '''                                var updatedAttributes = currentMessage.attributes
                                // MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_MARKER1
                                // Preserve the cloud view-once identity for retained media, but disarm the
                                // timestamp operation. countdownBeginTime == nil does not schedule another pass.
                                for i in 0 ..< updatedAttributes.count {
                                    if let attribute = updatedAttributes[i] as? AutoclearTimeoutMessageAttribute {
                                        if jerkgramKeepOneTimeIdentity && attribute.timeout == viewOnceTimeout {
                                            updatedAttributes[i] = AutoclearTimeoutMessageAttribute(timeout: viewOnceTimeout, countdownBeginTime: nil)
                                        } else {
                                            updatedAttributes.remove(at: i)
                                        }
                                        break
                                    }
                                }
'''

OLD_VOICE = '''                var isConsumed: Bool?
                
                var consumableContentIcon: UIImage?
                for attribute in arguments.message.attributes {
                    if let attribute = attribute as? ConsumableContentMessageAttribute {
                        if !attribute.consumed {
                            if arguments.incoming {
                                consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentIncomingIcon(arguments.presentationData.theme.theme)
                            } else {
                                consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentOutgoingIcon(arguments.presentationData.theme.theme)
                            }
                        }
                        isConsumed = attribute.consumed
                        break
                    }
                }
'''

NEW_VOICE = '''                var isConsumed: Bool?
                
                var consumableContentIcon: UIImage?
                for attribute in arguments.message.attributes {
                    if let attribute = attribute as? ConsumableContentMessageAttribute {
                        // MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_VOICE_VISUAL1
                        // A retained one-time voice must stay visibly one-time after playback.
                        // Keep the real consumed bit untouched; it is also the source of truth for
                        // the outgoing viewed/listened state.
                        let jerkgramKeepConsumedOneTimeVisual = (
                            ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true)
                            && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false)
                            && arguments.message.id.peerId.namespace != Namespaces.Peer.SecretChat
                            && arguments.message.minAutoremoveOrClearTimeout == viewOnceTimeout
                        )
                        if !attribute.consumed || jerkgramKeepConsumedOneTimeVisual {
                            if arguments.incoming {
                                consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentIncomingIcon(arguments.presentationData.theme.theme)
                            } else {
                                consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentOutgoingIcon(arguments.presentationData.theme.theme)
                            }
                        }
                        isConsumed = attribute.consumed
                        break
                    }
                }
'''


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 one-time persistence] " + message)


def patch_autoremove_text(text: str) -> str:
    if MEDIA_MARKER in text and AUTOREMOVE_MARKER in text:
        return text

    updated = text

    # Migrate the first Build124 form before moving the decision ahead of media
    # expiration. This avoids two jerkgramKeepOneTimeIdentity declarations if a
    # previously materialized Build124 tree is patched again.
    if MEDIA_MARKER not in updated and AUTOREMOVE_MARKER in updated:
        require(
            updated.count(OLD_BUILD124_AUTOCLEAR) == 1,
            f"expected one legacy Build124 autoclear owner, found {updated.count(OLD_BUILD124_AUTOCLEAR)}",
        )
        updated = updated.replace(OLD_BUILD124_AUTOCLEAR, NEW_AUTOCLEAR, 1)

    if MEDIA_MARKER not in updated:
        require(updated.count(OLD_MEDIA) == 1, f"expected one managed-autoremove media owner, found {updated.count(OLD_MEDIA)}")
        updated = updated.replace(OLD_MEDIA, NEW_MEDIA, 1)

    if AUTOREMOVE_MARKER not in updated:
        require(updated.count(OLD_AUTOCLEAR) == 1, f"expected one managed-autoremove autoclear owner, found {updated.count(OLD_AUTOCLEAR)}")
        updated = updated.replace(OLD_AUTOCLEAR, NEW_AUTOCLEAR, 1)

    require(MEDIA_MARKER in updated, "persistent one-time media marker missing after patch")
    require(AUTOREMOVE_MARKER in updated, "persistent one-time marker missing after patch")
    require("if !jerkgramKeepOneTimeIdentity {" in updated, "one-time media expiration guard missing")
    require("AutoclearTimeoutMessageAttribute(timeout: viewOnceTimeout, countdownBeginTime: nil)" in updated, "disarmed persistent one-time attribute missing")
    require(updated.count("let jerkgramKeepOneTimeIdentity = (") == 1, "one-time persistence decision must have one owner")
    require(updated.index("let jerkgramKeepOneTimeIdentity = (") < updated.index("var updatedMedia = currentMessage.media"), "one-time persistence decision runs after media expiration")
    return updated


def patch_voice_file_text(text: str) -> str:
    if VOICE_MARKER in text:
        return text
    require(text.count(OLD_VOICE) == 1, f"expected one consumable voice icon owner, found {text.count(OLD_VOICE)}")
    updated = text.replace(OLD_VOICE, NEW_VOICE, 1)
    require(VOICE_MARKER in updated, "persistent one-time voice visual marker missing after patch")
    require("isConsumed = attribute.consumed" in updated, "real consumed state was lost")
    return updated


def main() -> None:
    require(AUTOREMOVE_TARGET.is_file(), f"target missing: {AUTOREMOVE_TARGET}")
    require(VOICE_TARGET.is_file(), f"target missing: {VOICE_TARGET}")

    autoremove_original = AUTOREMOVE_TARGET.read_text(encoding="utf-8")
    voice_original = VOICE_TARGET.read_text(encoding="utf-8")

    autoremove_updated = patch_autoremove_text(autoremove_original)
    voice_updated = patch_voice_file_text(voice_original)

    AUTOREMOVE_TARGET.write_text(autoremove_updated, encoding="utf-8")
    VOICE_TARGET.write_text(voice_updated, encoding="utf-8")

    print("[Build124 one-time persistence] GREEN")
    print("[Build124 one-time persistence] retained one-time media stays real and keeps its identity without rearming autoremove")
    print("[Build124 one-time persistence] consumed voice keeps the one-time visual while preserving consumed=true")


if __name__ == "__main__":
    main()
