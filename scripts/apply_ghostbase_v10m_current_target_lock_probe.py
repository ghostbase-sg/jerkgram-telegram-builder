#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"
BASE = ROOT / "scripts/apply_ghostbase_v10l_exact_target_classifier_probe.py"

def read(p):
    return Path(p).read_text()

def write(p, s):
    Path(p).write_text(s)

def ensure(s, needle, label):
    if needle not in s:
        raise SystemExit(f"[v1.0M] ERROR: missing {label}: {needle}")

def replace_once(s, old, new, label):
    if old in s:
        return s.replace(old, new, 1)
    if new in s:
        return s
    raise SystemExit(f"[v1.0M] ERROR: pattern not found: {label}")

print("[v1.0M] running base v1.0L patcher...")
subprocess.check_call([sys.executable, str(BASE)], cwd=str(ROOT))

core_p = SRC / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
settings_p = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

core = read(core_p)
settings = read(settings_p)

ensure(core, "GhostBase v1.0L Exact Target Classifier Probe", "v1.0L marker")
ensure(core, "ghostBaseV10LRecordExactHit", "v1.0L exact recorder")
ensure(settings, "Version: v1.0L", "settings v1.0L")

marker = "// MARK: GhostBase v1.0M Current Target Lock Probe"

if marker not in core:
    helper = r'''
// MARK: GhostBase v1.0M Current Target Lock Probe
private func ghostBaseV10MRawKey(_ key: String) -> String {
    return "GhostBase.V10F.Raw." + key
}

private func ghostBaseV10MSet(_ key: String, _ value: String) {
    UserDefaults.standard.set(value, forKey: ghostBaseV10MRawKey(key))
}

private func ghostBaseV10MRecord(_ name: String, amount: Int = 1) {
    guard amount > 0 else {
        return
    }
    let key = ghostBaseV10MRawKey(name + ".Count")
    UserDefaults.standard.set(UserDefaults.standard.integer(forKey: key) + amount, forKey: key)
}

private func ghostBaseV10MAppend(_ key: String, _ value: String, maxLines: Int = 16) {
    let rawKey = ghostBaseV10MRawKey(key)
    let clean = value.replacingOccurrences(of: "\n", with: " ")
    var lines: [String] = []
    if let current = UserDefaults.standard.string(forKey: rawKey), !current.isEmpty {
        lines = current.components(separatedBy: "\n")
    }
    lines.append(clean)
    if lines.count > maxLines {
        lines = Array(lines.suffix(maxLines))
    }
    UserDefaults.standard.set(lines.joined(separator: "\n"), forKey: rawKey)
}

private func ghostBaseV10MContainsDeletedMarker(_ text: String) -> Bool {
    return text.contains("M_D_")
}

private func ghostBaseV10MContainsKeepMarker(_ text: String) -> Bool {
    return text.contains("M_KEEP_")
}

private func ghostBaseV10MContainsAnyMarker(_ text: String) -> Bool {
    return ghostBaseV10MContainsDeletedMarker(text) || ghostBaseV10MContainsKeepMarker(text)
}

private func ghostBaseV10MMarker(_ text: String) -> String {
    for part in text.components(separatedBy: CharacterSet.whitespacesAndNewlines) {
        if part.contains("M_D_") || part.contains("M_KEEP_") {
            return part
        }
    }
    return "none"
}

private func ghostBaseV10MSetVerdictIfEmpty(_ verdict: String) {
    if UserDefaults.standard.string(forKey: ghostBaseV10MRawKey("MTargetVerdict")) == nil {
        ghostBaseV10MSet("MTargetVerdict", verdict)
    }
}

private func ghostBaseV10MSetVerdict(_ verdict: String) {
    ghostBaseV10MSet("MTargetVerdict", verdict)
}

'''
    anchor = "// MARK: GhostBase v1.0L Exact Target Classifier Probe"
    core = replace_once(core, anchor, helper + "\n" + anchor, "insert v1.0M helper")

old = '''    if key == "LastSnapshotText" && ghostBaseV10LContainsTarget(value) {
        ghostBaseV10LRecord("targetSnapshotHit")
        ghostBaseV10LSet("TargetMarker", ghostBaseV10LTargetMarker(value))
        ghostBaseV10LSet("TargetSnapshotText", ghostBaseV10FRawPreview(value, limit: 180))
        ghostBaseV10LSet("TargetVerdict", "TARGET_SNAPSHOT_TEXT")
    }
'''

