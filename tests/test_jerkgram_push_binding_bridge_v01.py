from pathlib import Path
import json
import subprocess
import sys


PLIST = """<plist>\n<array>\n\t\t<dict>\n\t\t\t<key>CFBundleTypeRole</key>\n\t\t\t<string>Viewer</string>\n\t\t\t<key>CFBundleURLName</key>\n\t\t\t<string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>\n\t\t\t<key>CFBundleURLSchemes</key>\n\t\t\t<array>\n\t\t\t\t<string>telegram</string>\n\t\t\t</array>\n\t\t</dict>\n\t\t<dict>\n\t\t\t<key>CFBundleTypeRole</key>\n\t\t\t<string>Viewer</string>\n\t\t\t<key>CFBundleURLName</key>\n\t\t\t<string>$(PRODUCT_BUNDLE_IDENTIFIER).compatibility</string>\n\t\t\t<key>CFBundleURLSchemes</key>\n\t\t\t<array>\n\t\t\t\t<string>tg</string>\n\t\t\t\t<string>$(APP_SPECIFIC_URL_SCHEME)</string>\n\t\t\t</array>\n\t\t</dict>\n</array>\n</plist>\n"""

BUILD = """        <dict>\n            <key>CFBundleTypeRole</key>\n            <string>Viewer</string>\n            <key>CFBundleURLName</key>\n            <string>{telegram_bundle_id}</string>\n            <key>CFBundleURLSchemes</key>\n            <array>\n                <string>telegram</string>\n            </array>\n        </dict>\n        <dict>\n            <key>CFBundleTypeRole</key>\n            <string>Viewer</string>\n            <key>CFBundleURLName</key>\n            <string>{telegram_bundle_id}.compatibility</string>\n            <key>CFBundleURLSchemes</key>\n            <array>\n                <string>tg</string>\n            </array>\n        </dict>\n"""

APP_DELEGATE = """class AppDelegate {\n    private let sharedContextPromise = Promise<SharedApplicationContext>()\n    var mainWindow: Window1?\n\n    private func openChatWhenReady(accountId: AccountRecordId?, peerId: PeerId, threadId: Int64?, messageId: MessageId? = nil, activateInput: Bool = false, storyId: StoryId?, openAppIfAny: Bool = false, alwaysKeepMessageId: Bool = false) {}\n\n    func application(_ application: UIApplication, open url: URL, sourceApplication: String?, annotation: Any) -> Bool {\n        self.openUrl(url: url)\n        return true\n    }\n}\n"""

REGISTER_NOTIFICATION_TOKEN = """import Foundation\nimport SwiftSignalKit\nimport Postbox\nimport TelegramApi\n\npublic enum NotificationTokenType {\n    case aps(encrypt: Bool)\n    case voip\n}\n\nfunc _internal_unregisterNotificationToken(account: Account, token: Data, type: NotificationTokenType, otherAccountUserIds: [PeerId.Id]) -> Signal<Never, NoError> {\n    let mappedType: Int32\n    switch type {\n        case .aps:\n            mappedType = 1\n        case .voip:\n            mappedType = 9\n    }\n    return account.network.request(Api.functions.account.unregisterDevice(tokenType: mappedType, token: hexString(token), otherUids: [])) |> retryRequest |> ignoreValues\n}\n\nfunc _internal_registerNotificationToken(account: Account, token: Data, type: NotificationTokenType, sandbox: Bool, otherAccountUserIds: [PeerId.Id], excludeMutedChats: Bool) -> Signal<Bool, NoError> {\n    fatalError()\n}\n"""


def write_fixture(root: Path):
    app = root / "submodules/TelegramUI/Sources/AppDelegate.swift"
    info_bazel = root / "Telegram/Telegram-iOS/InfoBazel.plist"
    info = root / "Telegram/Telegram-iOS/Info.plist"
    build = root / "Telegram/BUILD"
    register = root / "submodules/TelegramCore/Sources/TelegramEngine/AccountData/RegisterNotificationToken.swift"
    for path in (app, info_bazel, info, build, register):
        path.parent.mkdir(parents=True, exist_ok=True)
    app.write_text(APP_DELEGATE)
    info_bazel.write_text(PLIST)
    info.write_text(PLIST)
    build.write_text(BUILD)
    register.write_text(REGISTER_NOTIFICATION_TOKEN)
    return app


