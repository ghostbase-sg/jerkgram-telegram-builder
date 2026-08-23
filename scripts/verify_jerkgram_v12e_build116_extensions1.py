#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()

OWNERS = {
    "submodules/TelegramUI/Sources/AppDelegate.swift": ("app", "profile", "container", "root", "encryption", "account"),
    "Telegram/SiriIntents/IntentHandler.swift": ("siri", "profile", "container", "root", "encryption", "account"),
    "Telegram/WidgetKitWidget/TodayViewController.swift": ("widget", "profile", "container", "root", "encryption", "account"),
    "Telegram/BroadcastUpload/BroadcastUploadExtension.swift": ("broadcast", "profile", "container", "root", "broadcastCoordination"),
    "Telegram/Share/ShareRootController.swift": ("share", "profile", "container", "root", "encryption", "account"),
    "Telegram/NotificationContent/NotificationViewController.swift": ("notificationContent", "profile", "container", "root", "encryption", "account"),
    "Telegram/NotificationService/Sources/NotificationService.swift": ("notificationService", "profile", "container", "root", "encryption", "account"),
}


def require(value, message):
    if not value:
        raise RuntimeError("[verify Build116 extensions] " + message)


def verify(header, implementation, settings, settings_build, owners):
    require("jerkgramRecordExtensionDiagnostic" in header, "diagnostic API missing")
    require("jerkgramExtensionDiagnosticsReport" in header, "report API missing")
    require(implementation.count("BUILD116_EXTENSION_DIAGNOSTICS1") == 1, "implementation marker count != 1")
    for token in (
        "jerkgram-extension-diagnostics",
        "substringToIndex:240",
        "NSDataWritingAtomic",
        "NSJSONWritingSortedKeys",
        "schemaVersion",
    ):
        require(token in implementation, "bounded implementation token missing: " + token)
    require("appendData" not in implementation, "append-only diagnostics survived")

    require(settings.count("copyExtensionDiagnostics") == 3, "copy action token count != 3")
    require("BuildConfig.jerkgramExtensionDiagnosticsReport()" in settings, "report copy call missing")
    require("jerkgram.Runtime.Diagnostics.V11G" not in settings, "raw Runtime list survived")
    require('"//submodules/BuildConfig:BuildConfig"' in settings_build, "SettingsUI BuildConfig dependency missing")

    require(set(owners) == set(OWNERS), "runtime owner set mismatch")
    for relative, expected in OWNERS.items():
        text = owners[relative]
        process, *stages = expected
        require(text.count("BUILD116_EXTENSION_STAGE1") == 1, "owner marker count != 1: " + relative)
        require('process: "' + process + '"' in text, "process name missing: " + process)
        for stage in stages:
            require('stage: "' + stage + '"' in text, f"stage {stage} missing: {relative}")


def main():
    header_path = ROOT / "submodules/BuildConfig/PublicHeaders/BuildConfig/BuildConfig.h"
    implementation_path = ROOT / "submodules/BuildConfig/Sources/BuildConfig.m"
    settings_path = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
    settings_build_path = ROOT / "submodules/SettingsUI/BUILD"
    paths = (header_path, implementation_path, settings_path, settings_build_path)
    for path in paths:
        require(path.is_file(), "source owner missing: " + str(path))
    owners = {}
    for relative in OWNERS:
        path = ROOT / relative
        require(path.is_file(), "runtime owner missing: " + relative)
        owners[relative] = path.read_text(encoding="utf-8")
    verify(
        header_path.read_text(encoding="utf-8"),
        implementation_path.read_text(encoding="utf-8"),
        settings_path.read_text(encoding="utf-8"),
        settings_build_path.read_text(encoding="utf-8"),
        owners,
    )
    print("[verify Build116 extensions] GREEN: 7 owners, bounded atomic diagnostics")


if __name__ == "__main__":
    main()
