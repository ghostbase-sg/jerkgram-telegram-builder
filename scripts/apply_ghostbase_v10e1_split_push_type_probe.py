#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"
BASE = ROOT / "scripts/apply_ghostbase_v10e_main_push_probe.py"

def read(p):
    return Path(p).read_text()

def write(p, s):
    Path(p).write_text(s)

def ensure(s, needle, label):
    if needle not in s:
        raise SystemExit(f"[v1.0E.1] ERROR: missing {label}: {needle}")

def replace_once(s, old, new, label):
    if old in s:
        return s.replace(old, new, 1)
    if new in s:
        return s
    raise SystemExit(f"[v1.0E.1] ERROR: pattern not found: {label}")

print("[v1.0E.1] running base v1.0E patcher...")
subprocess.check_call([sys.executable, str(BASE)], cwd=str(ROOT))

reg_p = SRC / "submodules/TelegramCore/Sources/TelegramEngine/AccountData/RegisterNotificationToken.swift"
core_helper_p = SRC / "submodules/TelegramCore/Sources/TelegramEngine/AccountData/GhostBaseV10EPushProbeCore.swift"
app_p = SRC / "submodules/TelegramUI/Sources/AppDelegate.swift"
settings_p = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

reg = read(reg_p)
helper = read(core_helper_p)
app = read(app_p)
settings = read(settings_p)

ensure(reg, 'GhostBaseV10EPushProbeCore.record("registerDeviceEntry")', "base registerDeviceEntry")
ensure(helper, "enum GhostBaseV10EPushProbeCore", "core helper")
ensure(settings, "Main Push Registration Probe", "settings section")

if "static func setRegisterDeviceTypeSummary" not in helper:
    extra = r'''
    static func count(_ name: String) -> Int {
        return UserDefaults.standard.integer(forKey: "GhostBase.V10E.Push." + name + ".Count")
    }

    static func typeStatus(prefix: String) -> String {
        let request = count(prefix + "Request")
        let success = count(prefix + "Success")
        let invalidated = count(prefix + "Invalidated")
        let error = count(prefix + "Error")

        if success > 0 {
            return "success"
        } else if invalidated > 0 {
            return "invalidated"
        } else if error > 0 {
            return "error"
        } else if request > 0 {
            return "requested"
        } else {
            return "not-seen"
        }
    }

    static func setRegisterDeviceTypeSummary(lastType: Int32, kind: String) {
        let t1Entry = count("registerDeviceType1Entry")
        let t1Request = count("registerDeviceType1Request")
        let t1Success = count("registerDeviceType1Success")
        let t1Invalidated = count("registerDeviceType1Invalidated")
        let t1Error = count("registerDeviceType1Error")

        let t9Entry = count("registerDeviceType9Entry")
        let t9Request = count("registerDeviceType9Request")
        let t9Success = count("registerDeviceType9Success")
        let t9Invalidated = count("registerDeviceType9Invalidated")
        let t9Error = count("registerDeviceType9Error")

        let t1Status = typeStatus(prefix: "registerDeviceType1")
        let t9Status = typeStatus(prefix: "registerDeviceType9")

        let summary = "last=\(lastType)/\(kind); type1=\(t1Status) E/R/S/I/ERR=\(t1Entry)/\(t1Request)/\(t1Success)/\(t1Invalidated)/\(t1Error); type9=\(t9Status) E/R/S/I/ERR=\(t9Entry)/\(t9Request)/\(t9Success)/\(t9Invalidated)/\(t9Error)"
        set("LastRegisterDeviceType", summary)
    }
'''
    idx = helper.rfind("\n}")
    if idx == -1:
        raise SystemExit("[v1.0E.1] ERROR: helper enum end not found")
    helper = helper[:idx] + extra + helper[idx:]
    write(core_helper_p, helper)

if "let ghostBaseRegisterDeviceKind: String" not in reg:
    reg = replace_once(
        reg,
        '    GhostBaseV10EPushProbeCore.record("registerDeviceEntry")\n',
        '''    let ghostBaseRegisterDeviceKind: String
    switch type {
        case .aps:
            ghostBaseRegisterDeviceKind = "Type1"
        case .voip:
            ghostBaseRegisterDeviceKind = "Type9"
    }

    GhostBaseV10EPushProbeCore.record("registerDeviceEntry")
    GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Entry")
    GhostBaseV10EPushProbeCore.set("LastRegisterDeviceKind", ghostBaseRegisterDeviceKind)
''',
        "insert token type kind"
    )

if 'registerDevice" + ghostBaseRegisterDeviceKind + "Request"' not in reg:
    reg = replace_once(
        reg,
        '        GhostBaseV10EPushProbeCore.record("registerDeviceRequest")\n',
        '''        GhostBaseV10EPushProbeCore.record("registerDeviceRequest")
        GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Request")
''',
        "typed request"
    )

