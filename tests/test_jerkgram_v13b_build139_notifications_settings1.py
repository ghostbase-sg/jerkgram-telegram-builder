import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCHER = REPO / "scripts/apply_jerkgram_v13b_build139_notifications_settings1.py"


def load_patcher():
    if not PATCHER.is_file():
        raise AssertionError(f"missing Build139 notification settings patcher: {PATCHER}")
    spec = importlib.util.spec_from_file_location("build139_notifications_settings", PATCHER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


SETTINGS_FIXTURE = r'''import Foundation
import JerkgramCore
import UIKit

private enum GhostBaseSettingsPage: Equatable {
    case root
    case dataAndBackup
    case stars
    case home
    case ghostMode
    case messages
    case protectedContent
    case mediaStories
    case appearance
    case debugResearch
    case about

    var title: String {
        switch self {
        case .root:
            return "Jerkgram"
        case .debugResearch:
            return "Debug / Research"
        case .about:
            return "About"
        default:
            return "Other"
        }
    }

    func localizedTitle(strings: JerkgramStrings) -> String {
        switch self {
        case .root:
            return "Jerkgram"
        case .debugResearch:
            return strings.debugResearch
        case .about:
            return strings.about
        default:
            return "Other"
        }
    }
}

private func ghostBaseSettingsEntries(state: GhostBaseSettingsState, context: AccountContext, page: GhostBaseSettingsPage, strings: JerkgramStrings) -> [GhostBaseSettingsEntry] {
    if page == .root {
        return [
            .header(0, strings.features),
            .disclosure(0, 1, strings.basicFunctions, "Jerkgram/Settings/Airplane", .home),
            .disclosure(0, 7, strings.debugResearch, "Chat/Context Menu/FormatCode", .debugResearch),
            .disclosure(0, 8, strings.dataAndBackup, "Item List/Icons/Stories", .dataAndBackup),
            .disclosure(0, 9, strings.about, "Chat/Context Menu/Info", .about)
        ]
    }

    if page == .about {
        return [.info(0, strings.about)]
    }

    return []
}

private func controller(context: AccountContext) {
    let statePromise = ValuePromise(initialState, ignoreRepeated: false)
    let stateValue = Atomic(value: initialState)
    let refreshResearchPage: () -> Void = {
        statePromise.set(stateValue.with { $0 })
    }

    let arguments = GhostBaseSettingsArguments(
        context: context,
        openAboutChannel: { _ in },
        runResearchAction: { action in
            switch action {
            case "copyExtensionDiagnostics":
                break
            default:
                break
            }
        },
        updateBool: { _, _ in },
        openPage: { _ in },
        openSendTextStyle: {}
    )
}
'''

STRINGS_FIXTURE = r'''import Foundation
public struct JerkgramStrings {
    public let languageCode: String
}
'''


class Build139NotificationsSettingsContract(unittest.TestCase):
    def test_notifications_is_a_native_settings_destination_with_account_scoped_status(self):
        module = load_patcher()
        patched = module.patch_settings_text(SETTINGS_FIXTURE)

        for token in (
            "case notifications",
            'return "Jerkgram Notifications"',
            "return strings.notifications",
            ".notifications)",
            "if page == .notifications {",
            "context.account.id.int64",
            "context.account.peerId.id._internalGetInt64Value()",
            "JerkgramNotificationsStore.shared.record(nativeAccountId: nativeAccountId)",
            "record.telegramUserId == telegramUserId",
            "strings.notificationsStatus",
        ):
            self.assertIn(token, patched)

    def test_enable_starts_pairing_for_the_selected_account_and_opens_only_test_companion(self):
        module = load_patcher()
        patched = module.patch_settings_text(SETTINGS_FIXTURE)

        for token in (
            'case "notificationsEnable":',
            "let nativeAccountId = context.account.id.int64",
            "let telegramUserId = context.account.peerId.id._internalGetInt64Value()",
            "JerkgramNotificationsStore.shared.beginPairing(",
            "nativeAccountId: nativeAccountId",
            "telegramUserId: telegramUserId",
            'https://pixxxionix.github.io/jerkgram-notifications/',
            "UIApplication.shared.open(url)",
            "refreshResearchPage()",
        ):
            self.assertIn(token, patched)

        self.assertNotIn("push.jerkgram.app", patched)

    def test_explicit_disable_is_not_marked_disconnected_until_targeted_revoke_completes(self):
        module = load_patcher()
        patched = module.patch_settings_text(SETTINGS_FIXTURE)

        for token in (
            'case "notificationsDisable", "notificationsRetryDisconnect":',
            "JerkgramNotificationsStore.shared.beginRevoke(nativeAccountId: nativeAccountId)",
            "context.engine.privacy.activeSessions()",
            "activeSessionsContext.remove(hash: hash)",
            "completed: {",
            "JerkgramNotificationsStore.shared.finishRevoke(nativeAccountId: nativeAccountId)",
            "error: { _ in",
            "JerkgramNotificationsStore.shared.markPendingRevoke(nativeAccountId: nativeAccountId)",
        ):
            self.assertIn(token, patched)

    def test_strings_cover_all_user_visible_lifecycle_states(self):
        module = load_patcher()
        patched = module.patch_strings_text(STRINGS_FIXTURE)

        for token in (
            "var notifications: String",
            "var notificationsStatus: String",
            "var notificationsDescription: String",
            "var enableNotifications: String",
            "var disableNotifications: String",
            "var openNotificationsSetup: String",
            "var retryDisconnectNotifications: String",
            "var notificationsNotConnected: String",
            "var notificationsConnecting: String",
            "var notificationsActive: String",
            "var notificationsPermissionDisabled: String",
            "var notificationsRepairRequired: String",
            "var notificationsDisconnecting: String",
            "var notificationsPendingRevoke: String",
            "var notificationsError: String",
        ):
            self.assertIn(token, patched)


if __name__ == "__main__":
    unittest.main()
