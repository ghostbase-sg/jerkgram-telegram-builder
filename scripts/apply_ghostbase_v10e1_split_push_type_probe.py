#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"
BASE = ROOT / "scripts/apply_ghostbase_v10e_main_push_probe.py"


def read(path):
    return Path(path).read_text()


def write(path, text):
    Path(path).write_text(text)


def ensure(text, needle, label):
    if needle not in text:
        raise SystemExit(f"[v1.0E.1] ERROR: missing {label}: {needle}")


def replace_once(text, old, new, label):
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    raise SystemExit(f"[v1.0E.1] ERROR: pattern not found: {label}")


print("[v1.0E.1] running base v1.0E patcher...")
subprocess.check_call([sys.executable, str(BASE)], cwd=str(ROOT))

reg_p = SRC / "submodules/TelegramCore/Sources/TelegramEngine/AccountData/RegisterNotificationToken.swift"
helper_p = SRC / "submodules/TelegramCore/Sources/TelegramEngine/AccountData/GhostBaseV10EPushProbeCore.swift"
app_p = SRC / "submodules/TelegramUI/Sources/AppDelegate.swift"
settings_p = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

reg = read(reg_p)
helper = read(helper_p)
app = read(app_p)
settings = read(settings_p)

ensure(reg, 'GhostBaseV10EPushProbeCore.record("registerDeviceEntry")', "base registerDeviceEntry")
ensure(helper, "enum GhostBaseV10EPushProbeCore", "core helper")
ensure(settings, "Main Push Registration Probe", "settings section")

if "static func recordType1Request" not in helper:
    extra = r'''
    private static func incrementDedicated(_ key: String) {
        let defaults = UserDefaults.standard
        let fullKey = "GhostBase.V10E.Push." + key
        defaults.set(defaults.integer(forKey: fullKey) + 1, forKey: fullKey)
    }

    static func recordType1Request(sandbox: Bool, encrypt: Bool, secretLength: Int, otherUidsCount: Int) {
        incrementDedicated("Type1RequestCount")
        set("Type1AppSandbox", sandbox ? "true" : "false")
        set("Type1Encrypt", encrypt ? "true" : "false")
        set("Type1SecretLength", "\(secretLength)")
        set("Type1OtherUidsCount", "\(otherUidsCount)")
        set("Type1LastErrorCode", "none")
        set("Type1LastErrorDescription", "none")
    }

    static func recordType1Success() {
        incrementDedicated("Type1SuccessCount")
        set("Type1LastErrorCode", "none")
        set("Type1LastErrorDescription", "none")
    }

    static func recordType1Failure(errorCode: Int32, errorDescription: String) {
        incrementDedicated("Type1FailureCount")
        set("Type1LastErrorCode", "\(errorCode)")
        set("Type1LastErrorDescription", errorDescription)
    }

    static func updateTypeSummary(lastType: Int32, kind: String) {
        let defaults = UserDefaults.standard
        let prefix = "GhostBase.V10E.Push."
        let t1r = defaults.integer(forKey: prefix + "Type1RequestCount")
        let t1s = defaults.integer(forKey: prefix + "Type1SuccessCount")
        let t1f = defaults.integer(forKey: prefix + "Type1FailureCount")
        let sandbox = defaults.string(forKey: prefix + "Type1AppSandbox") ?? "none"
        let encrypt = defaults.string(forKey: prefix + "Type1Encrypt") ?? "none"
        let secretLength = defaults.string(forKey: prefix + "Type1SecretLength") ?? "none"
        let otherUids = defaults.string(forKey: prefix + "Type1OtherUidsCount") ?? "none"
        let errorCode = defaults.string(forKey: prefix + "Type1LastErrorCode") ?? "none"
        let errorDescription = defaults.string(forKey: prefix + "Type1LastErrorDescription") ?? "none"
        let type9Requests = defaults.integer(forKey: prefix + "registerDeviceType9Request.Count")
        let type9Success = defaults.integer(forKey: prefix + "registerDeviceType9Success.Count")
        let type9Errors = defaults.integer(forKey: prefix + "registerDeviceType9Error.Count")
        set("LastRegisterDeviceType", "last=\(lastType)/\(kind); Type1 R/S/F=\(t1r)/\(t1s)/\(t1f) sandbox=\(sandbox) encrypt=\(encrypt) secretLen=\(secretLength) otherUids=\(otherUids) rpc=\(errorCode):\(errorDescription); Type9 R/S/E=\(type9Requests)/\(type9Success)/\(type9Errors)")
    }
'''
    idx = helper.rfind("\n}")
    if idx < 0:
        raise SystemExit("[v1.0E.1] ERROR: helper enum end not found")
    helper = helper[:idx] + extra + helper[idx:]
    write(helper_p, helper)

