"""Executable source-boundary guards, including scans through restored-view links."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))

class BotBridgeIntegration(unittest.TestCase):
    def guard(self):
        path=ROOT/'scripts/verify_jg131_botbridge1.py'
        self.assertTrue(path.exists(), 'BOTBRIDGE1 source verifier missing')
        spec=importlib.util.spec_from_file_location('botbridge_guard',path)
        mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        return mod

    def test_collision_scan_follows_restored_view_directory_links(self):
        guard=self.guard()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); source=root/'source'; source.mkdir(); linked=root/'real'; linked.mkdir()
            (source/'linked').symlink_to(linked,target_is_directory=True)
            (linked/'third_party.swift').write_text('let existing = 0x4a470002\n')
            with self.assertRaisesRegex(RuntimeError,'collision'):
                guard.verify_preference_key_available(source)

    def test_collision_scan_includes_decimal_spelling(self):
        guard=self.guard()
        with tempfile.TemporaryDirectory() as d:
            source=Path(d); (source/'Other.swift').write_text('let key = '+str(0x4A470002)+'\n')
            with self.assertRaisesRegex(RuntimeError,'collision'):
                guard.verify_preference_key_available(source)

    def test_collision_scan_ignores_git_metadata_but_counts_product_files(self):
        guard=self.guard()
        with tempfile.TemporaryDirectory() as d:
            source=Path(d); (source/'.git').mkdir(); (source/'.git/log').write_text('0x4A470002')
            (source/'Clean.swift').write_text('let key = 3\n')
            self.assertEqual(guard.verify_preference_key_available(source),1)

    def test_collision_scan_is_bounded_on_directory_cycle(self):
        guard=self.guard()
        with tempfile.TemporaryDirectory() as d:
            source=Path(d); (source/'loop').symlink_to(source,target_is_directory=True)
            (source/'Clean.swift').write_text('let key = 4\n')
            try:
                self.assertEqual(guard.verify_preference_key_available(source),1)
            except RuntimeError as error:
                self.fail('Repeated physical directory must be scanned only once: '+str(error))

    def test_provenance_tamper_refused(self):
        guard=self.guard()
        self.assertTrue(hasattr(guard, 'verify_provenance_files'), 'portable provenance guard missing')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'proof.json').write_bytes(b'known\n')
            import hashlib
            expected={'proof.json':hashlib.sha256(b'known\n').hexdigest()}
            guard.verify_provenance_files(root,expected)
            (root/'proof.json').write_bytes(b'tampered\n')
            with self.assertRaisesRegex(RuntimeError,'provenance'):
                guard.verify_provenance_files(root,expected)

    def test_full_checkout_rejects_missing_tracked_source_despite_correct_git_pin(self):
        guard=self.guard()
        from unittest.mock import patch
        pin='279f89e4d4f63f17227bf877dc3d8990f22ecd58'
        tracked=b'\0'.join(b'100644 '+b'a'*40+b' 0\tF'+str(i).encode()+b'.swift' for i in range(1001))+b'\0'
        with tempfile.TemporaryDirectory() as d:
            with patch.object(guard.subprocess,'check_output',side_effect=[pin+'\n',tracked]):
                with self.assertRaisesRegex(RuntimeError,'missing tracked product input'):
                    guard.verify_full_checkout(Path(d),pin)

    def test_required_native_gate_refuses_missing_toolchain(self):
        import os,subprocess
        env=dict(os.environ,PATH='')
        result=subprocess.run([sys.executable,str(ROOT/'tests/run_jg131_botbridge1.py'),'--require-native','--bot-only'],cwd=ROOT,env=env,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('requires macOS Swift compiler and xcrun',result.stdout+result.stderr)

    def test_final_verifier_refuses_partial_bot_stage_before_legacy_fallback(self):
        import verify_jg13_source as final
        previous=final.SOURCE
        with tempfile.TemporaryDirectory() as d:
            source=Path(d); new=source/'submodules/TelegramCore/Sources/State/JerkgramBotBridgeHistory.swift'
            new.parent.mkdir(parents=True);new.write_text('tampered\n')
            try:
                final.SOURCE=source
                with self.assertRaisesRegex(RuntimeError,'BOTBRIDGE1 output changed'):
                    try:
                        final.main()
                    except OSError as error:
                        self.fail('Partial BOT stage fell through to a legacy owner: '+str(error))
            finally:final.SOURCE=previous

    def test_full_checkout_presence_accepts_git_directory_symlink(self):
        guard=self.guard()
        from unittest.mock import patch
        pin='279f89e4d4f63f17227bf877dc3d8990f22ecd58'
        with tempfile.TemporaryDirectory() as d:
            source=Path(d); (source/'directory').mkdir()
            (source/'DirLink').symlink_to(source/'directory',target_is_directory=True)
            for i in range(1000): (source/('F'+str(i)+'.swift')).write_text('')
            tracked=b'\0'.join(b'100644 '+b'a'*40+b' 0\tF'+str(i).encode()+b'.swift' for i in range(1000))
            tracked+=b'\0'+b'120000 '+b'b'*40+b' 0\tDirLink\0'
            with patch.object(guard.subprocess,'check_output',side_effect=[pin+'\n',tracked]):
                try:
                    self.assertEqual(guard.verify_full_checkout(source,pin),1001)
                except RuntimeError as error:
                    self.fail('Valid tracked directory symlink rejected: '+str(error))
