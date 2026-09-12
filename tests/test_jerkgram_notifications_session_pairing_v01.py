from pathlib import Path
import subprocess
import sys


APP_DELEGATE = """class AppDelegate {\n    private let sharedContextPromise = Promise<SharedApplicationContext>()\n    var window: Window?\n\n    private func handleJerkgramPushBindingUrl(_ url: URL) -> Bool {\n        return false\n    }\n\n    private func handleJerkgramPushUrl(_ url: URL) -> Bool {\n        return false\n    }\n\n    private func handleJerkgramExternalUrl(_ url: URL) -> Bool {\n        if self.handleJerkgramPushBindingUrl(url) {\n            return true\n        }\n        if self.handleJerkgramPushUrl(url) {\n            return true\n        }\n        return false\n    }\n\n    func application(_ application: UIApplication, open url: URL, sourceApplication: String?, annotation: Any) -> Bool {\n        if self.handleJerkgramExternalUrl(url) {\n            return true\n        }\n        self.openUrl(url: url)\n        return true\n    }\n}\n"""


def extract_function(text: str, signature: str) -> str:
    start = text.index(signature)
    brace = text.index("{", start)
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
    raise AssertionError("unterminated function")


def test_notifications_session_pairing_is_strict_explicit_and_idempotent(tmp_path: Path):
    root = tmp_path / "telegram"
    app = root / "submodules/TelegramUI/Sources/AppDelegate.swift"
    app.parent.mkdir(parents=True)
    app.write_text(APP_DELEGATE)

    patcher = Path(__file__).parents[1] / "scripts/apply_jerkgram_notifications_session_pairing_v01.py"
    first = subprocess.run([sys.executable, str(patcher), str(root)], capture_output=True, text=True)
    assert first.returncode == 0, first.stderr + first.stdout

    swift = app.read_text()
    signature = "private func handleJerkgramNotificationsSessionPairingUrl(_ url: URL) -> Bool"
    assert swift.count(signature) == 1
    helper = extract_function(swift, signature)

    assert 'url.scheme?.lowercased() == "jerkgram"' in helper
    assert 'url.host?.lowercased() == "push"' in helper
    assert 'url.path == "/authorize"' in helper
    assert "url.absoluteString.utf8.count <= 2304" in helper
    assert 'queryItems.allSatisfy({ $0.name == "pair" || $0.name == "token" })' in helper
    assert "pairItems.count == 1" in helper
    assert "tokenItems.count == 1" in helper
    assert "rawPairId.count >= 16" in helper
    assert "rawPairId.count <= 128" in helper
    assert "rawToken.count <= 1536" in helper
    assert "tokenData.count <= 1024" in helper
    assert 'case "A"..."Z", "a"..."z", "0"..."9", "-", "_"' in helper

    assert "activeAccountContexts" in helper
    assert "guard let primary = activeAccounts.primary else" in helper
    assert "transaction.getPeer(primary.account.peerId)" in helper
    assert "as? TelegramUser" in helper
    assert "user?.username" in helper
    assert "[user.firstName, user.lastName]" in helper

    assert 'UIAlertAction(title: "Connect", style: .default' in helper
    assert "approveAuthTransferToken(" in helper
    assert "primary.engine.privacy.activeSessions()" in helper
    assert helper.index('UIAlertAction(title: "Connect", style: .default') < helper.index("approveAuthTransferToken(")
    assert "A separate Telegram session will be created" in helper
    assert "full Telegram account session" in helper
    assert "Connection request expired. Start again." in helper
    assert "Could not connect Jerkgram Notifications. Try again." in helper
    assert "self.window?.rootViewController?.present(" in helper
    assert "self.mainWindow?.viewController?.present(" not in helper

    for forbidden in (
        "UserDefaults",
        "print(rawToken)",
        "print(tokenData)",
        "print(rawPairId)",
        "debugPrint",
        "NSLog",
        "auth_key",
        "Keychain",
        "Postbox.copy",
    ):
        assert forbidden not in helper

    dispatcher = extract_function(swift, "private func handleJerkgramExternalUrl(_ url: URL) -> Bool")
    assert dispatcher.count("handleJerkgramNotificationsSessionPairingUrl(url)") == 1
    assert dispatcher.index("handleJerkgramNotificationsSessionPairingUrl(url)") < dispatcher.index("handleJerkgramPushBindingUrl(url)") < dispatcher.index("handleJerkgramPushUrl(url)")

    verifier = Path(__file__).parents[1] / "scripts/verify_jerkgram_notifications_session_pairing_v01.py"
    verified = subprocess.run([sys.executable, str(verifier), str(root)], capture_output=True, text=True)
    assert verified.returncode == 0, verified.stderr + verified.stdout
    assert "PASS" in verified.stdout

    second = subprocess.run([sys.executable, str(patcher), str(root)], capture_output=True, text=True)
    assert second.returncode == 0, second.stderr + second.stdout
    assert app.read_text() == swift
