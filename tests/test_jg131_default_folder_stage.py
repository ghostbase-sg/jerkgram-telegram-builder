"""Exercise TASK B's real materializer using the same adversarial stage fixtures."""
import unittest
import test_jg131_translation_repair_stage as shared


class DefaultFolderStage(shared.RepairStage):
    MATERIALIZER = shared.ROOT / 'scripts/materialize_jg131_default_folder.py'

    def setUp(self):
        super().setUp()
        # Adapt only the test's common callbacks, not the production module.
        self.stage.apply_repair = self.stage.apply_folder
        self.stage.verify_repair = self.stage.verify_folder


if __name__ == '__main__':
    unittest.main()
