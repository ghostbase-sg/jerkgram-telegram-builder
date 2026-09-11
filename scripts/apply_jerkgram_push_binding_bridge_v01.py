#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"

if not APP_DELEGATE.exists():
    raise SystemExit(f"[jerkgram-push-binding] missing {APP_DELEGATE}")

text = APP_DELEGATE.read_text()
marker = "private func handleJerkgramPushBindingUrl(_ url: URL) -> Bool"
click_marker = "private func handleJerkgramPushUrl(_ url: URL) -> Bool"

if click_marker not in text:
    raise SystemExit("[jerkgram-push-binding] click bridge must be applied first")

click_dispatch = """    func application(_ application: UIApplication, open url: URL, sourceApplication: String?, annotation: Any) -> Bool {\n        if self.handleJerkgramPushUrl(url) {\n            return true\n        }\n        self.openUrl(url: url)\n        return true\n    }\n"""

bound_dispatch = """    func application(_ application: UIApplication, open url: URL, sourceApplication: String?, annotation: Any) -> Bool {\n        if self.handleJerkgramPushBindingUrl(url) {\n            return true\n        }\n        if self.handleJerkgramPushUrl(url) {\n            return true\n        }\n        self.openUrl(url: url)\n        return true\n    }\n"""

helper = r'''    // MARK: Jerkgram Notifications passwordless Web Push binding
    private func handleJerkgramPushBindingUrl(_ url: URL) -> Bool {
        guard url.scheme?.lowercased() == "jerkgram",
              url.host?.lowercased() == "push",
              url.path == "/register" || url.path == "/unregister" else {
            return false
        }

        // Jerkgram owns these two paths. Consume malformed requests locally so
        // capability material can never fall through to Telegram's generic URL router.
        guard url.absoluteString.utf8.count <= 8192,
              let components = URLComponents(url: url, resolvingAgainstBaseURL: false) else {
            return true
        }

        let queryItems = components.queryItems ?? []
        let bindingItems = queryItems.filter({ $0.name == "binding" })
        guard queryItems.allSatisfy({ $0.name == "binding" }),
              bindingItems.count == 1,
              let rawBinding = bindingItems[0].value,
              !rawBinding.isEmpty,
              rawBinding.count <= 7168,
              rawBinding.allSatisfy({ character in
                  switch character {
                  case "A"..."Z", "a"..."z", "0"..."9", "-", "_":
                      return true
                  default:
                      return false
                  }
              }) else {
            return true
        }

        var base64 = rawBinding.replacingOccurrences(of: "-", with: "+")
            .replacingOccurrences(of: "_", with: "/")
        while base64.count % 4 != 0 {
            base64.append("=")
        }
        guard let decodedData = Data(base64Encoded: base64),
              !decodedData.isEmpty,
              decodedData.count <= 5376,
              let jsonObject = try? JSONSerialization.jsonObject(with: decodedData),
              let root = jsonObject as? [String: Any],
              Set(root.keys) == Set(["v", "installationId", "subscription"]),
              let version = root["v"] as? NSNumber,
              CFGetTypeID(version) != CFBooleanGetTypeID(),
              version.intValue == 1,
              let installationId = root["installationId"] as? String,
              let uuid = UUID(uuidString: installationId),
              installationId.lowercased() == uuid.uuidString.lowercased(),
              let subscription = root["subscription"] as? [String: Any],
              Set(subscription.keys) == Set(["endpoint", "keys", "vapid"]),
              let vapid = subscription["vapid"] as? NSNumber,
              CFGetTypeID(vapid) == CFBooleanGetTypeID(),
              vapid.boolValue,
              let endpoint = subscription["endpoint"] as? String,
              !endpoint.isEmpty,
              endpoint.utf8.count <= 4096,
              let endpointComponents = URLComponents(string: endpoint),
              endpointComponents.scheme?.lowercased() == "https",
              !(endpointComponents.host ?? "").isEmpty,
              let keys = subscription["keys"] as? [String: Any],
              Set(keys.keys) == Set(["p256dh", "auth"]),
              let p256dh = keys["p256dh"] as? String,
              !p256dh.isEmpty,
              p256dh.count <= 256,
              let auth = keys["auth"] as? String,
              !auth.isEmpty,
              auth.count <= 128 else {
            return true
        }

        func isBase64Url(_ value: String) -> Bool {
            return value.allSatisfy({ character in
                switch character {
                case "A"..."Z", "a"..."z", "0"..."9", "-", "_":
                    return true
                default:
                    return false
                }
            })
        }
        guard isBase64Url(p256dh), isBase64Url(auth) else {
            return true
        }

        let subscriptionObject: [String: Any] = [
            "endpoint": endpoint,
            "keys": ["p256dh": p256dh, "auth": auth],
            "vapid": true
        ]
        guard let tokenData = try? JSONSerialization.data(withJSONObject: subscriptionObject, options: [.sortedKeys]),
              let canonicalToken = String(data: tokenData, encoding: .utf8) else {
            return true
        }

        let isRegister = url.path == "/register"
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
                        message: isRegister
                            ? "Could not connect Jerkgram Notifications. Try again."
                            : "Could not disconnect Jerkgram Notifications. Try again.",
                        preferredStyle: .alert
                    )
                    failed.addAction(UIAlertAction(title: "OK", style: .default))
                    self.mainWindow?.viewController?.present(failed, animated: true)
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
                        message: isRegister
                            ? "Allow Jerkgram Notifications for \(accountLabel)?"
                            : "Disconnect Jerkgram Notifications from \(accountLabel)?",
                        preferredStyle: .alert
                    )
                    alert.addAction(UIAlertAction(title: "Cancel", style: .cancel))

                    if isRegister {
                        alert.addAction(UIAlertAction(title: "Connect", style: .default, handler: { [weak self] _ in
                            guard let self = self else {
                                return
                            }
                            let _ = (_internal_registerJerkgramWebPushToken(
                                account: primary.account,
                                token: canonicalToken,
                                excludeMutedChats: true
                            )
                            |> deliverOnMainQueue).start(next: { [weak self] success in
                                guard let self = self else {
                                    return
                                }
                                let result = UIAlertController(
                                    title: "Jerkgram Notifications",
                                    message: success
                                        ? "Jerkgram Notifications connected."
                                        : "Could not connect Jerkgram Notifications. Try again.",
                                    preferredStyle: .alert
                                )
                                result.addAction(UIAlertAction(title: "OK", style: .default))
                                self.mainWindow?.viewController?.present(result, animated: true)
                            })
                        }))
                    } else {
                        alert.addAction(UIAlertAction(title: "Disconnect", style: .destructive, handler: { [weak self] _ in
                            guard let self = self else {
                                return
                            }
                            let _ = (_internal_unregisterJerkgramWebPushToken(
                                account: primary.account,
                                token: canonicalToken
                            )
                            |> deliverOnMainQueue).start(next: { [weak self] success in
                                guard let self = self else {
                                    return
                                }
                                let result = UIAlertController(
                                    title: "Jerkgram Notifications",
                                    message: success
                                        ? "Jerkgram Notifications disconnected."
                                        : "Could not disconnect Jerkgram Notifications. Try again.",
                                    preferredStyle: .alert
                                )
                                result.addAction(UIAlertAction(title: "OK", style: .default))
                                self.mainWindow?.viewController?.present(result, animated: true)
                            })
                        }))
                    }

                    self.mainWindow?.viewController?.present(alert, animated: true)
                })
            })
        })

        return true
    }

'''

