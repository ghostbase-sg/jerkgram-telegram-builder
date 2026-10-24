"""Source compatibility regressions specific to the upstream API transition."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'work/swiftgram-src'

class MigrationTests(unittest.TestCase):
    def test_profile_caller_does_not_use_removed_header_transition_property(self):
        screen = (SOURCE / 'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreen.swift').read_text()
        self.assertFalse('self.headerNode.navigationTransition' in screen, 'caller references a header property removed in Telegram 13.1.1')

    def test_api_diagnostic_change_preserves_wire_function_implementation(self):
        owner = 'submodules/TelegramApi/Sources/TLObjectSupport.swift'
        original = subprocess.check_output(['git', 'show', 'HEAD:' + owner], cwd=SOURCE, text=True)
        actual = (SOURCE / owner).read_text()
        marker = '// MARK: - Engine bridge'
        self.assertEqual(actual.split(marker, 1)[1], original.split(marker, 1)[1])
        self.assertIn('fieldName == "botAuthToken" ? "[REDACTED]"', actual)

if __name__ == '__main__': unittest.main()
