#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"

if not APP_DELEGATE.exists():
    raise SystemExit(f"[jerkgram-notifications-session-pairing] missing {APP_DELEGATE}")

text = APP_DELEGATE.read_text()
marker = "private func handleJerkgramNotificationsSessionPairingUrl(_ url: URL) -> Bool"
external_marker = "private func handleJerkgramExternalUrl(_ url: URL) -> Bool"

if external_marker not in text:
    raise SystemExit("[jerkgram-notifications-session-pairing] passwordless binding dispatcher must be applied first")

helper = r'''    // MARK: Jerkgram Notifications backend-session authorization
    private func handleJerkgramNotificationsSessionPairingUrl(_ url: URL) -> Bool {
        guard url.scheme?.lowercased() == "jerkgram",
              url.host?.lowercased() == "push",
              url.path == "/authorize" else {
            return false
        }

        // This path owns a Telegram login token. Consume malformed requests here;
        // never forward them to Telegram's generic URL router and never log them.
        guard url.absoluteString.utf8.count <= 2304,
              let components = URLComponents(url: url, resolvingAgainstBaseURL: false) else {
            return true
        }

        let queryItems = components.queryItems ?? []
        let pairItems = queryItems.filter({ $0.name == "pair" })
        let tokenItems = queryItems.filter({ $0.name == "token" })
        guard queryItems.allSatisfy({ $0.name == "pair" || $0.name == "token" }),
              pairItems.count == 1,
              tokenItems.count == 1,
              let rawPairId = pairItems[0].value,
              rawPairId.count >= 16,
              rawPairId.count <= 128,
              rawPairId.allSatisfy({ character in
                  switch character {
                  case "A"..."Z", "a"..."z", "0"..."9", "-", "_":
                      return true
                  default:
                      return false
                  }
              }),
              let rawToken = tokenItems[0].value,
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
              tokenData.count <= 1024 else {
            return true
        }

        let _ = (self.sharedContextPromise.get()
        |> take(1)
        |> deliverOnMainQueue).start(next: { [weak self] sharedApplicationContext in
            guard let self = self else {
                return
            }
            let _ = (sharedApplicationContext.sharedContext.activeAccountContexts
            |> take(1)
            |> deliverOnMainQueue).start(next: { [weak self] activeAccounts in
                guard let self = self else {
                    return
                }
                guard let primary = activeAccounts.primary else {
                    let failed = UIAlertController(
                        title: "Jerkgram Notifications",
                        message: "Could not connect Jerkgram Notifications. Try again.",
                        preferredStyle: .alert
                    )
                    failed.addAction(UIAlertAction(title: "OK", style: .default))
                    self.window?.rootViewController?.present(failed, animated: true)
                    return
                }

                let _ = (primary.account.postbox.transaction { transaction -> TelegramUser? in
                    return transaction.getPeer(primary.account.peerId) as? TelegramUser
                }
                |> take(1)
                |> deliverOnMainQueue).start(next: { [weak self] user in
                    guard let self = self else {
                        return
                    }

                    let accountLabel: String
                    if let username = user?.username, !username.isEmpty {
                        accountLabel = "@\(username)"
                    } else if let user = user {
                        let displayName = [user.firstName, user.lastName]
                            .compactMap({ value -> String? in
                                guard let value = value, !value.isEmpty else {
                                    return nil
                                }
                                return value
                            })
                            .joined(separator: " ")
                        accountLabel = displayName.isEmpty ? "Current Telegram account" : displayName
                    } else {
                        accountLabel = "Current Telegram account"
                    }

                    let alert = UIAlertController(
                        title: "Jerkgram Notifications",
                        message: "Allow Jerkgram Notifications to connect to \(accountLabel)?\n\nA separate Telegram session will be created for notifications. This is a full Telegram account session, not a notification-only credential. No keys from this Jerkgram session are copied to the backend.",
                        preferredStyle: .alert
                    )
                    alert.addAction(UIAlertAction(title: "Cancel", style: .cancel))
                    alert.addAction(UIAlertAction(title: "Connect", style: .default, handler: { [weak self] _ in
                        guard let self = self else {
                            return
                        }
                        let activeSessionsContext = primary.engine.privacy.activeSessions()
                        let _ = (approveAuthTransferToken(
                            account: primary.account,
                            token: tokenData,
                            activeSessionsContext: activeSessionsContext
                        )
                        |> deliverOnMainQueue).start(next: { [weak self] _ in
                            guard let self = self else {
                                return
                            }
                            let done = UIAlertController(
                                title: "Jerkgram Notifications",
                                message: "Jerkgram Notifications connected. Return to notification setup to continue.",
                                preferredStyle: .alert
                            )
                            done.addAction(UIAlertAction(title: "OK", style: .default))
                            self.window?.rootViewController?.present(done, animated: true)
                        }, error: { [weak self] error in
                            guard let self = self else {
                                return
                            }
                            let message: String
                            switch error {
                            case .expired, .alreadyAccepted:
                                message = "Connection request expired. Start again."
                            case .invalid, .generic:
                                message = "Could not connect Jerkgram Notifications. Try again."
                            }
                            let failed = UIAlertController(
                                title: "Jerkgram Notifications",
                                message: message,
                                preferredStyle: .alert
                            )
                            failed.addAction(UIAlertAction(title: "OK", style: .default))
                            self.window?.rootViewController?.present(failed, animated: true)
                        })
                    }))
                    self.window?.rootViewController?.present(alert, animated: true)
                })
            })
        })

        return true
    }

'''

