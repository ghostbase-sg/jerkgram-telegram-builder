from pathlib import Path
import re
import unittest


REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".github/workflows/build.yml"
INSTALL = REPO / "scripts/install_jerkgram_v12h_build119_probe_hook.py"
APPLY = REPO / "scripts/apply_jerkgram_v12h_build119_hybrid_ui1.py"
APPLY_CORRECTION = REPO / "scripts/apply_jerkgram_v12h_build119_hybrid_ui2.py"
VERIFY = REPO / "scripts/verify_jerkgram_v12h_build119_hybrid_ui1.py"
BUILD117_RELEASE = REPO / "scripts/verify_jerkgram_v12f_build117_release_readiness1.py"
FINALIZE = REPO / "scripts/jerkgram_finalize_build119_identity.py"
FINAL_VERIFY = REPO / "scripts/verify_jerkgram_v12h_build119_final_ipa.py"
PUBLISH = REPO / "scripts/jerkgram_publish_build119_artifact.py"


class Build119HybridUIContractTests(unittest.TestCase):
    def test_workflow_preserves_build119_gates_under_successor_builds(self) -> None:
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertRegex(source, r"name: Jerkgram 12\.9\.2 Build\d+")
        self.assertNotIn("GhostBase Swiftgram Builder", source)
        self.assertIn("scripts/install_jerkgram_v12h_build119_probe_hook.py", source)
        self.assertIn("python3 -m unittest tests.test_jerkgram_v12h_build119_hybrid_ui1", source)

        installer = INSTALL.read_text(encoding="utf-8")
        for token in (
            "apply_jerkgram_v12h_build119_hybrid_ui2.py",
            "verify_jerkgram_v12h_build119_hybrid_ui1.py",
            "jerkgram_finalize_build119_identity.py",
            "verify_jerkgram_v12h_build119_final_ipa.py",
        ):
            self.assertIn(token, installer)

        current_builds = [int(value) for value in re.findall(r"name: Jerkgram 12\.9\.2 Build(\d+)", source)]
        self.assertTrue(current_builds, "current Jerkgram workflow build missing")
        current_build = max(current_builds)
        self.assertGreaterEqual(current_build, 119)
        artifact_paths = (
            f"artifacts/Jerkgram-build{current_build}.ipa",
            f"artifacts/Jerkgram-Build{current_build}-canary.ipa",
        )
        self.assertTrue(
            any(path in source for path in artifact_paths),
            f"current Jerkgram artifact path missing for build {current_build}",
        )
        self.assertNotIn("name: Jerkgram 12.9.2 Build118", source)
        self.assertNotIn("name: Jerkgram-build118", source)

    def test_installer_materializes_corrected_source_overlay_after_build118_before_bazel(self) -> None:
        source = INSTALL.read_text(encoding="utf-8")
        for token in (
            "verify_jerkgram_v12g_build118_release_readiness1.py",
            "apply_jerkgram_v12h_build119_hybrid_ui2.py",
            "verify_jerkgram_v12h_build119_hybrid_ui1.py",
            '\"$BAZEL_BIN\" build',
        ):
            self.assertIn(token, source)
        self.assertNotIn('"apply_jerkgram_v12h_build119_hybrid_ui1.py",\n    "verify_jerkgram', source)
        self.assertIn("source_positions == sorted(source_positions)", source)
        self.assertIn("source_positions[-1] < text.index(BAZEL_ANCHOR)", source)

    def test_installer_materializes_final_identity_after_build114(self) -> None:
        source = INSTALL.read_text(encoding="utf-8")
        for token in (
            "verify_jerkgram_v12c_build114_final_ipa.py",
            "jerkgram_finalize_build119_identity.py",
            "verify_jerkgram_v12h_build119_final_ipa.py",
        ):
            self.assertIn(token, source)
        self.assertIn("final_positions == sorted(final_positions)", source)
        self.assertIn("final_positions[0] > text.index(FINAL_ANCHOR)", source)

    def test_about_correction_uses_exact_materialized_build118_owner(self) -> None:
        source = APPLY_CORRECTION.read_text(encoding="utf-8")
        self.assertIn("apply_jerkgram_v12h_build119_hybrid_ui1.py", source)
        self.assertIn('"BUILD118_ABOUT_CHANNEL_CARDS1" in text', source)
        self.assertNotIn('"BUILD118_ABOUT_CHANNEL_CARDS1" in block', source)
        self.assertIn("old_footer =", source)
        self.assertIn("Jerkgram\\\\nBase: Official Telegram 12.9.2\\\\nBuild: 118", source)
        self.assertIn("block.count(old_footer) == 1", source)
        self.assertIn("strings.aboutBuild119Summary", source)
        self.assertIn("module.patch_about = patch_about", source)
        self.assertIn("module.main()", source)

    def test_correction_targets_materialized_time_machine_owner(self) -> None:
        source = APPLY_CORRECTION.read_text(encoding="utf-8")
        self.assertIn("module.TIME_MACHINE =", source)
        self.assertIn(
            "submodules/TelegramUI/Components/Chat/ChatSearchNavigationContentNode/Sources/JerkgramTimeMachineController.swift",
            source,
        )
        self.assertNotIn(
            'module.ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramTimeMachineController.swift"',
            source,
        )

    def test_build117_release_gate_accepts_truthful_successor_artifact(self) -> None:
        source = BUILD117_RELEASE.read_text(encoding="utf-8")
        self.assertIn('re.findall(r"Jerkgram-build(\\d+)"', source)
        self.assertIn("max(artifact_builds) >= 118", source)
        self.assertIn("Build118-or-newer Jerkgram artifact missing", source)
        self.assertNotIn('require("Jerkgram-build118" in workflow', source)
        self.assertIn('workflow.count("uses: actions/upload-artifact@v4") == 1', source)
        self.assertIn('"Whitegram" not in workflow', source)

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

    def test_verifier_checks_materialized_owners_and_invariants(self) -> None:
        source = VERIFY.read_text(encoding="utf-8")
        self.assertIn(
            "submodules/TelegramUI/Components/Chat/ChatSearchNavigationContentNode/Sources/JerkgramTimeMachineController.swift",
            source,
        )
        self.assertNotIn(
            'ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramTimeMachineController.swift"',
            source,
        )
        self.assertIn('"BUILD118_ABOUT_CHANNEL_CARDS1" in settings', source)
        self.assertNotIn('"BUILD118_ABOUT_CHANNEL_CARDS1" in about', source)
        self.assertIn("def region(text, start_signature, end_signature):", source)
        self.assertIn('"private enum GhostBaseSettingsPage"', source)
        self.assertIn('"private final class GhostBaseSettingsArguments"', source)
        self.assertIn('page_enum.count("    case stars\\n") == 1', source)
        self.assertIn('page_enum.count("        case .stars:\\n") == 2', source)
        self.assertNotIn('settings.count("case stars")', source)
        self.assertIn('"private enum GhostBaseSettingsEntry"', source)
        self.assertIn('"private func ghostBaseSettingsEntries("', source)
        self.assertIn("entry_enum.count(", source)
        self.assertNotIn('settings.count("case valueDisclosure")', source)
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
