"""Compile and execute the actual pure metadata policy when Swift is available."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(os.environ.get('JG_METADATA_SOURCE', Path(__file__).resolve().parents[1] / 'work/swiftgram-src'))
OWNER = 'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift'

class ProfileMetadataTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('swiftc'), 'Swift compiler unavailable; native policy execution pending macOS CI')
    def test_actual_policy_bounds_and_flags(self):
        text = (SOURCE/OWNER).read_text()
        policy = text.split('// JG170 metadata policy begin\n',1)[1].split('// JG170 metadata policy end',1)[0]
        fixture = '''
assert(!JerkgramProfileMetadataPolicy.showMutualContact(isMutual: false, isSelf: false, isBot: false))
assert(!JerkgramProfileMetadataPolicy.showMutualContact(isMutual: true, isSelf: true, isBot: false))
assert(!JerkgramProfileMetadataPolicy.showMutualContact(isMutual: true, isSelf: false, isBot: true))
assert(JerkgramProfileMetadataPolicy.showMutualContact(isMutual: true, isSelf: false, isBot: false))
assert(JerkgramProfileMetadataPolicy.registrationMonth("0.2020", currentYear: 2026) == nil)
assert(JerkgramProfileMetadataPolicy.registrationMonth("13.2020", currentYear: 2026) == nil)
assert(JerkgramProfileMetadataPolicy.registrationMonth("1.2030", currentYear: 2026) == nil)
assert(JerkgramProfileMetadataPolicy.registrationMonth("1.2020", currentYear: 2026)?.month == 1)
assert(JerkgramProfileMetadataPolicy.estimatedYears(userId: -1) == nil)
assert(JerkgramProfileMetadataPolicy.estimatedYears(userId: 9_000_000_000) == nil)
assert(JerkgramProfileMetadataPolicy.estimatedYears(userId: 400_169_472)?.lowerBound == 2017)
assert(JerkgramProfileMetadataPolicy.estimatedYears(userId: 400_169_472)?.upperBound == 2017)
assert(JerkgramProfileMetadataPolicy.estimatedYears(userId: 500_000_000)?.lowerBound == 2017)
assert(JerkgramProfileMetadataPolicy.estimatedYears(userId: 500_000_000)?.upperBound == 2019)
print("metadata policy PASS")
'''
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'main.swift';p.write_text('import Foundation\n'+policy+fixture)
            subprocess.run(['swiftc', '-warnings-as-errors', str(p), '-o', d+'/check'],check=True)
            subprocess.run([d+'/check'],check=True)
if __name__ == '__main__': unittest.main()
