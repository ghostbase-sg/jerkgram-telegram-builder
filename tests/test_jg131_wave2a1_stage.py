"""Reuse exact apply/reverse/no-partial-write fixtures for the two-owner stage."""
import hashlib
import json
import unittest
import test_jg131_translation_repair_stage as shared


class Wave2A1Stage(shared.RepairStage):
    MATERIALIZER = shared.ROOT / 'scripts/materialize_jg131_wave2a1.py'

    def setUp(self):
        super().setUp()
        self.stage.apply_repair = self.stage.apply_wave2a1
        self.stage.verify_repair = self.stage.verify_wave2a1
        values = json.loads(self.manifest.read_text())
        values['parent_owners'] = {'submodules/Protected.swift': hashlib.sha256(b'protected baseline\n').hexdigest()}
        self.manifest.write_text(json.dumps(values))
        (self.source / 'submodules/Protected.swift').write_bytes(b'protected baseline\n')

    def snapshot(self):
        return {str(p.relative_to(self.source)): p.read_bytes() for p in self.source.rglob('*') if p.is_file()}

    def test_reapply_checks_protected_baseline(self):
        self.stage.apply_repair(self.source)
        path = self.source / 'submodules/Protected.swift'
        path.write_bytes(b'changed')
        before = self.snapshot()
        with self.assertRaises(RuntimeError):
            self.stage.apply_repair(self.source)
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
