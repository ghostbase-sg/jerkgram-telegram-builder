#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"
BASE = ROOT / "scripts/apply_ghostbase_v10j_history_around_tombstone_probe.py"

def read(p):
    return Path(p).read_text()

def write(p, s):
    Path(p).write_text(s)

def ensure(s, needle, label):
    if needle not in s:
        raise SystemExit(f"[v1.0K] ERROR: missing {label}: {needle}")

def replace_once(s, old, new, label):
    if old in s:
        return s.replace(old, new, 1)
    if new in s:
        return s
    raise SystemExit(f"[v1.0K] ERROR: pattern not found: {label}")

print("[v1.0K] running base v1.0J patcher...")
subprocess.check_call([sys.executable, str(BASE)], cwd=str(ROOT))

core_p = SRC / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
settings_p = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

core = read(core_p)
settings = read(settings_p)

ensure(core, "GhostBase v1.0J History Around Tombstone Probe", "v1.0J marker")
ensure(core, "private func ghostBaseV10FRawRecord", "raw record helper")
ensure(core, "private func ghostBaseV10FRawSet", "raw set helper")
ensure(settings, "Version: v1.0J", "settings v1.0J")

marker = "// MARK: GhostBase v1.0K Clean Timeline Probe"

if marker not in core:
    helper = r'''
// MARK: GhostBase v1.0K Clean Timeline Probe
private var ghostBaseV10KDidResetDiagnosticsOnLaunch = false

private func ghostBaseV10KMaybeResetDiagnosticsOnLaunch() {
    if ghostBaseV10KDidResetDiagnosticsOnLaunch {
        return
    }
    ghostBaseV10KDidResetDiagnosticsOnLaunch = true

    let defaults = UserDefaults.standard
    let keys = Array(defaults.dictionaryRepresentation().keys)
    for key in keys {
        if key.hasPrefix("GhostBase.V10F.Raw.") {
            defaults.removeObject(forKey: key)
        }
    }

    defaults.set("v1.0K", forKey: "GhostBase.V10F.Raw." + "TestEpoch")
    defaults.set("\(Int(Date().timeIntervalSince1970))", forKey: "GhostBase.V10F.Raw." + "EpochStartedAt")
    defaults.set("autoResetOnLaunch", forKey: "GhostBase.V10F.Raw." + "ResetMode")
}

private func ghostBaseV10KTimeline(_ event: String) {
    let defaults = UserDefaults.standard
    let key = "GhostBase.V10F.Raw." + "Timeline"
    let ts = Int(Date().timeIntervalSince1970)
    let clean = event.replacingOccurrences(of: "\n", with: " ")
    let line = "\(ts) \(ghostBaseV10FRawPreview(clean, limit: 180))"

    var lines: [String] = []
    if let current = defaults.string(forKey: key), !current.isEmpty {
        lines = current.components(separatedBy: "\n")
    }
    lines.append(line)
    if lines.count > 60 {
        lines = Array(lines.suffix(60))
    }
    defaults.set(lines.joined(separator: "\n"), forKey: key)
}

'''
    anchor = "// MARK: GhostBase v1.0J History Around Tombstone Probe"
    core = replace_once(core, anchor, helper + "\n" + anchor, "insert v1.0K helper")


import re

if "ghostBaseV10KTimeline(\"record" not in core:
    core, n = re.subn(
        r'(private func ghostBaseV10FRawRecord\([^{]+\)\s*\{\n)',
        r'\1    ghostBaseV10KMaybeResetDiagnosticsOnLaunch()\n    ghostBaseV10KTimeline("record \\(name) +\\(amount)")\n',
        core,
        count=1
    )
    if n != 1:
        raise SystemExit("[v1.0K] ERROR: regex failed: patch raw record")

if "ghostBaseV10KTimeline(\"set" not in core:
    core, n = re.subn(
        r'(private func ghostBaseV10FRawSet\([^{]+\)\s*\{\n)',
        r'\1    ghostBaseV10KMaybeResetDiagnosticsOnLaunch()\n    if key.hasPrefix("Last") || key == "Timeline" || key == "TestEpoch" || key == "EpochStartedAt" || key == "ResetMode" {\n        ghostBaseV10KTimeline("set \\(key)=\\(ghostBaseV10FRawPreview(value, limit: 140))")\n    }\n',
        core,
        count=1
    )
    if n != 1:
        raise SystemExit("[v1.0K] ERROR: regex failed: patch raw set")

write(core_p, core)



if "TestEpoch:" not in settings:
    timeline_block = r'''
TestEpoch: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "TestEpoch") ?? "none")
EpochStartedAt: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "EpochStartedAt") ?? "none")
ResetMode: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "ResetMode") ?? "none")

Timeline:
\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "Timeline") ?? "none")

'''
    if "LastDeleteSnapshotKey:" not in settings:
        raise SystemExit("[v1.0K] ERROR: LastDeleteSnapshotKey anchor missing for timeline settings")
    settings = settings.replace("LastDeleteSnapshotKey:", timeline_block + "LastDeleteSnapshotKey:", 1)

settings = settings.replace("Version: v1.0J", "Version: v1.0K")
write(settings_p, settings)

core = read(core_p)
settings = read(settings_p)

ensure(core, "GhostBase v1.0K Clean Timeline Probe", "v1.0K helper")
ensure(core, "ghostBaseV10KMaybeResetDiagnosticsOnLaunch()", "auto reset call")
ensure(core, "ghostBaseV10KTimeline", "timeline helper")
ensure(settings, "Version: v1.0K", "settings version")
ensure(settings, "Timeline:", "timeline settings")
ensure(settings, "ResetMode:", "reset mode settings")

print("[v1.0K] Clean Timeline Probe patch OK")
