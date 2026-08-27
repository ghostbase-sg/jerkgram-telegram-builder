from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
import zipfile


REPO = Path(__file__).resolve().parents[1]
STATE = REPO / "scripts/apply_jerkgram_v12l_build123_state_runtime1.py"
MESSAGE = REPO / "scripts/apply_jerkgram_v12l_build123_message_fidelity1.py"
PROFILE = REPO / "scripts/apply_jerkgram_v12l_build123_profile_ui1.py"
SETTINGS = REPO / "scripts/apply_jerkgram_v12l_build123_settings_ui1.py"
VERIFY = REPO / "scripts/verify_jerkgram_v12l_build123_release_recovery1.py"
INSTALL = REPO / "scripts/install_jerkgram_v12l_build123_probe_hook.py"
WORKFLOW = REPO / ".github/workflows/build.yml"
FINALIZE = REPO / "scripts/jerkgram_finalize_build123_identity.py"
FINAL_VERIFY = REPO / "scripts/verify_jerkgram_v12l_build123_final_ipa.py"


class Build123ReleaseRecoveryTests(unittest.TestCase):
    def sources(self):
        return [path.read_text(encoding="utf-8") for path in (STATE, MESSAGE, PROFILE, SETTINGS, VERIFY, INSTALL)]

    def test_settings_has_one_account_owner_and_targeted_async_commit(self):
        source = STATE.read_text(encoding="utf-8")
        for token in (
            "BUILD123_ACCOUNT_SETTINGS_OWNER1",
            "JerkgramSettingsCommitQueue",
            "jerkgramPersistChangedSettings",
            "jerkgramProjectActiveSettings",
            "GhostBaseKey.scheduledSend",
            "GhostBaseKey.oneTimeSave",
        ):
            self.assertIn(token, source)
        self.assertIn("dictionaryRepresentation() survived the toggle path", source)

    def test_message_snapshots_preserve_entities_dates_and_portable_actions(self):
        source = MESSAGE.read_text(encoding="utf-8")
        for token in (
            "BUILD123_MESSAGE_SNAPSHOT1",
            "editHistoryEntities",
            "TextEntitiesMessageAttribute(entities:",
            "EmbeddedMediaStickersMessageAttribute",
            "GhostBaseEditEntitySnapshot",
            "inlineStickerFiles",
            "previousEntities",
            "entity-only edits",
            "BUILD123_PORTABLE_FORWARD1",
            "BUILD123_DELETED_ENTITY_SNAPSHOT1",
            "originalEntities: currentMessage.textEntitiesAttribute?.entities ?? []",
            "canUsePortableCopy",
            "TelegramMediaPaidContent",
            "Переслать без автора",
        ):
            self.assertIn(token, source)
        self.assertIn("data.messageActions.options.contains(.forward) survived portable gate", source)

    def test_profile_links_groups_description_and_login_have_explicit_owners(self):
        source = PROFILE.read_text(encoding="utf-8")
        for token in (
            "BUILD123_LINKS_INTRINSIC_GLASS1",
            "jerkgramLinksReadabilityEnabled ? .zero",
            "BUILD123_COMMON_GROUPS_SURFACE1",
            "BUILD123_DESCRIPTION_EXPAND_GLASS1",
            "BUILD123_SAFE_LOGIN_ALL_ACCOUNTS1",
            "ghostBaseSafeLoginNode.isHidden = false",
        ):
            self.assertIn(token, source)

    def test_every_internal_settings_page_and_time_machine_use_shared_visual_contract(self):
        source = SETTINGS.read_text(encoding="utf-8")
        for token in (
            "BUILD123_SETTINGS_SYSTEM1",
            "JerkgramSettingsSectionHeaderItem",
            "JerkgramSettingsStatusItem",
            "BUILD123_SETTINGS_TOGGLE_ICONS1",
            "icon: jerkgramSettingsToggleIcon(key)",
            "BUILD123_TIME_MACHINE_UI1",
            "jerkgramTimeMachineDateText",
        ):
            self.assertIn(token, source)

    def test_build123_is_wired_after_build122_and_before_bazel(self):
        install = INSTALL.read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for name in (
            "apply_jerkgram_v12l_build123_state_runtime1.py",
            "apply_jerkgram_v12l_build123_message_fidelity1.py",
            "apply_jerkgram_v12l_build123_profile_ui1.py",
            "apply_jerkgram_v12l_build123_settings_ui1.py",
            "verify_jerkgram_v12l_build123_release_recovery1.py",
        ):
            self.assertIn(name, install)
            self.assertIn(name, workflow)
        self.assertIn("name: Jerkgram 12.9.2 Build123", workflow)
        self.assertIn("Jerkgram-build123.ipa", workflow)

    def test_build123_identity_stamps_app_and_extensions(self):
        extension_names = (
            "BroadcastUploadExtension.appex", "IntentsExtension.appex",
            "NotificationContentExtension.appex", "NotificationServiceExtensionv1.appex",
            "ShareExtension.appex", "WidgetExtension.appex",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app = root / "payload/Payload/Telegram.app"
            (app / "PlugIns").mkdir(parents=True)
            (app / "Info.plist").write_bytes(plistlib.dumps({
                "CFBundleDisplayName": "Jerkgram", "CFBundleName": "Jerkgram",
                "CFBundleIdentifier": "ph.telegra.Telegraph", "CFBundleVersion": "122",
            }))
            for index, name in enumerate(extension_names):
                extension = app / "PlugIns" / name
                extension.mkdir()
                (extension / "Info.plist").write_bytes(plistlib.dumps({
                    "CFBundleIdentifier": f"ph.telegra.Telegraph.extension{index}",
                    "CFBundleVersion": "122",
                }))
            ipa = root / "Build123.ipa"
            with zipfile.ZipFile(ipa, "w") as archive:
                for path in sorted((root / "payload").rglob("*")):
                    archive.write(path, path.relative_to(root / "payload"))
            subprocess.run(["python3", str(FINALIZE), str(ipa)], cwd=REPO, check=True, capture_output=True, text=True)
            subprocess.run(["python3", str(FINAL_VERIFY), str(ipa)], cwd=REPO, check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
