#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"

MARKER = "// MARK: Jerkgram v1.3B BUILD139_NOTIFICATIONS_SETTINGS1"
STRINGS_MARKER = "// MARK: Jerkgram v1.3B BUILD139_NOTIFICATIONS_SETTINGS_STRINGS1"
TEST_COMPANION_URL = "https://pixxxionix.github.io/jerkgram-notifications/"


STRINGS_EXTENSION = r'''

// MARK: Jerkgram v1.3B BUILD139_NOTIFICATIONS_SETTINGS_STRINGS1
public extension JerkgramStrings {
    var notifications: String {
        self.languageCode == "ru" ? "Уведомления Jerkgram" : "Jerkgram Notifications"
    }

    var notificationsStatus: String {
        self.languageCode == "ru" ? "Статус" : "Status"
    }

    var notificationsDescription: String {
        self.languageCode == "ru"
            ? "Получайте уведомления, даже когда Jerkgram не запущен. Для этого создаётся отдельная сессия Telegram только для уведомлений."
            : "Receive notifications even when Jerkgram is not running. A separate Telegram session is created only for notifications."
    }

    var enableNotifications: String {
        self.languageCode == "ru" ? "Включить уведомления" : "Enable Notifications"
    }

    var disableNotifications: String {
        self.languageCode == "ru" ? "Отключить уведомления" : "Disable Notifications"
    }

    var openNotificationsSetup: String {
        self.languageCode == "ru" ? "Открыть Jerkgram Notifications" : "Open Jerkgram Notifications"
    }

    var retryDisconnectNotifications: String {
        self.languageCode == "ru" ? "Повторить отключение" : "Retry Disconnect"
    }

    var notificationsNotConnected: String {
        self.languageCode == "ru" ? "Не подключено" : "Not Connected"
    }

    var notificationsConnecting: String {
        self.languageCode == "ru" ? "Готово к подключению" : "Ready to connect"
    }

    var notificationsActive: String {
        self.languageCode == "ru" ? "Активно" : "Active"
    }

    var notificationsPermissionDisabled: String {
        self.languageCode == "ru" ? "Уведомления отключены в iOS" : "Notifications Disabled in iOS"
    }

    var notificationsRepairRequired: String {
        self.languageCode == "ru" ? "Требуется восстановление" : "Repair Required"
    }

    var notificationsDisconnecting: String {
        self.languageCode == "ru" ? "Отключение…" : "Disconnecting…"
    }

    var notificationsPendingRevoke: String {
        self.languageCode == "ru" ? "Сессия всё ещё активна — повторите отключение" : "Session is still active — retry disconnect"
    }

    var notificationsError: String {
        self.languageCode == "ru" ? "Ошибка подключения" : "Connection Error"
    }
}
'''


STATUS_HELPER = r'''// MARK: Jerkgram v1.3B BUILD139_NOTIFICATIONS_SETTINGS1
private func jerkgramNotificationsStatusText(
    state: JerkgramNotificationLifecycleState,
    strings: JerkgramStrings
) -> String {
    switch state {
    case .disconnected:
        return strings.notificationsNotConnected
    case .connecting:
        return strings.notificationsConnecting
    case .active:
        return strings.notificationsActive
    case .permissionDisabled:
        return strings.notificationsPermissionDisabled
    case .repairRequired:
        return strings.notificationsRepairRequired
    case .disconnecting:
        return strings.notificationsDisconnecting
    case .pendingRevoke:
        return strings.notificationsPendingRevoke
    case .error:
        return strings.notificationsError
    }
}

'''


