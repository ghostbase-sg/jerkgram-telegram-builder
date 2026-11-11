"""Active source contracts belong to the genuine official 13.1.2 parent."""
from pathlib import Path
import hashlib
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
TARGET = '279f89e4d4f63f17227bf877dc3d8990f22ecd58'


class Migration1312(unittest.TestCase):
    def test_active_manifests_share_target_and_chain_proof(self):
        chain = json.loads((ROOT / 'docs/migrations/telegram-13.1.2-stage-chain.json').read_text())
        self.assertEqual(len(chain), 32)
        stages = {s['stage']: s for s in chain}
        for p in (ROOT / 'patches').glob('jg13*.sha256.json'):
            m = json.loads(p.read_text())
            if 'upstream_sha' in m:
                self.assertEqual(m['upstream_sha'], TARGET, p.name)
            if 'patch_sha256' in m:
                name = p.name.removesuffix('.sha256.json')
                data = (p.parent / (name + '.patch')).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), m['patch_sha256'])
                self.assertEqual(m['patch_sha256'], stages[name]['regenerated_patch_sha256'])

    def test_botbridge_chain_owners_match_terminal_manifest(self):
        chain = json.loads((ROOT / 'docs/migrations/telegram-13.1.2-stage-chain.json').read_text())
        stage = next(s for s in chain if s['stage'] == 'jg131-botbridge1')
        manifest = json.loads((ROOT / 'patches/jg131-botbridge1.sha256.json').read_text())

        self.assertEqual(set(stage['owners']), set(manifest['owners']))
        for path, owner in manifest['owners'].items():
            self.assertEqual(stage['owners'][path]['before'], owner['before_sha256'], path)
            self.assertEqual(stage['owners'][path]['after'], owner['after_sha256'], path)

    def test_recovery_chain_owners_match_terminal_manifest(self):
        chain = json.loads((ROOT / 'docs/migrations/telegram-13.1.2-stage-chain.json').read_text())
        stage = next(s for s in chain if s['stage'] == 'jg131-beta2-recovery')
        manifest = json.loads((ROOT / 'patches/jg131-beta2-recovery.sha256.json').read_text())
        self.assertEqual(stage['stage'], 'jg131-beta2-recovery')
        self.assertEqual(len(manifest['owners']), 5)
        self.assertEqual(set(stage['owners']), set(manifest['owners']))
        for path, row in manifest['owners'].items():
            self.assertEqual(stage['owners'][path]['before'], row['before_sha256'])
            self.assertEqual(stage['owners'][path]['after'], row['after_sha256'])

    def test_prepare_asserts_target_version_and_tlottie_gitlink(self):
        prepare = (ROOT / 'scripts/prepare_source_official.sh').read_text()
        self.assertIn('EXPECTED_COMMIT="' + TARGET + '"', prepare)
        self.assertIn("versions['app'] == '13.1.2'", prepare)
        self.assertIn('92df98dc209bc39b1e567ec74a8c86a0af5239de', prepare)
        self.assertIn('submodules/tlottie/tlottie', prepare)

    def test_historical_stable_and_snapshot_are_preserved(self):
        config = json.loads((ROOT / 'jerkgram-migration.json').read_text())
        self.assertEqual(config['source_snapshot_sha256'], '6499b01ab4a5db475dde15ac7b773643a1d6188d2432b9746dab2adde2a18813')
        self.assertEqual(config['source_snapshot_provenance']['upstream_version'], '13.1.1')
        original = (ROOT / 'patches/jg13-stable.product.patch').read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(), 'c6449542039d11cd351b0f32454e50013c53b1fcfe45a5130109a892facb30cf')

    def test_preservation_gate_runs_after_final_botbridge_in_both_entrypoints(self):
        for name in ('scripts/build_jg13.sh', '.github/workflows/no-ads-native.yml'):
            text = (ROOT / name).read_text()
            self.assertIn("-p 'test_jg1312*.py'", text, name)
            self.assertLess(text.index('python3 tests/run_jg131_saved_tags.py --require-native --require-full-source'),
                            text.index("-p 'test_jg1312*.py'"), name)


if __name__ == '__main__':
    unittest.main()
