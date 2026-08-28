#!/usr/bin/env python3

from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12m_build124_onetime_persistence1.py"
VERIFY = REPO / "scripts" / "verify_jerkgram_v12m_build124_onetime_persistence1.py"

AUTOREMOVE_FIXTURE = '''                                var updatedMedia = currentMessage.media
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
                                var updatedAttributes = currentMessage.attributes
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

    def test_autoremove_preserves_real_media_before_expired_content_replacement(self):
        module = self.load_patch()
        updated = module.patch_autoremove_text(AUTOREMOVE_FIXTURE)
        self.assertIn("BUILD124_PERSISTENT_ONETIME_MEDIA1", updated)
        self.assertIn("var updatedMedia = currentMessage.media", updated)
        self.assertIn("if !jerkgramKeepOneTimeIdentity {", updated)
        self.assertIn("TelegramMediaExpiredContent(data: .image)", updated)
        self.assertIn("TelegramMediaExpiredContent(data: .videoMessage)", updated)
        self.assertIn("TelegramMediaExpiredContent(data: .voiceMessage)", updated)
        self.assertIn("TelegramMediaExpiredContent(data: .file)", updated)
        self.assertLess(updated.index("let jerkgramKeepOneTimeIdentity"), updated.index("var updatedMedia = currentMessage.media"))
        self.assertLess(updated.index("var updatedMedia = currentMessage.media"), updated.index("var updatedAttributes = currentMessage.attributes"))

    def test_persistence_guard_remains_non_secret_and_view_once_only(self):
        module = self.load_patch()
        updated = module.patch_autoremove_text(AUTOREMOVE_FIXTURE)
        self.assertIn("currentMessage.id.peerId.namespace != Namespaces.Peer.SecretChat", updated)
        self.assertIn("currentMessage.minAutoremoveOrClearTimeout == viewOnceTimeout", updated)
        self.assertIn('GhostBase.ProtectedContent.OneTimeSave', updated)

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

    def test_source_verifier_enforces_real_media_persistence_owner_and_order(self):
        source = VERIFY.read_text(encoding="utf-8")
        self.assertIn("BUILD124_PERSISTENT_ONETIME_MEDIA1", source)
        self.assertIn('autoremove.count(MEDIA_MARKER) == 1', source)
        self.assertIn('"if !jerkgramKeepOneTimeIdentity {" in autoremove', source)
        self.assertIn('autoremove.count("let jerkgramKeepOneTimeIdentity = (") == 1', source)
        self.assertIn('autoremove.index("let jerkgramKeepOneTimeIdentity = (") < autoremove.index("var updatedMedia = currentMessage.media")', source)
        self.assertIn('autoremove.index("var updatedMedia = currentMessage.media") < autoremove.index("var updatedAttributes = currentMessage.attributes")', source)


if __name__ == "__main__":
    unittest.main()
