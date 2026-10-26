"""Avatar-DC mapping/source wiring; native execution requires Swift (no iOS build)."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG_METADATA_SOURCE', BASE / 'work/swiftgram-src'))
OWNER = 'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift'

class AvatarDataCenterTests(unittest.TestCase):
    def test_avatar_dc_row_uses_country_formatter_and_dc_label(self):
        source = (SOURCE / OWNER).read_text()
        self.assertTrue('static func avatarDataCenterText(_ id: Int, isRussian: Bool)' in source, 'formatter must accept the resource DC Int without narrowing')
        row = source.split('if ghostBaseMetricsSettings.showDCs,', 1)[1].split('if ghostBaseMetricsSettings.showRegistration,', 1)[0]
        self.assertIn('JerkgramProfileMetadataPolicy.avatarDataCenterText(resource.datacenterId, isRussian: isRussian)', row)
        self.assertIn('label: "DC"', row)
        self.assertEqual(row.count('UIPasteboard.general.string = dcText'), 2)

    @unittest.skipUnless(shutil.which('swiftc'), 'Swift compiler unavailable; native DC behavior unverified')
    def test_documented_countries_both_languages_and_unknown_ids(self):
        source = (SOURCE / OWNER).read_text()
        policy = source.split('// JG170 metadata policy begin\n',1)[1].split('// JG170 metadata policy end',1)[0]
        fixture = '''
// The production photo resource exposes Int; literals alone hid the old Int32 mismatch.
let examples: [(Int, String, String)] = [
    (1, "1 · USA", "1 · США"), (2, "2 · Netherlands", "2 · Нидерланды"),
    (3, "3 · USA", "3 · США"), (4, "4 · Netherlands", "4 · Нидерланды"),
    (5, "5 · Singapore", "5 · Сингапур"), (0, "0", "0"), (6, "6", "6"), (-1, "-1", "-1")
]
for (id, english, russian) in examples {
    assert(JerkgramProfileMetadataPolicy.avatarDataCenterText(id, isRussian: false) == english)
    assert(JerkgramProfileMetadataPolicy.avatarDataCenterText(id, isRussian: true) == russian)
}
print("Avatar DC country policy PASS")
'''
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'main.swift'
            p.write_text('import Foundation\n' + policy + fixture)
            subprocess.run(['swiftc', '-warnings-as-errors', str(p), '-o', d+'/check'], check=True)
            subprocess.run([d+'/check'], check=True)

if __name__ == '__main__': unittest.main()
