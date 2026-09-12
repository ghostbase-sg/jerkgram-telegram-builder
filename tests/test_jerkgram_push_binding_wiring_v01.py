from pathlib import Path
import importlib.util
import unittest


ROOT = Path(__file__).parents[1]
INSTALLER = ROOT / "scripts/install_jerkgram_v12w_build133_probe_hook.py"
BUILD_WORKFLOW = ROOT / ".github/workflows/build.yml"

NATIVE_CLICK_ORDER = (
    "apply_jerkgram_push_click_bridge_v01.py",
    "verify_jerkgram_push_click_bridge_v01.py",
)

ISOLATED_TYPE10_BINDING = (
    "apply_jerkgram_webpush_registration_v01.py",
    "verify_jerkgram_webpush_registration_v01.py",
    "apply_jerkgram_push_binding_bridge_v01.py",
    "verify_jerkgram_push_binding_bridge_v01.py",
)

OLD_PAIRING = (
    "apply_jerkgram_push_pairing_bridge_v01.py",
    "verify_jerkgram_push_pairing_bridge_v01.py",
)


def load_installer_module():
    spec = importlib.util.spec_from_file_location("build133_native_type1_diag", INSTALLER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NativeType1PushWiringTests(unittest.TestCase):
    def test_native_type1_diagnostic_is_isolated_from_webpush_before_bazel(self):
        installer = INSTALLER.read_text()
        for name in NATIVE_CLICK_ORDER:
            self.assertEqual(installer.count(name), 1, f"{name} must be wired exactly once")
        for name in ISOLATED_TYPE10_BINDING + OLD_PAIRING:
            self.assertNotIn(name, installer, f"non-Type1 push bridge still active: {name}")

        positions = [installer.index(name) for name in NATIVE_CLICK_ORDER]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("native Type1 push diagnostic", installer)

        module = load_installer_module()
        probe = (
            "header\n"
            + module.BUILD130_SOURCE_ANCHOR
            + "\n"
            + module.BAZEL_ANCHOR
            + " //Telegram:Telegram\n"
            + module.BUILD130_FINAL_ANCHOR
            + "\n"
        )
        generated = module.patch_probe(probe)
        generated_positions = [generated.index(name) for name in NATIVE_CLICK_ORDER]
        self.assertEqual(generated_positions, sorted(generated_positions))
        bazel_position = generated.index(module.BAZEL_ANCHOR)
        self.assertTrue(all(position < bazel_position for position in generated_positions))
        for name in ISOLATED_TYPE10_BINDING + OLD_PAIRING:
            self.assertNotIn(name, generated)

    def test_release_workflow_preflights_native_type1_isolation_contract(self):
        workflow = BUILD_WORKFLOW.read_text()
        for name in NATIVE_CLICK_ORDER + ISOLATED_TYPE10_BINDING:
            self.assertIn(f"scripts/{name}", workflow)
        for name in OLD_PAIRING:
            self.assertNotIn(f"scripts/{name}", workflow)

        test_command = "python3 -m unittest tests.test_jerkgram_push_binding_wiring_v01"
        self.assertIn(test_command, workflow)
        self.assertNotIn("python3 -m unittest tests.test_jerkgram_push_pairing_wiring_v01", workflow)
        self.assertLess(
            workflow.index(test_command),
            workflow.index("python3 scripts/install_jerkgram_v12d_build115_probe_hook.py"),
        )


if __name__ == "__main__":
    unittest.main()