NOTIFICATIONS_PAGE = r'''    if page == .notifications {
        let nativeAccountId = context.account.id.int64
        let telegramUserId = context.account.peerId.id._internalGetInt64Value()
        let record = JerkgramNotificationsStore.shared.record(nativeAccountId: nativeAccountId)
        let effectiveState: JerkgramNotificationLifecycleState
        if let record, record.telegramUserId == telegramUserId {
            effectiveState = record.lifecycleState
        } else if record != nil {
            effectiveState = .repairRequired
        } else {
            effectiveState = .disconnected
        }

        var entries: [GhostBaseSettingsEntry] = [
            .header(0, strings.notifications),
            .researchInfo(0, 1, "\(strings.notificationsStatus): \(jerkgramNotificationsStatusText(state: effectiveState, strings: strings))"),
            .info(0, strings.notificationsDescription)
        ]

        switch effectiveState {
        case .disconnected, .repairRequired, .error:
            entries.append(.researchAction(1, 1, strings.enableNotifications, "notificationsEnable"))
        case .connecting:
            entries.append(.researchAction(1, 1, strings.openNotificationsSetup, "notificationsOpenSetup"))
        case .active, .permissionDisabled:
            entries.append(.researchAction(1, 1, strings.disableNotifications, "notificationsDisable"))
        case .disconnecting:
            break
        case .pendingRevoke:
            entries.append(.researchAction(1, 1, strings.retryDisconnectNotifications, "notificationsRetryDisconnect"))
        }
        return entries
    }

'''


ACTION_CASES = rf'''            case "notificationsEnable":
                let nativeAccountId = context.account.id.int64
                let telegramUserId = context.account.peerId.id._internalGetInt64Value()
                let started = JerkgramNotificationsStore.shared.beginPairing(
                    nativeAccountId: nativeAccountId,
                    telegramUserId: telegramUserId
                )
                if started, let url = URL(string: "{TEST_COMPANION_URL}") {{
                    UIApplication.shared.open(url)
                }}
                refreshResearchPage()

            case "notificationsOpenSetup":
                if let url = URL(string: "{TEST_COMPANION_URL}") {{
                    UIApplication.shared.open(url)
                }}

            case "notificationsDisable", "notificationsRetryDisconnect":
                let nativeAccountId = context.account.id.int64
                guard let hash = JerkgramNotificationsStore.shared.beginRevoke(nativeAccountId: nativeAccountId) else {{
                    refreshResearchPage()
                    break
                }}
                refreshResearchPage()
                let activeSessionsContext = context.engine.privacy.activeSessions()
                jerkgramNotificationsRevokeDisposable.set(
                    (activeSessionsContext.remove(hash: hash)
                    |> deliverOnMainQueue).start(error: {{ _ in
                        JerkgramNotificationsStore.shared.markPendingRevoke(nativeAccountId: nativeAccountId)
                        refreshResearchPage()
                    }}, completed: {{
                        JerkgramNotificationsStore.shared.finishRevoke(nativeAccountId: nativeAccountId)
                        refreshResearchPage()
                    }})
                )

'''


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build139 Notifications settings] " + message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    require(count == 1, f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


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
    raise RuntimeError("[Build139 Notifications settings] unbalanced block: " + signature)


def patch_root_notifications_row(text: str) -> str:
    start, end = block_bounds(text, "if page == .root {")
    root = text[start:end]
    require(".notifications)" not in root, "live root already contains Notifications without marker")

    about_pattern = re.compile(
        r'(?m)^(?P<indent>[ \t]*)\.disclosure\(\s*(?P<section>\d+),\s*(?P<index>\d+),\s*strings\.about,\s*"[^"]+",\s*\.about\)(?P<comma>,?)\s*$'
    )
    matches = list(about_pattern.finditer(root))
    require(len(matches) == 1, f"live root About row: expected one, found {len(matches)}")
    match = matches[0]
    section = int(match.group("section"))
    disclosure_ids = [
        int(value)
        for value in re.findall(rf"\.disclosure\(\s*{section},\s*(\d+)", root)
    ]
    require(disclosure_ids, "live root disclosure ids missing")
    notifications_index = max(disclosure_ids) + 1
    about_line = match.group(0).rstrip()
    if not about_line.endswith(","):
        about_line += ","
    notifications_row = (
        f'\n{match.group("indent")}.disclosure({section}, {notifications_index}, strings.notifications, '
        '"Chat/Context Menu/MessageBubble", .notifications)'
    )
    root = root[:match.start()] + about_line + notifications_row + root[match.end():]
    require(root.count(".notifications)") == 1, "Notifications destination is not unique in live root")
    return text[:start] + root + text[end:]


