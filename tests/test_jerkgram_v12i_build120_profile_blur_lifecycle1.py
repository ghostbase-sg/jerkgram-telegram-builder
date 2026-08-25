from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
WORKFLOW = ROOT / ".github/workflows/build.yml"

APPLY = SCRIPTS / "apply_jerkgram_v12i_build120_profile_blur_lifecycle1.py"
VERIFY = SCRIPTS / "verify_jerkgram_v12i_build120_profile_blur_lifecycle1.py"
STICKER_APPLY = SCRIPTS / "apply_jerkgram_v12i_build120_sticker_alpha1.py"
STICKER_VERIFY = SCRIPTS / "verify_jerkgram_v12i_build120_sticker_alpha1.py"
HOOK = SCRIPTS / "install_jerkgram_v12i_build120_probe_hook.py"
FINALIZE = SCRIPTS / "jerkgram_finalize_build120_identity.py"
FINAL_VERIFY = SCRIPTS / "verify_jerkgram_v12i_build120_final_ipa.py"
PUBLISH = SCRIPTS / "jerkgram_publish_build120_artifact.py"


class Build120ProfileBlurLifecycleTests(unittest.TestCase):
    def test_build120_files_exist(self) -> None:
        for path in (
            APPLY,
            VERIFY,
            STICKER_APPLY,
            STICKER_VERIFY,
            HOOK,
            FINALIZE,
            FINAL_VERIFY,
            PUBLISH,
        ):
            self.assertTrue(path.is_file(), f"missing Build120 file: {path}")

    def test_profile_patch_targets_final_build114_chain(self) -> None:
        source = APPLY.read_text(encoding="utf-8")
        self.assertIn("BUILD120_PROFILE_COLDSTART1", source)
        self.assertIn("GhostBase v1.1T BUILD97_STATIC_AVATAR_PIPELINE1", source)
        self.assertIn("GhostBase v1.1U BUILD106_STATIC_AVATAR_BLUR1", source)
        self.assertIn("Jerkgram v1.2C BUILD114_SOURCE_LUMINANCE1", source)
        self.assertIn("REMOVED_BUILD113_MARK not in text", source)
        self.assertIn("synchronousLoad:", source)
        self.assertIn("true", source)
        self.assertIn("blurred:", source)
        self.assertIn("false", source)

    def test_profile_verifier_guards_cold_reopen_invariants(self) -> None:
        source = VERIFY.read_text(encoding="utf-8")
        for token in (
            "BUILD120_PROFILE_COLDSTART1",
            "synchronousLoad:",
            "blurred:",
            "BUILD106_STATIC_AVATAR_BLUR1",
            "BUILD114_SOURCE_LUMINANCE1",
            "self.blurView.alpha = 1.0",
            "AVATAR_REOPEN_NO_GREY1",
        ):
            self.assertIn(token, source)
        self.assertIn("REMOVED_BUILD113_MARK not in text", source)
        self.assertIn("synchronousLoad false", source)

    def test_sticker_alpha_targets_dedicated_renderer_only(self) -> None:
        apply = STICKER_APPLY.read_text(encoding="utf-8")
        verify = STICKER_VERIFY.read_text(encoding="utf-8")
        self.assertIn("ChatMessageStickerItemNode/Sources/", apply)
        self.assertIn("ChatMessageStickerItemNode.swift", apply)
        self.assertIn("override public func setupItem(_ item: ChatMessageItem", apply)
        self.assertIn("BUILD120_STICKER_DELETED_ALPHA1", apply)
        self.assertIn("GhostBaseMessageAttribute", apply)
        self.assertIn("isDeleted", apply)
        self.assertIn("? 0.55 : 1.0", apply)
        self.assertIn("contextSourceNode.contentNode.alpha", apply)
        self.assertNotIn("sticker recovery", apply.lower())
        for token in (
            "BUILD120_STICKER_DELETED_ALPHA1",
            "GhostBaseMessageAttribute",
            "? 0.55 : 1.0",
            "contextSourceNode.contentNode.alpha",
            "no media recovery/cache path added",
        ):
            self.assertIn(token, verify)

    def test_probe_hook_runs_after_build119_and_before_bazel(self) -> None:
        source = HOOK.read_text(encoding="utf-8")
        source_order_start = source.index("SOURCE_ORDERED = (")
        source_order_end = source.index(")\nSOURCE_ANCHOR", source_order_start)
        source_order = source[source_order_start:source_order_end]
        ordered = (
            "apply_jerkgram_v12i_build120_profile_blur_lifecycle1.py",
            "verify_jerkgram_v12i_build120_profile_blur_lifecycle1.py",
            "apply_jerkgram_v12i_build120_sticker_alpha1.py",
            "verify_jerkgram_v12i_build120_sticker_alpha1.py",
        )
        positions = [source_order.index(token) for token in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertIn(
            'SOURCE_ANCHOR = "python3 ../../scripts/verify_jerkgram_v12h_build119_hybrid_ui1.py\\n"',
            source,
        )
        self.assertIn(
            'require(text.index("verify_jerkgram_v12h_build119_hybrid_ui1.py") < source_positions[0]',
            source,
        )
        self.assertIn(
            'require(source_positions[-1] < text.index(BAZEL_ANCHOR)',
            source,
        )
        self.assertIn("jerkgram_finalize_build120_identity.py", source)
        self.assertIn("verify_jerkgram_v12i_build120_final_ipa.py", source)

    def test_build120_identity_is_real_not_filename_only(self) -> None:
        finalize = FINALIZE.read_text(encoding="utf-8")
        final_verify = FINAL_VERIFY.read_text(encoding="utf-8")
        publish = PUBLISH.read_text(encoding="utf-8")
        self.assertIn('BUILD = "120"', finalize)
        self.assertIn('EXPECTED_BUILD = "120"', final_verify)
        self.assertIn('EXPECTED_BUILD = "120"', publish)
        self.assertIn('Jerkgram-build120.ipa', publish)
        self.assertIn('Jerkgram-build120-info.txt', publish)

    def test_workflow_is_build120_and_runs_contract(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("name: Jerkgram 12.9.2 Build120", workflow)
        self.assertIn("tests/test_jerkgram_v12i_build120_profile_blur_lifecycle1.py", workflow)
        self.assertIn("python3 -m unittest tests.test_jerkgram_v12i_build120_profile_blur_lifecycle1", workflow)
        self.assertIn("install_jerkgram_v12i_build120_probe_hook.py", workflow)
        self.assertIn("jerkgram_publish_build120_artifact.py", workflow)
        self.assertIn("name: Jerkgram-build120", workflow)
        self.assertIn("artifacts/Jerkgram-build120.ipa", workflow)
        self.assertIn("artifacts/Jerkgram-build120-info.txt", workflow)


if __name__ == "__main__":
    unittest.main()
