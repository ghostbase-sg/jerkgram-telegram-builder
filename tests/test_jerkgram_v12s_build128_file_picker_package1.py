import importlib.util
from pathlib import Path
import sys
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "jerkgram_finalize_build128_file_picker_package1.py"
sys.path.insert(0, str(REPO / "scripts"))


class Build128FilePickerPackageTests(unittest.TestCase):
    def load_package(self):
        self.assertTrue(PATCH.is_file(), "Build128 FilePicker package step is missing")
        spec = importlib.util.spec_from_file_location("build128_file_picker_package", PATCH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def test_file_picker_is_main_app_only_with_a_pinned_asset(self):
        module = self.load_package()
        self.assertEqual(module.FILE_PICKER_NAME, "FilePickerFix.dylib")
        self.assertEqual(module.FILE_PICKER_INSTALL_NAME, "@executable_path/Frameworks/FilePickerFix.dylib")
        self.assertEqual(module.FILE_PICKER_SHA256, "ece2756a52ee34110b3a0252008cce3cd58b359d7571edd080032e064bf0cc7a")
        self.assertEqual(module.approved_file_picker().sha256, module.FILE_PICKER_SHA256)


if __name__ == "__main__":
    unittest.main()
