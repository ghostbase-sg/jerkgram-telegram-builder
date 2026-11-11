"""Saved Tags exact stage preflights every parent before touching source."""
import hashlib
import json
import unittest
import test_jg131_translation_repair_stage as shared


class SavedTagsStage(shared.RepairStage):
    MATERIALIZER = shared.ROOT / 'scripts/materialize_jg131_saved_tags.py'

    def setUp(self):
        self.assertTrue(self.MATERIALIZER.exists(), 'Saved Tags materializer missing')
        super().setUp()
        self.stage.apply_repair = self.stage.apply_tags
        self.stage.verify_repair = self.stage.verify_tags
        values = json.loads(self.manifest.read_text())
        values['parent_owners'] = {'submodules/Hub.swift': hashlib.sha256(b'accepted hub\n').hexdigest()}
        self.manifest.write_text(json.dumps(values))
        (self.source / 'submodules/Hub.swift').write_bytes(b'accepted hub\n')

    def snapshot(self):
        return {str(p.relative_to(self.source)): p.read_bytes() for p in self.source.rglob('*') if p.is_file()}

    def test_each_parent_corruption_refused_without_any_write(self):
        values = json.loads(self.manifest.read_text())
        for name in [*values['owners'], *values['parent_owners']]:
            with self.subTest(owner=name):
                path = self.source / name
                original = path.read_bytes() if path.exists() else None
                path.write_bytes(b'corrupt or unexpectedly present\n')
                before = self.snapshot()
                with self.assertRaisesRegex(RuntimeError, 'exact Hub parent'):
                    self.stage.apply_tags(self.source)
                self.assertEqual(self.snapshot(), before)
                if original is None:
                    path.unlink()
                else:
                    path.write_bytes(original)

    def test_reapply_checks_unchanged_context_before_returning(self):
        self.stage.apply_tags(self.source)
        (self.source / 'submodules/Hub.swift').write_bytes(b'unknown\n')
        before = self.snapshot()
        with self.assertRaisesRegex(RuntimeError, 'exact Hub parent'):
            self.stage.apply_tags(self.source)
        self.assertEqual(self.snapshot(), before)

    def test_scope_and_owner_escape_refused(self):
        values = json.loads(self.manifest.read_text())
        values['parent_owners'] = {'../outside.swift': 'invalid'}
        self.manifest.write_text(json.dumps(values))
        before = self.snapshot()
        with self.assertRaises((RuntimeError, ValueError)):
            self.stage.apply_tags(self.source)
        self.assertEqual(self.snapshot(), before)

    def test_patch_scope_mismatch_refused(self):
        values = json.loads(self.manifest.read_text())
        del values['owners']['submodules/Z.swift']
        self.manifest.write_text(json.dumps(values))
        before = self.snapshot()
        with self.assertRaisesRegex(RuntimeError, 'patch scope changed'):
            self.stage.apply_tags(self.source)
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
