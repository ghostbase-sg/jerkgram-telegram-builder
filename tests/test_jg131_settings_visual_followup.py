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
    def test_backdrop_is_source_cached_and_works_when_source_controller_is_hidden(self):
        folder='submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/'
        s=self.read(folder+'PeerInfoScreen.swift')
        provider=s.split('self.jerkgramSettingsBackdropProvider =',1)[1].split('\n        }',1)[0]
        self.assertNotIn('drawHierarchy',provider)
        self.assertIn('settingsBackdropImage',provider)
        s=self.read(folder+'GhostBaseProfileFullscreenBackground.swift')
        function=s.split('func settingsBackdropImage(',1)[1].split('    private let imageView:',1)[0]
        self.assertNotIn('currentStateKey != nil',function)
        self.assertIn('if let cached = self.settingsSnapshot',function)
        self.assertIn('192.0',function)
    def test_bio_outer_section_is_the_single_background_and_corner_owner(self):
        s=self.read('submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenMultilineInputtem.swift')
        self.assertIn('backgroundColor: GhostBaseGlassStyle.isEnabled ? .clear : nil',s)
        s=self.read('submodules/ItemListUI/Sources/Items/ItemListMultilineInputItem.swift')
        self.assertIn('item.noInsets && item.backgroundColor != nil && GhostBaseGlassStyle.isEnabled',s)
        self.assertIn('strongSelf.maskNode.image = nil',s)
if __name__=='__main__': unittest.main()
