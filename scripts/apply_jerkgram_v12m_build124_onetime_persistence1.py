#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
AUTOREMOVE_TARGET = ROOT / "submodules/TelegramCore/Sources/State/ManagedAutoremoveMessageOperations.swift"
REMOTE_TARGET = ROOT / "submodules/TelegramCore/Sources/TelegramEngine/Messages/MarkMessageContentAsConsumedInteractively.swift"
VOICE_TARGET = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift"

MEDIA_MARKER = "// MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_MEDIA1"
AUTOREMOVE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_MARKER1"
REMOTE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_REMOTE1"
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

LEGACY_OT1_MEDIA_START = '''                                var updatedMedia = currentMessage.media
                                let ghostBaseOT1KeepOutgoingTimerLocal = '''
ATTRIBUTES_START = '''                                var updatedAttributes = currentMessage.attributes
'''

NEW_MEDIA = '''                                // MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_MEDIA1
                                // Decide before Telegram replaces one-time media with ExpiredContent.
                                // Secret chats deliberately remain on Telegram's native lifecycle.
                                let jerkgramKeepOneTimeIdentity = (
                                    ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.Enabled") as? Bool) ?? true)
                                    && ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.OneTimeSave") as? Bool) ?? false)
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
                                    ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.Enabled") as? Bool) ?? true)
                                    && ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.OneTimeSave") as? Bool) ?? false)
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

REMOTE_DECISION_ANCHOR = '''        let timestamp = Int32(CFAbsoluteTimeGetCurrent() + NSTimeIntervalSince1970)
        let countdownBeginTime = consumeDate ?? timestamp
        
        for i in 0 ..< updatedAttributes.count {
'''

REMOTE_DECISION = '''        let timestamp = Int32(CFAbsoluteTimeGetCurrent() + NSTimeIntervalSince1970)
        let countdownBeginTime = consumeDate ?? timestamp
        
        // MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_REMOTE1
        // A remote read receipt is the real consumed=true owner for outgoing
        // one-time media. Preserve the media and keep the view-once timeout
        // unscheduled when OneTimeSave is enabled; Secret Chats stay stock.
        let jerkgramKeepOneTimeRemoteMedia = (
            ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.Enabled") as? Bool) ?? true)
            && ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.OneTimeSave") as? Bool) ?? false)
            && message.id.peerId.namespace != Namespaces.Peer.SecretChat
            && message.minAutoremoveOrClearTimeout == viewOnceTimeout
        )
        
        for i in 0 ..< updatedAttributes.count {
'''

REMOTE_AUTOREMOVE_ASSIGNMENT = '''                    updatedAttributes[i] = AutoremoveTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: countdownBeginTime)
'''

REMOTE_AUTOREMOVE_ASSIGNMENT_PERSISTENT = '''                    if jerkgramKeepOneTimeRemoteMedia && attribute.timeout == viewOnceTimeout {
                        updatedAttributes[i] = AutoremoveTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: nil)
                    } else {
                        updatedAttributes[i] = AutoremoveTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: countdownBeginTime)
                    }
'''

REMOTE_AUTOCLEAR_ASSIGNMENT = '''                    updatedAttributes[i] = AutoclearTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: countdownBeginTime)
'''

REMOTE_AUTOCLEAR_ASSIGNMENT_PERSISTENT = '''                    if jerkgramKeepOneTimeRemoteMedia && attribute.timeout == viewOnceTimeout {
                        updatedAttributes[i] = AutoclearTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: nil)
                    } else {
                        updatedAttributes[i] = AutoclearTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: countdownBeginTime)
                    }
