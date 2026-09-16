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
            "public var pendingPairing: JerkgramNotificationPendingPairing?",
            "public var bridgeProtocolVersion: Int",
            "public static let bridgeProtocolVersion = 1",
        ):
            self.assertIn(token, source)

    def test_pending_pairing_is_short_lived_single_use_and_does_not_guess_an_account(self):
        module = load_patcher()
        source = module.NOTIFICATIONS_SOURCE

        for token in (
            "public func beginPairing(nativeAccountId: Int64, telegramUserId: Int64",
            "pairingLifetime: TimeInterval = 120.0",
            "public func claimPendingPairing(nonce: String",
            "unexpiredPending.count == 1",
            "usedPairingNonces.contains(nonce)",
            "usedPairingNonces.append(nonce)",
            "public func completePairing(",
            "record.telegramUserId == telegramUserId",
            "record.pendingPairing?.nonce == nonce",
        ):
            self.assertIn(token, source)

        self.assertNotIn("primaryAccount", source)
        self.assertNotIn("activeAccounts.primary", source)

    def test_authorize_bridge_requires_v1_nonce_token_and_exact_pending_account(self):
        module = load_patcher()
        fixture = '''import Foundation\nimport UIKit\n\nfinal class AppDelegate {\n    func application(_ application: UIApplication, open url: URL, sourceApplication: String?, annotation: Any) -> Bool {\n        self.openUrl(url: url)\n        return true\n    }\n}\n'''
        patched = module.patch_app_delegate_text(fixture)

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
            "recordId.int64 == pending.nativeAccountId",
            "context.account.peerId.id._internalGetInt64Value() == pending.telegramUserId",
            "approveAuthTransferToken(",
            "session.hash",
            "completePairing(",
            "if self.handleJerkgramNotificationsAuthorizeUrl(url)",
        ):
            self.assertIn(token, patched)

        self.assertNotIn("activeAccounts.primary", patched)

    def test_authorize_bridge_consumes_malformed_jerkgram_authorize_urls_locally(self):
        module = load_patcher()
        fixture = '''import Foundation\nimport UIKit\n\nfinal class AppDelegate {\n    func application(_ application: UIApplication, open url: URL, sourceApplication: String?, annotation: Any) -> Bool {\n        self.openUrl(url: url)\n        return true\n    }\n}\n'''
        patched = module.patch_app_delegate_text(fixture)
        self.assertIn("return true", patched)
        self.assertIn("url.absoluteString.utf8.count <= 3072", patched)
        self.assertIn("queryItems.count == values.count", patched)
        self.assertIn("nonce.count >= 32", patched)
        self.assertIn("tokenData.count <= 1024", patched)


if __name__ == "__main__":
    unittest.main()
