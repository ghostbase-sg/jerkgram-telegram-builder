#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
NOTIFICATIONS = ROOT / "submodules/JerkgramCore/Sources/JerkgramNotifications.swift"

MARKER = "// MARK: Jerkgram v1.3A BUILD139_NOTIFICATIONS_FOUNDATION1"


NOTIFICATIONS_SOURCE = r'''import Foundation

public enum JerkgramNotificationLifecycleState: String, Codable, Equatable {
    case disconnected
    case connecting
    case active
    case permissionDisabled
    case repairRequired
    case disconnecting
    case pendingRevoke
    case error
}

public struct JerkgramNotificationPendingPairing: Codable, Equatable {
    public let nativeAccountId: Int64
    public let telegramUserId: Int64
    public let createdAt: TimeInterval
    public let expiresAt: TimeInterval
    public var nonce: String?

    public init(
        nativeAccountId: Int64,
        telegramUserId: Int64,
        createdAt: TimeInterval,
        expiresAt: TimeInterval,
        nonce: String? = nil
    ) {
        self.nativeAccountId = nativeAccountId
        self.telegramUserId = telegramUserId
        self.createdAt = createdAt
        self.expiresAt = expiresAt
        self.nonce = nonce
    }
}

public struct JerkgramNotificationAccountRecord: Codable, Equatable {
    public let nativeAccountId: Int64
    public let telegramUserId: Int64
    public var telegramAuthorizationHash: Int64?
    public var installationId: String?
    public var lifecycleState: JerkgramNotificationLifecycleState
    public var pushPermissionState: String?
    public var pushSubscriptionState: String?
    public var pendingPairing: JerkgramNotificationPendingPairing?
    public var pendingRevokeAuthorizationHash: Int64?
    public var bridgeProtocolVersion: Int

    public init(
        nativeAccountId: Int64,
        telegramUserId: Int64,
        telegramAuthorizationHash: Int64? = nil,
        installationId: String? = nil,
        lifecycleState: JerkgramNotificationLifecycleState = .disconnected,
        pushPermissionState: String? = nil,
        pushSubscriptionState: String? = nil,
        pendingPairing: JerkgramNotificationPendingPairing? = nil,
        pendingRevokeAuthorizationHash: Int64? = nil,
        bridgeProtocolVersion: Int = JerkgramNotificationsStore.bridgeProtocolVersion
    ) {
        self.nativeAccountId = nativeAccountId
        self.telegramUserId = telegramUserId
        self.telegramAuthorizationHash = telegramAuthorizationHash
        self.installationId = installationId
        self.lifecycleState = lifecycleState
        self.pushPermissionState = pushPermissionState
        self.pushSubscriptionState = pushSubscriptionState
        self.pendingPairing = pendingPairing
        self.pendingRevokeAuthorizationHash = pendingRevokeAuthorizationHash
        self.bridgeProtocolVersion = bridgeProtocolVersion
    }
}

public final class JerkgramNotificationsStore {
    public static let shared = JerkgramNotificationsStore()
    public static let bridgeProtocolVersion = 1

    private let defaults: UserDefaults
    private let recordsKey = "jerkgram.notifications.accounts.v1"
    private let usedNoncesKey = "jerkgram.notifications.usedNonces.v1"
    private let queue = DispatchQueue(label: "com.jerkgram.notifications.state")
    private let maximumUsedNonces = 64

    public init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
    }

    public func record(nativeAccountId: Int64, now: Date = Date()) -> JerkgramNotificationAccountRecord? {
        return self.queue.sync {
            var records = self.loadRecords()
            self.expirePendingPairings(records: &records, now: now.timeIntervalSince1970)
            self.saveRecords(records)
            return records[String(nativeAccountId)]
        }
    }

    @discardableResult
    public func beginPairing(
        nativeAccountId: Int64,
        telegramUserId: Int64,
        now: Date = Date(),
        pairingLifetime: TimeInterval = 120.0
    ) -> Bool {
        return self.queue.sync {
            var records = self.loadRecords()
            let timestamp = now.timeIntervalSince1970
            self.expirePendingPairings(records: &records, now: timestamp)

            let anotherPending = records.values.contains { record in
                guard record.nativeAccountId != nativeAccountId,
                      let pending = record.pendingPairing else {
                    return false
                }
                return pending.expiresAt > timestamp
            }
            guard !anotherPending else {
                self.saveRecords(records)
                return false
            }

            var record = records[String(nativeAccountId)] ?? JerkgramNotificationAccountRecord(
                nativeAccountId: nativeAccountId,
                telegramUserId: telegramUserId
            )
            guard record.telegramUserId == telegramUserId,
                  record.telegramAuthorizationHash == nil else {
                self.saveRecords(records)
                return false
            }
            record.lifecycleState = .connecting
            record.bridgeProtocolVersion = Self.bridgeProtocolVersion
            record.pendingPairing = JerkgramNotificationPendingPairing(
                nativeAccountId: nativeAccountId,
                telegramUserId: telegramUserId,
                createdAt: timestamp,
                expiresAt: timestamp + pairingLifetime
            )
            records[String(nativeAccountId)] = record
            self.saveRecords(records)
            return true
        }
    }

    public func claimPendingPairing(nonce: String, now: Date = Date()) -> JerkgramNotificationPendingPairing? {
        return self.queue.sync {
            guard Self.isValidNonce(nonce) else {
                return nil
            }
            var usedPairingNonces = self.loadUsedNonces()
            guard !usedPairingNonces.contains(nonce) else {
                return nil
            }

            var records = self.loadRecords()
            let timestamp = now.timeIntervalSince1970
            self.expirePendingPairings(records: &records, now: timestamp)
            let unexpiredPending = records.values.compactMap { record -> JerkgramNotificationPendingPairing? in
                guard let pending = record.pendingPairing,
                      pending.expiresAt > timestamp,
                      pending.nonce == nil,
                      record.telegramAuthorizationHash == nil else {
                    return nil
                }
                return pending
            }
            guard unexpiredPending.count == 1, var pending = unexpiredPending.first else {
                self.saveRecords(records)
                return nil
            }

            pending.nonce = nonce
            guard var record = records[String(pending.nativeAccountId)],
                  record.telegramUserId == pending.telegramUserId else {
                return nil
            }
            record.pendingPairing = pending
            records[String(pending.nativeAccountId)] = record
            usedPairingNonces.append(nonce)
            if usedPairingNonces.count > self.maximumUsedNonces {
                usedPairingNonces.removeFirst(usedPairingNonces.count - self.maximumUsedNonces)
            }
            self.saveUsedNonces(usedPairingNonces)
            self.saveRecords(records)
            return pending
        }
    }

    @discardableResult
    public func acceptPairingAuthorization(
        nativeAccountId: Int64,
        telegramUserId: Int64,
        authorizationHash: Int64,
        nonce: String
    ) -> Bool {
        return self.queue.sync {
            var records = self.loadRecords()
            guard var record = records[String(nativeAccountId)],
                  record.telegramUserId == telegramUserId,
                  record.pendingPairing?.nonce == nonce,
                  record.telegramAuthorizationHash == nil else {
                return false
            }
            record.telegramAuthorizationHash = authorizationHash
            record.pendingRevokeAuthorizationHash = nil
            record.lifecycleState = .connecting
            record.bridgeProtocolVersion = Self.bridgeProtocolVersion
            records[String(nativeAccountId)] = record
            self.saveRecords(records)
            return true
        }
    }

    @discardableResult
    public func completePairing(
        telegramUserId: Int64,
        installationId: String,
        nonce: String,
        now: Date = Date()
    ) -> Bool {
        return self.queue.sync {
            guard UUID(uuidString: installationId) != nil else {
                return false
            }
            var records = self.loadRecords()
            let timestamp = now.timeIntervalSince1970
            let matches = records.values.filter { record in
                guard let pending = record.pendingPairing else {
                    return false
                }
                return pending.nonce == nonce && pending.expiresAt > timestamp
            }
            guard matches.count == 1,
                  var record = matches.first,
                  record.telegramUserId == telegramUserId,
                  record.pendingPairing?.nonce == nonce,
                  record.telegramAuthorizationHash != nil else {
                return false
            }
            record.installationId = installationId
            record.pendingPairing = nil
            record.pendingRevokeAuthorizationHash = nil
            record.lifecycleState = .active
            record.bridgeProtocolVersion = Self.bridgeProtocolVersion
            records[String(record.nativeAccountId)] = record
            self.saveRecords(records)
            return true
        }
    }

    public func markPairingError(nativeAccountId: Int64) {
        self.queue.sync {
            var records = self.loadRecords()
            guard var record = records[String(nativeAccountId)] else {
                return
            }
            record.pendingPairing = nil
            record.lifecycleState = record.telegramAuthorizationHash == nil ? .error : .repairRequired
            records[String(nativeAccountId)] = record
            self.saveRecords(records)
        }
    }

    public func markPairingMismatch(nonce: String) {
        self.queue.sync {
            var records = self.loadRecords()
            guard let key = records.first(where: { $0.value.pendingPairing?.nonce == nonce })?.key,
                  var record = records[key] else {
                return
            }
            record.pendingPairing = nil
            record.lifecycleState = record.telegramAuthorizationHash == nil ? .error : .repairRequired
            records[key] = record
            self.saveRecords(records)
        }
    }

    public func beginRevoke(nativeAccountId: Int64) -> Int64? {
        return self.queue.sync {
            var records = self.loadRecords()
            guard var record = records[String(nativeAccountId)],
                  let hash = record.telegramAuthorizationHash else {
                return nil
            }
            record.lifecycleState = .disconnecting
            record.pendingRevokeAuthorizationHash = hash
            records[String(nativeAccountId)] = record
            self.saveRecords(records)
            return hash
        }
    }

    public func finishRevoke(nativeAccountId: Int64) {
        self.queue.sync {
            var records = self.loadRecords()
            guard var record = records[String(nativeAccountId)] else {
                return
            }
            record.telegramAuthorizationHash = nil
            record.installationId = nil
            record.pushPermissionState = nil
            record.pushSubscriptionState = nil
            record.pendingRevokeAuthorizationHash = nil
            record.pendingPairing = nil
            record.lifecycleState = .disconnected
            records[String(nativeAccountId)] = record
            self.saveRecords(records)
        }
    }

    public func markPendingRevoke(nativeAccountId: Int64) {
        self.queue.sync {
            var records = self.loadRecords()
            guard var record = records[String(nativeAccountId)] else {
                return
            }
            record.lifecycleState = .pendingRevoke
            records[String(nativeAccountId)] = record
            self.saveRecords(records)
        }
    }

    private static func isValidNonce(_ nonce: String) -> Bool {
        guard nonce.count >= 32, nonce.count <= 128 else {
            return false
        }
        return nonce.allSatisfy { character in
            switch character {
            case "A"..."Z", "a"..."z", "0"..."9", "-", "_":
                return true
            default:
                return false
            }
        }
    }

    private func expirePendingPairings(records: inout [String: JerkgramNotificationAccountRecord], now: TimeInterval) {
        for key in Array(records.keys) {
            guard var record = records[key],
                  let pending = record.pendingPairing,
                  pending.expiresAt <= now else {
                continue
            }
            record.pendingPairing = nil
            if record.lifecycleState == .connecting {
                record.lifecycleState = record.telegramAuthorizationHash == nil ? .disconnected : .repairRequired
            }
            records[key] = record
        }
    }

    private func loadRecords() -> [String: JerkgramNotificationAccountRecord] {
        guard let data = self.defaults.data(forKey: self.recordsKey),
              let value = try? JSONDecoder().decode([String: JerkgramNotificationAccountRecord].self, from: data) else {
            return [:]
        }
        return value
    }

    private func saveRecords(_ records: [String: JerkgramNotificationAccountRecord]) {
        if let data = try? JSONEncoder().encode(records) {
            self.defaults.set(data, forKey: self.recordsKey)
        }
    }

    private func loadUsedNonces() -> [String] {
        return self.defaults.stringArray(forKey: self.usedNoncesKey) ?? []
    }

    private func saveUsedNonces(_ nonces: [String]) {
        self.defaults.set(nonces, forKey: self.usedNoncesKey)
    }
}
'''