'''

REMOTE_EXPIRE_CONDITION = '''if attribute.timeout == viewOnceTimeout || timestamp >= countdownBeginTime + attribute.timeout {'''
REMOTE_EXPIRE_CONDITION_PERSISTENT = '''if !jerkgramKeepOneTimeRemoteMedia && (attribute.timeout == viewOnceTimeout || timestamp >= countdownBeginTime + attribute.timeout) {'''

LEGACY_REMOTE_IMAGE = '''                                if let _ = updatedMedia[i] as? TelegramMediaImage {
                                    let ghostBaseOT1KeepOutgoingTimerLocal = (((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat)
                                    if ghostBaseOT1KeepOutgoingTimerLocal {
                                        UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "GhostBase.OT1.OutgoingKeepBlocked.Count") + 1, forKey: "GhostBase.OT1.OutgoingKeepBlocked.Count")
                                        UserDefaults.standard.set("consumeImage", forKey: "GhostBase.OT1.OutgoingKeepPath")
                                    } else {
                                        updatedMedia[i] = TelegramMediaExpiredContent(data: .image)
                                    }
                                } else if let file = updatedMedia[i] as? TelegramMediaFile {
'''

STOCK_REMOTE_IMAGE = '''                                if let _ = updatedMedia[i] as? TelegramMediaImage {
                                    updatedMedia[i] = TelegramMediaExpiredContent(data: .image)
                                } else if let file = updatedMedia[i] as? TelegramMediaFile {
'''

LEGACY_REMOTE_FILE = '''                                    let ghostBaseKeepVoiceCircleLocal = (((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat && (file.isInstantVideo || file.isVoice))
                                    let ghostBaseOT1KeepOutgoingTimerLocal = (((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat)

                                    if file.isInstantVideo {
                                        if !(ghostBaseKeepVoiceCircleLocal || ghostBaseOT1KeepOutgoingTimerLocal) {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .videoMessage)
                                        } else {
                                            UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "GhostBase.OT1.OutgoingKeepBlocked.Count") + 1, forKey: "GhostBase.OT1.OutgoingKeepBlocked.Count")
                                            UserDefaults.standard.set("consumeInstantVideo", forKey: "GhostBase.OT1.OutgoingKeepPath")
                                        }
                                    } else if file.isVoice {
                                        if !(ghostBaseKeepVoiceCircleLocal || ghostBaseOT1KeepOutgoingTimerLocal) {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .voiceMessage)
                                        } else {
                                            UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "GhostBase.OT1.OutgoingKeepBlocked.Count") + 1, forKey: "GhostBase.OT1.OutgoingKeepBlocked.Count")
                                            UserDefaults.standard.set("consumeVoice", forKey: "GhostBase.OT1.OutgoingKeepPath")
                                        }
                                    } else {
                                        if !ghostBaseOT1KeepOutgoingTimerLocal {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .file)
                                        } else {
                                            UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "GhostBase.OT1.OutgoingKeepBlocked.Count") + 1, forKey: "GhostBase.OT1.OutgoingKeepBlocked.Count")
                                            UserDefaults.standard.set("consumeFile", forKey: "GhostBase.OT1.OutgoingKeepPath")
                                        }
                                    }
