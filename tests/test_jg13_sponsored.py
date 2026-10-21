import importlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/swiftgram-src'))
sys.path.insert(0, str(ROOT / 'scripts'))


class SponsoredStageTests(unittest.TestCase):
    def test_exact_sponsored_stage(self):
        self.assertTrue((ROOT / 'scripts/materialize_jg13_sponsored.py').exists(), 'Sponsored-only stage missing')
        stage = importlib.import_module('materialize_jg13_sponsored')
        stage.verify_sponsored(SOURCE)

    def test_round_trip_repeat_tamper_and_atomic_parent_failure(self):
        self.assertTrue((ROOT / 'patches/jg13-sponsored.sha256.json').exists(), 'Reviewed sponsored manifest missing')
        stage = importlib.import_module('materialize_jg13_sponsored')
        m = stage.read_manifest()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            for name in set(m['owners']) | set(m['locks']):
                p = source / name
                p.parent.mkdir(parents=True, exist_ok=True)
                data = (SOURCE / name).read_bytes()
                if name in m['owners']:
                    parent = stage.restore_owner(name, data.decode())
                    if parent is None: continue
                    data = parent.encode()
                p.write_bytes(data)
            names = [n for n in m['owners'] if (source/n).exists()]
            target = source / names[-1]
            original = target.read_bytes()
            target.write_bytes(original + b'\n// parent tamper\n')
            before = {n: (source/n).read_bytes() for n in names}
            with self.assertRaises(RuntimeError): stage.apply_sponsored(source)
            self.assertEqual(before, {n: (source/n).read_bytes() for n in names})
            self.assertFalse((source/stage.POLICY).exists())
            target.write_bytes(original)
            stage.apply_sponsored(source)
            stage.verify_sponsored(source)
            with self.assertRaises(RuntimeError): stage.apply_sponsored(source)
            for name in set(m['owners']) | set(m['locks']):
                p = source/name; original = p.read_bytes()
                p.write_bytes(original + b'\n// final tamper\n')
                with self.assertRaises(RuntimeError): stage.verify_sponsored(source)
                p.write_bytes(original)


if __name__ == '__main__': unittest.main()