AUTHORIZE_HELPER = r'''    // MARK: Jerkgram v1.3A BUILD139_NOTIFICATIONS_FOUNDATION1
    private func handleJerkgramNotificationsAuthorizeUrl(_ url: URL) -> Bool {
        guard url.scheme?.lowercased() == "jerkgram",
              url.host?.lowercased() == "push",
              url.path == "/authorize" else {
            return false
        }

        guard url.absoluteString.utf8.count <= 3072,
              let components = URLComponents(url: url, resolvingAgainstBaseURL: false) else {
            return true
        }

        let queryItems = components.queryItems ?? []
        var values: [String: String] = [:]
        for item in queryItems {
            guard values[item.name] == nil, let value = item.value else {
                return true
            }
            values[item.name] = value
        }
        guard queryItems.count == values.count,
              Set(values.keys) == Set(["v", "token", "nonce"]),
              values["v"] == "1",
              let nonce = values["nonce"],
              nonce.count >= 32,
              nonce.count <= 128,
              nonce.allSatisfy({ character in
                  switch character {
                  case "A"..."Z", "a"..."z", "0"..."9", "-", "_":
                      return true
                  default:
                      return false
                  }
              }),
              let rawToken = values["token"],
              !rawToken.isEmpty,
              rawToken.count <= 1536,
              rawToken.allSatisfy({ character in
                  switch character {
                  case "A"..."Z", "a"..."z", "0"..."9", "-", "_":
                      return true
                  default:
                      return false
                  }
              }) else {
            return true
        }

        var base64 = rawToken.replacingOccurrences(of: "-", with: "+")
            .replacingOccurrences(of: "_", with: "/")
        while base64.count % 4 != 0 {
            base64.append("=")
        }
        guard let tokenData = Data(base64Encoded: base64),
              !tokenData.isEmpty,
              tokenData.count <= 1024,
              let pending = JerkgramNotificationsStore.shared.claimPendingPairing(nonce: nonce) else {
            return true
        }

        let _ = (self.sharedContextPromise.get()
        |> take(1)
        |> deliverOnMainQueue).start(next: { [weak self] sharedApplicationContext in
            guard let self else { return }
            let _ = (sharedApplicationContext.sharedContext.activeAccountContexts
            |> take(1)
            |> deliverOnMainQueue).start(next: { [weak self] activeAccounts in
                guard let self else { return }

                var targetContext: AccountContext?
                for (recordId, context, _) in activeAccounts.accounts {
                    if recordId.int64 == pending.nativeAccountId,
                       context.account.peerId.id._internalGetInt64Value() == pending.telegramUserId {
                        targetContext = context
                        break
                    }
                }
                guard let context = targetContext else {
                    JerkgramNotificationsStore.shared.markPairingError(nativeAccountId: pending.nativeAccountId)
                    return
                }

                let _ = (context.account.postbox.transaction { transaction -> TelegramUser? in
                    return transaction.getPeer(context.account.peerId) as? TelegramUser
                }
                |> take(1)
                |> deliverOnMainQueue).start(next: { [weak self] user in
                    guard let self else { return }
                    let accountLabel: String
                    if let username = user?.username, !username.isEmpty {
                        accountLabel = "@\(username)"
                    } else if let user {
                        let displayName = [user.firstName, user.lastName]
                            .compactMap { value -> String? in
                                guard let value, !value.isEmpty else { return nil }
                                return value
                            }
                            .joined(separator: " ")
                        accountLabel = displayName.isEmpty ? "Telegram account" : displayName
                    } else {
                        accountLabel = "Telegram account"
                    }

                    let alert = UIAlertController(
                        title: "Jerkgram Notifications",
                        message: "Connect notifications for \(accountLabel)?\n\nA separate Telegram session will be created only for notifications.",
                        preferredStyle: .alert
                    )
                    alert.addAction(UIAlertAction(title: "Cancel", style: .cancel))
                    alert.addAction(UIAlertAction(title: "Connect", style: .default, handler: { [weak self] _ in
                        guard let self else { return }
                        let activeSessionsContext = context.engine.privacy.activeSessions()
                        let _ = (approveAuthTransferToken(
                            account: context.account,
                            token: tokenData,
                            activeSessionsContext: activeSessionsContext
                        )
                        |> deliverOnMainQueue).start(next: { [weak self] session in
                            guard let self else { return }
                            let stored = JerkgramNotificationsStore.shared.acceptPairingAuthorization(
                                nativeAccountId: pending.nativeAccountId,
                                telegramUserId: pending.telegramUserId,
                                authorizationHash: session.hash,
                                nonce: nonce
                            )
                            guard stored else {
                                JerkgramNotificationsStore.shared.markPairingError(nativeAccountId: pending.nativeAccountId)
                                return
                            }
                            let done = UIAlertController(
                                title: "Jerkgram Notifications",
                                message: "Telegram approved the notification session. Return to Jerkgram Notifications to finish verification.",
                                preferredStyle: .alert
                            )
                            done.addAction(UIAlertAction(title: "OK", style: .default))
                            self.mainWindow?.viewController?.present(done, animated: true)
                        }, error: { _ in
                            JerkgramNotificationsStore.shared.markPairingError(nativeAccountId: pending.nativeAccountId)
                        })
                    }))
                    self.mainWindow?.viewController?.present(alert, animated: true)
                })
            })
        })
        return true
    }

'''


