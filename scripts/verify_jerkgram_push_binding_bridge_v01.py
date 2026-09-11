#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"

errors = []
if not APP_DELEGATE.exists():
    errors.append(f"missing AppDelegate: {APP_DELEGATE}")
else:
    text = APP_DELEGATE.read_text()
    marker = "private func handleJerkgramPushBindingUrl(_ url: URL) -> Bool"
    click_marker = "private func handleJerkgramPushUrl(_ url: URL) -> Bool"

    for required in (
        marker,
        click_marker,
        'url.scheme?.lowercased() == "jerkgram"',
        'url.host?.lowercased() == "push"',
        'url.path == "/register" || url.path == "/unregister"',
        "url.absoluteString.utf8.count <= 8192",
        'queryItems.allSatisfy({ $0.name == "binding" })',
        "bindingItems.count == 1",
        "rawBinding.count <= 7168",
        'case "A"..."Z", "a"..."z", "0"..."9", "-", "_"',
        "decodedData.count <= 5376",
        'Set(root.keys) == Set(["v", "installationId", "subscription"])',
        "CFGetTypeID(version) != CFBooleanGetTypeID()",
        "version.intValue == 1",
        "UUID(uuidString: installationId)",
        "installationId.lowercased() == uuid.uuidString.lowercased()",
        'Set(subscription.keys) == Set(["endpoint", "keys", "vapid"])',
        "CFGetTypeID(vapid) == CFBooleanGetTypeID()",
        "vapid.boolValue",
        'Set(keys.keys) == Set(["p256dh", "auth"])',
        "endpoint.utf8.count <= 4096",
        'endpointComponents.scheme?.lowercased() == "https"',
        '!(endpointComponents.host ?? "").isEmpty',
        "p256dh.count <= 256",
        "auth.count <= 128",
        'let subscriptionObject: [String: Any] = [',
        '"endpoint": endpoint',
        '"keys": ["p256dh": p256dh, "auth": auth]',
        '"vapid": true',
        "JSONSerialization.data(withJSONObject: subscriptionObject, options: [.sortedKeys])",
        "let canonicalToken = String(data: tokenData, encoding: .utf8)",
        "activeAccountContexts",
        "guard let primary = activeAccounts.primary else",
        "transaction.getPeer(primary.account.peerId)",
        "as? TelegramUser",
        "user?.username",
        "[user.firstName, user.lastName]",
        "_internal_registerJerkgramWebPushToken(",
        "excludeMutedChats: true",
        "_internal_unregisterJerkgramWebPushToken(",
        'UIAlertAction(title: "Connect", style: .default',
        'UIAlertAction(title: "Disconnect", style: .destructive',
        "Jerkgram Notifications connected.",
        "Jerkgram Notifications disconnected.",
        "Could not connect Jerkgram Notifications. Try again.",
        "Could not disconnect Jerkgram Notifications. Try again.",
        "if self.handleJerkgramPushBindingUrl(url)",
        "if self.handleJerkgramPushUrl(url)",
    ):
        if required not in text:
            errors.append(f"missing invariant: {required}")

    if text.count(marker) != 1:
        errors.append(f"binding handler count={text.count(marker)}, expected 1")
    if text.count("if self.handleJerkgramPushBindingUrl(url)") != 1:
        errors.append("binding dispatch must exist exactly once")
    if text.count(click_marker) != 1:
        errors.append("existing click handler must still exist exactly once")

    if marker in text and "func application(_ application: UIApplication, open url: URL" in text:
        helper_start = text.index(marker)
        dispatch_start = text.index("func application(_ application: UIApplication, open url: URL")
        helper = text[helper_start:dispatch_start]

        canonical_start = helper.find("let subscriptionObject")
        async_start = helper.find("let _ = (self.sharedContextPromise.get()")
        if canonical_start >= 0 and async_start > canonical_start:
            canonical_scope = helper[canonical_start:async_start]
            if "installationId" in canonical_scope:
                errors.append("installationId leaked into canonical Telegram token scope")

        for forbidden in (
            "jerkgram://push/authorize",
            "approveAuthTransferToken",
            "activeSessions",
            "UserDefaults",
            "print(rawBinding)",
            "print(canonicalToken)",
            "debugPrint",
            "user_id",
            "accountId",
        ):
            if forbidden in helper:
                errors.append(f"binding helper contains forbidden legacy/sensitive marker: {forbidden}")

        dispatch = text[dispatch_start:]
        if all(value in dispatch for value in (
            "handleJerkgramPushBindingUrl(url)",
            "handleJerkgramPushUrl(url)",
            "self.openUrl(url: url)",
        )):
            if not (
                dispatch.index("handleJerkgramPushBindingUrl(url)")
                < dispatch.index("handleJerkgramPushUrl(url)")
                < dispatch.index("self.openUrl(url: url)")
            ):
                errors.append("dispatch order must be binding -> click -> generic URL")

if errors:
    print("[jerkgram-push-binding-verify] FAIL")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("[jerkgram-push-binding-verify] PASS")