if "let ghostBaseRegisterDeviceKind: String" not in reg:
    reg = replace_once(reg,
        '    GhostBaseV10EPushProbeCore.record("registerDeviceEntry")\n',
        '''    let ghostBaseRegisterDeviceKind: String
    let ghostBaseRegisterDeviceEncrypt: Bool
    switch type {
    case let .aps(encrypt):
        ghostBaseRegisterDeviceKind = "Type1"
        ghostBaseRegisterDeviceEncrypt = encrypt
    case .voip:
        ghostBaseRegisterDeviceKind = "Type9"
        ghostBaseRegisterDeviceEncrypt = false
    }

    GhostBaseV10EPushProbeCore.record("registerDeviceEntry")
    GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Entry")
    GhostBaseV10EPushProbeCore.set("LastRegisterDeviceKind", ghostBaseRegisterDeviceKind)
''', "token type classifier")

if 'registerDevice" + ghostBaseRegisterDeviceKind + "Request"' not in reg:
    reg = replace_once(reg,
        '        GhostBaseV10EPushProbeCore.record("registerDeviceRequest")\n',
        '''        GhostBaseV10EPushProbeCore.record("registerDeviceRequest")
        GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Request")
''', "typed request")

if "LastRegisterDeviceTypeRaw" not in reg:
    reg = replace_once(reg,
        '        GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType", "\\(mappedType)")\n',
        '''        GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType", "\\(mappedType)")
        GhostBaseV10EPushProbeCore.set("LastRegisterDeviceTypeRaw", "\\(mappedType)")
''', "raw mapped type")

if "recordType1Request(" not in reg:
    reg = replace_once(reg,
        '        GhostBaseV10EPushProbeCore.set("LastRegisterDeviceSecretLength", "\\(keyData.count)")\n',
        '''        GhostBaseV10EPushProbeCore.set("LastRegisterDeviceSecretLength", "\\(keyData.count)")
        if mappedType == 1 {
            GhostBaseV10EPushProbeCore.recordType1Request(sandbox: sandbox, encrypt: ghostBaseRegisterDeviceEncrypt, secretLength: keyData.count, otherUidsCount: otherAccountUserIds.count)
        }
        GhostBaseV10EPushProbeCore.updateTypeSummary(lastType: mappedType, kind: ghostBaseRegisterDeviceKind)
''', "Type1 request metadata")

if 'registerDevice" + ghostBaseRegisterDeviceKind + "Success"' not in reg:
    reg = replace_once(reg,
        '''        |> map { _ -> Bool in
            GhostBaseV10EPushProbeCore.record("registerDeviceSuccess")
            return true
        }
''',
        '''        |> map { _ -> Bool in
            GhostBaseV10EPushProbeCore.record("registerDeviceSuccess")
            GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Success")
            if mappedType == 1 {
                GhostBaseV10EPushProbeCore.recordType1Success()
            }
            GhostBaseV10EPushProbeCore.updateTypeSummary(lastType: mappedType, kind: ghostBaseRegisterDeviceKind)
            return true
        }
''', "typed success")