RECONCILE_HELPER = r'''    private func handleJerkgramNotificationsReconcileUrl(_ url: URL) -> Bool {
        guard url.scheme?.lowercased() == "jerkgram",
              url.host?.lowercased() == "push",
              url.path == "/reconcile" else {
            return false
        }
        guard url.absoluteString.utf8.count <= 3072,
              let components = URLComponents(url: url, resolvingAgainstBaseURL: false) else {
            return true
        }

        let queryItems = components.queryItems ?? []
        var values: [String: String] = [:]
        for item in queryItems {
            guard values[item.name] == nil, let value = item.value else {
                return true
            }
            values[item.name] = value
        }
        guard queryItems.count == values.count,
              Set(values.keys) == Set(["v", "nonce", "user", "installation"]),
              values["v"] == "1",
              let nonce = values["nonce"],
              nonce.count >= 32,
              nonce.count <= 128,
              nonce.allSatisfy({ character in
                  switch character {
                  case "A"..."Z", "a"..."z", "0"..."9", "-", "_": return true
                  default: return false
                  }
              }),
              let rawUserId = values["user"],
              rawUserId.count <= 20,
              rawUserId.allSatisfy({ $0 >= "0" && $0 <= "9" }),
              let telegramUserId = Int64(rawUserId),
              telegramUserId > 0,
              let installationId = values["installation"],
              UUID(uuidString: installationId) != nil else {
            return true
        }

        let completed = JerkgramNotificationsStore.shared.completePairing(
            telegramUserId: telegramUserId,
            installationId: installationId,
            nonce: nonce
        )
        if !completed {
            JerkgramNotificationsStore.shared.markPairingMismatch(nonce: nonce)
            return true
        }

        let done = UIAlertController(
            title: "Jerkgram Notifications",
            message: "Notifications are connected for this account.",
            preferredStyle: .alert
        )
        done.addAction(UIAlertAction(title: "OK", style: .default))
        self.mainWindow?.viewController?.present(done, animated: true)
        return true
    }

'''


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build139 Notifications foundation] " + message)


