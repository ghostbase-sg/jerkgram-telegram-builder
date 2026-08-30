import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12o_build126_circle_viewed_state1.py"


class Build126CircleViewedStateTests(unittest.TestCase):
    def load_patch(self):
        self.assertTrue(PATCH.is_file(), "Build126 circle viewed-state patch is missing")
        spec = importlib.util.spec_from_file_location("build126_circle_viewed", PATCH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def owner_fixture(self):
        return '''            // MARK: Jerkgram v1.2M BUILD124_OUTGOING_ONETIME_VIEWED_CIRCLE1
            var notConsumed = false
            var jerkgramOutgoingOneTimeCircleViewed = false
            for attribute in item.message.attributes {
                if let attribute = attribute as? ConsumableContentMessageAttribute {
                    if !attribute.consumed {
                        notConsumed = true
                    } else if ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.OneTimeSave") as? Bool) ?? false) && !item.message.effectivelyIncoming(item.context.account.peerId) {
                        jerkgramOutgoingOneTimeCircleViewed = true
                        notConsumed = true
                    }
                    break
                }
            }
            if item.message.id.namespace == Namespaces.Message.Local {
                notConsumed = true
            }
            
            var updatedPlaybackStatus: Signal<FileMediaResourceStatus, NoError>?
'''

    def test_outgoing_circle_check_uses_remote_consumed_state_without_feature_toggle(self):
        module = self.load_patch()
        result = module.patch_text(self.owner_fixture())
        self.assertIn(module.MARKER, result)
        self.assertIn("else if !item.message.effectivelyIncoming(item.context.account.peerId) && attribute.consumed", result)
        self.assertNotIn("jerkgram.ProtectedContent.OneTimeSave", result)
        viewed_branch = result.index("jerkgramOutgoingOneTimeCircleViewed = true")
        next_break = result.index("break", viewed_branch)
        self.assertNotIn("notConsumed = true", result[viewed_branch:next_break])

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_text(self.owner_fixture())
        self.assertEqual(once, module.patch_text(once))


if __name__ == "__main__":
    unittest.main()
