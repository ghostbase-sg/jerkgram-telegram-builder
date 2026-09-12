#!/usr/bin/env python3

from pathlib import Path
import sys


ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
REGISTER = ROOT / "submodules/TelegramCore/Sources/TelegramEngine/AccountData/RegisterNotificationToken.swift"
BUILD_CONFIG = ROOT / "submodules/BuildConfig/Sources/BuildConfig.m"
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

SWIFT_MARKER = "// MARK: Jerkgram Native Push Type1 diagnostics v0.1"
OBJC_MARKER = "// MARK: Jerkgram Native Push Type1 diagnostics report v0.1"

REPORT_MARKERS = (
    "=== Native Push Type1 ===",
    "APNsRegistered: %@",
    "Type1RequestCount: %ld",
    "Type1SuccessCount: %ld",
    "Type1FailureCount: %ld",
    "Sandbox: %@",
    "Encrypt: %@",
    "SecretLength: %@",
    "OtherUidsCount: %@",
    "RPCCode: %@",
    "RPCDescription: %@",
    "Timestamp: %@",
)


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[verify-native-push-type1] " + message)


def main() -> None:
    for path in (REGISTER, BUILD_CONFIG, SETTINGS):
        require(path.is_file(), "final materialized owner missing: " + str(path))

    register = REGISTER.read_text(encoding="utf-8")
    build_config = BUILD_CONFIG.read_text(encoding="utf-8")
    settings = SETTINGS.read_text(encoding="utf-8")

    require(register.count(SWIFT_MARKER) == 1, "Type1 Swift marker count")
    require(build_config.count(OBJC_MARKER) == 1, "Type1 BuildConfig marker count")

    for token in (
        'LastRegisterDeviceType1Sandbox',
        'LastRegisterDeviceType1Encrypt',
        'LastRegisterDeviceType1SecretLength',
        'LastRegisterDeviceType1OtherUidsCount',
        'LastRegisterDeviceType1ErrorCode',
        'LastRegisterDeviceType1Timestamp',
        'registerDevice" + ghostBaseRegisterDeviceKind + "Request"',
        'registerDevice" + ghostBaseRegisterDeviceKind + "Success"',
        'registerDevice" + ghostBaseRegisterDeviceKind + "Invalidated"',
        'registerDevice" + ghostBaseRegisterDeviceKind + "Error"',
        'error.errorCode',
        'error.errorDescription',
    ):
        require(token in register, "Type1 storage/result invariant missing: " + token)

    for marker in REPORT_MARKERS:
        require(build_config.count(marker) == 1, "final Copy Extension Diagnostics marker missing/ambiguous: " + marker)

    for key in (
        "didRegisterDeviceToken.Count",
        "registerDeviceType1Request.Count",
        "registerDeviceType1Success.Count",
        "registerDeviceType1Invalidated.Count",
        "registerDeviceType1Error.Count",
        "LastRegisterDeviceType1Sandbox",
        "LastRegisterDeviceType1Encrypt",
        "LastRegisterDeviceType1SecretLength",
        "LastRegisterDeviceType1OtherUidsCount",
        "LastRegisterDeviceType1ErrorCode",
        "LastRegisterDeviceType1Error",
        "LastRegisterDeviceType1Timestamp",
    ):
        require(key in build_config, "report storage key missing: " + key)

    require(
        "UIPasteboard.general.string = BuildConfig.jerkgramExtensionDiagnosticsReport()" in settings,
        "real Copy Extension Diagnostics action no longer copies BuildConfig report",
    )
    require(
        build_config.count("stringByAppendingString:JerkgramNativePushType1Diagnostics()") == 2,
        "Type1 diagnostics must survive both normal and shared-container-unavailable report paths",
    )

    register_scope_start = register.find("func _internal_registerNotificationToken(")
    register_scope_end = register.find("public func _internal_registerJerkgramWebPushToken(", register_scope_start)
    require(register_scope_start >= 0 and register_scope_end > register_scope_start, "native/WebPush register scope boundary missing")
    native_scope = register[register_scope_start:register_scope_end]
    require('if error.errorDescription == "TOKEN_WAS_INVALIDATED"' in native_scope, "stock invalidated branch missing")
    require("return .single(false)" in native_scope, "stock TOKEN_WAS_INVALIDATED false semantics missing")
    require("return .single(true)" in native_scope, "stock generic-error true semantics missing")

    for token in (
        "public enum JerkgramWebPushRegistrationResult",
        "public func _internal_registerJerkgramWebPushToken(",
        "public func _internal_unregisterJerkgramWebPushToken(",
        "tokenType: 10",
    ):
        require(token in register, "WebPush regression: missing " + token)

    helper_start = build_config.find(OBJC_MARKER)
    helper_end = build_config.find("@implementation BuildConfig (JerkgramExtensionDiagnostics)", helper_start)
    require(helper_start >= 0 and helper_end > helper_start, "native report helper scope missing")
    helper_scope = build_config[helper_start:helper_end]
    for forbidden in (
        "LastRegisterDeviceTokenLength",
        "hexString(token)",
        "p256dh",
        "canonicalToken",
        "rawBinding",
    ):
        require(forbidden not in helper_scope, "sensitive/raw diagnostic source leaked into report helper: " + forbidden)

    print("[verify-native-push-type1] GREEN")
    print("  final Copy Extension Diagnostics contains Type1 request/result/RPC markers")
    print("  WebPush type10 preserved; stock native registerDevice return semantics preserved")


if __name__ == "__main__":
    main()