if marker not in text:
    anchor = "    " + external_marker
    if text.count(anchor) != 1:
        raise SystemExit(
            f"[jerkgram-notifications-session-pairing] expected one external dispatcher anchor, found {text.count(anchor)}"
        )
    text = text.replace(anchor, helper + anchor, 1)

old_dispatcher = '''    private func handleJerkgramExternalUrl(_ url: URL) -> Bool {
        if self.handleJerkgramPushBindingUrl(url) {
            return true
        }
        if self.handleJerkgramPushUrl(url) {
            return true
        }
        return false
    }
'''
new_dispatcher = '''    private func handleJerkgramExternalUrl(_ url: URL) -> Bool {
        if self.handleJerkgramNotificationsSessionPairingUrl(url) {
            return true
        }
        if self.handleJerkgramPushBindingUrl(url) {
            return true
        }
        if self.handleJerkgramPushUrl(url) {
            return true
        }
        return false
    }
'''

if new_dispatcher not in text:
    if text.count(old_dispatcher) != 1:
        raise SystemExit(
            f"[jerkgram-notifications-session-pairing] expected one binding dispatcher, found {text.count(old_dispatcher)}"
        )
    text = text.replace(old_dispatcher, new_dispatcher, 1)

for invariant in (
    marker,
    'url.path == "/authorize"',
    "pairItems.count == 1",
    "tokenItems.count == 1",
    "tokenData.count <= 1024",
    "guard let primary = activeAccounts.primary else",
    "transaction.getPeer(primary.account.peerId)",
    "approveAuthTransferToken(",
    "primary.engine.privacy.activeSessions()",
    "A separate Telegram session will be created",
    "full Telegram account session",
    "if self.handleJerkgramNotificationsSessionPairingUrl(url)",
):
    if invariant not in text:
        raise SystemExit(f"[jerkgram-notifications-session-pairing] invariant missing: {invariant}")

if text.count(marker) != 1:
    raise SystemExit(
        f"[jerkgram-notifications-session-pairing] handler count={text.count(marker)}, expected 1"
    )

APP_DELEGATE.write_text(text)
print("[jerkgram-notifications-session-pairing] OK")
print("  patched:", APP_DELEGATE)
