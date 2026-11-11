"""Actual production table + pinned ValueBox protocol + real SQLite harness.

Native is mandatory with --require-native / JG_SAVED_TAGS_REQUIRE_NATIVE=1.
No Python reimplementation substitutes for production Swift behavior.
"""
from pathlib import Path
import os, re, shutil, subprocess, sys, tempfile, unittest
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG_SAVED_TAGS_SOURCE', ROOT.parent/'jerkgram-next/beta2/saved-tags/source'))
OWNER = SOURCE/'submodules/Postbox/Sources/LocalSavedTagsTable.swift'
class SavedTagsFixture(unittest.TestCase):
    def test_pinned_inputs_and_exact_assembly(self):
        from saved_tags_native import verify_fixture, assemble
        verify_fixture(ROOT)
        with tempfile.TemporaryDirectory(prefix='saved-tags-assemble-') as tmp:
            paths = assemble(ROOT, SOURCE, Path(tmp))
            self.assertTrue(all(p.is_file() for p in paths))
            boundary = (Path(tmp)/'Boundary.swift').read_text()
            api = (SOURCE/'submodules/Postbox/Sources/Postbox.swift').read_text().split('// BEGIN LOCAL SAVED TAGS TRANSACTION API')[1].split('// END LOCAL SAVED TAGS TRANSACTION API')[0]
            self.assertIn(api, boundary)
            self.assertNotIn('/* EXACT_', boundary)

    def test_provenance_tamper_is_rejected_for_both_input_sets(self):
        from saved_tags_native import verify_fixture
        with tempfile.TemporaryDirectory(prefix='saved-tags-tamper-') as tmp:
            root = Path(tmp)
            for name in ('beta2_saved_tags', 'beta2_bot_codec'):
                shutil.copytree(ROOT/'tests/fixtures'/name, root/'tests/fixtures'/name)
            for name, owner in (('beta2_saved_tags', 'ValueBox.swift'), ('beta2_bot_codec', 'PreferencesEntry.swift')):
                path = root/'tests/fixtures'/name/'official/submodules/Postbox/Sources'/owner
                original = path.read_bytes()
                path.write_bytes(original + b'\n')
                with self.assertRaises(AssertionError, msg=name):
                    verify_fixture(root)
                path.write_bytes(original)

    @unittest.skipIf(shutil.which('swiftc') and shutil.which('xcrun'), 'missing-tool gate applies only without native tools')
    def test_required_native_fails_closed(self):
        result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--require-native', 'SavedTagsNative.test_production_sqlite'], capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Required native Saved Tags gate needs macOS', result.stdout + result.stderr)

    def test_allocations_and_existing_postbox_owner_preserved(self):
        before = Path(os.environ.get('JG_SAVED_TAGS_BEFORE', SOURCE.parent/'before'))
        postbox = (SOURCE/'submodules/Postbox/Sources/Postbox.swift').read_text()
        old = (before/'submodules/Postbox/Sources/Postbox.swift').read_text()
        allocated = {int(v, 0) for v in re.findall(r'\.tableSpec\((0x[0-9a-fA-F]+|[0-9]+)\)', old)}
        self.assertNotIn(0x4A470001, allocated)
        self.assertIn('LocalSavedTagsTable.tableSpec(0x4A470001)', postbox)
        self.assertIn('tables.append(self.localSavedTagsTable)', postbox)
        from saved_tags_native import declaration
        self.assertEqual(declaration(postbox, 'fileprivate func setPreferencesEntry(key:'), declaration(old, 'fileprivate func setPreferencesEntry(key:'))
        # Reverse views link unchanged directories. Follow those branches while
        # keeping the registration scan within Postbox, including on full trees.
        swift = (Path(folder)/name
                 for folder, _, names in os.walk(before/'submodules/Postbox/Sources', followlinks=True)
                 for name in names if name.endswith('.swift'))
        self.assertFalse(any(re.search(r'0x4[aA]470003', p.read_text()) for p in swift),
                         '0x4A470003 preference key already allocated in exact Postbox parent')
        build = SOURCE/'submodules/Postbox/BUILD'
        if not build.exists():
            # Partial source proofs omit BUILD. This declaration-only fallback
            # is checked in and verified, never a private research dependency.
            from saved_tags_native import verify_fixture
            verify_fixture(ROOT)
            build = ROOT/'tests/fixtures/beta2_saved_tags/official/submodules/Postbox/BUILD'
        self.assertIn('"Sources/**/*.swift"', build.read_text())

    def test_allocation_check_in_clean_layout_with_exact_symlink_parent(self):
        """Run the real child check without private research or SDD inputs."""
        sys.path.insert(0, str(ROOT/'scripts'))
        from materialize_jg131_saved_tags import manifest, parent_source_view
        with tempfile.TemporaryDirectory(prefix='saved-tags-clean-layout-') as tmp:
            base = Path(tmp)
            builder = base/'builder'
            tests = builder/'tests'
            tests.mkdir(parents=True)
            for name in ('test_jg131_beta2_saved_tags_store.py', 'saved_tags_native.py'):
                shutil.copyfile(ROOT/'tests'/name, tests/name)
            for name in ('beta2_saved_tags', 'beta2_bot_codec'):
                shutil.copytree(ROOT/'tests/fixtures'/name, tests/'fixtures'/name)
            final = builder/'work/swiftgram-src'
            values = manifest()
            # Copy actual inputs for the reverse view and registration proof,
            # without duplicating a multi-gigabyte full Telegram checkout.
            for name in set(values['owners']) | set(values['parent_owners']):
                path = final/name
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(SOURCE/name, path)
            shutil.copytree(SOURCE/'submodules/Postbox/Sources',
                            final/'submodules/Postbox/Sources', dirs_exist_ok=True)
            # This unchanged directory becomes a directory symlink in the real
            # reverse view. Path.rglob does not descend through it.
            probe = final/'submodules/Postbox/Sources/UnchangedAllocationOwner/Probe.swift'
            probe.parent.mkdir()
            probe.write_text('// no occupied preference key\n')
            with parent_source_view(final) as before:
                self.assertTrue((before/probe.relative_to(final).parent).is_symlink())
                self.assertFalse((builder/'work/before').exists())
                self.assertFalse((base/'jerkgram-next').exists())
                self.assertFalse((builder/'.superpowers').exists())

                def run_check():
                    return subprocess.run(
                        [sys.executable, str(tests/'test_jg131_beta2_saved_tags_store.py'),
                         'SavedTagsFixture.test_allocations_and_existing_postbox_owner_preserved'],
                        cwd=builder, env=dict(os.environ, JG_SAVED_TAGS_SOURCE=str(final),
                                             JG_SAVED_TAGS_BEFORE=str(before)),
                        capture_output=True, text=True, timeout=30)

                result = run_check()
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                probe.write_text('let occupiedPreferenceKey = 0x4A470003\n')
                result = run_check()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('0x4A470003', result.stdout + result.stderr)
                probe.write_text('// no occupied preference key\n')

                postbox = before/'submodules/Postbox/Sources/Postbox.swift'
                original = postbox.read_text()
                postbox.write_text(original + '\n// existing .tableSpec(0x4A470001)\n')
                result = run_check()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('unexpectedly found', result.stdout + result.stderr)
                postbox.write_text(original.replace(
                    'fileprivate func setPreferencesEntry(key:',
                    'fileprivate func changedPreferencesSink(key:', 1))
                result = run_check()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('substring not found', result.stdout + result.stderr)
                postbox.write_text(original)

                # A selected checkout's declaration takes priority over fallback
                # evidence. A missing glob must not be hidden by a valid fixture.
                build = final/'submodules/Postbox/BUILD'
                pinned = tests/'fixtures/beta2_saved_tags/official/submodules/Postbox/BUILD'
                build.write_bytes(pinned.read_bytes())
                result = run_check()
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                build.write_text('# source glob missing\n')
                result = run_check()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Sources/**/*.swift', result.stdout + result.stderr)
                build.unlink()

                pinned.write_bytes(pinned.read_bytes() + b'\n')
                result = run_check()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('submodules/Postbox/BUILD', result.stdout + result.stderr)

    def test_exhausted_revision_rejects_before_mutation(self):
        from saved_tags_native import declaration
        body = OWNER.read_text()
        self.assertTrue('guard result.revision < Int64.max - 1' in body, 'revision must preflight before writes')
        for name in ('create', 'rename', 'set', 'updateMetadata', 'delete', 'removeMessages', 'removeRange'):
            self.assertIn('try mutationMetadata(selfPeerId)', declaration(body, 'func ' + name + '('))

    def test_range_preflight_checks_secondary_key_identity(self):
        from saved_tags_native import declaration
        body = declaration(OWNER.read_text(), 'func removeRange(')
        self.assertIn('guard k == expectedKey', body)

    def test_global_batch_rejects_before_allocating_identity_array(self):
        from saved_tags_native import declaration
        body = declaration(OWNER.read_text(), 'func removeGlobalIds(')
        self.assertIn('guard ids.count <= 1000', body)
        self.assertLess(body.index('guard ids.count <= 1000'), body.index('ids.map'))

class SavedTagsNative(unittest.TestCase):
    def test_production_sqlite(self):
        self.assertTrue(OWNER.is_file(), 'durable Saved Tags production table has not been implemented')
        if not shutil.which('swiftc') or not shutil.which('xcrun'):
            if '--require-native' in sys.argv or os.environ.get('JG_SAVED_TAGS_REQUIRE_NATIVE') == '1':
                self.fail('Required native Saved Tags gate needs macOS Swift/Clang/xcrun; no native persistence evidence available')
            self.skipTest('Native SQLite production-table fixture pending: no macOS Swift/Clang/xcrun')
        from saved_tags_native import run_native
        run_native(ROOT, SOURCE)
if __name__ == '__main__':
    unittest.main(argv=[a for a in sys.argv if a != '--require-native'], verbosity=2)
