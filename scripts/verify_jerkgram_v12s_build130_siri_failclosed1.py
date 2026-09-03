#!/usr/bin/env python3

import os
from pathlib import Path


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
TELEGRAM_UI_BUILD = ROOT / "submodules/TelegramUI/BUILD"
MARKER = "// MARK: Jerkgram v1.2S BUILD130_SIRI_RUNTIME_FAILCLOSED1"
GATE = "buildConfig.isSiriEnabled && jerkgramHasRuntimeSiriEntitlement()"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[verify Build130 Siri fail-closed] " + message)


def balanced_region(text: str, token: str) -> str:
    start = text.find(token)
    require(start >= 0, "missing owner: " + token)
    brace = text.find("{", start)
    require(brace >= 0, "missing opening brace: " + token)
    depth = 0
    for index in range(brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise RuntimeError("[verify Build130 Siri fail-closed] unbalanced owner: " + token)


def verify_app_delegate(text: str) -> None:
    require(text.count(MARKER) == 1, "Build130 helper marker count")
    require(text.count("import Security") == 1, "Security import count")
    helper = balanced_region(text, "private func jerkgramHasRuntimeSiriEntitlement() -> Bool")
    for token in (
        "SecTaskCreateFromSelf(nil)",
        'SecTaskCopyValueForEntitlement(task, "com.apple.developer.siri" as CFString, &error)',
        "CFGetTypeID(value) == CFBooleanGetTypeID()",
        "CFBooleanGetValue(value as! CFBoolean)",
        "error?.release()",
    ):
        require(token in helper, "runtime helper invariant missing: " + token)
    for forbidden in ("TeamIdentifier", "team-identifier", "application-identifier", "bundleIdentifier", "signingIdentity"):
        require(forbidden not in helper, "signer-specific helper input: " + forbidden)

    request = balanced_region(text, "requestSiriAuthorization: { completion in")
    require(GATE in request, "request binding lacks combined compile-time/runtime gate")
    require("completion(false)" in request, "request binding lacks fail-closed completion")
    require(request.index(GATE) < request.index("INPreferences.requestSiriAuthorization"), "request Siri API is reachable before gate")

    status = balanced_region(text, "siriAuthorization: {")
    require(GATE in status, "status binding lacks combined compile-time/runtime gate")
    require("return .denied" in status, "status binding lacks fail-closed denied result")
    require(status.index(GATE) < status.index("INPreferences.siriAuthorizationStatus()"), "status Siri API is reachable before gate")
    for token in ("case .authorized:", "return .allowed", "case .denied, .restricted:", "case .notDetermined:", "@unknown default:"):
        require(token in status, "native Siri status mapping changed: " + token)


def main() -> None:
    for path in (APP_DELEGATE, TELEGRAM_UI_BUILD):
        require(path.is_file(), "missing source owner: " + str(path))
    verify_app_delegate(APP_DELEGATE.read_text(encoding="utf-8"))
    # Telegram's existing LocalAuth and WebUI Swift targets already import
    # Security without a manual sdk_frameworks list. TelegramUI follows that
    # project-owned Swift/Bazel convention; no speculative bridge is added.
    build = TELEGRAM_UI_BUILD.read_text(encoding="utf-8")
    require("swift_library(" in build and 'name = "TelegramUI"' in build, "TelegramUI Bazel owner drifted")
    print("[verify Build130 Siri fail-closed] SOURCE VERIFIED")


if __name__ == "__main__":
    main()
