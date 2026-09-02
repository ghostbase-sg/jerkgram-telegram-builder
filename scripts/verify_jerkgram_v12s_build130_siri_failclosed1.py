#!/usr/bin/env python3

import os
from pathlib import Path


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
TELEGRAM_UI_BUILD = ROOT / "submodules/TelegramUI/BUILD"
BRIDGE_HEADER = ROOT / "submodules/JerkgramSiriEntitlement/Sources/JerkgramSiriEntitlement.h"
BRIDGE_IMPLEMENTATION = ROOT / "submodules/JerkgramSiriEntitlement/Sources/JerkgramSiriEntitlement.m"
BRIDGE_SWIFT_PROBE = ROOT / "submodules/JerkgramSiriEntitlement/Sources/JerkgramSiriEntitlementSwiftProbe.swift"
BRIDGE_BUILD = ROOT / "submodules/JerkgramSiriEntitlement/BUILD"
MARKER = "// MARK: Jerkgram v1.2S BUILD130_SIRI_RUNTIME_FAILCLOSED1"
GATE = "buildConfig.isSiriEnabled && jerkgramHasRuntimeSiriEntitlement()"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[verify Build130 Siri fail-closed] " + message)


def balanced_region(text: str, token: str) -> str:
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
                return text[start:index + 1]
    raise RuntimeError("[verify Build130 Siri fail-closed] unbalanced owner: " + token)


def verify_app_delegate(text: str) -> None:
    require(text.count(MARKER) == 1, "Build130 helper marker count")
    require(text.count("import JerkgramSiriEntitlement") == 1, "Siri bridge import count")
    require("import Security" not in text, "Swift Security import must not bypass the bridge")
    helper = balanced_region(text, "private func jerkgramHasRuntimeSiriEntitlement() -> Bool")
    for token in (
        "return JerkgramHasRuntimeSiriEntitlement()",
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
    for path in (APP_DELEGATE, TELEGRAM_UI_BUILD, BRIDGE_HEADER, BRIDGE_IMPLEMENTATION, BRIDGE_SWIFT_PROBE, BRIDGE_BUILD):
        require(path.is_file(), "missing source owner: " + str(path))
    app_delegate = APP_DELEGATE.read_text(encoding="utf-8")
    verify_app_delegate(app_delegate)
    bridge = BRIDGE_IMPLEMENTATION.read_text(encoding="utf-8")
    for token in (
        "#import <Security/SecTask.h>",
        "SecTaskCreateFromSelf(kCFAllocatorDefault)",
        'CFSTR("com.apple.developer.siri")',
        "CFGetTypeID(value) == CFBooleanGetTypeID()",
        "CFBooleanGetValue((CFBooleanRef)value)",
        "CFRelease(value)",
        "CFRelease(error)",
        "CFRelease(task)",
    ):
        require(token in bridge, "bridge runtime entitlement invariant missing: " + token)
    for forbidden in ("TeamIdentifier", "team-identifier", "application-identifier", "bundleIdentifier", "signingIdentity"):
        require(forbidden not in bridge, "bridge signer-specific input: " + forbidden)
    build = TELEGRAM_UI_BUILD.read_text(encoding="utf-8")
    require("swift_library(" in build and 'name = "TelegramUI"' in build, "TelegramUI Bazel owner drifted")
    require(build.count('"//submodules/JerkgramSiriEntitlement:JerkgramSiriEntitlement",') == 1, "TelegramUI bridge dependency missing or ambiguous")
    bridge_build = BRIDGE_BUILD.read_text(encoding="utf-8")
    require("objc_library(" in bridge_build and 'module_name = "JerkgramSiriEntitlement"' in bridge_build, "bridge Bazel target drifted")
    require('"Security"' in bridge_build, "bridge Security framework dependency missing")
    require('name = "JerkgramSiriEntitlementSwiftProbe"' in bridge_build, "bridge Swift compile probe missing")
    require("import JerkgramSiriEntitlement" in BRIDGE_SWIFT_PROBE.read_text(encoding="utf-8"), "bridge Swift probe import missing")
    print("[verify Build130 Siri fail-closed] SOURCE VERIFIED")


if __name__ == "__main__":
    main()
