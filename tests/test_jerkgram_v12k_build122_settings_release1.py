from pathlib import Path
import plistlib
import re
import subprocess
import tempfile
import unittest
import zipfile


REPO = Path(__file__).resolve().parents[1]
APPLY = REPO / "scripts/apply_jerkgram_v12k_build122_settings_release1.py"
VERIFY = REPO / "scripts/verify_jerkgram_v12k_build122_settings_release1.py"
INSTALL = REPO / "scripts/install_jerkgram_v12k_build122_probe_hook.py"
WORKFLOW = REPO / ".github/workflows/build.yml"
FINALIZE = REPO / "scripts/jerkgram_finalize_build122_identity.py"
FINAL_VERIFY = REPO / "scripts/verify_jerkgram_v12k_build122_final_ipa.py"
PUBLISH = REPO / "scripts/jerkgram_publish_build122_artifact.py"


class Build122SettingsReleaseContractTests(unittest.TestCase):
    def test_root_menu_is_restored_without_build119_hero(self) -> None:
        source = APPLY.read_text(encoding="utf-8")
        self.assertIn("BUILD122_SETTINGS_RELEASE1", source)
        self.assertIn("restore_root_menu", source)
        self.assertIn("strings.debugResearch", source)
        self.assertIn("root Jerkgram hero survived", source)
        self.assertIn("root menu must keep nine destinations", source)

    def test_stars_is_a_draft_editor_and_only_save_commits(self) -> None:
        source = APPLY.read_text(encoding="utf-8")
        for token in (
            "JerkgramStarsEditorController.swift",
            "JerkgramStarsDraftState",
            "Common_Cancel",
            "Common_Save",
            "rightNavigationButton",
            "jerkgramCommitStarsDraft",
            "jerkgramStarsPreset",
        ):
            self.assertIn(token, source)
        self.assertIn("Stars input must not write UserDefaults", source)
        self.assertNotIn("UserDefaults.standard.set(ghostBaseSanitizeStarsAmount(updatedText), forKey: key)", source)
        self.assertIn("case let .input(_, _, _, title, text):", source)

    def test_action_rows_do_not_fake_navigation(self) -> None:
        source = APPLY.read_text(encoding="utf-8")
        self.assertIn("ItemListActionItem", source)
        self.assertIn('action == "perChat" ? .arrow : .none', source)
        self.assertIn("BUILD122_TIME_MACHINE_POLISH1", source)
        self.assertIn("disclosureStyle: .none", source)

    def test_archive_import_is_exact_multi_account_and_transactional(self) -> None:
        source = APPLY.read_text(encoding="utf-8")
        for token in (
            "activeAccountContexts",
            "availableAccountPeerIds",
            "matchingAccounts",
            "disconnected",
            "JerkgramRetentionConfigurationStore",
            "incomingRetention",
            "retentionRollback",
            "removeObject(forKey: scoped)",
            "selectedAccountPeerIds.isSubset(of: availableAccountPeerIds)",
        ):
            self.assertIn(token, source)
        self.assertNotIn("availableAccountPeerIds: [context.account.peerId.toInt64()]", source)
        self.assertIn("BUILD122_ARCHIVE_RESULT_FEEDBACK1", source)

    def test_overlay_is_wired_after_build121_before_bazel(self) -> None:
        install = INSTALL.read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for token in (
            "apply_jerkgram_v12k_build122_settings_release1.py",
            "verify_jerkgram_v12k_build122_settings_release1.py",
        ):
            self.assertIn(token, install)
        self.assertIn("install_jerkgram_v12k_build122_probe_hook.py", workflow)
        self.assertIn("python3 -m unittest tests.test_jerkgram_v12k_build122_settings_release1", workflow)
        self.assertIn("source_positions == sorted(source_positions)", install)

    def test_verifier_checks_materialized_release_owners(self) -> None:
        source = VERIFY.read_text(encoding="utf-8")
        for token in (
            "BUILD122_SETTINGS_RELEASE1",
            "BUILD122_STARS_DRAFT_EDITOR1",
            "BUILD122_ARCHIVE_EXACT_ACCOUNTS1",
            "BUILD122_TIME_MACHINE_POLISH1",
            "retentionRollback",
            "root Jerkgram hero",
            "per-keystroke Stars persistence",
        ):
            self.assertIn(token, source)

    def test_build122_identity_and_artifact_are_wired_end_to_end(self) -> None:
        install = INSTALL.read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for path in (FINALIZE, FINAL_VERIFY, PUBLISH):
            self.assertTrue(path.is_file(), str(path))
            self.assertIn("122", path.read_text(encoding="utf-8"))
        for token in (
            "jerkgram_finalize_build122_identity.py",
            "verify_jerkgram_v12k_build122_final_ipa.py",
        ):
            self.assertIn(token, install)

        current_builds = [int(value) for value in re.findall(r"name: Jerkgram 12\.9\.2 Build(\d+)", workflow)]
        self.assertTrue(current_builds, "current Jerkgram workflow build missing")
        current_build = max(current_builds)
        self.assertGreaterEqual(current_build, 123)
        self.assertIn(f"python3 scripts/jerkgram_publish_build{current_build}_artifact.py", workflow)
        if "Canary" in workflow:
            self.assertIn(f"name: Jerkgram-Build{current_build}-canary", workflow)
            self.assertIn(f"artifacts/Jerkgram-Build{current_build}-canary.ipa", workflow)
        else:
            self.assertTrue(
                f"name: Jerkgram-build{current_build}" in workflow
                or f"name: Jerkgram-Build{current_build}" in workflow
            )
            self.assertTrue(
                f"artifacts/Jerkgram-build{current_build}.ipa" in workflow
                or f"artifacts/Jerkgram-Build{current_build}.ipa" in workflow
            )
        self.assertNotIn("python3 scripts/jerkgram_publish_build121_artifact.py", workflow)

    def test_build122_finalizer_stamps_main_and_all_extensions(self) -> None:
        extension_names = (
            "BroadcastUploadExtension.appex",
            "IntentsExtension.appex",
            "NotificationContentExtension.appex",
            "NotificationServiceExtensionv1.appex",
            "ShareExtension.appex",
            "WidgetExtension.appex",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app = root / "payload/Payload/Telegram.app"
            (app / "PlugIns").mkdir(parents=True)
            main = {
                "CFBundleDisplayName": "Jerkgram",
                "CFBundleIdentifier": "ph.telegra.Telegraph",
                "CFBundleVersion": "121",
            }
            (app / "Info.plist").write_bytes(plistlib.dumps(main))
            for index, name in enumerate(extension_names):
                extension = app / "PlugIns" / name
                extension.mkdir()
                info = {
                    "CFBundleIdentifier": f"ph.telegra.Telegraph.extension{index}",
                    "CFBundleVersion": "121",
                }
                (extension / "Info.plist").write_bytes(plistlib.dumps(info))
            ipa = root / "Build122.ipa"
            with zipfile.ZipFile(ipa, "w") as archive:
                for path in sorted((root / "payload").rglob("*")):
                    archive.write(path, path.relative_to(root / "payload"))
            subprocess.run(["python3", str(FINALIZE), str(ipa)], cwd=REPO, check=True, capture_output=True, text=True)
            subprocess.run(["python3", str(FINAL_VERIFY), str(ipa)], cwd=REPO, check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
