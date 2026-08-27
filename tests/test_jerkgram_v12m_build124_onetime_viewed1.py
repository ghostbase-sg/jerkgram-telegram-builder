#!/usr/bin/env python3

from pathlib import Path
import importlib

from scripts.apply_jerkgram_v12m_build124_onetime_viewed1 import (
    patch_media_text,
    patch_voice_text,
)


MEDIA_FIXTURE = '''            if let remainingTime {
                if remainingTime == viewOnceTimeout {
                    badgeContent = .text(inset: 10.0, backgroundColor: messageTheme.mediaDateAndStatusFillColor, foregroundColor: messageTheme.mediaDateAndStatusTextColor, text: NSAttributedString(string: "1"), iconName: "Chat/Message/SecretMediaOnce")
                } else {
                    badgeContent = .text(inset: 10.0, backgroundColor: messageTheme.mediaDateAndStatusFillColor, foregroundColor: messageTheme.mediaDateAndStatusTextColor, text: NSAttributedString(string: strings.MessageTimer_ShortSeconds(Int32(remainingTime))), iconName: "Chat/Message/SecretMediaPlay")
                }
            }
'''

VOICE_FIXTURE = '''                        // MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_VOICE_VISUAL1
                        let jerkgramKeepConsumedOneTimeVisual = true
                        if !attribute.consumed || jerkgramKeepConsumedOneTimeVisual {
                            if arguments.incoming {
                                consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentIncomingIcon(arguments.presentationData.theme.theme)
                            } else {
                                consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentOutgoingIcon(arguments.presentationData.theme.theme)
                            }
                        }
                        isConsumed = attribute.consumed
'''


def test_outgoing_photo_video_badge_preserves_one_time_effect_and_adds_viewed_state():
    updated = patch_media_text(MEDIA_FIXTURE)

    assert "BUILD124_OUTGOING_ONETIME_VIEWED_MEDIA1" in updated
    assert "ConsumableContentMessageAttribute" in updated
    assert "attribute.consumed" in updated
    assert "!message.flags.contains(.Incoming)" in updated
    assert 'jerkgramOneTimeBadgeText = jerkgramOutgoingOneTimeViewed ? "1 ✓" : "1"' in updated
    assert 'iconName: "Chat/Message/SecretMediaOnce"' in updated


def test_outgoing_voice_indicator_keeps_one_time_dot_and_adds_viewed_check():
    updated = patch_voice_text(VOICE_FIXTURE)

    assert "BUILD124_OUTGOING_ONETIME_VIEWED_VOICE1" in updated
    assert "jerkgramKeepConsumedOneTimeVisual && attribute.consumed" in updated
    assert "context.fillEllipse" in updated
    assert "context.strokePath()" in updated
    assert "isConsumed = attribute.consumed" in updated


def test_viewed_patch_is_idempotent():
    once_media = patch_media_text(MEDIA_FIXTURE)
    assert patch_media_text(once_media) == once_media

    once_voice = patch_voice_text(VOICE_FIXTURE)
    assert patch_voice_text(once_voice) == once_voice


def test_circle_keeps_telegram_native_seen_state_owner():
    module = importlib.import_module("scripts.apply_jerkgram_v12m_build124_onetime_viewed1")
    source = Path(module.__file__).read_text(encoding="utf-8")

    assert "ChatMessageInteractiveInstantVideoNode" not in source
    assert "ChatMessageInteractiveMediaNode/Sources/ChatMessageInteractiveMediaNode.swift" in source
    assert "ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift" in source
