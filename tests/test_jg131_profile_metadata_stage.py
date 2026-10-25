"""Exercise exact profile-metadata materialization against the complete previous owners."""
from pathlib import Path
import importlib.util
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ProfileMetadataStageTests(unittest.TestCase):
    def test_atomic_apply_restore_and_refuse_unknown_owners(self):
        module = ROOT / 'scripts/materialize_jg131_profile_metadata.py'
        self.assertTrue(module.exists(), 'profile metadata stage is not implemented')
        spec = importlib.util.spec_from_file_location('profile_metadata', module)
        stage = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(stage)
        source = Path(__import__('os').environ.get('JG_METADATA_SOURCE', ROOT / 'work/swiftgram-src'))
        parents = {n: stage.parent_bytes(n, (source / n).read_bytes()) for n in stage.manifest()['owners']}
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            for n, data in parents.items():
                p = target / n
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(data)
            bad = list(parents)[-1]
            (target / bad).write_bytes(parents[bad] + b'\n// unknown input\n')
            before = {n: (target/n).read_bytes() for n in parents}
            with self.assertRaises(RuntimeError): stage.apply_profile_metadata(target)
            self.assertEqual(before, {n: (target/n).read_bytes() for n in parents})
            (target / bad).write_bytes(parents[bad])
            stage.apply_profile_metadata(target)
            stage.verify_profile_metadata(target)
            for n, data in parents.items():
                self.assertEqual(stage.parent_bytes(n, (target/n).read_bytes()), data)
                self.assertEqual((target/n).read_bytes(), (source/n).read_bytes())
            with self.assertRaises(RuntimeError): stage.apply_profile_metadata(target)
            (target / bad).write_bytes((target / bad).read_bytes() + b'\n// unknown output\n')
            with self.assertRaises(RuntimeError): stage.verify_profile_metadata(target)

if __name__ == '__main__': unittest.main()