def extract_function(text: str, signature: str) -> str:
    start = text.index(signature)
    brace = text.index("{", start)
    depth = 0
    for index in range(brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise AssertionError(f"unterminated function: {signature}")


def reference_accepts(payload: object) -> bool:
    if not isinstance(payload, dict) or set(payload) != {"v", "installationId", "subscription"}:
        return False
    if type(payload["v"]) is not int or payload["v"] != 1:
        return False
    installation_id = payload["installationId"]
    if not isinstance(installation_id, str) or installation_id.lower() != "123e4567-e89b-42d3-a456-426614174000":
        return False
    subscription = payload["subscription"]
    if not isinstance(subscription, dict) or set(subscription) != {"endpoint", "keys", "vapid"}:
        return False
    if subscription["vapid"] is not True:
        return False
    endpoint = subscription["endpoint"]
    if not isinstance(endpoint, str) or not endpoint.startswith("https://") or len(endpoint.encode()) > 4096:
        return False
    host = endpoint[8:].split("/", 1)[0]
    if not host:
        return False
    keys = subscription["keys"]
    if not isinstance(keys, dict) or set(keys) != {"p256dh", "auth"}:
        return False
    for name, maximum in (("p256dh", 256), ("auth", 128)):
        value = keys[name]
        if not isinstance(value, str) or not (1 <= len(value) <= maximum):
            return False
        if not all(c.isalnum() or c in "-_" for c in value):
            return False
    return True


def test_native_binding_bridge_is_strict_primary_account_only_and_preserves_click_bridge(tmp_path: Path):
    root = tmp_path / "telegram"
    app = write_fixture(root)

    click_patcher = Path(__file__).parents[1] / "scripts/apply_jerkgram_push_click_bridge_v01.py"
    click = subprocess.run([sys.executable, str(click_patcher), str(root)], capture_output=True, text=True)
    assert click.returncode == 0, click.stderr + click.stdout

    click_signature = "private func handleJerkgramPushUrl(_ url: URL) -> Bool"
    click_before = extract_function(app.read_text(), click_signature)

    binding_patcher = Path(__file__).parents[1] / "scripts/apply_jerkgram_push_binding_bridge_v01.py"
    first = subprocess.run([sys.executable, str(binding_patcher), str(root)], capture_output=True, text=True)
    assert first.returncode == 0, first.stderr + first.stdout

    swift = app.read_text()
    click_after = extract_function(swift, click_signature)
    assert click_after == click_before, "existing jerkgram://push/open helper changed"

    marker = "private func handleJerkgramPushBindingUrl(_ url: URL) -> Bool"
    assert swift.count(marker) == 1
    helper = extract_function(swift, marker)

    # Ownership and routing: only /register and /unregister are handled here; the
    # existing /open bridge remains the next dispatch target.
    assert 'url.scheme?.lowercased() == "jerkgram"' in helper
    assert 'url.host?.lowercased() == "push"' in helper
    assert 'url.path == "/register" || url.path == "/unregister"' in helper
    assert "url.absoluteString.utf8.count <= 8192" in helper
    assert "queryItems.allSatisfy({ $0.name == \"binding\" })" in helper
    assert "bindingItems.count == 1" in helper
    assert "rawBinding.count <= 7168" in helper
    assert 'case "A"..."Z", "a"..."z", "0"..."9", "-", "_"' in helper
    assert "decodedData.count <= 5376" in helper

    # Fail-closed JSON schema and type validation.
    assert 'Set(root.keys) == Set(["v", "installationId", "subscription"])' in helper
    assert "CFGetTypeID(version) != CFBooleanGetTypeID()" in helper
    assert "version.intValue == 1" in helper
    assert "UUID(uuidString: installationId)" in helper
    assert "installationId.lowercased() == uuid.uuidString.lowercased()" in helper
    assert 'Set(subscription.keys) == Set(["endpoint", "keys", "vapid"])' in helper
    assert "CFGetTypeID(vapid) == CFBooleanGetTypeID()" in helper
    assert "vapid.boolValue" in helper
    assert 'Set(keys.keys) == Set(["p256dh", "auth"])' in helper
    assert "endpoint.utf8.count <= 4096" in helper
    assert 'endpointComponents.scheme?.lowercased() == "https"' in helper
    assert "!(endpointComponents.host ?? \"\").isEmpty" in helper
    assert "p256dh.count <= 256" in helper
    assert "auth.count <= 128" in helper

    # Telegram receives canonical subscription JSON only, never installationId.
    assert 'let subscriptionObject: [String: Any] = [' in helper
    assert '"endpoint": endpoint' in helper
    assert '"keys": ["p256dh": p256dh, "auth": auth]' in helper
    assert '"vapid": true' in helper
    assert "JSONSerialization.data(withJSONObject: subscriptionObject, options: [.sortedKeys])" in helper
    assert "let canonicalToken = String(data: tokenData, encoding: .utf8)" in helper
    canonical_scope = helper[helper.index("let subscriptionObject"):helper.index("let _ = (self.sharedContextPromise.get()")]
    assert "installationId" not in canonical_scope

    # Native primary account is authoritative. PWA account identity is never read.
    assert "activeAccountContexts" in helper
    assert "guard let primary = activeAccounts.primary else" in helper
    assert "transaction.getPeer(primary.account.peerId)" in helper
    assert "as? TelegramUser" in helper
    assert "user?.username" in helper
    assert "[user.firstName, user.lastName]" in helper
    assert "user_id" not in helper
    assert "accountId" not in helper

    # Explicit action-specific confirmation precedes TelegramCore registration.
    assert 'Allow Jerkgram Notifications for \\(accountLabel)?' in helper
    assert 'Disconnect Jerkgram Notifications from \\(accountLabel)?' in helper
    assert 'UIAlertAction(title: "Connect", style: .default' in helper
    assert 'UIAlertAction(title: "Disconnect", style: .destructive' in helper
    assert "_internal_registerJerkgramWebPushToken(" in helper
    assert "excludeMutedChats: true" in helper
    assert "_internal_unregisterJerkgramWebPushToken(" in helper
    assert helper.index("UIAlertController(") < helper.index("_internal_registerJerkgramWebPushToken(")

    for copy in (
        "Jerkgram Notifications connected.",
        "Jerkgram Notifications disconnected.",
        "Could not connect Jerkgram Notifications. Try again.",
        "Could not disconnect Jerkgram Notifications. Try again.",
    ):
        assert copy in helper

    # The old auth-transfer architecture must not survive in the new handler.
    for forbidden in (
        "jerkgram://push/authorize",
        "approveAuthTransferToken",
        "activeSessions",
        "UserDefaults",
        "print(rawBinding)",
        "print(canonicalToken)",
        "debugPrint",
    ):
        assert forbidden not in helper

    dispatch = swift[swift.index("func application(_ application: UIApplication, open url: URL"):]
    assert dispatch.count("handleJerkgramPushBindingUrl(url)") == 1
    assert dispatch.index("handleJerkgramPushBindingUrl(url)") < dispatch.index("handleJerkgramPushUrl(url)") < dispatch.index("self.openUrl(url: url)")

    verifier = Path(__file__).parents[1] / "scripts/verify_jerkgram_push_binding_bridge_v01.py"
    verified = subprocess.run([sys.executable, str(verifier), str(root)], capture_output=True, text=True)
    assert verified.returncode == 0, verified.stderr + verified.stdout
    assert "PASS" in verified.stdout

    second = subprocess.run([sys.executable, str(binding_patcher), str(root)], capture_output=True, text=True)
    assert second.returncode == 0, second.stderr + second.stdout
    assert app.read_text() == swift


def test_rejection_matrix_matches_v1_contract():
    valid = {
        "v": 1,
        "installationId": "123e4567-e89b-42d3-a456-426614174000",
        "subscription": {
            "endpoint": "https://push.example.test/sub/abc",
            "keys": {"p256dh": "Abc_123-xyz", "auth": "Def_456-xyz"},
            "vapid": True,
        },
    }
    assert reference_accepts(valid)

    cases = []
    cases.append({**valid, "extra": True})
    cases.append({**valid, "v": True})
    cases.append({**valid, "v": 2})
    cases.append({**valid, "installationId": "not-a-uuid"})
    cases.append({**valid, "subscription": {**valid["subscription"], "extra": True}})
    cases.append({**valid, "subscription": {**valid["subscription"], "vapid": False}})
    cases.append({**valid, "subscription": {**valid["subscription"], "endpoint": "http://push.example.test/a"}})
    cases.append({**valid, "subscription": {**valid["subscription"], "endpoint": "https://"}})
    cases.append({**valid, "subscription": {**valid["subscription"], "keys": {**valid["subscription"]["keys"], "extra": "x"}}})
    cases.append({**valid, "subscription": {**valid["subscription"], "keys": {"p256dh": "bad+key", "auth": "ok"}}})
    cases.append({**valid, "subscription": {**valid["subscription"], "keys": {"p256dh": "ok", "auth": "bad/key"}}})
    cases.append({**valid, "subscription": {**valid["subscription"], "keys": {"p256dh": "A" * 257, "auth": "B"}}})
    cases.append({**valid, "subscription": {**valid["subscription"], "keys": {"p256dh": "A", "auth": "B" * 129}}})
    cases.append({**valid, "subscription": {**valid["subscription"], "endpoint": "https://e.test/" + "a" * 4097}})
    cases.append({**valid, "subscription": []})
    cases.append({**valid, "installationId": 42})

    for case in cases:
        assert not reference_accepts(case), json.dumps(case)[:200]
