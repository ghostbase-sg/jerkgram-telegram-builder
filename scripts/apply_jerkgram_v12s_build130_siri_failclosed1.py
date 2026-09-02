#!/usr/bin/env python3

import os
from pathlib import Path


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
TELEGRAM_UI_BUILD = ROOT / "submodules/TelegramUI/BUILD"
BRIDGE_DIR = ROOT / "submodules/JerkgramSiriEntitlement"
BRIDGE_HEADER = BRIDGE_DIR / "Sources/JerkgramSiriEntitlement.h"
BRIDGE_IMPLEMENTATION = BRIDGE_DIR / "Sources/JerkgramSiriEntitlement.m"
BRIDGE_SWIFT_PROBE = BRIDGE_DIR / "Sources/JerkgramSiriEntitlementSwiftProbe.swift"
BRIDGE_BUILD = BRIDGE_DIR / "BUILD"
MARKER = "// MARK: Jerkgram v1.2S BUILD130_SIRI_RUNTIME_FAILCLOSED1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build130 Siri fail-closed] " + message)


def balanced_region(text: str, token: str) -> tuple[int, int]:
    start = text.find(token)
    require(start >= 0, "missing owner: " + token)
    # Both Siri binding tokens include their closure's opening brace. Starting
    # after the token would instead capture the nested `if #available` body.
    token_brace = token.rfind("{")
    brace = start + token_brace if token_brace >= 0 else text.find("{", start + len(token))
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
    return JerkgramHasRuntimeSiriEntitlement()
}
'''

BRIDGE_HEADER_CONTENT = '''#import <Foundation/Foundation.h>

FOUNDATION_EXPORT BOOL JerkgramHasRuntimeSiriEntitlement(void);
'''

BRIDGE_IMPLEMENTATION_CONTENT = '''#import "JerkgramSiriEntitlement.h"
#import <Security/SecTask.h>

BOOL JerkgramHasRuntimeSiriEntitlement(void) {
    SecTaskRef task = SecTaskCreateFromSelf(kCFAllocatorDefault);
    if (task == NULL) {
        return NO;
    }

    CFErrorRef error = NULL;
    CFTypeRef value = SecTaskCopyValueForEntitlement(task, CFSTR("com.apple.developer.siri"), &error);
    BOOL allowed = NO;
    if (value != NULL && CFGetTypeID(value) == CFBooleanGetTypeID()) {
        allowed = CFBooleanGetValue((CFBooleanRef)value) ? YES : NO;
    }

    if (value != NULL) {
        CFRelease(value);
    }
    if (error != NULL) {
        CFRelease(error);
    }
    CFRelease(task);
    return allowed;
}
'''

BRIDGE_SWIFT_PROBE_CONTENT = '''import JerkgramSiriEntitlement

let jerkgramSiriEntitlementSwiftProbe: Bool = JerkgramHasRuntimeSiriEntitlement()
'''

BRIDGE_BUILD_CONTENT = '''load("@build_bazel_rules_swift//swift:swift.bzl", "swift_library")

objc_library(
    name = "JerkgramSiriEntitlement",
    enable_modules = True,
    module_name = "JerkgramSiriEntitlement",
    srcs = ["Sources/JerkgramSiriEntitlement.m"],
    hdrs = ["Sources/JerkgramSiriEntitlement.h"],
    sdk_frameworks = [
        "Foundation",
        "Security",
    ],
    visibility = ["//visibility:public"],
)

swift_library(
    name = "JerkgramSiriEntitlementSwiftProbe",
    module_name = "JerkgramSiriEntitlementSwiftProbe",
    srcs = ["Sources/JerkgramSiriEntitlementSwiftProbe.swift"],
    deps = [":JerkgramSiriEntitlement"],
    visibility = ["//visibility:public"],
)
'''


def write_bridge(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_text(encoding="utf-8") == content, "bridge owner drifted: " + str(path))
    else:
        path.write_text(content, encoding="utf-8")


def patch_telegram_ui_build(text: str) -> str:
    dependency = '        "//submodules/JerkgramSiriEntitlement:JerkgramSiriEntitlement",\n'
    if dependency in text:
        require(text.count(dependency) == 1, "bridge Bazel dependency is ambiguous")
        return text
    anchor = '        "//submodules/BuildConfig:BuildConfig",\n'
    require(text.count(anchor) == 1, "TelegramUI BuildConfig dependency owner missing or ambiguous")
    return text.replace(anchor, anchor + dependency, 1)


def patch_app_delegate(text: str) -> str:
    if MARKER in text:
        require(text.count(MARKER) == 1, "Build130 marker is ambiguous")
        return text
    require(text.count("import Intents") == 1, "Intents import owner is missing or ambiguous")
    require("import Security" not in text, "unexpected preexisting Security import")
    require("import JerkgramSiriEntitlement" not in text, "unexpected preexisting bridge import")
    text = text.replace("import Intents", "import Intents\nimport JerkgramSiriEntitlement", 1)
    insertion = text.index("\n", text.index("import JerkgramSiriEntitlement")) + 1
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
    text = text[:siri_start] + siri + text[siri_end:]
    return text


def main() -> None:
    for path in (APP_DELEGATE, TELEGRAM_UI_BUILD):
        require(path.is_file(), "missing source owner: " + str(path))
    write_bridge(BRIDGE_HEADER, BRIDGE_HEADER_CONTENT)
    write_bridge(BRIDGE_IMPLEMENTATION, BRIDGE_IMPLEMENTATION_CONTENT)
    write_bridge(BRIDGE_SWIFT_PROBE, BRIDGE_SWIFT_PROBE_CONTENT)
    write_bridge(BRIDGE_BUILD, BRIDGE_BUILD_CONTENT)
    APP_DELEGATE.write_text(patch_app_delegate(APP_DELEGATE.read_text(encoding="utf-8")), encoding="utf-8")
    TELEGRAM_UI_BUILD.write_text(patch_telegram_ui_build(TELEGRAM_UI_BUILD.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build130 Siri fail-closed] GREEN")


if __name__ == "__main__":
    main()
