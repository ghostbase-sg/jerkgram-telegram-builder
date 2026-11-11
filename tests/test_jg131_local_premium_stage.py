"""Exact stage rejects every bad parent before mutation; reverse stays exact."""
import hashlib
import json
import unittest
import test_jg131_translation_repair_stage as shared


class LocalPremiumStage(shared.RepairStage):
    MATERIALIZER = shared.ROOT / 'scripts/materialize_jg131_local_premium.py'

    def setUp(self):
        self.assertTrue(self.MATERIALIZER.exists(), 'Local Premium materializer missing')
        super().setUp()
        self.stage.apply_repair = self.stage.apply_hub
        self.stage.verify_repair = self.stage.verify_hub

    def test_corrupt_unchanged_recovery_parent_refused_before_write(self):
        values = json.loads(self.manifest.read_text())
        values['parent_owners'] = {'submodules/Recovery.swift': hashlib.sha256(b'accepted recovery\n').hexdigest()}
        self.manifest.write_text(json.dumps(values))
        owner = self.source / 'submodules/Recovery.swift'
        owner.write_bytes(b'unknown\n')
        with self.assertRaisesRegex(RuntimeError, 'exact recovery parent'):
            self.stage.apply_hub(self.source)
        for name, data in self.before.items():
            self.assertEqual((self.source / name).read_bytes(), data)
        self.assertFalse((self.source / 'submodules/New.swift').exists())

    def test_scope_and_owner_escape_refused(self):
        values = json.loads(self.manifest.read_text())
        values['parent_owners'] = {'../outside.swift': 'invalid'}
        self.manifest.write_text(json.dumps(values))
        with self.assertRaises((RuntimeError, ValueError)):
            self.stage.apply_hub(self.source)
        self.assertEqual((self.source / 'submodules/A.swift').read_bytes(), self.before['submodules/A.swift'])

    def test_patch_scope_mismatch_refused(self):
        values = json.loads(self.manifest.read_text())
        del values['owners']['submodules/Z.swift']
        self.manifest.write_text(json.dumps(values))
        with self.assertRaisesRegex(RuntimeError, 'patch scope changed'):
            self.stage.apply_hub(self.source)
        self.assertEqual((self.source / 'submodules/A.swift').read_bytes(), self.before['submodules/A.swift'])


if __name__ == '__main__':
    unittest.main()