new = '''    if key == "LastSnapshotText" && ghostBaseV10MContainsAnyMarker(value) {
        ghostBaseV10MRecord("mTargetSnapshotHit")
        ghostBaseV10MSet("MCurrentMarker", ghostBaseV10MMarker(value))
        ghostBaseV10MSet("MTargetSnapshotText", ghostBaseV10FRawPreview(value, limit: 180))
        ghostBaseV10MSetVerdict("TARGET_SNAPSHOT_TEXT")
    }
    if key.hasPrefix("LastFetchShape") {
        ghostBaseV10MSet("M" + key, value)
    }
    if key == "LastFetchShapeCase" && value == "messageEmpty" {
        ghostBaseV10MSetVerdictIfEmpty("FETCH_MESSAGE_EMPTY")
    }
'''

core = replace_once(core, old, new, "replace snapshot detector")

old = '''    if text.isEmpty {
        ghostBaseV10LRecord("exactHitWithoutText")
        ghostBaseV10LSetVerdictIfEmpty("EXACT_HIT_NO_TEXT")
    } else {
        ghostBaseV10LRecord("exactHitWithText")
        ghostBaseV10LSetVerdictIfEmpty("EXACT_HIT_NON_TARGET_TEXT")
    }
'''

new = '''    if text.isEmpty {
        ghostBaseV10LRecord("exactHitWithoutText")
        ghostBaseV10MRecord("mExactHitWithoutText")
        ghostBaseV10LSetVerdictIfEmpty("EXACT_HIT_NO_TEXT")
        ghostBaseV10MSetVerdictIfEmpty("EXACT_HIT_NO_TEXT")
    } else {
        ghostBaseV10LRecord("exactHitWithText")
        ghostBaseV10MRecord("mExactHitWithText")

        if ghostBaseV10MContainsDeletedMarker(text) {
            ghostBaseV10MRecord("mTargetExactHit")
            ghostBaseV10MRecord("mTargetHistoryHit")
            ghostBaseV10MSet("MCurrentMarker", ghostBaseV10MMarker(text))
            ghostBaseV10MSet("MTargetText", ghostBaseV10FRawPreview(text, limit: 180))
            ghostBaseV10MSetVerdict("TARGET_EXACT_TEXT")
        } else {
            ghostBaseV10MRecord("mExactIdCollision")
            ghostBaseV10MSet("MExactCollisionRequestedId", "\\(requestedId)")
            ghostBaseV10MSet("MExactCollisionPeer", "\\(peerId)")
            ghostBaseV10MSet("MExactCollisionCase", caseName)
            ghostBaseV10MSet("MExactCollisionId", "\\(id)")
            ghostBaseV10MSet("MExactCollisionText", ghostBaseV10FRawPreview(text, limit: 140))
            ghostBaseV10MAppend("MExactCollisionList", "req=\\(requestedId) peer=\\(peerId) case=\\(caseName) id=\\(id) text=\\(ghostBaseV10FRawPreview(text, limit: 70))")
            ghostBaseV10MSetVerdictIfEmpty("EXACT_ID_COLLISION")
            ghostBaseV10LSetVerdictIfEmpty("EXACT_HIT_NON_TARGET_TEXT")
        }
    }
'''

core = replace_once(core, old, new, "replace exact text classifier")

old = '''    if ghostBaseV10LContainsTarget(text) {
        ghostBaseV10LRecord("targetExactHit")
        ghostBaseV10LRecord("targetHistoryHit")
        ghostBaseV10LSet("TargetMarker", ghostBaseV10LTargetMarker(text))
        ghostBaseV10LSet("TargetText", ghostBaseV10FRawPreview(text, limit: 180))
        ghostBaseV10LSet("TargetVerdict", "TARGET_EXACT_TEXT")
    }
'''

new = '''    if ghostBaseV10MContainsDeletedMarker(text) {
        ghostBaseV10LRecord("targetExactHit")
        ghostBaseV10LRecord("targetHistoryHit")
        ghostBaseV10LSet("TargetMarker", ghostBaseV10MMarker(text))
        ghostBaseV10LSet("TargetText", ghostBaseV10FRawPreview(text, limit: 180))
        ghostBaseV10LSet("TargetVerdict", "TARGET_EXACT_TEXT")
    }
'''

