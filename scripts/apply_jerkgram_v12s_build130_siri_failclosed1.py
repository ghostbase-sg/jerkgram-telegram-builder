#!/usr/bin/env python3

import os
from pathlib import Path


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
MARKER = "// MARK: Jerkgram v1.2S BUILD130_SIRI_RUNTIME_FAILCLOSED1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build130 Siri fail-closed] " + message)


def balanced_region(text: str, token: str) -> tuple[int, int]:
    start = text.find(token)
    require(start >= 0, "missing owner: " + token)
    brace = text.find("{", start + len(token))
    require(brace >= 0, "missing opening brace: " + token)
    depth = 0
    for index in range(brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return start, index + 1
    raise RuntimeError("[Build130 Siri fail-closed] unbalanced owner: " + token)


HELPER = r'''// MARK: Jerkgram v1.2S BUILD130_SIRI_RUNTIME_FAILCLOSED1
private func jerkgramHasRuntimeSiriEntitlement() -> Bool {
    guard let task = SecTaskCreateFromSelf(nil) else {
        return false
    }
    var error: Unmanaged<CFError>?
    defer {
        error?.release()
    }
    guard let value = SecTaskCopyValueForEntitlement(task, "com.apple.developer.siri" as CFString, &error) else {
        return false
    }
    guard CFGetTypeID(value) == CFBooleanGetTypeID() else {
        return false
    }
    return CFBooleanGetValue(value as! CFBoolean)
}
'''


def patch_app_delegate(text: str) -> str:
    if MARKER in text:
        require(text.count(MARKER) == 1, "Build130 marker is ambiguous")
        return text
    require(text.count("import Intents") == 1, "Intents import owner is missing or ambiguous")
    require("import Security" not in text, "unexpected preexisting Security import")
    text = text.replace("import Intents", "import Intents\nimport Security", 1)
    insertion = text.index("\n", text.index("import Security")) + 1
    text = text[:insertion] + "\n" + HELPER + text[insertion:]

    request_start, request_end = balanced_region(text, "requestSiriAuthorization: { completion in")
    request = '''requestSiriAuthorization: { completion in
            if buildConfig.isSiriEnabled && jerkgramHasRuntimeSiriEntitlement() {
                if #available(iOS 10, *) {
                    INPreferences.requestSiriAuthorization { status in
                        if case .authorized = status {
                            completion(true)
                        } else {
                            completion(false)
                        }
                    }
                } else {
                    completion(false)
                }
            } else {
                completion(false)
            }
        }'''
    text = text[:request_start] + request + text[request_end:]

    siri_start, siri_end = balanced_region(text, "siriAuthorization: {")
    siri = '''siriAuthorization: {
            if buildConfig.isSiriEnabled && jerkgramHasRuntimeSiriEntitlement() {
                if #available(iOS 10, *) {
                    switch INPreferences.siriAuthorizationStatus() {
                    case .authorized:
                        return .allowed
                    case .denied, .restricted:
                        return .denied
                    case .notDetermined:
                        return .notDetermined
                    @unknown default:
                        return .notDetermined
                    }
                } else {
                    return .denied
                }
            } else {
                return .denied
            }
        }'''
    return text[:siri_start] + siri + text[siri_end:]


# Siri must not own public Settings/About rendering. Those views display the
# packaged app version directly; changing their source here made this security
# patch depend on stale UI anchors.
def patch_settings(text: str) -> str:
    return text


def patch_strings(text: str) -> str:
    return text

def main() -> None:
    require(APP_DELEGATE.is_file(), "missing source owner: " + str(APP_DELEGATE))
    APP_DELEGATE.write_text(patch_app_delegate(APP_DELEGATE.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build130 Siri fail-closed] GREEN")


if __name__ == "__main__":
    main()