if "LastRegisterDeviceTypeRaw" not in reg:
    reg = replace_once(
        reg,
        '        GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType", "\\(mappedType)")\n',
        '''        GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType", "\\(mappedType)")
        GhostBaseV10EPushProbeCore.set("LastRegisterDeviceTypeRaw", "\\(mappedType)")
        GhostBaseV10EPushProbeCore.setRegisterDeviceTypeSummary(lastType: mappedType, kind: ghostBaseRegisterDeviceKind)
''',
        "type summary"
    )

if 'registerDevice" + ghostBaseRegisterDeviceKind + "Success"' not in reg:
    reg = replace_once(
        reg,
        '''        |> map { _ -> Bool in
            GhostBaseV10EPushProbeCore.record("registerDeviceSuccess")
            return true
        }
''',
        '''        |> map { _ -> Bool in
            GhostBaseV10EPushProbeCore.record("registerDeviceSuccess")
            GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Success")
            GhostBaseV10EPushProbeCore.set("LastRegisterDevice" + ghostBaseRegisterDeviceKind + "Error", "none")
            GhostBaseV10EPushProbeCore.setRegisterDeviceTypeSummary(lastType: mappedType, kind: ghostBaseRegisterDeviceKind)
            return true
        }
''',
        "typed success"
    )

if 'LastRegisterDevice" + ghostBaseRegisterDeviceKind + "Error"' not in reg:
    reg = replace_once(
        reg,
        '            GhostBaseV10EPushProbeCore.set("LastRegisterDeviceError", error.errorDescription)\n',
        '''            GhostBaseV10EPushProbeCore.set("LastRegisterDeviceError", error.errorDescription)
            GhostBaseV10EPushProbeCore.set("LastRegisterDevice" + ghostBaseRegisterDeviceKind + "Error", error.errorDescription)
''',
        "typed last error"
    )

if 'registerDevice" + ghostBaseRegisterDeviceKind + "Invalidated"' not in reg:
    reg = replace_once(
        reg,
        '                GhostBaseV10EPushProbeCore.record("registerDeviceInvalidated")\n',
        '''                GhostBaseV10EPushProbeCore.record("registerDeviceInvalidated")
                GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Invalidated")
                GhostBaseV10EPushProbeCore.setRegisterDeviceTypeSummary(lastType: mappedType, kind: ghostBaseRegisterDeviceKind)
''',
        "typed invalidated"
    )

if 'registerDevice" + ghostBaseRegisterDeviceKind + "Error"' not in reg:
    reg = replace_once(
        reg,
        '                GhostBaseV10EPushProbeCore.record("registerDeviceError")\n',
        '''                GhostBaseV10EPushProbeCore.record("registerDeviceError")
                GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Error")
                GhostBaseV10EPushProbeCore.setRegisterDeviceTypeSummary(lastType: mappedType, kind: ghostBaseRegisterDeviceKind)
''',
        "typed error"
    )

write(reg_p, reg)

if "registered=\\(ghostBaseRuntimeRegistered)" not in app:
    app = replace_once(
        app,
        '            GhostBaseV10EPushProbe.set("LastAuthorizationStatus", "\\(settings.authorizationStatus)")\n',
        '''            let ghostBaseRuntimeRegistered = UIApplication.shared.isRegisteredForRemoteNotifications ? "true" : "false"
            let ghostBaseRuntimeBundleId = Bundle.main.bundleIdentifier ?? "unknown"
            GhostBaseV10EPushProbe.set("LastAuthorizationStatus", "\\(settings.authorizationStatus); registered=\\(ghostBaseRuntimeRegistered); bundle=\\(ghostBaseRuntimeBundleId)")
''',
        "runtime authorization status"
    )
write(app_p, app)

settings = settings.replace("v1.0E.1", "v1.0E")
settings = settings.replace("v1.0E", "v1.0E.1")
write(settings_p, settings)

reg = read(reg_p)
helper = read(core_helper_p)
app = read(app_p)
settings = read(settings_p)

ensure(reg, 'ghostBaseRegisterDeviceKind = "Type1"', "Type1 branch")
ensure(reg, 'ghostBaseRegisterDeviceKind = "Type9"', "Type9 branch")
ensure(reg, 'registerDevice" + ghostBaseRegisterDeviceKind + "Request"', "typed request")
ensure(reg, 'registerDevice" + ghostBaseRegisterDeviceKind + "Success"', "typed success")
ensure(reg, 'registerDevice" + ghostBaseRegisterDeviceKind + "Invalidated"', "typed invalidated")
ensure(helper, "setRegisterDeviceTypeSummary", "summary helper")
ensure(helper, "type1=", "type1 summary")
ensure(app, "registered=\\(ghostBaseRuntimeRegistered); bundle=\\(ghostBaseRuntimeBundleId)", "runtime status")
ensure(settings, "v1.0E.1", "settings version")

print("[v1.0E.1] Split Type + Runtime Push Verdict Probe patch OK")
