import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
INSTALLER = REPO / "scripts" / "install_jerkgram_build124_telegram_api_probe_hook1.py"


class TelegramApiProbeHookTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("telegram_api_probe_hook", INSTALLER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self):
        return '''cat >> build-input/configuration-repository/variables.bzl <<'EOF'\n\n# Added by GhostBase builder\ntelegram_bazel_path = "."\ntelegram_use_xcode_managed_codesigning = False\n\n# Swiftgram config placeholder for BuildConfig\nsg_config = "{}"\nEOF\n\necho "after config"\n\n"$BAZEL_BIN" build //Telegram:Telegram\n'''

    def test_injects_apply_and_verify_after_active_config_exists(self):
        module = self.load_module()
        result = module.patch_probe(self.fixture())
        apply_name = "apply_jerkgram_build124_telegram_api_credentials1.py"
        verify_name = "verify_jerkgram_build124_telegram_api_credentials1.py"
        self.assertIn(apply_name, result)
        self.assertIn(verify_name, result)
        self.assertLess(result.index("sg_config = \"{}\""), result.index(apply_name))
        self.assertLess(result.index(apply_name), result.index(verify_name))
        self.assertLess(result.index(verify_name), result.index('"$BAZEL_BIN" build'))

    def test_patch_is_idempotent(self):
        module = self.load_module()
        once = module.patch_probe(self.fixture())
        twice = module.patch_probe(once)
        self.assertEqual(once, twice)
        self.assertEqual(once.count("apply_jerkgram_build124_telegram_api_credentials1.py"), 1)
        self.assertEqual(once.count("verify_jerkgram_build124_telegram_api_credentials1.py"), 1)


if __name__ == "__main__":
    unittest.main()
