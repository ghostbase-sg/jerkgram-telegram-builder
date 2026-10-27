"""Native-owner source contracts. These do not prove rendered iOS behavior."""
from pathlib import Path
import os
import unittest

ROOT = Path(__file__).resolve().parents[1]
PREPARED = ROOT.parent
ORIGINAL = Path('/home/pixi/Projects/Jerkgram/iOS/jerkgram-telegram-builder/work/swiftgram-src')


def read(name):
    source = Path(os.environ.get('JG_SETTINGS_SOURCE', ROOT / 'work/swiftgram-src'))
    if source.exists():
        return (source / name).read_text()
    for stage in reversed(('translation', 'profile-polish', 'profile-metadata', 'excluded-history', 'settings-transparency', 'performance-followup')):
        path = PREPARED / stage / 'after' / name
        if path.exists():
            return path.read_text()
    return (ORIGINAL / name).read_text()


class Settings175SurfaceTests(unittest.TestCase):
    def test_custom_appearance_rows_use_resolved_surface_theme(self):
        source = read('submodules/SettingsUI/Sources/Themes/ThemeSettingsController.swift')
        factory = source.split('func item(presentationData:', 1)[1].split('private func', 1)[0]
        self.assertIn('systemStyle: .glass, theme: presentationData.theme, componentTheme: theme', factory)
        self.assertIn('ThemeCarouselThemeItem(context: arguments.context, theme: presentationData.theme', factory)
        self.assertIn('ThemeSettingsAppIconItem(theme: presentationData.theme', factory)

    def test_disabled_switch_preserves_surface_alpha(self):
        source = read('submodules/ItemListUI/Sources/Items/ItemListSwitchItem.swift')
        self.assertIn('currentDisabledOverlayNode.backgroundColor = itemBackgroundColor.withMultipliedAlpha(0.6)', source)
        self.assertNotIn('currentDisabledOverlayNode.backgroundColor = itemBackgroundColor.withAlphaComponent(0.6)', source)

    def test_stars_adaptor_uses_resolved_theme_without_second_background(self):
        source = read('submodules/TelegramUI/Components/Stars/StarsTransactionsScreen/Sources/StarsTransactionsScreen.swift')
        earn = source.split('let earnStarsSectionSize =', 1)[1].split('let earnStarsSectionFrame', 1)[0]
        self.assertIn('ItemListPresentationData(presentationData.withUpdated(theme: environment.theme))', earn)
        self.assertIn('backgroundColor: .clear', earn)

    def test_status_popup_declines_fullscreen_settings_backdrop(self):
        source = read('submodules/TelegramUI/Components/EmojiStatusSelectionComponent/Sources/EmojiStatusSelectionComponent.swift')
        controller = source.split('public final class EmojiStatusSelectionController: ViewController {', 1)[1]
        self.assertIn('override public var jerkgramAcceptsSettingsSurface: Bool { return false }', controller)

    def test_preview_corners_use_surface_theme_and_keep_chat_theme_separate(self):
        source = read('submodules/SettingsUI/Sources/Themes/ThemeSettingsChatPreviewItem.swift')
        self.assertIn('PresentationResourcesItemList.cornersImage(item.theme,', source)
        self.assertNotIn('PresentationResourcesItemList.cornersImage(item.componentTheme,', source)
        self.assertIn('bubbleTheme: item.componentTheme', source)

    def test_session_modal_declines_fullwindow_backdrop_and_keeps_native_sheet(self):
        source = read('submodules/SettingsUI/Sources/Privacy and Security/RecentSessionScreen.swift')
        controller = source.split('public class RecentSessionScreen: ViewControllerComponentContainer {', 1)[1]
        self.assertIn('override public var jerkgramAcceptsSettingsSurface: Bool { return false }', controller)
        self.assertIn('backgroundColor: .color(environment.theme.list.modalBlocksBackgroundColor)', source)
        self.assertIn('self.navigationPresentation = .flatModal', controller)
        self.assertNotIn('jerkgramSettingsBackdropProvider', source)

    def test_session_details_keep_native_modal_sections(self):
        source = read('submodules/SettingsUI/Sources/Privacy and Security/RecentSessionScreen.swift')
        self.assertIn('let theme = environment.theme.withModalBlocksBackground()', source)
        for section in ('clientSection', 'optionsSection'):
            block = source.split('let ' + section + ' = ' + section + '.update(', 1)[1]
            self.assertIn('component: ListSectionComponent(\n', block)
            self.assertIn('theme: theme,\n', block)
            self.assertIn('style: .glass,', block)


if __name__ == '__main__':
    unittest.main()
