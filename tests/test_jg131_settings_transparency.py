"""Execute the actual settings-surface scope policy where Swift is available."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('JG_SETTINGS_SOURCE', ROOT/'work/swiftgram-src'))
class SettingsScopeNativeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('swiftc'), 'Swift compiler unavailable; native settings policy execution pending macOS CI')
    def test_settings_scope_requires_every_gate(self):
        text=(SOURCE/'submodules/Display/Source/GhostBaseGlass.swift').read_text()
        policy=text.split('// JG170 settings policy begin\n',1)[1].split('// JG170 settings policy end',1)[0]
        fixture='''
for mask in 0 ..< 32 {
    let bits = (0 ..< 5).map { mask & (1 << $0) != 0 }
    let actual = JerkgramSettingsSurfacePolicy.active(isSettings: bits[0], accepts: bits[1], master: bits[2], enabled: bits[3], hasBackdrop: bits[4])
    assert(actual == (mask == 31))
}
print("settings scope PASS")
'''
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'main.swift';p.write_text(policy+fixture)
            subprocess.run(['swiftc','-warnings-as-errors',str(p),'-o',d+'/check'],check=True)
            subprocess.run([d+'/check'],check=True)
if __name__=='__main__': unittest.main()
