#!/usr/bin/env python3
"""Extend the existing GhostBase v1.0E.1 native APNs type-1 probe.

This patch intentionally runs after WebPush/binding verifiers and after the
Build140 identity overlay. It does not add another registerDevice interceptor;
it augments the already-materialized v1.0E.1 counters and appends a Type1
section to the existing Copy Extension Diagnostics report.
"""

from pathlib import Path
import re
import sys


ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
REGISTER_REL = Path("submodules/TelegramCore/Sources/TelegramEngine/AccountData/RegisterNotificationToken.swift")
BUILD_CONFIG_REL = Path("submodules/BuildConfig/Sources/BuildConfig.m")

SWIFT_MARKER = "// MARK: Jerkgram Native Push Type1 diagnostics v0.2"
OBJC_MARKER = "// MARK: Jerkgram Native Push Type1 diagnostics report v0.2"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[native-push-type1-probe] " + message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    require(count == 1, f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def patch_register_text(text: str) -> str:
    if SWIFT_MARKER in text:
        return text

    for required in (
        'ghostBaseRegisterDeviceKind = "Type1"',
        'ghostBaseRegisterDeviceKind = "Type9"',
        'registerDevice" + ghostBaseRegisterDeviceKind + "Request"',
        'registerDevice" + ghostBaseRegisterDeviceKind + "Success"',
        'registerDevice" + ghostBaseRegisterDeviceKind + "Invalidated"',
        'registerDevice" + ghostBaseRegisterDeviceKind + "Error"',
        'GhostBaseV10EPushProbeCore.set("LastRegisterDeviceError", error.errorDescription)',
        "public func _internal_registerJerkgramWebPushToken(",
        "tokenType: 10",
    ):
        require(required in text, "live v1.0E.1/WebPush prerequisite missing: " + required)

    text = replace_once(
        text,
        "        var keyData = Data()\n",
        "        var keyData = Data()\n"
        "        var jerkgramType1Encrypt = false\n",
        "Type1 encrypt state",
    )

    aps_pattern = re.compile(
        r"(?m)^(?P<indent>[ \t]*)case let \.aps\(encrypt\):\n"
        r"(?P=indent)    mappedType = 1\n"
        r"(?P=indent)    if encrypt \{\n"
    )
    aps_matches = list(aps_pattern.finditer(text))
    require(
        len(aps_matches) == 1,
        f"APS encrypt capture: expected exactly one structural match, found {len(aps_matches)}",
    )
    aps_match = aps_matches[0]
    aps_indent = aps_match.group("indent")
    aps_replacement = (
        f"{aps_indent}case let .aps(encrypt):\n"
        f"{aps_indent}    mappedType = 1\n"
        f"{aps_indent}    jerkgramType1Encrypt = encrypt\n"
        f"{aps_indent}    if encrypt {{\n"
    )
    text = text[:aps_match.start()] + aps_replacement + text[aps_match.end():]

    typed_request = (
        '        GhostBaseV10EPushProbeCore.record("registerDevice" + '
        'ghostBaseRegisterDeviceKind + "Request")\n'
    )
    text = replace_once(
        text,
        typed_request,
        typed_request
        + '        if mappedType == 1 {\n'
        + '            GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType1Sandbox", sandbox ? "true" : "false")\n'
        + '            GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType1Encrypt", jerkgramType1Encrypt ? "true" : "false")\n'
        + '            GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType1SecretLength", "\\(keyData.count)")\n'
        + '            GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType1OtherUidsCount", "\\(otherAccountUserIds.count)")\n'
        + '            GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType1Error", "none")\n'
        + '            GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType1ErrorCode", "none")\n'
        + '            GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType1Timestamp", "\\(Int(Date().timeIntervalSince1970))")\n'
        + '        }\n',
        "Type1 request metadata",
    )

    typed_success = (
        '            GhostBaseV10EPushProbeCore.record("registerDevice" + '
        'ghostBaseRegisterDeviceKind + "Success")\n'
    )
    text = replace_once(
        text,
        typed_success,
        typed_success
        + '            if mappedType == 1 {\n'
        + '                GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType1Error", "none")\n'
        + '                GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType1ErrorCode", "none")\n'
        + '                GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType1Timestamp", "\\(Int(Date().timeIntervalSince1970))")\n'
        + '            }\n',
        "Type1 success result",
    )

    generic_error = (
        '            GhostBaseV10EPushProbeCore.set("LastRegisterDeviceError", '
        'error.errorDescription)\n'
    )
    text = replace_once(
        text,
        generic_error,
        generic_error
        + '            if mappedType == 1 {\n'
        + '                GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType1Error", error.errorDescription)\n'
        + '                GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType1ErrorCode", "\\(error.errorCode)")\n'
        + '                GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType1Timestamp", "\\(Int(Date().timeIntervalSince1970))")\n'
        + '            }\n',
        "Type1 RPC result",
    )

    marker_anchor = '    GhostBaseV10EPushProbeCore.record("registerDeviceEntry")\n'
    text = replace_once(
        text,
        marker_anchor,
        SWIFT_MARKER + "\n" + marker_anchor,
        "Type1 marker",
    )

    require('if error.errorDescription == "TOKEN_WAS_INVALIDATED"' in text, "invalidated semantics missing")
    require("return .single(false)" in text, "invalidated false return missing")
    require("return .single(true)" in text, "generic error true return missing")
    return text


