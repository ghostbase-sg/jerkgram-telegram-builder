import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12n_build125_profile_edit1.py"


class Build125ProfileEditTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build125_profile_edit", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def owner_fixture(self) -> str:
        return '''        // MARK: GhostBase v1.1P HEADER_FIELD_GLASS_OWNER1
        let ghostBaseGlassEnabled =
            GhostBaseProfileBlurSettings
                .loadEnabled() != nil

        if ghostBaseGlassEnabled {
            let isDark = presentationData.theme.overallDarkAppearance
            self.backgroundNode.backgroundColor =
                UIColor(
                    white:
                        isDark
                        ? 0.0
                        : 1.0,
                    alpha:
                        isDark
                        ? 0.13
                        : 0.16
                )
        }
'''

    def test_uses_the_same_glass_toggle_as_the_rest_of_profile_ui(self):
        module = self.load_patch()
        result = module.patch_text(self.owner_fixture(), "bio")
        self.assertIn("BUILD125_PROFILE_EDIT_GLASS_OWNER1", result)
        self.assertIn("GhostBaseGlassStyle.isEnabled", result)
        self.assertNotIn("GhostBaseProfileBlurSettings", result)

    def test_uses_translucent_tint_not_the_opaque_list_card(self):
        module = self.load_patch()
        result = module.patch_text(self.owner_fixture(), "bio")
        self.assertIn("UIColor.white.withAlphaComponent(0.055)", result)
        self.assertIn("UIColor.black.withAlphaComponent(0.045)", result)
        self.assertNotIn("itemBlocksBackgroundColor.withAlphaComponent", result)
        self.assertNotIn("let isDark =", result)

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_text(self.owner_fixture(), "bio")
        self.assertEqual(once, module.patch_text(once, "bio"))

    def test_accepts_previously_materialized_glass_toggle_without_marker(self):
        module = self.load_patch()
        already_materialized = self.owner_fixture().replace(
            '''        let ghostBaseGlassEnabled =
            GhostBaseProfileBlurSettings
                .loadEnabled() != nil''',
            '''        let ghostBaseGlassEnabled = GhostBaseGlassStyle.isEnabled''',
        ).replace(
            '''            self.backgroundNode.backgroundColor =
                UIColor(
                    white:
                        isDark
                        ? 0.0
                        : 1.0,
                    alpha:
                        isDark
                        ? 0.13
                        : 0.16
                )''',
            '''            let isDark = presentationData.theme.overallDarkAppearance
            self.backgroundNode.isOpaque = false
            self.backgroundNode.backgroundColor = isDark
                ? UIColor.white.withAlphaComponent(0.055)
                : UIColor.black.withAlphaComponent(0.045)''',
        )
        result = module.patch_text(already_materialized, "bio")
        self.assertIn("BUILD125_PROFILE_EDIT_GLASS_OWNER1", result)
        self.assertEqual(result.count("GhostBaseGlassStyle.isEnabled"), 1)


if __name__ == "__main__":
    unittest.main()
