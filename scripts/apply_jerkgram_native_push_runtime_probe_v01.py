#!/usr/bin/env python3
"""Instrument Telegram's native APNs registerDevice(type=1) without changing behavior.

The probe stores only non-sensitive metadata and the exact RPC result in
UserDefaults. It never stores the APNs token, notification encryption key, API
hash, or any other secret material.
"""

from pathlib import Path
import sys


MARKER = "JERKGRAM_NATIVE_PUSH_TYPE1_RUNTIME_PROBE_V01"
REGISTER_REL = Path("submodules/TelegramCore/Sources/TelegramEngine/AccountData/RegisterNotificationToken.swift")
APP_DELEGATE_REL = Path("submodules/TelegramUI/Sources/AppDelegate.swift")

RECORDER = r'''// JERKGRAM_NATIVE_PUSH_TYPE1_RUNTIME_PROBE_V01
private enum JerkgramNativePushRuntimeProbe {
    private static let defaults = UserDefaults.standard
    private static let prefix = "jerkgram.nativePush.type1."

    private static func set(_ value: Any?, _ key: String) {
        if let value = value {
            defaults.set(value, forKey: prefix + key)
        } else {
            defaults.removeObject(forKey: prefix + key)
        }
    }

    static func recordAttempt(tokenBytes: Int, sandbox: Bool, secretBytes: Int, otherUidsCount: Int, flags: Int32) {
        set("attempt", "phase")
        set(Date().timeIntervalSince1970, "timestamp")
        set(1, "mappedType")
        set(tokenBytes, "tokenBytes")
        set(sandbox, "sandbox")
        set(secretBytes, "secretBytes")
        set(otherUidsCount, "otherUidsCount")
        set(Int(flags), "flags")
        set(nil, "errorCode")
        set(nil, "errorDescription")
        defaults.synchronize()
    }

    static func recordSuccess() {
        set("success", "phase")
        set(Date().timeIntervalSince1970, "timestamp")
        set(nil, "errorCode")
        set(nil, "errorDescription")
        defaults.synchronize()
    }

    static func recordFailure(errorCode: Int32, errorDescription: String) {
        set("failure", "phase")
        set(Date().timeIntervalSince1970, "timestamp")
        set(Int(errorCode), "errorCode")
        set(errorDescription, "errorDescription")
        defaults.synchronize()
    }
}

'''

APP_HELPER = r'''    // JERKGRAM_NATIVE_PUSH_TYPE1_RUNTIME_PROBE_V01
    private func handleJerkgramNativePushDiagnosticUrl(_ url: URL) -> Bool {
        guard url.scheme?.lowercased() == "jerkgram",
              url.host?.lowercased() == "push",
              url.path == "/native-debug" else {
            return false
        }

        let defaults = UserDefaults.standard
        let prefix = "jerkgram.nativePush.type1."
        let phase = defaults.string(forKey: prefix + "phase") ?? "no-record"
        let mappedType = defaults.object(forKey: prefix + "mappedType") as? NSNumber
        let tokenBytes = defaults.object(forKey: prefix + "tokenBytes") as? NSNumber
        let sandbox = defaults.object(forKey: prefix + "sandbox") as? NSNumber
        let secretBytes = defaults.object(forKey: prefix + "secretBytes") as? NSNumber
        let otherUidsCount = defaults.object(forKey: prefix + "otherUidsCount") as? NSNumber
        let flags = defaults.object(forKey: prefix + "flags") as? NSNumber
        let errorCode = defaults.object(forKey: prefix + "errorCode") as? NSNumber
        let errorDescription = defaults.string(forKey: prefix + "errorDescription") ?? ""
        let timestamp = defaults.object(forKey: prefix + "timestamp") as? NSNumber

        var lines: [String] = ["Phase: \(phase)"]
        if let mappedType = mappedType { lines.append("Type: \(mappedType)") }
        if let tokenBytes = tokenBytes { lines.append("APNs token bytes: \(tokenBytes)") }
        if let sandbox = sandbox { lines.append("Sandbox: \(sandbox.boolValue)") }
        if let secretBytes = secretBytes { lines.append("Secret bytes: \(secretBytes)") }
        if let otherUidsCount = otherUidsCount { lines.append("Other UIDs: \(otherUidsCount)") }
        if let flags = flags { lines.append("Flags: \(flags)") }
        if let errorCode = errorCode {
            lines.append("RPC: \(errorCode) \(errorDescription)")
        } else if phase == "success" {
            lines.append("RPC: SUCCESS")
        }
        if let timestamp = timestamp {
            let date = Date(timeIntervalSince1970: timestamp.doubleValue)
            lines.append("Recorded: \(date)")
        }
        if phase == "no-record" {
            lines.append("Native APNs type1 registration has not been observed yet.")
        }

        let alert = UIAlertController(
            title: "Jerkgram Native Push",
            message: lines.joined(separator: "\n"),
            preferredStyle: .alert
        )
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        self.window?.rootViewController?.present(alert, animated: true)
        return true
    }

'''


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[native-push-type1-probe] " + message)


