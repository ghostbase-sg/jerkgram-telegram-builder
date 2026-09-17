#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
MAIN_ITEMS = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoSettingsItems.swift"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build139 Notifications settings verify] " + message)


def block_bounds(text: str, signature: str) -> tuple[int, int]:
    start = text.find(signature)
    require(start >= 0, "missing block: " + signature)
    brace = text.find("{", start)
    require(brace >= 0, "missing opening brace: " + signature)
    depth = 0
    in_string = False
    escaped = False
    for index in range(brace, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return start, index + 1
    raise RuntimeError("[Build139 Notifications settings verify] unbalanced block: " + signature)


def verify_settings_text(settings: str) -> None:

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
    require('case "root":\n        page = .root' in settings, "controller does not expose the Jerkgram root route")

    root_start, root_end = block_bounds(settings, "if page == .root {")
    root = settings[root_start:root_end]
    require(root.count(".notifications)") == 1, "live root must contain exactly one Notifications destination")
    require("strings.notifications" in root, "live root Notifications title missing")
    require('"Chat/Context Menu/MessageBubble"' in root, "live root Notifications icon missing")


def verify_main_items_text(main_items: str) -> None:
    marker = "// MARK: Jerkgram v1.3B BUILD139_NOTIFICATIONS_ROOT_ROUTE1"
    require(main_items.count(marker) == 1, "Jerkgram root route marker count != 1")
    start = main_items.index(marker)
    end = main_items.find("interaction.openSettings(.ghostbase)", start)
    require(end >= 0, "Jerkgram main row action missing")
    route = main_items[start:end]
    require(
        "text: presentationData.strings.jerkgram.settingsTitle" in route,
        "root route is not owned by the visible Jerkgram row",
    )
    require(
        '"root"' in route and 'forKey: "GhostBase.Settings.InitialPage"' in route,
        "visible Jerkgram row does not target root",
    )


def main() -> None:
    require(SETTINGS.is_file(), "Settings owner missing")
    require(STRINGS.is_file(), "JerkgramStrings missing")
    require(MAIN_ITEMS.is_file(), "Main settings owner missing")
    settings = SETTINGS.read_text(encoding="utf-8")
    strings = STRINGS.read_text(encoding="utf-8")
    main_items = MAIN_ITEMS.read_text(encoding="utf-8")

    verify_settings_text(settings)
    verify_main_items_text(main_items)

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
