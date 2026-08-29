#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
MEDIA_TARGET = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveMediaNode/Sources/ChatMessageInteractiveMediaNode.swift"
VOICE_TARGET = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift"
INSTANT_VIDEO_TARGET = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveInstantVideoNode/Sources/ChatMessageInteractiveInstantVideoNode.swift"

MEDIA_MARKER = "// MARK: Jerkgram v1.2M BUILD124_OUTGOING_ONETIME_VIEWED_MEDIA1"
VOICE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_OUTGOING_ONETIME_VIEWED_VOICE1"
PERSISTENT_VOICE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_VOICE_VISUAL1"
CIRCLE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_OUTGOING_ONETIME_VIEWED_CIRCLE1"


OLD_MEDIA = '''            if let remainingTime {
                if remainingTime == viewOnceTimeout {
                    badgeContent = .text(inset: 10.0, backgroundColor: messageTheme.mediaDateAndStatusFillColor, foregroundColor: messageTheme.mediaDateAndStatusTextColor, text: NSAttributedString(string: "1"), iconName: "Chat/Message/SecretMediaOnce")
                } else {
                    badgeContent = .text(inset: 10.0, backgroundColor: messageTheme.mediaDateAndStatusFillColor, foregroundColor: messageTheme.mediaDateAndStatusTextColor, text: NSAttributedString(string: strings.MessageTimer_ShortSeconds(Int32(remainingTime))), iconName: "Chat/Message/SecretMediaPlay")
                }
            }
'''

NEW_MEDIA = '''            if let remainingTime {
                let jerkgramOutgoingTimedMediaViewed = (
                    ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.Enabled") as? Bool) ?? true)
                    && ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.OneTimeSave") as? Bool) ?? false)
                    && message.id.peerId.namespace != Namespaces.Peer.SecretChat
                    && (context.map { !message.effectivelyIncoming($0.account.peerId) } ?? false)
                    && message.attributes.contains(where: { attribute in
                        if let attribute = attribute as? ConsumableContentMessageAttribute {
                            return attribute.consumed
                        }
                        return false
                    })
                )
                if remainingTime == viewOnceTimeout {
                    // MARK: Jerkgram v1.2M BUILD124_OUTGOING_ONETIME_VIEWED_MEDIA1
                    // Preserve Telegram's one-time badge and add a compact viewed state only
                    // when the real consumable-content state says the recipient opened it.
                    let jerkgramOneTimeBadgeText = jerkgramOutgoingTimedMediaViewed ? "1 ✓" : "1"
                    badgeContent = .text(inset: 10.0, backgroundColor: messageTheme.mediaDateAndStatusFillColor, foregroundColor: messageTheme.mediaDateAndStatusTextColor, text: NSAttributedString(string: jerkgramOneTimeBadgeText), iconName: "Chat/Message/SecretMediaOnce")
                } else {
                    let jerkgramTimedBadgeText = strings.MessageTimer_ShortSeconds(Int32(remainingTime)) + (jerkgramOutgoingTimedMediaViewed ? " ✓" : "")
                    badgeContent = .text(inset: 10.0, backgroundColor: messageTheme.mediaDateAndStatusFillColor, foregroundColor: messageTheme.mediaDateAndStatusTextColor, text: NSAttributedString(string: jerkgramTimedBadgeText), iconName: "Chat/Message/SecretMediaPlay")
                }
            }
'''

OLD_VOICE_OUTGOING = '''                            } else {
                                consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentOutgoingIcon(arguments.presentationData.theme.theme)
                            }
                        }
                        break
'''

