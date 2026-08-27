import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "apply_jerkgram_build124_telegram_api_credentials1.py"
VERIFY = REPO / "scripts" / "verify_jerkgram_build124_telegram_api_credentials1.py"
EXPECTED_API_ID = "22732185"


class TelegramApiCredentialsTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("telegram_api_credentials", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def official_variables(self):
        return '''telegram_bundle_id = "ph.telegra.Telegraph"\ntelegram_api_id = "8"\ntelegram_api_hash = "7245de8e747a0d6fbe11f7cc14fcc0bb"\ntelegram_team_id = "C67CF9S4VU"\n'''

    def test_replaces_only_api_credentials(self):
        module = self.load_module()
        result = module.patch_variables(self.official_variables(), EXPECTED_API_ID, "0123456789abcdef0123456789abcdef")
        self.assertIn(f'telegram_api_id = "{EXPECTED_API_ID}"', result)
        self.assertIn('telegram_api_hash = "0123456789abcdef0123456789abcdef"', result)
        self.assertIn('telegram_bundle_id = "ph.telegra.Telegraph"', result)
        self.assertIn('telegram_team_id = "C67CF9S4VU"', result)
        self.assertNotIn('telegram_api_id = "8"', result)
        self.assertNotIn('telegram_api_hash = "7245de8e747a0d6fbe11f7cc14fcc0bb"', result)

    def test_rejects_missing_credentials(self):
        module = self.load_module()
        for api_id, api_hash in (("", "0123456789abcdef0123456789abcdef"), (EXPECTED_API_ID, "")):
            with self.assertRaises(ValueError):
                module.validate_credentials(api_id, api_hash)

    def test_rejects_malformed_credentials(self):
        module = self.load_module()
        bad = (("abc", "0123456789abcdef0123456789abcdef"), (EXPECTED_API_ID, "not-a-telegram-api-hash"))
        for api_id, api_hash in bad:
            with self.assertRaises(ValueError):
                module.validate_credentials(api_id, api_hash)

    def test_rejects_any_api_id_other_than_build124_canary_identity(self):
        module = self.load_module()
        for api_id in ("8", "12345678", "22732184", "22732186"):
            with self.assertRaises(ValueError):
                module.validate_credentials(api_id, "0123456789abcdef0123456789abcdef")

    def test_uses_existing_jerkgram_secret_environment_names(self):
        source = SCRIPT.read_text(encoding="utf-8") + VERIFY.read_text(encoding="utf-8")
        self.assertIn('JERKGRAM_TELEGRAM_API_ID', source)
        self.assertIn('JERKGRAM_TELEGRAM_API_HASH', source)
        self.assertNotIn('os.environ.get("TELEGRAM_API_ID"', source)
        self.assertNotIn('os.environ.get("TELEGRAM_API_HASH"', source)

    def test_does_not_log_secret_values(self):
        source = SCRIPT.read_text(encoding="utf-8")
        print_lines = "\n".join(
            line for line in source.splitlines()
            if "print(" in line
        )
        self.assertNotIn("api_id", print_lines)
        self.assertNotIn("api_hash", print_lines)
        self.assertNotIn("{api_id}", print_lines)
        self.assertNotIn("{api_hash}", print_lines)

    def test_patch_is_idempotent(self):
        module = self.load_module()
        api_id = EXPECTED_API_ID
        api_hash = "0123456789abcdef0123456789abcdef"
        once = module.patch_variables(self.official_variables(), api_id, api_hash)
        twice = module.patch_variables(once, api_id, api_hash)
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()
