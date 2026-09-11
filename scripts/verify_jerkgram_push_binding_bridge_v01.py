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
    external_marker = "private func handleJerkgramExternalUrl(_ url: URL) -> Bool"
    click_marker = "private func handleJerkgramPushUrl(_ url: URL) -> Bool"

    for required in (
        marker,
        external_marker,
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
        '!["f", "d"].contains(String(cString: version.objCType))',
        "version.int64Value == 1",
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
        "self.window?.rootViewController?.present(",
    ):
        if required not in text:
            errors.append(f"missing invariant: {required}")

    if text.count(marker) != 1:
        errors.append(f"binding handler count={text.count(marker)}, expected 1")
    if text.count(external_marker) != 1:
        errors.append(f"external dispatcher count={text.count(external_marker)}, expected 1")
    if text.count(click_marker) != 1:
        errors.append("existing click handler must still exist exactly once")

    def scope(signature: str) -> str | None:
        start = text.find(signature)
        if start < 0:
            return None
        brace = text.find("{", start)
        depth = 0
        in_string = False
        escaped = False
        for index in range(brace, len(text)):
            ch = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:index + 1]
        return None

    if marker in text and external_marker in text:
        helper_start = text.index(marker)
        external_start = text.index(external_marker, helper_start)
        helper = text[helper_start:external_start]
        external_end = text.find("\n    func application(", external_start)
        if external_end < 0:
            external_end = len(text)
        dispatcher = text[external_start:external_end]

        canonical_start = helper.find("let subscriptionObject")
        async_start = helper.find("let _ = (self.sharedContextPromise.get()")
        if canonical_start >= 0 and async_start > canonical_start:
            canonical_scope = helper[canonical_start:async_start]
            if "installationId" in canonical_scope:
                errors.append("installationId leaked into canonical Telegram token scope")

        if helper.count("self.window?.rootViewController?.present(") != 4:
            errors.append("binding helper must present exactly four alerts via rootViewController")
        if "self.mainWindow?.viewController?.present(" in helper:
            errors.append("binding helper still uses ContainableController.present")

        for forbidden in (
            "jerkgram://push/authorize",
            "approveAuthTransferToken",
            "auth.acceptLoginToken",
            "auth.exportLoginToken",
            "auth.importLoginToken",
            "SESSION_PASSWORD_NEEDED",
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

        if "handleJerkgramPushBindingUrl(url)" not in dispatcher or "handleJerkgramPushUrl(url)" not in dispatcher:
            errors.append("shared dispatcher missing binding or click handler")
        elif dispatcher.index("handleJerkgramPushBindingUrl(url)") > dispatcher.index("handleJerkgramPushUrl(url)"):
            errors.append("shared dispatcher order must be binding -> click")
        if "self.openUrl(url: url)" in dispatcher:
            errors.append("shared Jerkgram dispatcher must not call generic openUrl")
        if "handleJerkgramPushPairingUrl" in dispatcher:
            errors.append("legacy pairing handler survived active dispatcher")

    signatures = (
        "func application(_ application: UIApplication, open url: URL, sourceApplication: String?) -> Bool",
        "func application(_ application: UIApplication, open url: URL, sourceApplication: String?, annotation: Any) -> Bool",
        "func application(_ app: UIApplication, open url: URL, options: [UIApplication.OpenURLOptionsKey : Any] = [:]) -> Bool",
    )
    seen = 0
    for signature in signatures:
        block = scope(signature)
        if block is None:
            continue
        seen += 1
        if block.count("self.handleJerkgramExternalUrl(url)") != 1:
            errors.append(f"URL entrypoint missing exactly one shared dispatch: {signature}")
        if "self.openUrl(url: url)" in block and "self.handleJerkgramExternalUrl(url)" in block:
            if block.index("self.handleJerkgramExternalUrl(url)") > block.index("self.openUrl(url: url)"):
                errors.append(f"shared dispatch must precede generic openUrl: {signature}")
        if "options: [UIApplication.OpenURLOptionsKey : Any]" in signature:
            if "guard self.openUrlInProgress != url" not in block:
                errors.append("modern URL callback lost openUrlInProgress guard")
            elif block.index("self.handleJerkgramExternalUrl(url)") > block.index("guard self.openUrlInProgress != url"):
                errors.append("binding/click dispatch must precede modern openUrlInProgress guard")
    if seen == 0:
        errors.append("no external URL UIApplicationDelegate entrypoints found")

if errors:
    print("[jerkgram-push-binding-verify] FAIL")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("[jerkgram-push-binding-verify] PASS")