NEW_VOICE_OUTGOING = '''                            } else {
                                // MARK: Jerkgram v1.2M BUILD124_OUTGOING_ONETIME_VIEWED_VOICE1
                                // Keep the native one-time dot and append a compact check after real consumption.
                                let jerkgramOutgoingOneTimeViewed = jerkgramKeepConsumedOneTimeVisual && attribute.consumed
                                if jerkgramOutgoingOneTimeViewed {
                                    let jerkgramViewedColor = arguments.presentationData.theme.theme.chat.message.outgoing.accentTextColor
                                    consumableContentIcon = generateImage(CGSize(width: 13.0, height: 7.0), contextGenerator: { size, context in
                                        context.clear(CGRect(origin: .zero, size: size))
                                        context.setFillColor(jerkgramViewedColor.cgColor)
                                        context.fillEllipse(in: CGRect(x: 0.0, y: 1.5, width: 4.0, height: 4.0))
                                        context.setStrokeColor(jerkgramViewedColor.cgColor)
                                        context.setLineWidth(1.4)
                                        context.setLineCap(.round)
                                        context.setLineJoin(.round)
                                        context.move(to: CGPoint(x: 6.0, y: 3.6))
                                        context.addLine(to: CGPoint(x: 8.2, y: 5.4))
                                        context.addLine(to: CGPoint(x: 12.2, y: 1.4))
                                        context.strokePath()
                                    })
                                } else {
                                    consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentOutgoingIcon(arguments.presentationData.theme.theme)
                                }
                            }
                        }
                        break
'''

OLD_CIRCLE_CONSUMED = '''            var notConsumed = false
            for attribute in item.message.attributes {
                if let attribute = attribute as? ConsumableContentMessageAttribute {
                    if !attribute.consumed {
                        notConsumed = true
                    }
                    break
                }
            }
            if item.message.id.namespace == Namespaces.Message.Local || item.message.id.namespace == Namespaces.Message.ScheduledLocal || item.message.id.namespace == Namespaces.Message.QuickReplyLocal {
                notConsumed = true
            }
'''

NEW_CIRCLE_CONSUMED = '''            // MARK: Jerkgram v1.2M BUILD124_OUTGOING_ONETIME_VIEWED_CIRCLE1
            // Preserve the one-time circle affordance after the recipient has
            // watched an outgoing circle, but keep Telegram's real consumed bit
            // as the source of the viewed state. Incoming circles stay native.
            var notConsumed = false
            var jerkgramOutgoingOneTimeCircleViewed = false
            for attribute in item.message.attributes {
                if let attribute = attribute as? ConsumableContentMessageAttribute {
                    if !attribute.consumed {
                        notConsumed = true
                    } else if (
                        ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.Enabled") as? Bool) ?? true)
                        && ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.OneTimeSave") as? Bool) ?? false)
                        && !item.message.effectivelyIncoming(item.context.account.peerId)
                    ) {
                        jerkgramOutgoingOneTimeCircleViewed = true
                        // Existing layout code uses notConsumed to retain the
                        // one-time effect. Do not falsify the message attribute.
                        notConsumed = true
                    }
                    break
                }
            }
            if item.message.id.namespace == Namespaces.Message.Local || item.message.id.namespace == Namespaces.Message.ScheduledLocal || item.message.id.namespace == Namespaces.Message.QuickReplyLocal {
                notConsumed = true
            }
'''

OLD_CIRCLE_SEEN = '''                        durationNode.isSeen = !notConsumed || item.presentationData.isPreview'''
NEW_CIRCLE_SEEN = '''                        durationNode.isSeen = !notConsumed || jerkgramOutgoingOneTimeCircleViewed || item.presentationData.isPreview'''


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 one-time viewed] " + message)


