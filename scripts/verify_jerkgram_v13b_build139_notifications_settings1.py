#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build139 Notifications settings verify] " + message)


def main() -> None:
    require(SETTINGS.is_file(), "Settings owner missing")
    require(STRINGS.is_file(), "JerkgramStrings missing")
    settings = SETTINGS.read_text(encoding="utf-8")
    strings = STRINGS.read_text(encoding="utf-8")

    for token in (
        "case notifications",
        "if page == .notifications {",
        "JerkgramNotificationsStore.shared.record(nativeAccountId: nativeAccountId)",
        'case "notificationsEnable":',
        "JerkgramNotificationsStore.shared.beginPairing(",
        'https://pixxxionix.github.io/jerkgram-notifications/',
        'case "notificationsDisable", "notificationsRetryDisconnect":',
        "JerkgramNotificationsStore.shared.beginRevoke(nativeAccountId: nativeAccountId)",
        "activeSessionsContext.remove(hash: hash)",
        "JerkgramNotificationsStore.shared.finishRevoke(nativeAccountId: nativeAccountId)",
        "JerkgramNotificationsStore.shared.markPendingRevoke(nativeAccountId: nativeAccountId)",
    ):
        require(token in settings, "settings invariant missing: " + token)
    require("push.jerkgram.app" not in settings, "production push origin leaked into Build139 test flow")

    for token in (
        "var notifications: String",
        "var notificationsStatus: String",
        "var enableNotifications: String",
        "var disableNotifications: String",
        "var notificationsPendingRevoke: String",
    ):
        require(token in strings, "strings invariant missing: " + token)
    print("[Build139 Notifications settings verify] GREEN")


if __name__ == "__main__":
    main()
