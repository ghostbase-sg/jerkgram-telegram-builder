"""BOT terminal stage must reject mixed/tampered parents before any write."""
import unittest
import test_jg131_translation_repair_stage as shared


class BotBridgeStage(shared.RepairStage):
    MATERIALIZER = shared.ROOT / 'scripts/materialize_jg131_botbridge1.py'

    def setUp(self):
        self.assertTrue(self.MATERIALIZER.exists(), 'BOTBRIDGE1 terminal materializer missing')
        super().setUp()
        self.stage.apply_repair = self.stage.apply_botbridge
        self.stage.verify_repair = self.stage.verify_botbridge

    def test_patch_owner_escape_refused(self):
        import json
        values = json.loads(self.manifest.read_text())
        values['owners']['../outside.swift'] = values['owners'].pop('submodules/A.swift')
        self.manifest.write_text(json.dumps(values))
        with self.assertRaises((RuntimeError, ValueError)):
            self.stage.apply_botbridge(self.source)
        self.assertEqual((self.source/'submodules/A.swift').read_bytes(), self.before['submodules/A.swift'])

    def test_scope_mismatch_refused(self):
        import json
        values = json.loads(self.manifest.read_text())
        del values['owners']['submodules/Z.swift']
        self.manifest.write_text(json.dumps(values))
        with self.assertRaises(RuntimeError):
            self.stage.apply_botbridge(self.source)
        self.assertEqual((self.source/'submodules/A.swift').read_bytes(), self.before['submodules/A.swift'])
