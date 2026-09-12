#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
errors: list[str] = []


def scope(text: str, signature: str) -> str | None:
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


if not APP_DELEGATE.exists():
    errors.append(f"missing AppDelegate: {APP_DELEGATE}")
else:
    text = APP_DELEGATE.read_text()
    marker = "private func handleJerkgramNotificationsSessionPairingUrl(_ url: URL) -> Bool"
    helper = scope(text, marker)
    dispatcher = scope(text, "private func handleJerkgramExternalUrl(_ url: URL) -> Bool")

    if text.count(marker) != 1:
        errors.append(f"pairing handler count={text.count(marker)}, expected 1")
    if helper is None:
        errors.append("pairing handler missing or malformed")
    else:
        for required in (
            'url.scheme?.lowercased() == "jerkgram"',
            'url.host?.lowercased() == "push"',
            'url.path == "/authorize"',
            "url.absoluteString.utf8.count <= 2304",
            'queryItems.allSatisfy({ $0.name == "pair" || $0.name == "token" })',
            "pairItems.count == 1",
            "tokenItems.count == 1",
            "rawPairId.count >= 16",
            "rawPairId.count <= 128",
            "rawToken.count <= 1536",
            "tokenData.count <= 1024",
            "activeAccountContexts",
            "guard let primary = activeAccounts.primary else",
            "transaction.getPeer(primary.account.peerId)",
            "as? TelegramUser",
            'UIAlertAction(title: "Connect", style: .default',
            "approveAuthTransferToken(",
            "primary.engine.privacy.activeSessions()",
            "A separate Telegram session will be created",
            "full Telegram account session",
            "Connection request expired. Start again.",
            "Could not connect Jerkgram Notifications. Try again.",
            "self.window?.rootViewController?.present(",
        ):
            if required not in helper:
                errors.append(f"pairing helper missing invariant: {required}")

        for forbidden in (
            "UserDefaults",
            "print(rawToken)",
            "print(tokenData)",
            "print(rawPairId)",
            "debugPrint",
            "NSLog",
            "auth_key",
            "Postbox.copy",
            "self.mainWindow?.viewController?.present(",
        ):
            if forbidden in helper:
                errors.append(f"pairing helper contains forbidden marker: {forbidden}")

    if dispatcher is None:
        errors.append("shared Jerkgram URL dispatcher missing")
    else:
        pairing = "handleJerkgramNotificationsSessionPairingUrl(url)"
        binding = "handleJerkgramPushBindingUrl(url)"
        click = "handleJerkgramPushUrl(url)"
        for required in (pairing, binding, click):
            if dispatcher.count(required) != 1:
                errors.append(f"dispatcher count for {required} is {dispatcher.count(required)}, expected 1")
        if all(required in dispatcher for required in (pairing, binding, click)):
            if not (dispatcher.index(pairing) < dispatcher.index(binding) < dispatcher.index(click)):
                errors.append("dispatcher order must be session-pairing -> binding -> click")
        if "self.openUrl(url: url)" in dispatcher:
            errors.append("shared Jerkgram dispatcher must not call generic openUrl")

if errors:
    print("[jerkgram-notifications-session-pairing-verify] FAIL")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("[jerkgram-notifications-session-pairing-verify] PASS")
