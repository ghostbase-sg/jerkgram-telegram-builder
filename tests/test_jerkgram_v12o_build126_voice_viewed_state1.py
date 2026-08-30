import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12o_build126_voice_viewed_state1.py"


class Build126VoiceViewedStateTests(unittest.TestCase):
    def load_patch(self):
        self.assertTrue(PATCH.is_file(), "Build126 voice viewed-state patch is missing")
        spec = importlib.util.spec_from_file_location("build126_voice_viewed", PATCH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def owner_fixture(self):
        return '''                var consumableContentIcon: UIImage?
                for attribute in arguments.message.attributes {
                    if let attribute = attribute as? ConsumableContentMessageAttribute {
                        // MARK: Jerkgram v1.2M BUILD124_PERSISTENT_ONETIME_VOICE_VISUAL1
                        let jerkgramKeepConsumedOneTimeVisual = true
                        if !attribute.consumed || jerkgramKeepConsumedOneTimeVisual {
                            if arguments.incoming {
                                consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentIncomingIcon(arguments.presentationData.theme.theme)
                            } else {
                                // MARK: Jerkgram v1.2M BUILD124_OUTGOING_ONETIME_VIEWED_VOICE1
                                let jerkgramOutgoingOneTimeViewed = jerkgramKeepConsumedOneTimeVisual && attribute.consumed
                                if jerkgramOutgoingOneTimeViewed {
                                    consumableContentIcon = viewedIcon
                                } else {
                                    consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentOutgoingIcon(arguments.presentationData.theme.theme)
                                }
                            }
                        }
                        break
                    }
                }
'''

    def test_outgoing_consumed_state_reaches_viewed_icon_branch(self):
        module = self.load_patch()
        result = module.patch_text(self.owner_fixture())
        self.assertIn(module.MARKER, result)
        self.assertIn("if arguments.incoming {", result)
        self.assertIn("if !attribute.consumed {", result)
        self.assertIn("} else if attribute.consumed {", result)
        self.assertIn("BUILD126_OUTGOING_ONETIME_VIEWED_VOICE1", result)
        self.assertNotIn("jerkgramOutgoingOneTimeViewed", result)

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_text(self.owner_fixture())
        self.assertEqual(once, module.patch_text(once))


if __name__ == "__main__":
    unittest.main()