if "recordType1Failure(errorCode: error.errorCode" not in reg:
    reg = replace_once(reg,
        '            GhostBaseV10EPushProbeCore.set("LastRegisterDeviceError", error.errorDescription)\n',
        '''            GhostBaseV10EPushProbeCore.set("LastRegisterDeviceError", error.errorDescription)
            GhostBaseV10EPushProbeCore.set("LastRegisterDevice" + ghostBaseRegisterDeviceKind + "Error", error.errorDescription)
            if mappedType == 1 {
                GhostBaseV10EPushProbeCore.recordType1Failure(errorCode: error.errorCode, errorDescription: error.errorDescription)
            }
''', "Type1 catch result")

if 'registerDevice" + ghostBaseRegisterDeviceKind + "Invalidated"' not in reg:
    reg = replace_once(reg,
        '                GhostBaseV10EPushProbeCore.record("registerDeviceInvalidated")\n',
        '''                GhostBaseV10EPushProbeCore.record("registerDeviceInvalidated")
                GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Invalidated")
                GhostBaseV10EPushProbeCore.updateTypeSummary(lastType: mappedType, kind: ghostBaseRegisterDeviceKind)
''', "typed invalidated")

if 'record("registerDevice" + ghostBaseRegisterDeviceKind + "Error")' not in reg:
    reg = replace_once(reg,
        '                GhostBaseV10EPushProbeCore.record("registerDeviceError")\n',
        '''                GhostBaseV10EPushProbeCore.record("registerDeviceError")
                GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Error")
                GhostBaseV10EPushProbeCore.updateTypeSummary(lastType: mappedType, kind: ghostBaseRegisterDeviceKind)
''', "typed error")

write(reg_p, reg)

if "registered=\\(ghostBaseRuntimeRegistered)" not in app:
    app = replace_once(app,
        '            GhostBaseV10EPushProbe.set("LastAuthorizationStatus", "\\(settings.authorizationStatus)")\n',
        '''            let ghostBaseRuntimeRegistered = UIApplication.shared.isRegisteredForRemoteNotifications ? "true" : "false"
            let ghostBaseRuntimeBundleId = Bundle.main.bundleIdentifier ?? "unknown"
            GhostBaseV10EPushProbe.set("LastAuthorizationStatus", "\\(settings.authorizationStatus); registered=\\(ghostBaseRuntimeRegistered); bundle=\\(ghostBaseRuntimeBundleId)")
''', "runtime authorization status")
write(app_p, app)

settings = settings.replace("v1.0E.1", "v1.0E").replace("v1.0E", "v1.0E.1")
write(settings_p, settings)

reg = read(reg_p)
helper = read(helper_p)
app = read(app_p)
settings = read(settings_p)
for needle in (
    'ghostBaseRegisterDeviceKind = "Type1"', 'ghostBaseRegisterDeviceKind = "Type9"',
    "ghostBaseRegisterDeviceEncrypt = encrypt", "if mappedType == 1", "recordType1Request(",
    "recordType1Success()", "recordType1Failure(errorCode: error.errorCode",
    'record("registerDevice" + ghostBaseRegisterDeviceKind + "Error")'):
    ensure(reg, needle, "registerDevice invariant")
for needle in (
    "Type1RequestCount", "Type1SuccessCount", "Type1FailureCount", "Type1LastErrorCode",
    "Type1LastErrorDescription", "Type1AppSandbox", "Type1Encrypt", "Type1SecretLength", "Type1OtherUidsCount"):
    ensure(helper, needle, "Type1 dedicated field")
ensure(app, "registered=\\(ghostBaseRuntimeRegistered); bundle=\\(ghostBaseRuntimeBundleId)", "runtime status")
ensure(settings, "v1.0E.1", "settings version")

catch_block = reg[reg.index("|> `catch`"):]
if catch_block.index("recordType1Failure") > catch_block.index('if error.errorDescription == "TOKEN_WAS_INVALIDATED"'):
    raise SystemExit("[v1.0E.1] ERROR: Type1 failure recorder is after stock catch decision")

print("[v1.0E.1] Split Type + dedicated Type1 runtime verdict probe patch OK")
