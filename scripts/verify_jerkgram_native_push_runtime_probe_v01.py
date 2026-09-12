#!/usr/bin/env python3
"""Final materialized-source gate for native APNs registration + type-1 diagnostics."""

from pathlib import Path
import sys


ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
REGISTER = ROOT / "submodules/TelegramCore/Sources/TelegramEngine/AccountData/RegisterNotificationToken.swift"
BUILD_CONFIG = ROOT / "submodules/BuildConfig/Sources/BuildConfig.m"
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

SWIFT_MARKER = "// MARK: Jerkgram Native Push Type1 diagnostics v0.2"
OBJC_MARKER = "// MARK: Jerkgram Native Push Type1 diagnostics report v0.3"

REPORT_MARKERS = (
    "=== Native Push APNs Registration ===",
    "NotificationSettingsReadCount: %ld",
    "AuthorizationGrantedCount: %ld",
    "AuthorizationDeniedCount: %ld",
    "RegisterForRemoteNotificationsCount: %ld",
    "InvalidationRegisterCount: %ld",
    "DidRegisterTokenCount: %ld",
    "DidFailTokenCount: %ld",
    "DeviceTokenLength: %@",
    "AuthorizationStatus: %@",
    "LastRegisterFail: %@",
    "=== Native Push Type1 ===",
    "APNsRegistered: %@",
    "Type1EntryCount: %ld",
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


def verify_texts(register: str, build_config: str, settings: str) -> None:
    require(register.count(SWIFT_MARKER) == 1, "Type1 Swift marker must survive exactly once")
    require(build_config.count(OBJC_MARKER) == 1, "Type1 report marker must survive exactly once")

    for required in (
        'ghostBaseRegisterDeviceKind = "Type1"',
        'registerDevice" + ghostBaseRegisterDeviceKind + "Request"',
        'registerDevice" + ghostBaseRegisterDeviceKind + "Success"',
        'registerDevice" + ghostBaseRegisterDeviceKind + "Invalidated"',
        'registerDevice" + ghostBaseRegisterDeviceKind + "Error"',
        'LastRegisterDeviceType1Sandbox',
        'LastRegisterDeviceType1Encrypt',
        'LastRegisterDeviceType1SecretLength',
        'LastRegisterDeviceType1OtherUidsCount',
        'LastRegisterDeviceType1ErrorCode',
        'LastRegisterDeviceType1Error", error.errorDescription',
        "error.errorCode",
        'if error.errorDescription == "TOKEN_WAS_INVALIDATED"',
        "return .single(false)",
        "return .single(true)",
        "public func _internal_registerJerkgramWebPushToken(",
        "tokenType: 10",
    ):
        require(required in register, "final RegisterNotificationToken invariant missing: " + required)

    for marker in REPORT_MARKERS:
        require(marker in build_config, "Copy Extension Diagnostics marker missing: " + marker)

    for required in (
        'notificationSettingsRead.Count',
        'requestAuthorizationTrue.Count',
        'requestAuthorizationFalse.Count',
        'authorizedRegisterForRemoteNotifications.Count',
        'invalidationRegisterForRemoteNotifications.Count',
        'didRegisterDeviceToken.Count',
        'didFailRegisterDeviceToken.Count',
        'LastDeviceTokenLength',
        'LastAuthorizationStatus',
        'LastRegisterFail',
        'registerDeviceType1Entry.Count',
    ):
        require(required in build_config, "APNs registration diagnostic source missing: " + required)

    require(
        build_config.count("stringByAppendingString:JerkgramNativePushType1Diagnostics()") == 2,
        "native push report must be appended on normal and shared-container-error paths",
    )

    for required in (
        'case "copyExtensionDiagnostics":',
        "UIPasteboard.general.string = BuildConfig.jerkgramExtensionDiagnosticsReport()",
    ):
        require(required in settings, "real Copy Extension Diagnostics owner missing: " + required)

    require("LastRegisterDeviceType1Token" not in register, "raw Type1 token diagnostic key is forbidden")
    require("LastRegisterDeviceType1Secret\"" not in register, "raw Type1 secret diagnostic key is forbidden")

    report_start = build_config.index(OBJC_MARKER)
    report_end = build_config.index("@implementation BuildConfig (JerkgramExtensionDiagnostics)", report_start)
    report_helper = build_config[report_start:report_end]
    for forbidden in ("hexString(token)", "p256dh", "canonicalToken", "rawBinding", "api_hash"):
        require(forbidden not in report_helper, "sensitive material leaked into report helper: " + forbidden)


def main() -> None:
    for path in (REGISTER, BUILD_CONFIG, SETTINGS):
        require(path.is_file(), "final materialized owner missing: " + str(path))

    verify_texts(
        REGISTER.read_text(encoding="utf-8"),
        BUILD_CONFIG.read_text(encoding="utf-8"),
        SETTINGS.read_text(encoding="utf-8"),
    )
    print("[verify-native-push-type1] FINAL MATERIALIZED SOURCE GREEN")
    print("[verify-native-push-type1] Copy Extension Diagnostics contains APNs registration + Type1 entry/request/result diagnostics")


if __name__ == "__main__":
    main()
