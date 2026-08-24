#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()

def require(value, message):
    if not value: raise RuntimeError("[verify Build118 release] " + message)

def main():
    core = ROOT / "submodules/JerkgramCore/Sources"
    settings = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
    time_ui = ROOT / "submodules/TelegramUI/Components/Chat/ChatSearchNavigationContentNode/Sources/JerkgramTimeMachineController.swift"
    require(core.is_dir() and settings.is_file() and time_ui.is_file(), "Build118 owners missing")
    combined = "\n".join(path.read_text() for path in core.glob("*.swift")) + settings.read_text() + time_ui.read_text()
    for token in ("BUILD118_ACCOUNT_SETTINGS_SCOPE1", "BUILD118_RETENTION1", "BUILD118_ARCHIVE_V2", "BUILD118_TIME_MACHINE_UI1", "JerkgramCommunity", "Build: 118", "case forever", "case unlimited"):
        require(token in combined, "release invariant missing: " + token)
    require("Build: 117" not in settings.read_text(), "stale About build label")
    require(r'Jerkgram\\nBase:' not in settings.read_text(), "literal About newline regression")
    print("[verify Build118 release] GREEN: account scope, archive, retention, Time Machine and About")

if __name__ == "__main__": main()
