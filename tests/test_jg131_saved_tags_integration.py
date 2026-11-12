"""Terminal Tags chain keeps required native/full-checkout gates fail closed."""
import contextlib
import hashlib
import io
import importlib.util
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


class SavedTagsIntegration(unittest.TestCase):
    def test_required_native_fails_closed(self):
        runner = ROOT / 'tests/run_jg131_saved_tags.py'
        self.assertTrue(runner.exists(), 'Saved Tags composed runner missing')
        result = subprocess.run([sys.executable, str(runner), '--require-native'], env=dict(os.environ, PATH=''), capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Saved Tags requires macOS Swift, Clang and xcrun', result.stdout + result.stderr)

    def test_required_full_source_rejects_partial_tree(self):
        runner = ROOT / 'tests/run_jg131_saved_tags.py'
        self.assertTrue(runner.exists(), 'Saved Tags composed runner missing')
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(runner), '--require-full-source'], env=dict(os.environ, JG_SAVED_TAGS_SOURCE=directory), capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('composed source gates PASS', result.stdout)

    def test_chain_and_common_release_have_one_required_composed_gate(self):
        chain = json.loads((ROOT / 'docs/migrations/telegram-13.2-stage-chain.json').read_text())
        self.assertEqual((len(chain), chain[-1]['order'], chain[-1]['stage']), (32, 32, 'jg131-saved-tags'))
        manifest = json.loads((ROOT / 'patches/jg131-saved-tags.sha256.json').read_text())
        self.assertEqual(len(manifest['owners']), 12)
        self.assertEqual(sum(row['before_sha256'] is None for row in manifest['owners'].values()), 5)
        self.assertEqual(chain[-1]['regenerated_patch_sha256'], manifest['patch_sha256'])
        self.assertEqual(chain[-1]['owners'], {name: {'before': row['before_sha256'], 'after': row['after_sha256']} for name, row in manifest['owners'].items()})
        for name in ('scripts/build_jg13.sh', '.github/workflows/no-ads-native.yml'):
            source = (ROOT / name).read_text()
            stages = ('botbridge1', 'beta2_recovery', 'local_premium', 'saved_tags')
            positions = [source.index('scripts/materialize_jg131_' + stage + '.py') for stage in stages]
            self.assertEqual(positions, sorted(positions))
            gate = 'tests/run_jg131_saved_tags.py --require-native --require-full-source'
            self.assertEqual(source.count(gate), 1)
            self.assertLess(source.index(gate), source.index("-p 'test_jg1312*.py'"))
            for stage in stages[:-1]:
                self.assertNotIn('tests/run_jg131_' + stage + '.py --require-native', source)
        config = json.loads((ROOT / 'jerkgram-migration.json').read_text())
        self.assertEqual((config['build_number'], config['artifact_suffix']), (180, 'BETA3'))
        workflow = (ROOT / '.github/workflows/build.yml').read_text()
        self.assertIn('needs: source-preflight', workflow)
        self.assertIn('      - dev/beta2-local-premium-tags-179', workflow)
        self.assertNotIn('BETA2-RECOVERY', workflow)
        for suffix in ('.ipa', '.json'):
            self.assertIn('artifacts/Jerkgram-1.2.0-Build180-BETA3' + suffix, workflow)

    def test_partial_tags_cannot_fall_back_to_hub(self):
        self.assertTrue((ROOT / 'scripts/materialize_jg131_saved_tags.py').exists(), 'Saved Tags materializer missing')
        import materialize_jg131_saved_tags as tags
        import verify_jg13_source as verifier
        data = b'exact first tags owner'
        owners = {'submodules/First.swift': {'before_sha256': 'parent', 'after_sha256': hashlib.sha256(data).hexdigest()},
                  'submodules/Second.swift': {'before_sha256': 'parent', 'after_sha256': hashlib.sha256(b'second').hexdigest()}}
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            first = source / 'submodules/First.swift'
            first.parent.mkdir()
            first.write_bytes(data)
            with patch.object(verifier, 'SOURCE', source), patch.object(tags, 'manifest', return_value={'owners': owners}):
                with self.assertRaisesRegex(RuntimeError, '(?:Saved Tags output changed|Mixed/corrupt132baseline boundary)'):
                    verifier.main()

    def test_runner_propagates_native_source_and_exact_parent_to_all_children(self):
        runner = ROOT / 'tests/run_jg131_saved_tags.py'
        self.assertTrue(runner.exists(), 'Saved Tags composed runner missing')
        spec = importlib.util.spec_from_file_location('tags_runner', runner)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        values = module.manifest()
        calls = []
        from contextlib import contextmanager
        @contextmanager
        def parent_view(source):
            yield Path('/exact-reversed-hub')
        def run(args, **kwargs):
            calls.append((args, kwargs.get('env', {})))
            return subprocess.CompletedProcess(args, 0)
        with contextlib.redirect_stdout(io.StringIO()), patch.object(module, 'manifest', return_value=values), patch.object(module.platform, 'system', return_value='Darwin'), patch.object(module.shutil, 'which', return_value='/native/tool'), patch.object(module, 'verify_source'), patch.object(module, 'verify_full_checkout', return_value=12345), patch.object(module, 'parent_source_view', parent_view), patch.object(module.subprocess, 'run', side_effect=run):
            module.main(['--require-native', '--require-full-source'], Path('/final-tags'))
        for name in ('store', 'core'):
            args, env = next((a, e) for a, e in calls if 'tests/test_jg131_beta2_saved_tags_' + name + '.py' in a)
            self.assertEqual(env['JG_SAVED_TAGS_REQUIRE_NATIVE'], '1')
            self.assertEqual(env['JG_SAVED_TAGS_SOURCE'], '/final-tags')
            self.assertEqual(env['JG_SAVED_TAGS_BEFORE'], '/exact-reversed-hub')
        args, env = next((a, e) for a, e in calls if 'tests/run_jg131_local_premium.py' in a)
        self.assertIn('--require-native', args)
        self.assertIn('--require-full-source', args)
        self.assertEqual(env['JG_LOCAL_PREMIUM_SOURCE'], '/exact-reversed-hub')
        for older, younger, variable in [('local_premium', 'beta2_recovery', 'JG_BETA2_SOURCE'), ('beta2_recovery', 'botbridge1', 'JERKGRAM_BOTBRIDGE_SOURCE')]:
            body = (ROOT / ('tests/run_jg131_' + older + '.py')).read_text()
            self.assertIn('parent_source_view(SOURCE)', body)
            self.assertIn('tests/run_jg131_' + younger + '.py', body)
            self.assertIn(variable + '=str(parent)', body)
            self.assertIn("('--require-native', '--require-full-source')", body)


if __name__ == '__main__':
    unittest.main()
