"""BOT terminal stage must reject mixed/tampered parents before any write."""
import unittest
import test_jg131_translation_repair_stage as shared


class Beta2RecoveryStage(shared.RepairStage):
    MATERIALIZER = shared.ROOT / 'scripts/materialize_jg131_beta2_recovery.py'

    def setUp(self):
        self.assertTrue(self.MATERIALIZER.exists(), 'Beta2 recovery terminal materializer missing')
        super().setUp()
        self.stage.apply_repair = self.stage.apply_recovery
        self.stage.verify_repair = self.stage.verify_recovery

    def test_patch_owner_escape_refused(self):
        import json
        values = json.loads(self.manifest.read_text())
        values['owners']['../outside.swift'] = values['owners'].pop('submodules/A.swift')
        self.manifest.write_text(json.dumps(values))
        with self.assertRaises((RuntimeError, ValueError)):
            self.stage.apply_recovery(self.source)
        self.assertEqual((self.source/'submodules/A.swift').read_bytes(), self.before['submodules/A.swift'])

    def test_scope_mismatch_refused(self):
        import json
        values = json.loads(self.manifest.read_text())
        del values['owners']['submodules/Z.swift']
        self.manifest.write_text(json.dumps(values))
        with self.assertRaises(RuntimeError):
            self.stage.apply_recovery(self.source)
        self.assertEqual((self.source/'submodules/A.swift').read_bytes(), self.before['submodules/A.swift'])