def patch_strings_text(text: str) -> str:
    if STRINGS_MARKER in text:
        require(text.count(STRINGS_MARKER) == 1, "strings marker is ambiguous")
        return text
    require("JerkgramStrings" in text, "JerkgramStrings owner missing")
    require("languageCode" in text, "JerkgramStrings languageCode missing")
    return text.rstrip() + STRINGS_EXTENSION + "\n"


def patch_settings_text(text: str) -> str:
    if MARKER in text:
        require(text.count(MARKER) == 1, "settings marker is ambiguous")
        return text

    require("import JerkgramCore" in text, "JerkgramCore import missing")

    text = replace_once(
        text,
        "    case debugResearch\n    case about\n",
        "    case debugResearch\n    case notifications\n    case about\n",
        "notifications page enum",
    )

    text = replace_once(
        text,
        '        case .debugResearch:\n            return "Debug / Research"\n        case .about:\n',
        '        case .debugResearch:\n            return "Debug / Research"\n        case .notifications:\n            return "Jerkgram Notifications"\n        case .about:\n',
        "raw notifications page title",
    )

    text = replace_once(
        text,
        "        case .debugResearch:\n            return strings.debugResearch\n        case .about:\n",
        "        case .debugResearch:\n            return strings.debugResearch\n        case .notifications:\n            return strings.notifications\n        case .about:\n",
        "localized notifications page title",
    )

    text = patch_root_notifications_row(text)

    entries_anchor = "private func ghostBaseSettingsEntries("
    require(text.count(entries_anchor) == 1, "settings entries owner mismatch")
    text = text.replace(entries_anchor, STATUS_HELPER + entries_anchor, 1)

    about_anchor = "    if page == .about {\n"
    require(text.count(about_anchor) == 1, "About page anchor mismatch")
    text = text.replace(about_anchor, NOTIFICATIONS_PAGE + about_anchor, 1)

    arguments_anchor = "    let arguments = GhostBaseSettingsArguments(\n"
    require(text.count(arguments_anchor) == 1, "settings arguments anchor mismatch")
    text = text.replace(
        arguments_anchor,
        "    let jerkgramNotificationsRevokeDisposable = MetaDisposable()\n\n" + arguments_anchor,
        1,
    )

    action_anchor = '            case "copyExtensionDiagnostics":\n'
    require(text.count(action_anchor) == 1, "research action switch anchor mismatch")
    text = text.replace(action_anchor, ACTION_CASES + action_anchor, 1)

    for token in (
        "case notifications",
        "if page == .notifications {",
        "JerkgramNotificationsStore.shared.beginPairing(",
        "JerkgramNotificationsStore.shared.beginRevoke(nativeAccountId: nativeAccountId)",
        "activeSessionsContext.remove(hash: hash)",
        "JerkgramNotificationsStore.shared.finishRevoke(nativeAccountId: nativeAccountId)",
        "JerkgramNotificationsStore.shared.markPendingRevoke(nativeAccountId: nativeAccountId)",
        TEST_COMPANION_URL,
    ):
        require(token in text, "missing settings invariant: " + token)
    require("push.jerkgram.app" not in text, "Build139 test branch must not target production push origin")
    return text


def main() -> None:
    require(SETTINGS.is_file(), "Settings owner missing: " + str(SETTINGS))
    require(STRINGS.is_file(), "JerkgramStrings owner missing: " + str(STRINGS))
    SETTINGS.write_text(patch_settings_text(SETTINGS.read_text(encoding="utf-8")), encoding="utf-8")
    STRINGS.write_text(patch_strings_text(STRINGS.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build139 Notifications settings] SOURCE PATCHED")
    print("[Build139 Notifications settings] native account owns enable/disable; explicit disable waits for targeted revoke")


if __name__ == "__main__":
    main()
