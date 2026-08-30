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

    def test_bio_edit_gets_its_own_translucent_background_without_changing_all_input_rows(self):
        module = self.load_patch()
        bio = '''let inputItem = ItemListMultilineInputItem(presentationData: ItemListPresentationData(presentationData), systemStyle: .glass, text: item.text, placeholder: item.placeholder, maxLength: item.maxLength.flatMap { ItemListMultilineInputItemTextLimit(value: $0, display: true) }, sectionId: 0, style: .blocks, returnKeyType: .done)'''
        renderer = '''public class ItemListMultilineInputItem: ListViewItem, ItemListItem {
    let presentationData: ItemListPresentationData
    let systemStyle: ItemListSystemStyle
    let text: String
    public init(presentationData: ItemListPresentationData, systemStyle: ItemListSystemStyle = .legacy, text: String, placeholder: String, maxLength: ItemListMultilineInputItemTextLimit?, sectionId: ItemListSectionId, style: ItemListStyle, capitalization: Bool = true, autocorrection: Bool = true, returnKeyType: UIReturnKeyType = .default, minimalHeight: CGFloat? = nil, textUpdated: @escaping (String) -> Void, shouldUpdateText: @escaping (String) -> Bool = { _ in return true }, processPaste: ((String) -> Void)? = nil, updatedFocus: ((Bool) -> Void)? = nil, tag: ItemListItemTag? = nil, action: (() -> Void)? = nil, inlineAction: ItemListMultilineInputInlineAction? = nil, noInsets: Bool = false) {
        self.systemStyle = systemStyle
    }
}
case .blocks:
    itemBackgroundColor = item.presentationData.theme.list.itemBlocksBackgroundColor
'''
        patched_bio = module.patch_bio_input(bio)
        patched_renderer = module.patch_item_renderer(renderer)
        self.assertIn("backgroundColor: GhostBaseGlassStyle.isEnabled", patched_bio)
        self.assertIn("BUILD125_PROFILE_BIO_GLASS_OWNER1", patched_bio)
        self.assertIn("let backgroundColor: UIColor?", patched_renderer)
        self.assertIn("backgroundColor: UIColor? = nil", patched_renderer)
        self.assertIn("item.backgroundColor ?? item.presentationData.theme.list.itemBlocksBackgroundColor", patched_renderer)


if __name__ == "__main__":
    unittest.main()
