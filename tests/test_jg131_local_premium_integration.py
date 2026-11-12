"""Hub is the next terminal stage; prior source gates retain exact parents."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


class LocalPremiumIntegration(unittest.TestCase):
    def test_required_native_fails_closed(self):
        runner = ROOT / 'tests/run_jg131_local_premium.py'
        self.assertTrue(runner.exists(), 'Hub runner missing')
        result = subprocess.run([sys.executable, str(runner), '--require-native'], env=dict(os.environ, PATH=''), capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Local Premium requires macOS Swift, Clang and xcrun', result.stdout + result.stderr)

    def test_chain_and_build_use_exact_hub_after_recovery(self):
        chain = json.loads((ROOT / 'docs/migrations/telegram-13.2-stage-chain.json').read_text())
        stage = next(row for row in chain if row['stage'] == 'jg131-local-premium')
        self.assertEqual(chain[-1]['stage'], 'jg131-saved-tags')
        manifest = json.loads((ROOT / 'patches/jg131-local-premium.sha256.json').read_text())
        self.assertEqual(stage['regenerated_patch_sha256'], manifest['patch_sha256'])
        for name, row in manifest['owners'].items():
            self.assertEqual(stage['owners'][name], {'before': row['before_sha256'], 'after': row['after_sha256']})
        for name in ('scripts/build_jg13.sh', '.github/workflows/no-ads-native.yml'):
            source = (ROOT / name).read_text()
            self.assertLess(source.index('scripts/materialize_jg131_beta2_recovery.py'), source.index('scripts/materialize_jg131_local_premium.py'))
            self.assertLess(source.index('tests/run_jg131_saved_tags.py --require-native --require-full-source'), source.index("-p 'test_jg1312*.py'"))

    def test_partial_hub_cannot_fall_back_to_recovery(self):
        import materialize_jg131_local_premium as hub
        import verify_jg13_source as verifier
        self.assertIn('from materialize_jg131_local_premium import', Path(verifier.__file__).read_text(), 'Hub terminal detection missing')
        final_bytes = b'exact hub first owner'
        owners = {'submodules/First.swift': {'after_sha256': hashlib.sha256(final_bytes).hexdigest()},
                  'submodules/Second.swift': {'after_sha256': hashlib.sha256(b'second').hexdigest()}}
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            first = source / 'submodules/First.swift'
            first.parent.mkdir()
            first.write_bytes(final_bytes)
            with patch.object(verifier, 'SOURCE', source), patch.object(hub, 'manifest', return_value={'owners': owners}):
                with self.assertRaisesRegex(RuntimeError, '(?:Local Premium output changed|Mixed/corrupt132baseline boundary)'):
                    verifier.main()


if __name__ == '__main__':
    unittest.main()
