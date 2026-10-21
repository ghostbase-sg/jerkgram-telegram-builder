import importlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/swiftgram-src'))
sys.path.insert(0, str(ROOT / 'scripts'))


class ProfileCaptureTests(unittest.TestCase):
    def test_profile_capture_exact_delta(self):
        self.assertTrue((ROOT / 'scripts/materialize_jg13_profile_capture.py').exists(), 'Profile capture stage missing')
        stage = importlib.import_module('materialize_jg13_profile_capture')
        stage.verify_profile_capture(SOURCE)

    def test_round_trip_and_all_owner_tampering(self):
        self.assertTrue((ROOT / 'patches/jg13-profile-capture.sha256.json').exists(), 'Profile capture manifest missing')
        stage = importlib.import_module('materialize_jg13_profile_capture')
        m = stage.read_manifest()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            for name in set(m['owners']) | set(m['locks']):
                p = source/name; p.parent.mkdir(parents=True, exist_ok=True)
                text = (SOURCE/name).read_text()
                if name in m['owners']: text = stage.restore_owner(name,text)
                p.write_text(text)
            stage.apply_profile_capture(source)
            with self.assertRaises(RuntimeError): stage.apply_profile_capture(source)
            for name in set(m['owners']) | set(m['locks']):
                p=source/name; before=p.read_bytes(); p.write_bytes(before+b'\n// tamper\n')
                with self.assertRaises(RuntimeError): stage.verify_profile_capture(source)
                p.write_bytes(before)


if __name__ == '__main__': unittest.main()
