from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
VERIFY = REPO / "scripts" / "verify_jerkgram_build124_telegram_api_credentials1.py"
EXPECTED_API_ID = "22732185"
TEST_API_HASH = "0123456789abcdef0123456789abcdef"


class Build124TelegramApiSourceOwnerTests(unittest.TestCase):
    def run_verify(self, owner_text: str):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            variables = root / "variables.bzl"
            owner = root / "BuildConfig.m"
            variables.write_text(
                f'telegram_api_id = "{EXPECTED_API_ID}"\ntelegram_api_hash = "{TEST_API_HASH}"\n',
                encoding="utf-8",
            )
            owner.write_text(owner_text, encoding="utf-8")
            env = os.environ.copy()
            env["JERKGRAM_TELEGRAM_API_ID"] = EXPECTED_API_ID
            env["JERKGRAM_TELEGRAM_API_HASH"] = TEST_API_HASH
            return subprocess.run(
                [
                    sys.executable,
                    str(VERIFY),
                    "--variables",
                    str(variables),
                    "--build-config-owner",
                    str(owner),
                ],
                cwd=REPO,
                env=env,
                capture_output=True,
                text=True,
            )

    def good_owner(self) -> str:
        return '''// MARK: Jerkgram Build124 API identity proof
#define JERKGRAM_BUILD124_STRINGIFY_INNER(value) #value
#define JERKGRAM_BUILD124_STRINGIFY(value) JERKGRAM_BUILD124_STRINGIFY_INNER(value)
__attribute__((used))
static const char jerkgramBuild124ApiIdOwner[] =
    "JERKGRAM_BUILD124_API_ID=" JERKGRAM_BUILD124_STRINGIFY(APP_CONFIG_API_ID);

@implementation BuildConfig
- (instancetype)init {
    _apiId = APP_CONFIG_API_ID;
    _apiHash = @(APP_CONFIG_API_HASH);
    return self;
}
@end
'''

    def test_accepts_exact_macro_derived_build_config_owner(self):
        result = self.run_verify(self.good_owner())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_variables_only_without_compiled_owner_proof(self):
        result = self.run_verify('''@implementation BuildConfig
- (instancetype)init {
    _apiId = APP_CONFIG_API_ID;
    _apiHash = @(APP_CONFIG_API_HASH);
    return self;
}
@end
''')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(TEST_API_HASH, result.stdout + result.stderr)

    def test_rejects_detached_or_fake_api_id_marker(self):
        result = self.run_verify(self.good_owner().replace(
            'JERKGRAM_BUILD124_STRINGIFY(APP_CONFIG_API_ID)',
            '"22732185"',
        ))
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(TEST_API_HASH, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
