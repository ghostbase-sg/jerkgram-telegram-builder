"""Source regression contracts for visual bugs; not rendered/UI assertions."""
from pathlib import Path
import os
import unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('JG_SETTINGS_SOURCE', ROOT/'work/swiftgram-src'))
class SettingsVisualSourceTests(unittest.TestCase):
    def read(self, path): return (SOURCE/path).read_text()
    def test_clear_corner_filler_never_reads_uninitialized_pixels(self):
        s=self.read('submodules/TelegramPresentationData/Sources/Resources/PresentationResourcesItemList.swift')
        block=s.split('public static func cornersImage(',1)[1].split('public static func updateTranslucentRowCorners',1)[0]
        self.assertLess(block.index('context.clear(bounds)'),block.index('context.fill(bounds)'))
        self.assertIn('node.layer.mask = owned.layer',s)
        self.assertIn('node.layer.mask === previous.layer',s)
    def test_middle_rows_keep_inset_rectangular_masks(self):
        s=self.read('submodules/TelegramPresentationData/Sources/Resources/PresentationResourcesItemList.swift')
        self.assertIn('return theme.list.blocksBackgroundColor.cgColor.alpha == 0.0 ? JerkgramListCornerSpec.middleImage : nil',s)
        self.assertIn('JerkgramListCornerSpec(top: false, bottom: false, radius: 0.0)',s)
    def test_backdrop_preserves_native_material_and_transition_lifetime(self):
        folder='submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/'
        s=self.read(folder+'PeerInfoScreen.swift')
        self.assertIn('self.jerkgramSettingsHasOwnBackdrop = isSettings',s)
        s=self.read(folder+'GhostBaseProfileFullscreenBackground.swift')
        function=s.split('func makeSettingsBackdropView()',1)[1].split('    private let imageView:',1)[0]
        self.assertNotIn('drawHierarchy',function)
        self.assertNotIn('CIGaussianBlur',s)
        for value in ['self.imageView.image', 'self.blurView.effect', 'self.blurView.alpha', 'self.tintView.backgroundColor']:
            self.assertIn(value,function)
        vc=self.read('submodules/Display/Source/ViewController.swift')
        self.assertIn('&& self.jerkgramSettingsBackdropView == nil',vc)
        appearance=vc.split('open override func viewDidAppear(',1)[1].split('super.viewDidAppear',1)[0]
        self.assertIn('self.jerkgramRefreshSettingsSurface()',appearance)
        self.assertNotIn('invalidateBackdrop: true',appearance)
        self.assertIn('jerkgramRefreshSettingsSurface(invalidateBackdrop: true)',vc)
    def test_root_tint_is_restored_and_cards_use_root_colors(self):
        s=self.read('submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift')
        tint=s.split('private func applyTint(',1)[1].split('private func wallpaperEntrySignal',1)[0]
        self.assertIn('reduced ? 0.24 : 0.32',tint)
        self.assertIn('reduced ? 0.10 : 0.14',tint)
        self.assertNotIn('reduced ? 0.58 : 0.62',tint)
        theme=self.read('submodules/TelegramPresentationData/Sources/PresentationTheme.swift')
        self.assertIn('let surfaceColor = self.overallDarkAppearance ? UIColor.black : UIColor.white',theme)
        self.assertIn('itemBlocksBackgroundColor: surfaceColor.withAlphaComponent(alpha)',theme)
    def test_bio_outer_section_is_the_single_background_and_corner_owner(self):
        s=self.read('submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenMultilineInputtem.swift')
        self.assertIn('backgroundColor: GhostBaseGlassStyle.isEnabled ? .clear : nil',s)
        s=self.read('submodules/ItemListUI/Sources/Items/ItemListMultilineInputItem.swift')
        self.assertIn('item.noInsets && item.backgroundColor != nil && GhostBaseGlassStyle.isEnabled',s)
        self.assertIn('strongSelf.maskNode.image = nil',s)
if __name__=='__main__': unittest.main()
