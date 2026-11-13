from jg_release_expectations import candidate_identity
"""Release wiring and terminal detection must preserve all earlier source gates."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


class RecoveryIntegration(unittest.TestCase):
    def test_required_native_refuses_missing_toolchain(self):
        result = subprocess.run([sys.executable, str(ROOT/'tests/run_jg131_beta2_recovery.py'), '--require-native'], cwd=ROOT, env=dict(os.environ, PATH=''), capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Beta2 recovery requires macOS Swift, Clang and xcrun', result.stdout+result.stderr)

    def test_release_identity_and_gates_agree(self):
        config = json.loads((ROOT/'jerkgram-migration.json').read_text())
        self.assertEqual((config['product_display_version'], config['product_technical_version'], config['build_number'], config['artifact_suffix']), candidate_identity(config))
        for name in ('scripts/build_jg13.sh', '.github/workflows/no-ads-native.yml'):
            text = (ROOT/name).read_text()
            self.assertLess(text.index('scripts/materialize_jg131_botbridge1.py'), text.index('scripts/materialize_jg131_beta2_recovery.py'))
            self.assertLess(text.index('tests/run_jg131_saved_tags.py --require-native --require-full-source'), text.index("-p 'test_jg1312*.py'"))
        build = (ROOT/'scripts/build_jg13.sh').read_text()
        self.assertIn('--define=buildNumber='+str(candidate_identity(config)[2]), build)
        self.assertLess(build.index('tests/run_jg131_saved_tags.py'), build.index('"${BAZEL_BIN:-bazelisk}" build'))
        workflow = (ROOT/'.github/workflows/build.yml').read_text()
        self.assertIn('needs: source-preflight', workflow)
        self.assertIn('      - dev/beta2-local-premium-tags-179', workflow)
        self.assertIn('      - dev/botbridge1-legacy-history-modern-write', workflow)
        self.assertNotIn('            artifacts/build.log', workflow)
        for suffix in ('.ipa', '.json'):
            self.assertIn(f'artifacts/Jerkgram-1.2.0-Build{candidate_identity(config)[2]}-{candidate_identity(config)[3]}'+suffix, workflow)

    def test_final_verifier_refuses_partial_recovery_before_bot_fallback(self):
        import materialize_jg131_beta2_recovery as recovery
        import verify_jg13_source as verifier
        owner = 'submodules/First.swift'
        final_bytes = b'one exact final owner'
        owners = {owner: {'after_sha256': hashlib.sha256(final_bytes).hexdigest()}, 'submodules/Second.swift': {'after_sha256': hashlib.sha256(b'second exact owner').hexdigest()}}
        with tempfile.TemporaryDirectory() as d:
            source = Path(d); target = source/owner; target.parent.mkdir(parents=True); target.write_bytes(final_bytes)
            with patch.object(verifier, 'SOURCE', source), patch.object(recovery, 'manifest', return_value={'owners': owners}):
                with self.assertRaisesRegex(RuntimeError, '(?:Beta2 recovery output changed|Mixed/corrupt132baseline boundary)'):
                    verifier.main()

    def test_only_proven_strings_identity_dependencies_change(self):
        owner='submodules/TelegramPresentationData/Sources/JerkgramStrings.swift'
        chain=json.loads((ROOT/'docs/migrations/telegram-13.2-stage-chain.json').read_text())
        expected = {
            'jg131-profile-metadata': ('7f3583ea0308d7406ad6b17829e5fad75920ca3dab3d558522f49bc783c78a0f', 'd6d66bf69757418e59daa5989513f181214fb62f881c5f4200fd4c57e75a3ec1', '0dab43126da5fd172fa7e8088c99c46451ab3bc6dbe14bb47dd87636e5f7326b'),
            'jg131-translation-repair': ('d6d66bf69757418e59daa5989513f181214fb62f881c5f4200fd4c57e75a3ec1', '15677b2c2ed54ac471a15529cff3925fdbaa62d14d51bbad09ab453fb33c516d', '9bdd9e5c477699049763e590a023a5c25a2cedb4fd7f37d2d2fc25342cf8ca0a'),
        }
        for name, (before178, after178, feature_patch) in expected.items():
            manifest=json.loads((ROOT/f'patches/{name}.sha256.json').read_text())
            row=manifest['owners'][owner]; proof=next(s for s in chain if s['stage']==name)['owners'][owner]
            self.assertEqual(row['preserved_previous_beta1_178'], {'before_sha256': before178, 'after_sha256': after178})
            historical=json.loads((ROOT/'docs/migrations/telegram-13.1.2-stage-chain.json').read_text())
            self.assertEqual(next(s for s in historical if s['stage']==name)['regenerated_patch_sha256'], feature_patch)
            self.assertEqual(next(s for s in chain if s['stage']==name)['regenerated_patch_sha256'], manifest['patch_sha256'])
            self.assertEqual((proof['before'],proof['after']),(row['before_sha256'],row['after_sha256']))
            self.assertEqual(hashlib.sha256((ROOT/f'patches/{name}.patch').read_bytes()).hexdigest(),manifest['patch_sha256'])


if __name__ == '__main__':
    unittest.main()
