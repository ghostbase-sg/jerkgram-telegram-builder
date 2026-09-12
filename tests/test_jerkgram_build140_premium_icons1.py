import importlib.util
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
PATCH_PATH = REPO / "scripts/apply_jerkgram_build140_premium_icons1.py"


class PremiumIconUnlockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch = None
        if PATCH_PATH.exists():
            spec = importlib.util.spec_from_file_location("premium_icons", PATCH_PATH)
            cls.patch = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.patch)

    def test_unlocks_visual_lock_and_is_idempotent(self):
        self.assertIsNotNone(self.patch, "premium icon patch is missing")
        source = '''imageNode.setup(theme: item.theme, icon: image, title: title, locked: !item.isPremium && icon.isPremium, color: color, bordered: bordered, selected: selected, action: {\n    item.updated(icon)\n})\n'''
        actual = self.patch.patch_icon_item(source)
        self.assertIn("locked: false", actual)
        self.assertNotIn("locked: !item.isPremium && icon.isPremium", actual)
        self.assertEqual(actual, self.patch.patch_icon_item(actual))

    def test_disables_only_app_icon_premium_redirect_and_is_idempotent(self):
        self.assertIsNotNone(self.patch, "premium icon patch is missing")
        source = '''}, selectAppIcon: { icon in\n    let _ = (context.engine.data.get(Item())\n    |> deliverOnMainQueue).start(next: { peer in\n        let isPremium = peer?.isPremium ?? false\n        if icon.isPremium && !isPremium {\n            showPremium()\n        } else {\n            currentAppIconName.set(icon.name)\n            context.sharedContext.applicationBindings.requestSetAlternateIconName(icon.isDefault ? nil : icon.name, { _ in\n            })\n        }\n    })\n}, editTheme: { theme in\n'''
        actual = self.patch.patch_icon_selection(source)
        self.assertIn("if icon.isPremium && !isPremium && false {", actual)
        self.assertEqual(actual.count("requestSetAlternateIconName"), 1)
        self.assertEqual(actual, self.patch.patch_icon_selection(actual))

    def test_does_not_reclassify_premium_icon_metadata(self):
        self.assertIsNotNone(self.patch, "premium icon patch is missing")
        source = '''icons.append(PresentationAppIcon(name: "Premium", imageName: "Premium", isPremium: true))\nicons.append(PresentationAppIcon(name: "PremiumTurbo", imageName: "PremiumTurbo", isPremium: true))\nicons.append(PresentationAppIcon(name: "PremiumBlack", imageName: "PremiumBlack", isPremium: true))\n'''
        self.assertEqual(source, self.patch.patch_app_delegate_contract(source))


if __name__ == "__main__":
    unittest.main()
