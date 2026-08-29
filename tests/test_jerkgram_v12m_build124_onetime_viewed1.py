#!/usr/bin/env python3

from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12m_build124_onetime_viewed1.py"
VERIFY = REPO / "scripts" / "verify_jerkgram_v12m_build124_onetime_viewed1.py"

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
                        break
'''

CIRCLE_FIXTURE = '''            var notConsumed = false
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

                        durationNode.isSeen = !notConsumed || item.presentationData.isPreview
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
        self.assertIn("context.map { !message.effectivelyIncoming($0.account.peerId) } ?? false", updated)
        self.assertNotIn("!message.flags.contains(.Incoming)", updated)
        self.assertIn('jerkgramOneTimeBadgeText = jerkgramOutgoingTimedMediaViewed ? "1 ✓" : "1"', updated)
        self.assertIn('jerkgramTimedBadgeText = strings.MessageTimer_ShortSeconds(Int32(remainingTime)) + (jerkgramOutgoingTimedMediaViewed ? " ✓" : "")', updated)
        self.assertIn('iconName: "Chat/Message/SecretMediaOnce"', updated)

    def test_outgoing_voice_indicator_keeps_one_time_dot_and_adds_viewed_check(self):
        module = self.load_patch()
        updated = module.patch_voice_text(VOICE_FIXTURE)
        self.assertIn("BUILD124_OUTGOING_ONETIME_VIEWED_VOICE1", updated)
        self.assertIn("jerkgramKeepConsumedOneTimeVisual && attribute.consumed", updated)
        self.assertIn("context.fillEllipse", updated)
        self.assertIn("context.strokePath()", updated)
        self.assertIn("attribute.consumed", updated)

    def test_viewed_patch_is_idempotent(self):
        module = self.load_patch()
        once_media = module.patch_media_text(MEDIA_FIXTURE)
        self.assertEqual(once_media, module.patch_media_text(once_media))
        once_voice = module.patch_voice_text(VOICE_FIXTURE)
        self.assertEqual(once_voice, module.patch_voice_text(once_voice))

    def test_outgoing_circle_keeps_one_time_effect_and_marks_actual_view(self):
        module = self.load_patch()
        updated = module.patch_circle_text(CIRCLE_FIXTURE)
        self.assertIn("BUILD124_OUTGOING_ONETIME_VIEWED_CIRCLE1", updated)
        self.assertIn("!item.message.effectivelyIncoming(item.context.account.peerId)", updated)
        self.assertIn("jerkgramOutgoingOneTimeCircleViewed = true", updated)
        self.assertIn("notConsumed = true", updated)
        self.assertIn("durationNode.isSeen = !notConsumed || jerkgramOutgoingOneTimeCircleViewed", updated)
        self.assertEqual(updated, module.patch_circle_text(updated))


    def test_verifier_tracks_direct_consumed_state_without_stale_local_alias(self):
        source = VERIFY.read_text(encoding="utf-8")
        self.assertIn("context.map { !message.effectivelyIncoming($0.account.peerId) } ?? false", source)
        self.assertNotIn("!message.effectivelyIncoming(context.account.peerId)", source)
        self.assertIn('"ConsumableContentMessageAttribute(consumed: false)" not in voice', source)
        self.assertNotIn('"isConsumed = attribute.consumed"', source)
        self.assertIn("CIRCLE_MARKER", source)
        self.assertIn("!item.message.effectivelyIncoming(item.context.account.peerId)", source)


if __name__ == "__main__":
    unittest.main()
