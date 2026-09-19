import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCHER = REPO / "scripts/apply_jerkgram_v13a_build139_notifications_foundation1.py"


def load_patcher():
    if not PATCHER.is_file():
        raise AssertionError(f"missing Build139 notification foundation patcher: {PATCHER}")
    spec = importlib.util.spec_from_file_location("build139_notifications_foundation", PATCHER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


APP_FIXTURE = '''import Foundation\nimport UIKit\n\nfinal class AppDelegate {\n    func application(_ application: UIApplication, open url: URL, sourceApplication: String?) -> Bool {\n        self.openUrl(url: url)\n        return true\n    }\n\n    func application(_ application: UIApplication, open url: URL, sourceApplication: String?, annotation: Any) -> Bool {\n        self.openUrl(url: url)\n        return true\n    }\n\n    func application(_ app: UIApplication, open url: URL, options: [UIApplication.OpenURLOptionsKey : Any] = [:]) -> Bool {\n        self.openUrl(url: url)\n        return true\n    }\n\n    func application(_ application: UIApplication, handleOpen url: URL) -> Bool {\n        self.openUrl(url: url)\n        return true\n    }\n\n    private func openUrl(url: URL) {\n    }\n}\n'''


class Build139NotificationsFoundationContract(unittest.TestCase):
    def test_account_state_is_versioned_account_scoped_and_revocation_ready(self):
        module = load_patcher()
        source = module.NOTIFICATIONS_SOURCE

        for token in (
            "public enum JerkgramNotificationLifecycleState",
            "case disconnected",
            "case connecting",
            "case active",
            "case permissionDisabled",
            "case repairRequired",
            "case disconnecting",
            "case pendingRevoke",
            "case error",
            "public let nativeAccountId: Int64",
            "public let telegramUserId: Int64",
            "public var telegramAuthorizationHash: Int64?",
            "public var installationId: String?",
            "public var pendingPairing: JerkgramNotificationPendingPairing?",
            "public var bridgeProtocolVersion: Int",
            "public static let bridgeProtocolVersion = 1",
        ):
            self.assertIn(token, source)

    def test_pairing_is_short_lived_single_use_and_not_active_until_pwa_user_reconciles(self):
        module = load_patcher()
        source = module.NOTIFICATIONS_SOURCE

        for token in (
            "public func beginPairing(",
            "nativeAccountId: Int64",
            "telegramUserId: Int64",
            "pairingLifetime: TimeInterval = 120.0",
            "public func claimPendingPairing(nonce: String",
            "public func claimDirectPairing(",
            "A direct PWA retry for the same native account supersedes",
            "unexpiredPending.count == 1",
            "usedPairingNonces.contains(nonce)",
            "usedPairingNonces.append(nonce)",
            "public func acceptPairingAuthorization(",
            "record.telegramAuthorizationHash = authorizationHash",
            "record.lifecycleState = .connecting",
            "public func completePairing(",
            "record.telegramUserId == telegramUserId",
            "record.pendingPairing?.nonce == nonce",
            "record.telegramAuthorizationHash != nil",
            "record.installationId = installationId",
            "record.lifecycleState = .active",
        ):
            self.assertIn(token, source)

        self.assertNotIn("primaryAccount", source)
        self.assertNotIn("activeAccounts.primary", source)

        direct_start = source.index("public func claimDirectPairing(")
        direct_end = source.index("@discardableResult", direct_start)
        direct_block = source[direct_start:direct_end]
        self.assertNotIn("record.pendingPairing == nil", direct_block)
        self.assertIn("record.telegramAuthorizationHash == nil", direct_block)

    def test_authorize_bridge_requires_v1_nonce_token_and_exact_pending_account(self):
        module = load_patcher()
        patched = module.patch_app_delegate_text(APP_FIXTURE)

        for token in (
            "import JerkgramCore",
            "private func handleJerkgramNotificationsAuthorizeUrl(_ url: URL) -> Bool",
            'url.scheme?.lowercased() == "jerkgram"',
            'url.host?.lowercased() == "push"',
            'url.path == "/authorize"',
            'values["v"] == "1"',
            'values["nonce"]',
            'values["token"]',
            "JerkgramNotificationsStore.shared.claimPendingPairing(nonce: nonce)",
            "JerkgramNotificationsStore.shared.claimDirectPairing(",
            "candidates.count == 1",
            "Choose the account in Jerkgram Notifications settings",
            "recordId.int64 == pending.nativeAccountId",
            "context.account.peerId.id._internalGetInt64Value() == pending.telegramUserId",
            "approveAuthTransferToken(",
            "authorizationHash: session.hash",
            "acceptPairingAuthorization(",
            "if self.handleJerkgramNotificationsAuthorizeUrl(url)",
        ):
            self.assertIn(token, patched)

        self.assertNotIn("activeAccounts.primary", patched)
        self.assertIn("candidates.count == 1", patched)

    def test_modern_ios_url_callback_reaches_central_notification_dispatch(self):
        module = load_patcher()
        patched = module.patch_app_delegate_text(APP_FIXTURE)

        self.assertIn(
            "func application(_ app: UIApplication, open url: URL, options: [UIApplication.OpenURLOptionsKey : Any] = [:]) -> Bool",
            patched,
        )
        central_start = patched.index("private func openUrl(url: URL) {")
        central_end = patched.index("}\n", central_start)
        central_block = patched[central_start:central_end]
        self.assertIn("handleJerkgramNotificationsAuthorizeUrl(url)", central_block)
        self.assertIn("handleJerkgramNotificationsReconcileUrl(url)", central_block)

    def test_reconcile_bridge_requires_same_nonce_expected_user_and_valid_installation_id(self):
        module = load_patcher()
        patched = module.patch_app_delegate_text(APP_FIXTURE)

        for token in (
            "private func handleJerkgramNotificationsReconcileUrl(_ url: URL) -> Bool",
            'url.path == "/reconcile"',
            'Set(values.keys) == Set(["v", "nonce", "user", "installation"])',
            'values["v"] == "1"',
            'values["nonce"]',
            'values["user"]',
            'values["installation"]',
            "UUID(uuidString: installationId) != nil",
            "JerkgramNotificationsStore.shared.completePairing(",
            "telegramUserId: telegramUserId",
            "installationId: installationId",
            "nonce: nonce",
            "if self.handleJerkgramNotificationsReconcileUrl(url)",
        ):
            self.assertIn(token, patched)

    def test_authorize_and_reconcile_bridges_consume_malformed_routes_locally(self):
        module = load_patcher()
        patched = module.patch_app_delegate_text(APP_FIXTURE)
        self.assertIn("return true", patched)
        self.assertIn("url.absoluteString.utf8.count <= 3072", patched)
        self.assertIn("queryItems.count == values.count", patched)
        self.assertIn("nonce.count >= 32", patched)
        self.assertIn("tokenData.count <= 1024", patched)
        self.assertIn("telegramUserId > 0", patched)


if __name__ == "__main__":
    unittest.main()