NATIVE_REPORT_HELPER = r"""
// MARK: Jerkgram Native Push Type1 diagnostics report v0.2
static NSString *JerkgramNativePushType1Diagnostics(void) {
    NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
    NSString *prefix = @"GhostBase.V10E.Push.";

    NSInteger apnsRegisteredCount = [defaults integerForKey:[prefix stringByAppendingString:@"didRegisterDeviceToken.Count"]];
    NSInteger requestCount = [defaults integerForKey:[prefix stringByAppendingString:@"registerDeviceType1Request.Count"]];
    NSInteger successCount = [defaults integerForKey:[prefix stringByAppendingString:@"registerDeviceType1Success.Count"]];
    NSInteger invalidatedCount = [defaults integerForKey:[prefix stringByAppendingString:@"registerDeviceType1Invalidated.Count"]];
    NSInteger errorCount = [defaults integerForKey:[prefix stringByAppendingString:@"registerDeviceType1Error.Count"]];
    NSInteger failureCount = invalidatedCount + errorCount;

    NSString *sandbox = [defaults stringForKey:[prefix stringByAppendingString:@"LastRegisterDeviceType1Sandbox"]] ?: @"none";
    NSString *encrypt = [defaults stringForKey:[prefix stringByAppendingString:@"LastRegisterDeviceType1Encrypt"]] ?: @"none";
    NSString *secretLength = [defaults stringForKey:[prefix stringByAppendingString:@"LastRegisterDeviceType1SecretLength"]] ?: @"none";
    NSString *otherUidsCount = [defaults stringForKey:[prefix stringByAppendingString:@"LastRegisterDeviceType1OtherUidsCount"]] ?: @"none";
    NSString *rpcCode = [defaults stringForKey:[prefix stringByAppendingString:@"LastRegisterDeviceType1ErrorCode"]] ?: @"none";
    NSString *rpcDescription = [defaults stringForKey:[prefix stringByAppendingString:@"LastRegisterDeviceType1Error"]] ?: @"none";
    NSString *timestamp = [defaults stringForKey:[prefix stringByAppendingString:@"LastRegisterDeviceType1Timestamp"]] ?: @"none";

    return [NSString stringWithFormat:
        @"\n\n=== Native Push Type1 ===\n"
         @"APNsRegistered: %@\n"
         @"Type1RequestCount: %ld\n"
         @"Type1SuccessCount: %ld\n"
         @"Type1FailureCount: %ld\n"
         @"Sandbox: %@\n"
         @"Encrypt: %@\n"
         @"SecretLength: %@\n"
         @"OtherUidsCount: %@\n"
         @"RPCCode: %@\n"
         @"RPCDescription: %@\n"
         @"Timestamp: %@\n",
        apnsRegisteredCount > 0 ? @"true" : @"false",
        (long)requestCount,
        (long)successCount,
        (long)failureCount,
        sandbox,
        encrypt,
        secretLength,
        otherUidsCount,
        rpcCode,
        rpcDescription,
        timestamp
    ];
}

"""


def patch_build_config_text(text: str) -> str:
    if OBJC_MARKER in text:
        return text

    for required in (
        "@implementation BuildConfig (JerkgramExtensionDiagnostics)",
        "+ (NSString *)jerkgramExtensionDiagnosticsReport {",
        'return @"{\\"schemaVersion\\":1,\\"error\\":\\"shared-container-unavailable\\"}";',
        'return [[NSString alloc] initWithData:json encoding:NSUTF8StringEncoding] ?: @"{}";',
    ):
        require(required in text, "BuildConfig diagnostics prerequisite missing: " + required)

    text = replace_once(
        text,
        "@implementation BuildConfig (JerkgramExtensionDiagnostics)\n",
        NATIVE_REPORT_HELPER + "@implementation BuildConfig (JerkgramExtensionDiagnostics)\n",
        "native Type1 report helper",
    )
    text = replace_once(
        text,
        '        return @"{\\"schemaVersion\\":1,\\"error\\":\\"shared-container-unavailable\\"}";',
        '        return [@"{\\"schemaVersion\\":1,\\"error\\":\\"shared-container-unavailable\\"}" stringByAppendingString:JerkgramNativePushType1Diagnostics()];',
        "shared-container early report",
    )
    text = replace_once(
        text,
        '    return [[NSString alloc] initWithData:json encoding:NSUTF8StringEncoding] ?: @"{}";',
        '    NSString *extensionReport = [[NSString alloc] initWithData:json encoding:NSUTF8StringEncoding] ?: @"{}";\n'
        '    return [extensionReport stringByAppendingString:JerkgramNativePushType1Diagnostics()];',
        "normal extension report",
    )
    return text


def apply_patch(root: Path) -> None:
    register_path = root / REGISTER_REL
    build_config_path = root / BUILD_CONFIG_REL
    for path in (register_path, build_config_path):
        require(path.is_file(), "missing materialized owner: " + str(path))

    register_path.write_text(
        patch_register_text(register_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    build_config_path.write_text(
        patch_build_config_text(build_config_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    print("[native-push-type1-probe] GREEN")
    print("  extended existing v1.0E.1 Type1 storage")
    print("  diagnostics owner: Copy Extension Diagnostics")


def main() -> None:
    apply_patch(ROOT)


if __name__ == "__main__":
    main()
