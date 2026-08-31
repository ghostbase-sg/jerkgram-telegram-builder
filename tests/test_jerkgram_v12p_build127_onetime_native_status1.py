import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12p_build127_onetime_native_status1.py"


class Build127OneTimeNativeStatusTests(unittest.TestCase):
    def load_patch(self):
        self.assertTrue(PATCH.is_file(), "Build127 native one-time status patch is missing")
        spec = importlib.util.spec_from_file_location("build127_onetime_native_status", PATCH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def test_voice_restores_native_unconsumed_icons_without_custom_viewed_glyph(self):
        module = self.load_patch()
        source = '''                        // MARK: Jerkgram v1.2O BUILD126_OUTGOING_ONETIME_VIEWED_VOICE1
                        if arguments.incoming {
                            if !attribute.consumed {
                                consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentIncomingIcon(arguments.presentationData.theme.theme)
                            }
                        } else if attribute.consumed {
                            consumableContentIcon = generateImage(CGSize(width: 13.0, height: 7.0), contextGenerator: { size, context in
                                context.fillEllipse(in: CGRect(x: 0.0, y: 1.5, width: 4.0, height: 4.0))
                            })
                        } else {
                            consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentOutgoingIcon(arguments.presentationData.theme.theme)
                        }

                        break
'''
        result = module.patch_voice_text(source)
        self.assertIn(module.VOICE_MARKER, result)
        self.assertIn("if !attribute.consumed {", result)
        self.assertIn("chatBubbleConsumableContentIncomingIcon", result)
        self.assertIn("chatBubbleConsumableContentOutgoingIcon", result)
        self.assertNotIn("generateImage", result)
        self.assertNotIn("fillEllipse", result)
        self.assertNotIn("attribute.consumed {\n                            consumableContentIcon", result)

    def test_circle_removes_unused_custom_viewed_state(self):
        module = self.load_patch()
        source = '''            // MARK: Jerkgram v1.2O BUILD126_OUTGOING_ONETIME_VIEWED_CIRCLE1
            var notConsumed = false
            var jerkgramOutgoingOneTimeCircleViewed = false
            for attribute in item.message.attributes {
                if let attribute = attribute as? ConsumableContentMessageAttribute {
                    if !attribute.consumed {
                        notConsumed = true
                    } else if !item.message.effectivelyIncoming(item.context.account.peerId) && attribute.consumed {
                        jerkgramOutgoingOneTimeCircleViewed = true
                    }
                    break
                }
            }
            var updatedPlaybackStatus: Signal<FileMediaResourceStatus, NoError>?
'''
        result = module.patch_circle_text(source)
        self.assertIn(module.CIRCLE_MARKER, result)
        self.assertIn("if !attribute.consumed {", result)
        self.assertNotIn("jerkgramOutgoingOneTimeCircleViewed", result)
        self.assertNotIn("effectivelyIncoming", result)

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        voice = """                        // MARK: Jerkgram v1.2O BUILD126_OUTGOING_ONETIME_VIEWED_VOICE1\n                        break\n"""
        circle = """            // MARK: Jerkgram v1.2O BUILD126_OUTGOING_ONETIME_VIEWED_CIRCLE1\n            var updatedPlaybackStatus: Signal<FileMediaResourceStatus, NoError>?\n"""
        self.assertEqual(module.patch_voice_text(voice), module.patch_voice_text(module.patch_voice_text(voice)))
        self.assertEqual(module.patch_circle_text(circle), module.patch_circle_text(module.patch_circle_text(circle)))

    def test_build_routes_apply_and_test_the_native_status_overlay_after_build126(self):
        runner = (REPO / "scripts" / "bazel_build_probe_official.sh").read_text(encoding="utf-8")
        workflow = (REPO / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")
        apply_name = "apply_jerkgram_v12p_build127_onetime_native_status1.py"
        test_name = "tests.test_jerkgram_v12p_build127_onetime_native_status1"
        self.assertIn(apply_name, runner)
        self.assertIn(apply_name, workflow)
        self.assertIn(test_name, workflow)
        self.assertGreater(runner.index(apply_name), runner.index("apply_jerkgram_v12o_build126_circle_viewed_state1.py"))


if __name__ == "__main__":
    unittest.main()