if marker not in text:
    if text.count(click_dispatch) != 1:
        raise SystemExit(f"[jerkgram-push-binding] expected one click dispatch anchor, found {text.count(click_dispatch)}")
    text = text.replace(click_dispatch, helper + click_dispatch, 1)

if bound_dispatch not in text:
    if text.count(click_dispatch) != 1:
        raise SystemExit(f"[jerkgram-push-binding] expected one unbound dispatch anchor, found {text.count(click_dispatch)}")
    text = text.replace(click_dispatch, bound_dispatch, 1)

for invariant in (
    marker,
    'url.path == "/register" || url.path == "/unregister"',
    "url.absoluteString.utf8.count <= 8192",
    "bindingItems.count == 1",
    "rawBinding.count <= 7168",
    "decodedData.count <= 5376",
    'Set(root.keys) == Set(["v", "installationId", "subscription"])',
    'Set(subscription.keys) == Set(["endpoint", "keys", "vapid"])',
    'Set(keys.keys) == Set(["p256dh", "auth"])',
    "JSONSerialization.data(withJSONObject: subscriptionObject, options: [.sortedKeys])",
    "_internal_registerJerkgramWebPushToken(",
    "_internal_unregisterJerkgramWebPushToken(",
    "if self.handleJerkgramPushBindingUrl(url)",
):
    if invariant not in text:
        raise SystemExit(f"[jerkgram-push-binding] invariant missing after patch: {invariant}")

if text.count(marker) != 1:
    raise SystemExit(f"[jerkgram-push-binding] binding handler count={text.count(marker)}, expected 1")
if text.count("if self.handleJerkgramPushBindingUrl(url)") != 1:
    raise SystemExit("[jerkgram-push-binding] binding dispatch must exist exactly once")

APP_DELEGATE.write_text(text)
print("[jerkgram-push-binding] OK")
print("  patched:", APP_DELEGATE)
