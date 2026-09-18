#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
NOTIFICATIONS = ROOT / "submodules/JerkgramCore/Sources/JerkgramNotifications.swift"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build139 Notifications foundation verify] " + message)


def main() -> None:
    require(APP_DELEGATE.is_file(), "AppDelegate missing")
    require(NOTIFICATIONS.is_file(), "JerkgramNotifications.swift missing")
    app = APP_DELEGATE.read_text(encoding="utf-8")
    state = NOTIFICATIONS.read_text(encoding="utf-8")

    for token in (
        "public final class JerkgramNotificationsStore",
        "public static let bridgeProtocolVersion = 1",
        "public let nativeAccountId: Int64",
        "public let telegramUserId: Int64",
        "public var telegramAuthorizationHash: Int64?",
        "public var installationId: String?",
        "public func claimPendingPairing(nonce: String",
        "public func claimDirectPairing(",
        "A direct PWA retry for the same native account supersedes",
        "unexpiredPending.count == 1",
        "usedPairingNonces.append(nonce)",
        "public func acceptPairingAuthorization(",
        "record.telegramAuthorizationHash = authorizationHash",
        "record.lifecycleState = .connecting",
        "public func completePairing(",
        "record.telegramUserId == telegramUserId",
        "record.telegramAuthorizationHash != nil",
        "record.installationId = installationId",
        "record.lifecycleState = .active",
        "public func beginRevoke(nativeAccountId: Int64)",
        "public func finishRevoke(nativeAccountId: Int64)",
        "public func markPendingRevoke(nativeAccountId: Int64)",
    ):
        require(token in state, "state invariant missing: " + token)

    for token in (
        "import JerkgramCore",
        "private func handleJerkgramNotificationsAuthorizeUrl(_ url: URL) -> Bool",
        'url.path == "/authorize"',
        'values["v"] == "1"',
        "JerkgramNotificationsStore.shared.claimPendingPairing(nonce: nonce)",
        "JerkgramNotificationsStore.shared.claimDirectPairing(",
        "candidates.count == 1",
        "Choose the account in Jerkgram Notifications settings",
        "recordId.int64 == pending.nativeAccountId",
        "context.account.peerId.id._internalGetInt64Value() == pending.telegramUserId",
        "approveAuthTransferToken(",
        "authorizationHash: session.hash",
        "JerkgramNotificationsStore.shared.acceptPairingAuthorization(",
        "private func handleJerkgramNotificationsReconcileUrl(_ url: URL) -> Bool",
        'url.path == "/reconcile"',
        'Set(values.keys) == Set(["v", "nonce", "user", "installation"])',
        "UUID(uuidString: installationId) != nil",
        "JerkgramNotificationsStore.shared.completePairing(",
        "telegramUserId: telegramUserId",
        "installationId: installationId",
        "nonce: nonce",
        "if self.handleJerkgramNotificationsAuthorizeUrl(url)",
        "if self.handleJerkgramNotificationsReconcileUrl(url)",
    ):
        require(token in app, "AppDelegate invariant missing: " + token)
    require("activeAccounts.primary" not in app, "authorize route guesses primary account")
    require("candidates.count == 1" in app, "direct authorize must fail closed for multiple accounts")

    direct_start = state.find("public func claimDirectPairing(")
    direct_end = state.find("@discardableResult", direct_start)
    require(direct_start >= 0 and direct_end > direct_start, "direct pairing helper bounds missing")
    direct_block = state[direct_start:direct_end]
    require("record.pendingPairing == nil" not in direct_block, "same-account retry is blocked by stale pending state")
    require("record.telegramAuthorizationHash == nil" in direct_block, "direct retry lost authorization-hash safety gate")
    print("[Build139 Notifications foundation verify] GREEN")


if __name__ == "__main__":
    main()
