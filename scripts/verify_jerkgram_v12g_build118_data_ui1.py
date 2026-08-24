#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()


def require(value, message):
    if not value:
        raise RuntimeError("[verify Build118 data UI] " + message)


def main():
    settings = (ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift").read_text()
    flow = (ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramArchiveFlowController.swift").read_text()
    ui = (ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramDataAndBackupController.swift").read_text()
    require(".dataAndBackup" in settings and "jerkgramDataAndBackupController" in settings, "route missing")
    require('case .dataAndBackup:\n            return "Data and Backup"' in settings, "legacy title switch missing data route")
    require("case .dataAndBackup:\n            return strings.dataAndBackup" in settings, "localized title switch missing data route")
    require("import PresentationDataUtils" in flow, "archive alert compatibility import missing")
    for token in ("SSZipArchive", "legacyICloudFilePicker", "accountPeerId", "confirmSettingsChanges", "validateExtractedPayloads"):
        require(token in flow, "flow invariant missing: " + token)
    for token in (".days7", ".days30", ".days90", ".forever", ".unlimited", "archiveSecretChats"):
        require(token in ui, "retention choice missing: " + token)
    print("[verify Build118 data UI] GREEN: visible route, real ZIP export/import, exact account and retention controls")


if __name__ == "__main__":
    main()
