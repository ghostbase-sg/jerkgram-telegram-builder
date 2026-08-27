#!/usr/bin/env python3

from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts/apply_jerkgram_v12m_build124_onetime_persistence1.py"

AUTOREMOVE_FIXTURE = '''                                var updatedAttributes = currentMessage.attributes
                                for i in 0 ..< updatedAttributes.count {
                                    if let _ = updatedAttributes[i] as? AutoclearTimeoutMessageAttribute {
                                        updatedAttributes.remove(at: i)
                                        break
                                    }
                                }
'''

VOICE_FIXTURE = '''                var isConsumed: Bool?
                
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


class Build124OneTimePersistenceTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_onetime_persistence", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_autoremove_keeps_view_once_identity_without_rearming_timestamp_operation(self):
        module = self.load_patch()
        updated = module.patch_autoremove_text(AUTOREMOVE_FIXTURE)
        self.assertIn("BUILD124_PERSISTENT_ONETIME_MARKER1", updated)
        self.assertIn("currentMessage.minAutoremoveOrClearTimeout == viewOnceTimeout", updated)
        self.assertIn("AutoclearTimeoutMessageAttribute(timeout: viewOnceTimeout, countdownBeginTime: nil)", updated)
        self.assertIn("updatedAttributes.remove(at: i)", updated)
        self.assertNotIn("ConsumableContentMessageAttribute(consumed: false)", updated)

    def test_voice_keeps_one_time_visual_after_consumption_but_preserves_consumed_state(self):
        module = self.load_patch()
        updated = module.patch_voice_file_text(VOICE_FIXTURE)
        self.assertIn("BUILD124_PERSISTENT_ONETIME_VOICE_VISUAL1", updated)
        self.assertIn("arguments.message.minAutoremoveOrClearTimeout == viewOnceTimeout", updated)
        self.assertIn("if !attribute.consumed || jerkgramKeepConsumedOneTimeVisual", updated)
        self.assertIn("isConsumed = attribute.consumed", updated)
        self.assertNotIn("ConsumableContentMessageAttribute(consumed: false)", updated)

    def test_build124_onetime_patch_is_idempotent(self):
        module = self.load_patch()
        once_auto = module.patch_autoremove_text(AUTOREMOVE_FIXTURE)
        self.assertEqual(once_auto, module.patch_autoremove_text(once_auto))
        once_voice = module.patch_voice_file_text(VOICE_FIXTURE)
        self.assertEqual(once_voice, module.patch_voice_file_text(once_voice))

    def test_patch_targets_only_materialized_official_owners(self):
        source = PATCH.read_text(encoding="utf-8")
        self.assertIn("submodules/TelegramCore/Sources/State/ManagedAutoremoveMessageOperations.swift", source)
        self.assertIn("submodules/TelegramUI/Components/Chat/ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift", source)
        self.assertNotIn("apply_ghostbase_v10p_sh1_ot1_combined.py", source)
        self.assertNotIn("apply_ghostbase_v10q_sh2_ot2_combined.py", source)


if __name__ == "__main__":
    unittest.main()
