from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
INSTALLER = REPO / "scripts/install_jerkgram_v12n_build125_probe_hook.py"


class Build125WiringTests(unittest.TestCase):
    def load_installer(self):
        spec = importlib.util.spec_from_file_location("build125_wiring", INSTALLER)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def fixture(self) -> str:
        return '''#!/bin/bash
# JERKGRAM_V12M_BUILD124_SOURCE_HOOK
python3 ../../scripts/verify_jerkgram_v12m_build124_settings_redesign1.py
"$BAZEL_BIN" build //Telegram:Telegram
python3 ../../scripts/verify_jerkgram_v12l_build123_final_ipa.py ghostbase-final/GhostBase.ipa
# JERKGRAM_V12M_BUILD124_FINAL_IDENTITY_HOOK
python3 ../../scripts/jerkgram_finalize_build124_identity.py ghostbase-final/GhostBase.ipa
python3 ../../scripts/verify_jerkgram_v12m_build124_final_ipa.py ghostbase-final/GhostBase.ipa
'''

    def test_every_build125_overlay_and_verifier_is_wired_before_bazel(self):
        module = self.load_installer()
        updated = module.patch_probe(self.fixture())

        self.assertEqual(updated.count(module.SOURCE_MARKER), 1)
        positions = [updated.index(name) for name in module.APPLY_ORDERED]
        verifier_positions = [updated.index(name) for name in module.VERIFY_ORDERED]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(verifier_positions, sorted(verifier_positions))
        self.assertLess(max(positions), min(verifier_positions))
        self.assertLess(max(verifier_positions), updated.index('"$BAZEL_BIN" build'))

    def test_final_build125_identity_follows_build124_identity(self):
        module = self.load_installer()
        updated = module.patch_probe(self.fixture())
        self.assertEqual(updated.count(module.FINAL_MARKER), 1)
        self.assertLess(
            updated.index("verify_jerkgram_v12m_build124_final_ipa.py"),
            updated.index("jerkgram_finalize_build125_identity.py"),
        )
        self.assertLess(
            updated.index("jerkgram_finalize_build125_identity.py"),
            updated.index("verify_jerkgram_v12n_build125_final_ipa.py"),
        )

    def test_patch_is_idempotent(self):
        module = self.load_installer()
        once = module.patch_probe(self.fixture())
        self.assertEqual(once, module.patch_probe(once))

    def test_adopts_the_preexisting_unmarked_build125_block_without_duplication(self):
        module = self.load_installer()
        anchor = "python3 ../../scripts/verify_jerkgram_v12m_build124_settings_redesign1.py\n"
        existing = (
            anchor
            + '\necho\necho "== Jerkgram v1.2N Build125 release owners =="\n'
            + "\n".join("python3 ../../scripts/" + name for name in module.APPLY_ORDERED)
            + "\n"
            + "\n".join("python3 ../../scripts/" + name for name in module.VERIFY_ORDERED)
            + "\n"
        )
        updated = module.patch_probe(self.fixture().replace(anchor, existing, 1))
        self.assertEqual(updated.count(module.SOURCE_MARKER), 1)
        for name in module.APPLY_ORDERED + module.VERIFY_ORDERED:
            self.assertEqual(updated.count(name), 1, name)

    def test_workflow_uses_build125_installer_and_materialized_wiring_gate(self):
        workflow = (REPO / ".github/workflows/build.yml").read_text(encoding="utf-8")
        self.assertIn("install_jerkgram_v12n_build125_probe_hook.py", workflow)
        self.assertIn("verify_jerkgram_v12n_build125_wiring1.py", workflow)
        self.assertNotIn("python3 scripts/install_jerkgram_v12m_build124_probe_hook.py\n", workflow)


if __name__ == "__main__":
    unittest.main()