def patch_media_text(text: str) -> str:
    if MEDIA_MARKER in text:
        return text
    require(text.count(OLD_MEDIA) == 1, f"expected one view-once media badge owner, found {text.count(OLD_MEDIA)}")
    updated = text.replace(OLD_MEDIA, NEW_MEDIA, 1)
    require(MEDIA_MARKER in updated, "outgoing media viewed marker missing after patch")
    require("context.map { !message.effectivelyIncoming($0.account.peerId) } ?? false" in updated, "outgoing media viewed state is not using optional Telegram context safely")
    require('jerkgramOneTimeBadgeText = jerkgramOutgoingTimedMediaViewed ? "1 ✓" : "1"' in updated, "viewed media badge state missing")
    require('jerkgramTimedBadgeText = strings.MessageTimer_ShortSeconds(Int32(remainingTime)) + (jerkgramOutgoingTimedMediaViewed ? " ✓" : "")' in updated, "timed media viewed badge state missing")
    require('iconName: "Chat/Message/SecretMediaOnce"' in updated, "one-time media effect icon was lost")
    return updated


def patch_voice_text(text: str) -> str:
    if VOICE_MARKER in text:
        return text
    require(PERSISTENT_VOICE_MARKER in text, "persistent one-time voice visual must be applied before viewed-state overlay")
    require(text.count(OLD_VOICE_OUTGOING) == 1, f"expected one outgoing consumable voice icon owner, found {text.count(OLD_VOICE_OUTGOING)}")
    updated = text.replace(OLD_VOICE_OUTGOING, NEW_VOICE_OUTGOING, 1)
    require(VOICE_MARKER in updated, "outgoing voice viewed marker missing after patch")
    require("jerkgramKeepConsumedOneTimeVisual && attribute.consumed" in updated, "viewed voice state is not tied to the real consumed bit")
    require("attribute.consumed" in updated, "real consumed state owner was lost")
    return updated


def patch_circle_text(text: str) -> str:
    if CIRCLE_MARKER in text:
        return text
    require(text.count(OLD_CIRCLE_CONSUMED) == 1, f"expected one instant-video consumable owner, found {text.count(OLD_CIRCLE_CONSUMED)}")
    require(text.count(OLD_CIRCLE_SEEN) == 1, f"expected one instant-video seen owner, found {text.count(OLD_CIRCLE_SEEN)}")
    updated = text.replace(OLD_CIRCLE_CONSUMED, NEW_CIRCLE_CONSUMED, 1)
    updated = updated.replace(OLD_CIRCLE_SEEN, NEW_CIRCLE_SEEN, 1)
    require(CIRCLE_MARKER in updated, "outgoing circle viewed marker missing after patch")
    require("!item.message.effectivelyIncoming(item.context.account.peerId)" in updated, "circle viewed state is not limited to outgoing messages")
    require("jerkgramOutgoingOneTimeCircleViewed ||" in updated, "circle viewed state is not reflected by the native seen affordance")
    return updated


def main() -> None:
    require(MEDIA_TARGET.is_file(), f"target missing: {MEDIA_TARGET}")
    require(VOICE_TARGET.is_file(), f"target missing: {VOICE_TARGET}")
    require(INSTANT_VIDEO_TARGET.is_file(), f"target missing: {INSTANT_VIDEO_TARGET}")

    media_original = MEDIA_TARGET.read_text(encoding="utf-8")
    voice_original = VOICE_TARGET.read_text(encoding="utf-8")
    circle_original = INSTANT_VIDEO_TARGET.read_text(encoding="utf-8")

    media_updated = patch_media_text(media_original)
    voice_updated = patch_voice_text(voice_original)
    circle_updated = patch_circle_text(circle_original)

    MEDIA_TARGET.write_text(media_updated, encoding="utf-8")
    VOICE_TARGET.write_text(voice_updated, encoding="utf-8")
    INSTANT_VIDEO_TARGET.write_text(circle_updated, encoding="utf-8")

    print("[Build124 one-time viewed] GREEN")
    print("[Build124 one-time viewed] outgoing photo/video keeps SecretMediaOnce and shows 1 ✓ after real consumption")
    print("[Build124 one-time viewed] outgoing voice keeps one-time dot and adds a viewed check after real consumption")
    print("[Build124 one-time viewed] outgoing circle keeps the one-time effect and reflects real consumed=true through Telegram's seen affordance")


if __name__ == "__main__":
    main()