core = replace_once(core, old, new, "replace old L exact target noise")

old = '''        if ghostBaseV10LContainsTarget(data.message) {
            ghostBaseV10LRecord("targetHistoryHit")
            ghostBaseV10LSet("TargetMarker", ghostBaseV10LTargetMarker(data.message))
            ghostBaseV10LSet("TargetText", ghostBaseV10FRawPreview(data.message, limit: 180))
            ghostBaseV10LSetVerdictIfEmpty("TARGET_HISTORY_NON_EXACT")
        }
'''

new = '''        if data.id != requestedId && ghostBaseV10MContainsDeletedMarker(data.message) {
            ghostBaseV10MRecord("mTargetHistoryHit")
            ghostBaseV10MSet("MCurrentMarker", ghostBaseV10MMarker(data.message))
            ghostBaseV10MSet("MTargetText", ghostBaseV10FRawPreview(data.message, limit: 180))
            ghostBaseV10MSetVerdictIfEmpty("TARGET_HISTORY_NON_EXACT")

            ghostBaseV10LRecord("targetHistoryHit")
            ghostBaseV10LSet("TargetMarker", ghostBaseV10MMarker(data.message))
            ghostBaseV10LSet("TargetText", ghostBaseV10FRawPreview(data.message, limit: 180))
            ghostBaseV10LSetVerdictIfEmpty("TARGET_HISTORY_NON_EXACT")
        }
'''

core = replace_once(core, old, new, "replace non-exact history target detector")

write(core_p, core)

if "v1.0M Current Test Verdict:" not in settings:
    summary = r'''v1.0M Current Test Verdict:
MTargetVerdict: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "MTargetVerdict") ?? "none")
MCurrentMarker: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "MCurrentMarker") ?? "none")

MTargetSnapshotHit: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "mTargetSnapshotHit.Count"))
MTargetHistoryHit: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "mTargetHistoryHit.Count"))
MTargetExactHit: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "mTargetExactHit.Count"))
MTargetText: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "MTargetText") ?? "none")
MTargetSnapshotText: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "MTargetSnapshotText") ?? "none")

MFetchShapeCase: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "MLastFetchShapeCase") ?? "none")
MFetchShapeId: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "MLastFetchShapeId") ?? "none")
MFetchShapePeer: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "MLastFetchShapePeer") ?? "none")
MFetchShapeTextLength: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "MLastFetchShapeTextLength") ?? "none")

MExactHitWithText: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "mExactHitWithText.Count"))
MExactHitWithoutText: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "mExactHitWithoutText.Count"))
MExactCollisionCount: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "mExactIdCollision.Count"))
MExactCollisionRequestedId: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "MExactCollisionRequestedId") ?? "none")
MExactCollisionPeer: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "MExactCollisionPeer") ?? "none")
MExactCollisionCase: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "MExactCollisionCase") ?? "none")
MExactCollisionId: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "MExactCollisionId") ?? "none")
MExactCollisionText: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "MExactCollisionText") ?? "none")

MExactCollisionList:
\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "MExactCollisionList") ?? "none")

'''
    if "v1.0L Target Verdict:" not in settings:
        raise SystemExit("[v1.0M] ERROR: v1.0L Target Verdict anchor missing")
    settings = settings.replace("v1.0L Target Verdict:", summary + "v1.0L Target Verdict:", 1)

settings = settings.replace("Version: v1.0L", "Version: v1.0M")
write(settings_p, settings)

core = read(core_p)
settings = read(settings_p)

ensure(core, "GhostBase v1.0M Current Target Lock Probe", "v1.0M helper")
ensure(core, "ghostBaseV10MContainsDeletedMarker", "M deleted marker helper")
ensure(core, "EXACT_ID_COLLISION", "collision verdict")
ensure(core, "mExactIdCollision", "collision counter")
ensure(settings, "v1.0M Current Test Verdict:", "M verdict settings")
ensure(settings, "MExactCollisionList:", "M collision list settings")
ensure(settings, "Version: v1.0M", "settings version")

print("[v1.0M] Current Target Lock Probe patch OK")
