"""Exercise exact profile-metadata materialization against the complete previous owners."""
from pathlib import Path
import importlib.util
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PerformanceFollowupStageTests(unittest.TestCase):
    def test_atomic_apply_restore_and_refuse_unknown_owners(self):
        module = ROOT / 'scripts/materialize_jg131_performance_followup.py'
        self.assertTrue(module.exists(), 'performance follow-up stage is not implemented')
        spec = importlib.util.spec_from_file_location('performance_followup', module)
        stage = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(stage)
        source = Path(__import__('os').environ.get('JG_PERFORMANCE_SOURCE', ROOT / 'work/swiftgram-src'))
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
            with self.assertRaises(RuntimeError): stage.apply_performance_followup(target)
            self.assertEqual(before, {n: (target/n).read_bytes() for n in parents})
            (target / bad).write_bytes(parents[bad])
            stage.apply_performance_followup(target)
            stage.verify_performance_followup(target)
            for n, data in parents.items():
                self.assertEqual(stage.parent_bytes(n, (target/n).read_bytes()), data)
                self.assertEqual((target/n).read_bytes(), (source/n).read_bytes())
            with self.assertRaises(RuntimeError): stage.apply_performance_followup(target)
            (target / bad).write_bytes((target / bad).read_bytes() + b'\n// unknown output\n')
            with self.assertRaises(RuntimeError): stage.verify_performance_followup(target)

if __name__ == '__main__': unittest.main()
