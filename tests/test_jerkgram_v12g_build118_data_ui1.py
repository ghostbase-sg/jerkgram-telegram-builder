import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
CORE = REPO / "scripts/apply_jerkgram_v12g_build118_core1.py"
RETENTION = REPO / "scripts/apply_jerkgram_v12g_build118_storage1.py"
ARCHIVE = REPO / "scripts/apply_jerkgram_v12g_build118_archive1.py"
OVERLAY = REPO / "scripts/apply_jerkgram_v12g_build118_data_ui1.py"


class Build118DataUITests(unittest.TestCase):
    def test_visible_route_zip_and_all_retention_modes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = root / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
            strings = root / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
            settings.parent.mkdir(parents=True)
            strings.parent.mkdir(parents=True)
            settings.write_text('''private enum GhostBaseSettingsPage: Equatable {\n    case root\n    case about\n    func localizedTitle(_ strings: JerkgramStrings) -> String {\n        switch self {\n        case .root: return strings.settingsTitle\n        case .about: return strings.about\n        }\n    }\n}\nif page == .root {\n    return [\n        .disclosure(0, 8, strings.about, "GhostBaseAbout", .about)\n    ]\n}\n''')
            strings.write_text('''public enum JerkgramStringKey: String, CaseIterable {\n    case about\n}\npublic struct JerkgramStrings {\n    public var about: String { self.text(.about) }\n    private static let english: [JerkgramStringKey: String] = [\n        .about: "About"\n    ]\n    private static let russian: [JerkgramStringKey: String] = [\n        .about: "О приложении"\n    ]\n}\n''')
            (root / "submodules/SettingsUI/BUILD").write_text('deps = [\n]')
            env = os.environ.copy()
            env["JERKGRAM_SOURCE_ROOT"] = str(root)
            for overlay in (CORE, RETENTION, ARCHIVE, OVERLAY):
                result = subprocess.run([sys.executable, str(overlay)], cwd=REPO, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                self.assertEqual(result.returncode, 0, result.stdout)
            flow = (root / "submodules/SettingsUI/Sources/Jerkgram/JerkgramArchiveFlowController.swift").read_text()
            ui = (root / "submodules/SettingsUI/Sources/Jerkgram/JerkgramDataAndBackupController.swift").read_text()
            rendered_settings = settings.read_text()
            self.assertIn(".dataAndBackup", rendered_settings)
            self.assertIn("jerkgramDataAndBackupController", rendered_settings)
            self.assertIn("SSZipArchive", flow)
            self.assertIn("legacyICloudFilePicker", flow)
            self.assertIn("confirmSettingsChanges", flow)
            for token in (".days7", ".days30", ".days90", ".forever", ".megabytes250", ".megabytes500", ".gigabytes1", ".gigabytes2", ".gigabytes5", ".unlimited"):
                self.assertIn(token, ui)
            self.assertIn("archiveSecretChats", ui)
            self.assertIn("Forever + Unlimited", ui)


if __name__ == "__main__":
    unittest.main()
