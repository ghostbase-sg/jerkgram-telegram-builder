"""Focused regressions for the observed native scope failure and IPA recovery."""
from pathlib import Path
import json, os, plistlib, sys, tempfile, unittest, zipfile
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import package_jg13 as package
SOURCE = Path(os.environ.get('JG_STABLE182_SOURCE', ROOT.parent / 'jerkgram-next/stable182-combined'))

class Recovery(unittest.TestCase):
    def test_server_apply_does_not_capture_local_store(self):
        sys.path.insert(0, str(ROOT / 'tests'))
        from test_jg131_beta2_bot_codec import declaration
        text = (SOURCE / 'submodules/TelegramUI/Components/Settings/PeerNameColorScreen/Sources/UserApperanceScreen.swift').read_text()
        method = declaration(text, 'private func applySettings()')
        local = declaration(method, 'if component.localAppearance {')
        self.assertIn('store.snapshot.emojiUnlocked', local)
        self.assertIn('expectedGeneration: component.localAppearanceGeneration', local)
        server = method[method.index(local) + len(local):]
        self.assertNotIn('store.', server, 'store is declared only in the returning local branch')
        self.assertIn('if resolvedState.changes.contains(.emojiStatus) {', server)

    def test_all_policy_consumers_import_owning_module(self):
        # Swift imports are file-scoped; imports in another TelegramUI file do not
        # make a Postbox declaration visible here. Cover all current consumers.
        consumers = []
        for file in (SOURCE / 'submodules').rglob('*.swift'):
            text = file.read_text()
            if 'JerkgramLocalPremiumPolicy' not in text or 'Postbox/Sources/' in file.as_posix():
                continue
            consumers.append(file)
            self.assertIn('import Postbox', text, str(file.relative_to(SOURCE)))
        self.assertGreater(len(consumers), 10)

    def test_raw_archive_survives_packaging_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'jerkgram-migration.json').write_text((ROOT / 'jerkgram-migration.json').read_text())
            original = root / 'compiled.ipa'; original.write_bytes(b'compiled IPA fixture')
            def fail(candidate):
                candidate.write_bytes(b'partially packaged')
                raise RuntimeError('packaging failed')
            with patch.object(package, 'ROOT', root), patch.object(sys, 'argv', ['package', str(original)]), patch.object(package.keychain, 'package_ipa', side_effect=fail):
                with self.assertRaisesRegex(RuntimeError, 'packaging failed'): package.main()
            raw = list((root / 'artifacts').glob('*-RAW-UNVERIFIED.ipa'))
            self.assertEqual(len(raw), 1)
            self.assertEqual(raw[0].read_bytes(), original.read_bytes())
            report = json.loads(raw[0].with_suffix('.json').read_text())
            self.assertEqual(report['status'], 'RAW COMPILED IPA; PACKAGING AND VERIFICATION NOT PASSED')
            self.assertEqual(report['ci_commit'], os.environ.get('GITHUB_SHA'))
            self.assertFalse(any(p.name.endswith(json.loads((root / 'jerkgram-migration.json').read_text())['artifact_suffix'] + '.json') for p in (root / 'artifacts').glob('*.json')))

    def test_final_verifier_failure_keeps_both_archives(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = json.loads((ROOT / 'jerkgram-migration.json').read_text())
            (root / 'jerkgram-migration.json').write_text(json.dumps(config))
            original = root / 'compiled.ipa'
            with zipfile.ZipFile(original, 'w') as archive:
                for folder in ['Payload/Jerkgram.app'] + ['Payload/Jerkgram.app/PlugIns/' + n for n in package.EXTENSIONS]:
                    archive.writestr(folder + '/Info.plist', plistlib.dumps(dict(CFBundleVersion=str(config['build_number']), CFBundleShortVersionString=config['bundle_short_version'], CFBundleExecutable='App', CFBundleIdentifier=config['bundle_id'])))
                    archive.writestr(folder + '/App', b'fixture executable')
            with patch.object(package, 'ROOT', root), patch.object(sys, 'argv', ['package', str(original)]), patch.object(package.keychain, 'package_ipa'), patch.object(package.picker, 'package_file_picker'), patch.object(package.subprocess, 'run'), patch.object(package, 'verify', side_effect=RuntimeError('final verify failed')):
                with self.assertRaisesRegex(RuntimeError, 'final verify failed'): package.main()
            raw = next((root / 'artifacts').glob('*-RAW-UNVERIFIED.ipa'))
            self.assertEqual(raw.read_bytes(), original.read_bytes())
            self.assertTrue(next((root / 'artifacts').glob('*-' + config['artifact_suffix'] + '.ipa')).is_file())
            self.assertFalse(list((root / 'artifacts').glob('*-' + config['artifact_suffix'] + '.json')))

    def test_build_configuration_still_uses_existing_generator(self):
        import configure_jg13
        config = json.loads((ROOT / 'jerkgram-migration.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            example = source / 'build-system/example-configuration'; example.mkdir(parents=True)
            (example / 'variables.bzl').write_text('telegram_bundle_id = "ph.telegra.Telegraph"\ntelegram_api_id = "0"\ntelegram_api_hash = "0"\n')
            with patch.dict(os.environ, JERKGRAM_TELEGRAM_API_ID='22732185', JERKGRAM_TELEGRAM_API_HASH='0' * 32):
                configure_jg13.configure_build_inputs(source, config)
            generated = source / 'build-input/configuration-repository'
            self.assertIn(config['bundle_id'], (generated / 'variables.bzl').read_text())
            self.assertIn('22732185', (generated / 'variables.bzl').read_text())
            self.assertTrue((generated / 'MODULE.bazel').is_file())

    def test_product_checks_run_once_and_recovery_upload_is_unconditional(self):
        workflow = (ROOT / '.github/workflows/build.yml').read_text()
        build = (ROOT / 'scripts/build_jg13.sh').read_text()
        self.assertNotIn('needs: source-preflight', workflow)
        self.assertNotIn('uses: ./.github/workflows/no-ads-native.yml', workflow)
        self.assertEqual(build.count('tests/run_jg132_post181.py'), 1)
        self.assertNotIn('tests/run_jg13_history_backend.py', build)
        self.assertIn('scripts/materialize_jg132_product.py', build)
        self.assertIn('Upload recovery IPA', workflow)
        recovery = workflow.split('- name: Upload recovery IPA', 1)[1].split('- name:', 1)[0]
        self.assertIn('if: always()', recovery)
        self.assertIn('RAW-UNVERIFIED', recovery)
        self.assertIn('artifacts/build.log', workflow)

if __name__ == '__main__': unittest.main(verbosity=2)
