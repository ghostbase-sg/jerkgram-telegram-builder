"""Exercise TASK C's real materializer using the same adversarial stage fixtures."""
import unittest
import test_jg131_translation_repair_stage as shared


class SettingsGlassStage(shared.RepairStage):
    MATERIALIZER = shared.ROOT / 'scripts/materialize_jg131_settings_glass_expansion.py'

    def setUp(self):
        super().setUp()
        # Adapt only the test's common callbacks, not the production module.
        self.stage.apply_repair = self.stage.apply_glass
        self.stage.verify_repair = self.stage.verify_glass


if __name__ == '__main__':
    unittest.main()
