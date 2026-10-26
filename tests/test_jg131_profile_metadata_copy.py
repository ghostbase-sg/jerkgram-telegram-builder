"""Source contract for native, explicit metadata copy gestures (UIKit device test required)."""
import os
from pathlib import Path
import unittest
ROOT=Path(os.environ.get('JG_METADATA_SOURCE', Path(__file__).resolve().parents[1]/'work/swiftgram-src'))
PREFIX='submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/'
class MetadataCopyTests(unittest.TestCase):
    def test_metadata_never_copies_on_tap_or_hold(self):
        s=(ROOT/(PREFIX+'PeerInfoProfileItems.swift')).read_text()
        rows=s.split('if ghostBaseMetricsSettings.showIds {',1)[1].split('if !metricItems.isEmpty',1)[0]
        self.assertNotIn('UIPasteboard.general.string', rows)
        self.assertEqual(rows.count('action: nil'),3)
        for value in ['idText','dcText','dateText']:
            self.assertIn('interaction.openPeerInfoContextMenu(.copyValue('+value+'), sourceNode, nil)', rows)
    def test_copy_is_only_performed_in_native_menu_action(self):
        s=(ROOT/(PREFIX+'PeerInfoScreenOpenPeerInfoContextMenu.swift')).read_text()
        self.assertIn('case let .copyValue(text):',s)
        case=s.split('case let .copyValue(text):',1)[1].split('case .birthday:',1)[0]
        self.assertIn('makeContextMenuController(actions:',case)
        self.assertIn('Conversation_ContextMenuCopy',case)
        self.assertIn('UIPasteboard.general.string = text',case)
        self.assertIn('Conversation_TextCopied',case)
if __name__=='__main__': unittest.main()