def patch_app_delegate_text(text: str) -> str:
    import_anchor = "import Foundation\n"
    if "import JerkgramCore\n" not in text:
        require(import_anchor in text, "AppDelegate Foundation import missing")
        text = text.replace(import_anchor, import_anchor + "import JerkgramCore\n", 1)

    authorize_marker = "private func handleJerkgramNotificationsAuthorizeUrl(_ url: URL) -> Bool"
    reconcile_marker = "private func handleJerkgramNotificationsReconcileUrl(_ url: URL) -> Bool"
    open_anchor = """    func application(_ application: UIApplication, open url: URL, sourceApplication: String?, annotation: Any) -> Bool {\n        self.openUrl(url: url)\n        return true\n    }\n"""
    old_patched_open = """    func application(_ application: UIApplication, open url: URL, sourceApplication: String?, annotation: Any) -> Bool {\n        if self.handleJerkgramNotificationsAuthorizeUrl(url) {\n            return true\n        }\n        self.openUrl(url: url)\n        return true\n    }\n"""
    patched_open = """    func application(_ application: UIApplication, open url: URL, sourceApplication: String?, annotation: Any) -> Bool {\n        if self.handleJerkgramNotificationsAuthorizeUrl(url) {\n            return true\n        }\n        if self.handleJerkgramNotificationsReconcileUrl(url) {\n            return true\n        }\n        self.openUrl(url: url)\n        return true\n    }\n"""

    if authorize_marker not in text:
        require(text.count(open_anchor) == 1, "AppDelegate open-url anchor count")
        text = text.replace(open_anchor, AUTHORIZE_HELPER + RECONCILE_HELPER + open_anchor, 1)
    elif reconcile_marker not in text:
        marker_index = text.index(authorize_marker)
        next_dispatch = text.find("    func application(_ application: UIApplication, open url: URL", marker_index)
        require(next_dispatch >= 0, "AppDelegate dispatch missing after authorize helper")
        text = text[:next_dispatch] + RECONCILE_HELPER + text[next_dispatch:]

    if patched_open not in text:
        if old_patched_open in text:
            text = text.replace(old_patched_open, patched_open, 1)
        else:
            require(text.count(open_anchor) == 1, "AppDelegate notification dispatch anchor count")
            text = text.replace(open_anchor, patched_open, 1)

    for token in (
        authorize_marker,
        reconcile_marker,
        'values["v"] == "1"',
        'values["nonce"]',
        'values["token"]',
        "JerkgramNotificationsStore.shared.claimPendingPairing(nonce: nonce)",
        "recordId.int64 == pending.nativeAccountId",
        "context.account.peerId.id._internalGetInt64Value() == pending.telegramUserId",
        "approveAuthTransferToken(",
        "authorizationHash: session.hash",
        "JerkgramNotificationsStore.shared.acceptPairingAuthorization(",
        'url.path == "/reconcile"',
        "JerkgramNotificationsStore.shared.completePairing(",
        "installationId: installationId",
        "if self.handleJerkgramNotificationsAuthorizeUrl(url)",
        "if self.handleJerkgramNotificationsReconcileUrl(url)",
    ):
        require(token in text, "missing AppDelegate invariant: " + token)
    require("activeAccounts.primary" not in text, "pairing must never guess the primary account")
    return text


def main() -> None:
    require(APP_DELEGATE.is_file(), "AppDelegate missing: " + str(APP_DELEGATE))
    NOTIFICATIONS.parent.mkdir(parents=True, exist_ok=True)
    NOTIFICATIONS.write_text(NOTIFICATIONS_SOURCE + "\n", encoding="utf-8")
    APP_DELEGATE.write_text(patch_app_delegate_text(APP_DELEGATE.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build139 Notifications foundation] SOURCE PATCHED")
    print("[Build139 Notifications foundation] accept remains CONNECTING; PWA user-id reconcile is required before ACTIVE")


if __name__ == "__main__":
    main()
