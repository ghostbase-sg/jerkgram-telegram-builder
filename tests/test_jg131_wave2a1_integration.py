"""Candidate identity and original required gates remain unchanged/in order."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WaveIntegration(unittest.TestCase):
    def test_baseline_native_then_candidate_native_before_build(self):
        for name in ('scripts/build_jg13.sh', '.github/workflows/no-ads-native.yml'):
            text = (ROOT / name).read_text()
            steps = ['python3 scripts/materialize_jg131_saved_tags.py',
                     'python3 tests/run_jg131_saved_tags.py --require-native --require-full-source',
                     "python3 -m unittest discover -s tests -p 'test_jg1312*.py'",
                     'python3 scripts/materialize_jg131_wave2a1.py',
                     'python3 tests/run_jg131_wave2a1.py --require-native --require-full-source']
            positions = [text.index(step) for step in steps]
            self.assertEqual(positions, sorted(positions), name)
            self.assertTrue(all(text.count(step) == 1 for step in steps))
        text = (ROOT / 'scripts/build_jg13.sh').read_text()
        self.assertLess(text.index('tests/run_jg131_wave2a1.py'), text.index('"${BAZEL_BIN:-bazelisk}" build'))

    def test_historical_ledger_and_version_preserved(self):
        path = ROOT / 'docs/migrations/telegram-13.1.2-stage-chain.json'
        old = json.loads(path.read_text())
        overlay = json.loads((ROOT / 'docs/migrations/build179-wave2a1-stage-chain.json').read_text())
        self.assertEqual(overlay['baseline_ledger_sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(overlay['stages'][:-1], old)
        self.assertEqual((len(old), overlay['stages'][-1]['order']), (32, 33))
        config = json.loads((ROOT / 'jerkgram-migration.json').read_text())
        self.assertEqual((config['build_number'], config['artifact_suffix'], config['upstream_new_sha']), (179, 'BETA2', '279f89e4d4f63f17227bf877dc3d8990f22ecd58'))
        workflow = (ROOT / '.github/workflows/build.yml').read_text()
        self.assertIn('      - perf/build179-wave2a1-chat-typing\n', workflow)
        self.assertIn('needs: source-preflight', workflow)
        self.assertIn('WAVE2A1-performance-candidate', workflow)
        self.assertIn('artifacts/Jerkgram-1.2.0-Build179-BETA2.ipa', workflow)

    def test_performance_manifest_is_outside_historical_discovery(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        from materialize_jg131_wave2a1 import MANIFEST, PATCH, manifest
        self.assertNotIn(MANIFEST, list((ROOT / 'patches').glob('jg13*.sha256.json')))
        self.assertEqual(MANIFEST.stem.removesuffix('.sha256'), PATCH.stem)
        self.assertEqual(manifest()['patch_sha256'], hashlib.sha256(PATCH.read_bytes()).hexdigest())

    def test_required_native_fails_closed_without_tools(self):
        result = subprocess.run([sys.executable, str(ROOT / 'tests/run_jg131_wave2a1.py'), '--require-native'], env=dict(os.environ, PATH=''), capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Wave2A1 requires macOS Swift/xcrun', result.stdout + result.stderr)

    def test_required_full_source_refuses_partial_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, str(ROOT / 'tests/run_jg131_wave2a1.py'), '--require-full-source'], env=dict(os.environ, JG_WAVE2A1_SOURCE=tmp), capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('focused gate PASS', result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
