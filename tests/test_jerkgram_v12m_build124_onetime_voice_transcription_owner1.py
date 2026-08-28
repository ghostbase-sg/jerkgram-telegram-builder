#!/usr/bin/env python3

from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12m_build124_onetime_persistence1.py"

POST_TRANSCRIPTION1_VOICE_FIXTURE = '''                var consumableContentIcon: UIImage?
                for attribute in arguments.message.attributes {
                    if let attribute = attribute as? ConsumableContentMessageAttribute {
                        if !attribute.consumed {
                            if arguments.incoming {
                                consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentIncomingIcon(arguments.presentationData.theme.theme)
                            } else {
                                consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentOutgoingIcon(arguments.presentationData.theme.theme)
                            }
                        }
                        break
                    }
                }
'''


class Build124OneTimeVoiceTranscriptionOwnerTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_onetime_voice_transcription_owner", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_voice_visual_accepts_post_transcription1_owner_without_reintroducing_dead_state(self):
        module = self.load_patch()
        self.assertEqual(POST_TRANSCRIPTION1_VOICE_FIXTURE.count(module.OLD_VOICE), 0)

        updated = module.patch_voice_file_text(POST_TRANSCRIPTION1_VOICE_FIXTURE)

        self.assertIn("BUILD124_PERSISTENT_ONETIME_VOICE_VISUAL1", updated)
        self.assertIn("if !attribute.consumed || jerkgramKeepConsumedOneTimeVisual", updated)
        self.assertNotIn("var isConsumed: Bool?", updated)
        self.assertNotIn("isConsumed = attribute.consumed", updated)
        self.assertNotIn("ConsumableContentMessageAttribute(consumed: false)", updated)


if __name__ == "__main__":
    unittest.main()