'''

STOCK_REMOTE_FILE = '''                                    if file.isInstantVideo {
                                        updatedMedia[i] = TelegramMediaExpiredContent(data: .videoMessage)
                                    } else if file.isVoice {
                                        updatedMedia[i] = TelegramMediaExpiredContent(data: .voiceMessage)
                                    } else {
                                        updatedMedia[i] = TelegramMediaExpiredContent(data: .file)
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
                            ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.Enabled") as? Bool) ?? true)
                            && ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.OneTimeSave") as? Bool) ?? false)
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


def replace_autoremove_media_owner(text: str) -> str:
    stock_count = text.count(OLD_MEDIA)
    legacy_count = text.count(LEGACY_OT1_MEDIA_START)
    require(not (stock_count and legacy_count), "both stock and legacy OT1 managed-autoremove owners are present")

    if stock_count == 1:
        return text.replace(OLD_MEDIA, NEW_MEDIA, 1)

    if legacy_count == 1:
        start = text.index(LEGACY_OT1_MEDIA_START)
        end = text.find(ATTRIBUTES_START, start)
        require(end >= 0, "legacy OT1 managed-autoremove owner has no attribute boundary")
        segment = text[start:end]
        require("ghostBaseOT1KeepOutgoingTimerLocal" in segment, "legacy OT1 keep decision missing")
        require("TelegramMediaExpiredContent(data: .image)" in segment, "legacy OT1 image fallback missing")
        require("TelegramMediaExpiredContent(data: .videoMessage)" in segment, "legacy OT1 instant-video fallback missing")
        require("TelegramMediaExpiredContent(data: .voiceMessage)" in segment, "legacy OT1 voice fallback missing")
        require("TelegramMediaExpiredContent(data: .file)" in segment, "legacy OT1 file fallback missing")
        return text[:start] + NEW_MEDIA + text[end:]

    require(stock_count == 1 or legacy_count == 1, f"expected one stock or legacy OT1 managed-autoremove media owner, found stock={stock_count} legacy={legacy_count}")
    return text


def normalize_legacy_remote_owner(text: str) -> str:
    legacy_present = (
        "ghostBaseOT1KeepOutgoingTimerLocal" in text
        or "GhostBase.OT1.OutgoingKeepBlocked.Count" in text
        or "GhostBase.OT1.OutgoingKeepPath" in text
    )
    if not legacy_present:
        return text

    # Build123 materialization has two historical shapes. Normalize the
    # verbatim shape when present; the equivalent newer bookkeeping is left for
    # the authoritative remote-consumption guard below.
    if text.count(LEGACY_REMOTE_IMAGE) != 1 or text.count(LEGACY_REMOTE_FILE) != 1:
        return text
    updated = text.replace(LEGACY_REMOTE_IMAGE, STOCK_REMOTE_IMAGE, 1)
    updated = updated.replace(LEGACY_REMOTE_FILE, STOCK_REMOTE_FILE, 1)
    require("ghostBaseOT1KeepOutgoingTimerLocal" not in updated, "legacy OT1 remote keep decision survived normalization")
    require("ghostBaseKeepVoiceCircleLocal" not in updated, "legacy voice/circle remote keep decision survived normalization")
    require("GhostBase.OT1.OutgoingKeepBlocked.Count" not in updated, "legacy OT1 remote diagnostics survived normalization")
    require("GhostBase.OT1.OutgoingKeepPath" not in updated, "legacy OT1 remote path diagnostics survived normalization")
    return updated


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
        updated = replace_autoremove_media_owner(updated)

    if AUTOREMOVE_MARKER not in updated:
        require(updated.count(OLD_AUTOCLEAR) == 1, f"expected one managed-autoremove autoclear owner, found {updated.count(OLD_AUTOCLEAR)}")
        updated = updated.replace(OLD_AUTOCLEAR, NEW_AUTOCLEAR, 1)

    require(MEDIA_MARKER in updated, "persistent one-time media marker missing after patch")
    require(AUTOREMOVE_MARKER in updated, "persistent one-time marker missing after patch")
    require("if !jerkgramKeepOneTimeIdentity {" in updated, "one-time media expiration guard missing")
    require("AutoclearTimeoutMessageAttribute(timeout: viewOnceTimeout, countdownBeginTime: nil)" in updated, "disarmed persistent one-time attribute missing")
    require(updated.count("let jerkgramKeepOneTimeIdentity = (") == 1, "one-time persistence decision must have one owner")
    require(updated.index("let jerkgramKeepOneTimeIdentity = (") < updated.index("var updatedMedia = currentMessage.media"), "one-time persistence decision runs after media expiration")
    require("ghostBaseOT1KeepOutgoingTimerLocal" not in updated, "legacy OT1 managed-autoremove decision survived Build124 replacement")
    require("GhostBase.OT1.AutoremoveKeepBlocked.Count" not in updated, "legacy OT1 managed-autoremove diagnostics survived Build124 replacement")
    return updated


def patch_remote_consumed_text(text: str) -> str:
    updated = normalize_legacy_remote_owner(text)
    if REMOTE_MARKER in updated:
        return updated

    # Anchor only the actual Telegram countdown prelude; whitespace between
    # the lines is non-semantic and varies across upstream formatting.
    decision = re.search(
        r"(?m)^(?P<indent>[ \t]*)let timestamp = Int32\(CFAbsoluteTimeGetCurrent\(\) \+ NSTimeIntervalSince1970\)\n"
        r"(?P=indent)let countdownBeginTime = consumeDate \?\? timestamp\n"
        r"[ \t]*\n(?P=indent)for i in 0 \.\.< updatedAttributes.count \{",
        updated,
    )
    require(decision is not None, "remote-consume countdown owner missing")
    require(updated.count(REMOTE_AUTOREMOVE_ASSIGNMENT) == 1, f"expected one remote autoremove assignment, found {updated.count(REMOTE_AUTOREMOVE_ASSIGNMENT)}")
    require(updated.count(REMOTE_AUTOCLEAR_ASSIGNMENT) == 1, f"expected one remote autoclear assignment, found {updated.count(REMOTE_AUTOCLEAR_ASSIGNMENT)}")
    require(updated.count(REMOTE_EXPIRE_CONDITION) == 2, f"expected two remote media-expiration owners, found {updated.count(REMOTE_EXPIRE_CONDITION)}")

    # REMOTE_DECISION includes the loop opener, so discard the matched source opener too.
    updated = updated[:decision.start()] + REMOTE_DECISION + updated[decision.end():]
    updated = updated.replace(REMOTE_AUTOREMOVE_ASSIGNMENT, REMOTE_AUTOREMOVE_ASSIGNMENT_PERSISTENT, 1)
    updated = updated.replace(REMOTE_AUTOCLEAR_ASSIGNMENT, REMOTE_AUTOCLEAR_ASSIGNMENT_PERSISTENT, 1)
    updated = updated.replace(REMOTE_EXPIRE_CONDITION, REMOTE_EXPIRE_CONDITION_PERSISTENT, 2)

    require(REMOTE_MARKER in updated, "remote one-time persistence marker missing after patch")
    require(updated.count("let jerkgramKeepOneTimeRemoteMedia = (") == 1, "remote one-time persistence decision must have one owner")
    require(updated.count(REMOTE_EXPIRE_CONDITION_PERSISTENT) == 2, "remote one-time media expiration guards are incomplete")
    require("AutoremoveTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: nil)" in updated, "remote autoremove view-once countdown is still armed")
    require("AutoclearTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: nil)" in updated, "remote autoclear view-once countdown is still armed")
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
    print("[Build124 one-time persistence] legacy OT1 autoremove and remote-consume owners collapse into the single Build124 owners")
    print("[Build124 one-time persistence] view-once countdown remains unscheduled when persistence is enabled")
    print("[Build124 one-time persistence] consumed voice keeps the one-time visual while preserving consumed=true")


if __name__ == "__main__":
    main()
