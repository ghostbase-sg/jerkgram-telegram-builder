#!/usr/bin/env python3

from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12m_build124_onetime_viewed1.py"

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
'''


class Build124OneTimeViewedTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_onetime_viewed", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_outgoing_photo_video_badge_preserves_one_time_effect_and_adds_viewed_state(self):
        module = self.load_patch()
        updated = module.patch_media_text(MEDIA_FIXTURE)
        self.assertIn("BUILD124_OUTGOING_ONETIME_VIEWED_MEDIA1", updated)
        self.assertIn("ConsumableContentMessageAttribute", updated)
        self.assertIn("attribute.consumed", updated)
        self.assertIn("!message.effectivelyIncoming(context.account.peerId)", updated)
        self.assertNotIn("!message.flags.contains(.Incoming)", updated)
        self.assertIn('jerkgramOneTimeBadgeText = jerkgramOutgoingOneTimeViewed ? "1 ✓" : "1"', updated)
        self.assertIn('iconName: "Chat/Message/SecretMediaOnce"', updated)

    def test_outgoing_voice_indicator_keeps_one_time_dot_and_adds_viewed_check(self):
        module = self.load_patch()
        updated = module.patch_voice_text(VOICE_FIXTURE)
        self.assertIn("BUILD124_OUTGOING_ONETIME_VIEWED_VOICE1", updated)
        self.assertIn("jerkgramKeepConsumedOneTimeVisual && attribute.consumed", updated)
        self.assertIn("context.fillEllipse", updated)
        self.assertIn("context.strokePath()", updated)
        self.assertIn("if !attribute.consumed || jerkgramKeepConsumedOneTimeVisual", updated)
        self.assertNotIn("ConsumableContentMessageAttribute(consumed: false)", updated)

    def test_post_transcription_voice_owner_does_not_require_dead_is_consumed_local(self):
        module = self.load_patch()
        self.assertNotIn("isConsumed = attribute.consumed", VOICE_FIXTURE)
        updated = module.patch_voice_text(VOICE_FIXTURE)
        self.assertIn("BUILD124_OUTGOING_ONETIME_VIEWED_VOICE1", updated)
        self.assertNotIn("isConsumed = attribute.consumed", updated)

    def test_viewed_patch_is_idempotent(self):
        module = self.load_patch()
        once_media = module.patch_media_text(MEDIA_FIXTURE)
        self.assertEqual(once_media, module.patch_media_text(once_media))
        once_voice = module.patch_voice_text(VOICE_FIXTURE)
        self.assertEqual(once_voice, module.patch_voice_text(once_voice))

    def test_circle_keeps_telegram_native_seen_state_owner(self):
        source = PATCH.read_text(encoding="utf-8")
        self.assertNotIn("ChatMessageInteractiveInstantVideoNode", source)
        self.assertIn("ChatMessageInteractiveMediaNode/Sources/ChatMessageInteractiveMediaNode.swift", source)
        self.assertIn("ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift", source)


if __name__ == "__main__":
    unittest.main()
