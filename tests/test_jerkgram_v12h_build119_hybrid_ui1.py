from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".github/workflows/build.yml"
BAZEL = REPO / "scripts/bazel_build_probe_official.sh"
APPLY = REPO / "scripts/apply_jerkgram_v12h_build119_hybrid_ui1.py"
VERIFY = REPO / "scripts/verify_jerkgram_v12h_build119_hybrid_ui1.py"
FINALIZE = REPO / "scripts/jerkgram_finalize_build119_identity.py"
FINAL_VERIFY = REPO / "scripts/verify_jerkgram_v12h_build119_final_ipa.py"
PUBLISH = REPO / "scripts/jerkgram_publish_build119_artifact.py"


class Build119HybridUIContractTests(unittest.TestCase):
    def test_workflow_is_real_build119_and_wires_all_gates(self) -> None:
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("name: Jerkgram 12.9.2 Build119", source)
        self.assertIn("scripts/apply_jerkgram_v12h_build119_hybrid_ui1.py", source)
        self.assertIn("scripts/verify_jerkgram_v12h_build119_hybrid_ui1.py", source)
        self.assertIn("scripts/jerkgram_finalize_build119_identity.py", source)
        self.assertIn("scripts/verify_jerkgram_v12h_build119_final_ipa.py", source)
        self.assertIn("scripts/jerkgram_publish_build119_artifact.py", source)
        self.assertIn("name: Jerkgram-build119", source)
        self.assertIn("artifacts/Jerkgram-build119.ipa", source)
        self.assertNotIn("name: Jerkgram 12.9.2 Build118", source)
        self.assertNotIn("name: Jerkgram-build118", source)

    def test_build119_source_overlay_is_after_build118_and_before_bazel(self) -> None:
        source = BAZEL.read_text(encoding="utf-8")
        build118 = source.index("verify_jerkgram_v12g_build118_release_readiness1.py")
        apply119 = source.index("apply_jerkgram_v12h_build119_hybrid_ui1.py")
        verify119 = source.index("verify_jerkgram_v12h_build119_hybrid_ui1.py")
        bazel = source.index('"$BAZEL_BIN" build')
        self.assertLess(build118, apply119)
        self.assertLess(apply119, verify119)
        self.assertLess(verify119, bazel)

    def test_build119_final_identity_is_after_build114_finalizer(self) -> None:
        source = BAZEL.read_text(encoding="utf-8")
        build114 = source.index("jerkgram_finalize_build114_resign_ready.py")
        build119 = source.index("jerkgram_finalize_build119_identity.py")
        verify119 = source.index("verify_jerkgram_v12h_build119_final_ipa.py")
        self.assertLess(build114, build119)
        self.assertLess(build119, verify119)

    def test_settings_overlay_replaces_permanent_stars_input_with_route(self) -> None:
        source = APPLY.read_text(encoding="utf-8")
        self.assertIn("BUILD119_HYBRID_UI1", source)
        self.assertIn("case stars", source)
        self.assertIn(".valueDisclosure", source)
        self.assertIn("strings.starsBalance", source)
        self.assertIn("strings.change", source)
        self.assertIn("page == .stars", source)
        self.assertIn("GhostBaseKey.localStarsAmount", source)
        self.assertIn("expected exactly one legacy Stars input", source)
        self.assertIn("permanent Stars input survived Basic Functions", source)

    def test_build119_visual_layer_is_bounded_away_from_profile_geometry(self) -> None:
        source = APPLY.read_text(encoding="utf-8")
        forbidden = (
            "PeerInfoScreen.swift",
            "PeerInfoHeaderNode.swift",
            "PeerInfoPaneContainerNode.swift",
            "PeerInfoScreenItemSectionContainerNode.swift",
        )
        for token in forbidden:
            self.assertNotIn(token, source)
        self.assertIn("GhostBaseSettingsController.swift", source)
        self.assertIn("JerkgramDataAndBackupController.swift", source)
        self.assertIn("JerkgramTimeMachineController.swift", source)

    def test_verifier_checks_invariants_not_only_marker(self) -> None:
        source = VERIFY.read_text(encoding="utf-8")
        for token in (
            "BUILD119_HYBRID_UI1",
            "localStarsAmount",
            "page == .stars",
            "Jerkgram-build119",
            "BUILD118_TIME_MACHINE_UI1",
            "eventPage(",
            "limit: 250",
            "Queue.concurrentDefaultQueue().async",
        ):
            self.assertIn(token, source)
        self.assertIn("legacy permanent Stars input", source)
        self.assertIn("Build118 paging contract", source)

    def test_identity_finalizer_stamps_main_and_extensions(self) -> None:
        source = FINALIZE.read_text(encoding="utf-8")
        self.assertIn('BUILD = "119"', source)
        self.assertIn('info["CFBundleVersion"] = BUILD', source)
        self.assertIn('rglob("Info.plist")', source)
        self.assertNotIn("jerkgram_finalize_build114_resign_ready", source)

    def test_final_ipa_verifier_requires_embedded_119(self) -> None:
        source = FINAL_VERIFY.read_text(encoding="utf-8")
        self.assertIn('EXPECTED_BUILD = "119"', source)
        self.assertIn("CFBundleVersion", source)
        self.assertIn("CFBundleDisplayName", source)
        self.assertIn("Jerkgram", source)
        self.assertIn("*.appex", source)

    def test_publisher_reopens_ipa_and_never_trusts_filename_only(self) -> None:
        source = PUBLISH.read_text(encoding="utf-8")
        self.assertIn("Jerkgram-build119.ipa", source)
        self.assertIn("Jerkgram-build119-info.txt", source)
        self.assertIn('EXPECTED_BUILD = "119"', source)
        self.assertIn("plistlib.load", source)
        self.assertIn("CFBundleVersion", source)
        self.assertIn("CFBundleDisplayName", source)
        self.assertIn("byte-identical", source)


if __name__ == "__main__":
    unittest.main()