def patch_register_text(text: str) -> str:
    if MARKER in text:
        return text

    enum_anchor = "public enum NotificationTokenType {"
    require(text.count(enum_anchor) == 1, "NotificationTokenType anchor count")
    text = text.replace(enum_anchor, RECORDER + enum_anchor, 1)

    request_anchor = """        return account.network.request(Api.functions.account.registerDevice(flags: flags, tokenType: mappedType, token: hexString(token), appSandbox: sandbox ? .boolTrue : .boolFalse, secret: Buffer(data: keyData), otherUids: otherAccountUserIds.map({ $0._internalGetInt64Value() })))\n        |> map { _ -> Bool in\n            return true\n        }\n        |> `catch` { error -> Signal<Bool, NoError> in\n            if error.errorDescription == \"TOKEN_WAS_INVALIDATED\" {\n                return .single(false)\n            } else {\n                return .single(true)\n            }\n        }\n"""
    replacement = """        if mappedType == 1 {\n            JerkgramNativePushRuntimeProbe.recordAttempt(\n                tokenBytes: token.count,\n                sandbox: sandbox,\n                secretBytes: keyData.count,\n                otherUidsCount: otherAccountUserIds.count,\n                flags: flags\n            )\n        }\n        return account.network.request(Api.functions.account.registerDevice(flags: flags, tokenType: mappedType, token: hexString(token), appSandbox: sandbox ? .boolTrue : .boolFalse, secret: Buffer(data: keyData), otherUids: otherAccountUserIds.map({ $0._internalGetInt64Value() })))\n        |> map { _ -> Bool in\n            if mappedType == 1 {\n                JerkgramNativePushRuntimeProbe.recordSuccess()\n            }\n            return true\n        }\n        |> `catch` { error -> Signal<Bool, NoError> in\n            if mappedType == 1 {\n                JerkgramNativePushRuntimeProbe.recordFailure(\n                    errorCode: error.errorCode,\n                    errorDescription: error.errorDescription\n                )\n            }\n            if error.errorDescription == \"TOKEN_WAS_INVALIDATED\" {\n                return .single(false)\n            } else {\n                return .single(true)\n            }\n        }\n"""
    require(text.count(request_anchor) == 1, "stock registerDevice pipeline anchor count")
    text = text.replace(request_anchor, replacement, 1)

    for invariant in (
        MARKER,
        '"jerkgram.nativePush.type1."',
        "mappedType == 1",
        "recordAttempt(",
        "tokenBytes: token.count",
        "secretBytes: keyData.count",
        "otherUidsCount: otherAccountUserIds.count",
        "recordSuccess()",
        "recordFailure(",
        "error.errorCode",
        "error.errorDescription",
        'if error.errorDescription == "TOKEN_WAS_INVALIDATED"',
    ):
        require(invariant in text, "missing register invariant: " + invariant)

    recorder = text[text.index("private enum JerkgramNativePushRuntimeProbe"):text.index(enum_anchor)]
    for forbidden in ("hexString(token)", "masterKey.data", "keyData.base64"):
        require(forbidden not in recorder, "sensitive recorder marker: " + forbidden)
    return text


def patch_app_delegate_text(text: str) -> str:
    helper_marker = "private func handleJerkgramNativePushDiagnosticUrl(_ url: URL) -> Bool"
    if helper_marker not in text:
        binding_anchor = "    private func handleJerkgramPushBindingUrl(_ url: URL) -> Bool"
        require(text.count(binding_anchor) == 1, "push binding helper anchor count")
        text = text.replace(binding_anchor, APP_HELPER + binding_anchor, 1)

    dispatch_anchor = """    private func handleJerkgramExternalUrl(_ url: URL) -> Bool {\n        if self.handleJerkgramPushBindingUrl(url) {\n            return true\n        }\n        if self.handleJerkgramPushUrl(url) {\n            return true\n        }\n        return false\n    }\n"""
    dispatch_replacement = """    private func handleJerkgramExternalUrl(_ url: URL) -> Bool {\n        if self.handleJerkgramNativePushDiagnosticUrl(url) {\n            return true\n        }\n        if self.handleJerkgramPushBindingUrl(url) {\n            return true\n        }\n        if self.handleJerkgramPushUrl(url) {\n            return true\n        }\n        return false\n    }\n"""
    if "if self.handleJerkgramNativePushDiagnosticUrl(url)" not in text:
        require(text.count(dispatch_anchor) == 1, "shared external URL dispatcher anchor count")
        text = text.replace(dispatch_anchor, dispatch_replacement, 1)

    for invariant in (
        helper_marker,
        'url.path == "/native-debug"',
        'title: "Jerkgram Native Push"',
        '"jerkgram.nativePush.type1."',
        'lines.append("RPC: \\(errorCode) \\(errorDescription)")',
        "if self.handleJerkgramNativePushDiagnosticUrl(url)",
        "if self.handleJerkgramPushBindingUrl(url)",
        "if self.handleJerkgramPushUrl(url)",
    ):
        require(invariant in text, "missing AppDelegate invariant: " + invariant)

    dispatcher = text[text.index("private func handleJerkgramExternalUrl"):]
    require(
        dispatcher.index("handleJerkgramNativePushDiagnosticUrl")
        < dispatcher.index("handleJerkgramPushBindingUrl")
        < dispatcher.index("handleJerkgramPushUrl"),
        "external URL dispatch order",
    )
    return text


def apply_patch(root: Path) -> None:
    register_path = root / REGISTER_REL
    app_delegate_path = root / APP_DELEGATE_REL
    require(register_path.is_file(), "missing " + str(register_path))
    require(app_delegate_path.is_file(), "missing " + str(app_delegate_path))

    register_text = register_path.read_text(encoding="utf-8")
    app_text = app_delegate_path.read_text(encoding="utf-8")
    register_path.write_text(patch_register_text(register_text), encoding="utf-8")
    app_delegate_path.write_text(patch_app_delegate_text(app_text), encoding="utf-8")
    print("[native-push-type1-probe] GREEN")
    print("  register:", register_path)
    print("  diagnostics: jerkgram://push/native-debug")


def main() -> None:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    apply_patch(root)


if __name__ == "__main__":
    main()
