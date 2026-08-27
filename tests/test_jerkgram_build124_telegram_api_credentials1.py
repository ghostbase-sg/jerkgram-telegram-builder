import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "apply_jerkgram_build124_telegram_api_credentials1.py"
VERIFY = REPO / "scripts" / "verify_jerkgram_build124_telegram_api_credentials1.py"
EXPECTED_API_ID = "22732185"
TEST_API_HASH = "0123456789abcdef0123456789abcdef"


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
        result = module.patch_variables(self.official_variables(), EXPECTED_API_ID, TEST_API_HASH)
        self.assertIn(f'telegram_api_id = "{EXPECTED_API_ID}"', result)
        self.assertIn(f'telegram_api_hash = "{TEST_API_HASH}"', result)
        self.assertIn('telegram_bundle_id = "ph.telegra.Telegraph"', result)
        self.assertIn('telegram_team_id = "C67CF9S4VU"', result)
        self.assertNotIn('telegram_api_id = "8"', result)
        self.assertNotIn('telegram_api_hash = "7245de8e747a0d6fbe11f7cc14fcc0bb"', result)

    def test_rejects_missing_credentials(self):
        module = self.load_module()
        for api_id, api_hash in (("", TEST_API_HASH), (EXPECTED_API_ID, "")):
            with self.assertRaises(ValueError):
                module.validate_credentials(api_id, api_hash)

    def test_rejects_malformed_credentials(self):
        module = self.load_module()
        bad = (("abc", TEST_API_HASH), (EXPECTED_API_ID, "not-a-telegram-api-hash"))
        for api_id, api_hash in bad:
            with self.assertRaises(ValueError):
                module.validate_credentials(api_id, api_hash)

    def test_rejects_any_api_id_other_than_build124_canary_identity(self):
        module = self.load_module()
        for api_id in ("8", "12345678", "22732184", "22732186"):
            with self.assertRaises(ValueError):
                module.validate_credentials(api_id, TEST_API_HASH)

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

    def test_verifier_rejects_wrong_configured_canary_id_without_echoing_hash(self):
        wrong_api_id = "12345678"
        with tempfile.TemporaryDirectory() as directory:
            variables = Path(directory) / "variables.bzl"
            variables.write_text(
                f'telegram_api_id = "{wrong_api_id}"\ntelegram_api_hash = "{TEST_API_HASH}"\n',
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["JERKGRAM_TELEGRAM_API_ID"] = wrong_api_id
            env["JERKGRAM_TELEGRAM_API_HASH"] = TEST_API_HASH
            result = subprocess.run(
                [sys.executable, str(VERIFY), "--variables", str(variables)],
                cwd=REPO,
                env=env,
                capture_output=True,
                text=True,
            )
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(TEST_API_HASH, output)

    def test_patch_is_idempotent(self):
        module = self.load_module()
        api_id = EXPECTED_API_ID
        api_hash = TEST_API_HASH
        once = module.patch_variables(self.official_variables(), api_id, api_hash)
        twice = module.patch_variables(once, api_id, api_hash)
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()
