from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
INSTALLER = REPO / "scripts/install_jerkgram_v12m_build124_probe_hook.py"


class Build124WiringTests(unittest.TestCase):
    def load_installer(self):
        spec = importlib.util.spec_from_file_location("build124_wiring", INSTALLER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self) -> str:
        return '''#!/bin/bash
python3 ../../scripts/verify_jerkgram_v12k_build122_settings_release1.py

echo
echo "== Jerkgram v1.2L Build123 release recovery =="
python3 ../../scripts/apply_jerkgram_v12l_build123_state_runtime1.py
python3 ../../scripts/apply_jerkgram_v12l_build123_message_fidelity1.py
python3 ../../scripts/apply_jerkgram_v12l_build123_profile_ui1.py
python3 ../../scripts/apply_jerkgram_v12l_build123_settings_ui1.py
python3 ../../scripts/verify_jerkgram_v12l_build123_release_recovery1.py

# Swiftgram config placeholder for BuildConfig
sg_config = "{}"
EOF

echo
echo "== Jerkgram private Telegram API credentials =="
python3 ../../scripts/apply_jerkgram_build124_telegram_api_credentials1.py --variables build-input/configuration-repository/variables.bzl
python3 ../../scripts/verify_jerkgram_build124_telegram_api_credentials1.py --variables build-input/configuration-repository/variables.bzl

"$BAZEL_BIN" build //Telegram:Telegram
python3 ../../scripts/verify_jerkgram_v12k_build122_final_ipa.py ghostbase-final/GhostBase.ipa

echo
echo "== Jerkgram v1.2L Build123 final identity =="
python3 ../../scripts/jerkgram_finalize_build123_identity.py ghostbase-final/GhostBase.ipa
python3 ../../scripts/verify_jerkgram_v12l_build123_final_ipa.py ghostbase-final/GhostBase.ipa
'''

    def test_all_build124_source_overlays_are_wired_once_after_build123(self):
        module = self.load_installer()
        updated = module.patch_probe(self.fixture())

        self.assertEqual(updated.count(module.SOURCE_MARKER), 1)
        build123 = updated.index("verify_jerkgram_v12l_build123_release_recovery1.py")
        bazel = updated.index('"$BAZEL_BIN" build')
        positions = []
        for name in module.APPLY_ORDERED:
            self.assertEqual(updated.count(name), 1, name)
            positions.append(updated.index(name))
        self.assertEqual(positions, sorted(positions))
        self.assertGreater(positions[0], build123)
        self.assertLess(positions[-1], bazel)

    def test_persistent_one_time_identity_precedes_viewed_overlay(self):
        module = self.load_installer()
        updated = module.patch_probe(self.fixture())
        self.assertLess(
            updated.index("apply_jerkgram_v12m_build124_onetime_persistence1.py"),
            updated.index("apply_jerkgram_v12m_build124_onetime_viewed1.py"),
        )

    def test_all_source_verifiers_run_after_all_applies_and_before_bazel(self):
        module = self.load_installer()
        updated = module.patch_probe(self.fixture())
        last_apply = max(updated.index(name) for name in module.APPLY_ORDERED)
        verifier_positions = []
        for name in module.VERIFY_ORDERED:
            self.assertEqual(updated.count(name), 1, name)
            verifier_positions.append(updated.index(name))
        self.assertEqual(verifier_positions, sorted(verifier_positions))
        self.assertGreater(verifier_positions[0], last_apply)
        self.assertLess(verifier_positions[-1], updated.index('"$BAZEL_BIN" build'))

    def test_private_api_hook_stays_at_configuration_owner_before_bazel(self):
        module = self.load_installer()
        updated = module.patch_probe(self.fixture())
        api_apply = updated.index("apply_jerkgram_build124_telegram_api_credentials1.py")
        api_verify = updated.index("verify_jerkgram_build124_telegram_api_credentials1.py")
        self.assertLess(api_apply, api_verify)
        self.assertLess(api_verify, updated.index('"$BAZEL_BIN" build'))
        self.assertNotIn("apply_jerkgram_build124_telegram_api_credentials1.py", module.APPLY_ORDERED)

    def test_build124_final_identity_runs_after_build123_final_verifier(self):
        module = self.load_installer()
        updated = module.patch_probe(self.fixture())
        self.assertEqual(updated.count(module.FINAL_MARKER), 1)
        previous = updated.index("verify_jerkgram_v12l_build123_final_ipa.py")
        finalizer = updated.index("jerkgram_finalize_build124_identity.py")
        verifier = updated.index("verify_jerkgram_v12m_build124_final_ipa.py")
        self.assertLess(previous, finalizer)
        self.assertLess(finalizer, verifier)

    def test_patch_is_idempotent(self):
        module = self.load_installer()
        once = module.patch_probe(self.fixture())
        self.assertEqual(once, module.patch_probe(once))


if __name__ == "__main__":
    unittest.main()
