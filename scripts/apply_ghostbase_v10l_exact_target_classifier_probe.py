#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"
BASE = ROOT / "scripts/apply_ghostbase_v10k_clean_timeline_probe.py"

def read(p):
    return Path(p).read_text()

def write(p, s):
    Path(p).write_text(s)

def ensure(s, needle, label):
    if needle not in s:
        raise SystemExit(f"[v1.0L] ERROR: missing {label}: {needle}")

def replace_once(s, old, new, label):
    if old in s:
        return s.replace(old, new, 1)
    if new in s:
        return s
    raise SystemExit(f"[v1.0L] ERROR: pattern not found: {label}")

print("[v1.0L] running base v1.0K patcher...")
subprocess.check_call([sys.executable, str(BASE)], cwd=str(ROOT))

core_p = SRC / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
settings_p = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

core = read(core_p)
settings = read(settings_p)

ensure(core, "GhostBase v1.0K Clean Timeline Probe", "v1.0K marker")
ensure(core, "ghostBaseV10JRecordHistoryMessage", "v1.0J history recorder")
ensure(settings, "Version: v1.0K", "settings v1.0K")

marker = "// MARK: GhostBase v1.0L Exact Target Classifier Probe"

if marker not in core:
    helper = r'''
// MARK: GhostBase v1.0L Exact Target Classifier Probe
private func ghostBaseV10LRawKey(_ key: String) -> String {
    return "GhostBase.V10F.Raw." + key
}

private func ghostBaseV10LSet(_ key: String, _ value: String) {
    UserDefaults.standard.set(value, forKey: ghostBaseV10LRawKey(key))
}

private func ghostBaseV10LRecord(_ name: String, amount: Int = 1) {
    guard amount > 0 else {
        return
    }
    let key = ghostBaseV10LRawKey(name + ".Count")
    UserDefaults.standard.set(UserDefaults.standard.integer(forKey: key) + amount, forKey: key)
}

private func ghostBaseV10LAppend(_ key: String, _ value: String, maxLines: Int = 24) {
    let rawKey = ghostBaseV10LRawKey(key)
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

private func ghostBaseV10LContainsTarget(_ text: String) -> Bool {
    return text.contains("L_D_") || text.contains("L_KEEP_")
}

private func ghostBaseV10LTargetMarker(_ text: String) -> String {
    for part in text.components(separatedBy: CharacterSet.whitespacesAndNewlines) {
        if part.contains("L_D_") || part.contains("L_KEEP_") {
            return part
        }
    }
    return "target-text"
}

private func ghostBaseV10LSetVerdictIfEmpty(_ verdict: String) {
    if UserDefaults.standard.string(forKey: ghostBaseV10LRawKey("TargetVerdict")) == nil {
        ghostBaseV10LSet("TargetVerdict", verdict)
    }
}

'''
    anchor = "// MARK: GhostBase v1.0K Clean Timeline Probe"
    core = replace_once(core, anchor, helper + "\n" + anchor, "insert v1.0L helper")

if "ghostBaseV10LRecordExactHit(" not in core:
    helper2 = r'''
private func ghostBaseV10LRecordExactHit(requestedId: Int32, peerId: PeerId, caseName: String, id: Int32, peerFrom: String, date: String, text: String, media: String, action: String) {
    ghostBaseV10LRecord("exactHitCount")
    ghostBaseV10LSet("ExactHitRequestedId", "\(requestedId)")
    ghostBaseV10LSet("ExactHitPeer", "\(peerId)")
    ghostBaseV10LSet("ExactHitCase", caseName)
    ghostBaseV10LSet("ExactHitId", "\(id)")
    ghostBaseV10LSet("ExactHitPeerFromMessage", peerFrom)
    ghostBaseV10LSet("ExactHitDate", date)
    ghostBaseV10LSet("ExactHitTextLength", "\(text.count)")
    ghostBaseV10LSet("ExactHitText", ghostBaseV10FRawPreview(text, limit: 180))
    ghostBaseV10LSet("ExactHitMedia", media)
    ghostBaseV10LSet("ExactHitAction", action)

    if caseName == "messageEmpty" {
        ghostBaseV10LRecord("exactHitEmpty")
    } else if caseName == "messageService" {
        ghostBaseV10LRecord("exactHitService")
    } else {
        ghostBaseV10LRecord("exactHitMessage")
    }

    if text.isEmpty {
        ghostBaseV10LRecord("exactHitWithoutText")
        ghostBaseV10LSetVerdictIfEmpty("EXACT_HIT_NO_TEXT")
    } else {
        ghostBaseV10LRecord("exactHitWithText")
        ghostBaseV10LSetVerdictIfEmpty("EXACT_HIT_NON_TARGET_TEXT")
    }

    let line = "req=\(requestedId) peer=\(peerId) case=\(caseName) id=\(id) len=\(text.count) text=\(ghostBaseV10FRawPreview(text, limit: 90))"
    ghostBaseV10LAppend("ExactHitList", line)

    if ghostBaseV10LContainsTarget(text) {
        ghostBaseV10LRecord("targetExactHit")
        ghostBaseV10LRecord("targetHistoryHit")
        ghostBaseV10LSet("TargetMarker", ghostBaseV10LTargetMarker(text))
        ghostBaseV10LSet("TargetText", ghostBaseV10FRawPreview(text, limit: 180))
        ghostBaseV10LSet("TargetVerdict", "TARGET_EXACT_TEXT")
    }
}

'''
    anchor = "// MARK: GhostBase v1.0K Clean Timeline Probe"
    core = replace_once(core, anchor, helper2 + "\n" + anchor, "insert exact recorder")

if "targetSnapshotHit" not in core:
    insert = r'''    if key == "LastSnapshotText" && ghostBaseV10LContainsTarget(value) {
        ghostBaseV10LRecord("targetSnapshotHit")
        ghostBaseV10LSet("TargetMarker", ghostBaseV10LTargetMarker(value))
        ghostBaseV10LSet("TargetSnapshotText", ghostBaseV10FRawPreview(value, limit: 180))
        ghostBaseV10LSet("TargetVerdict", "TARGET_SNAPSHOT_TEXT")
    }
'''
    core, n = re.subn(
        r'(private func ghostBaseV10FRawSet\([^{]+\)\s*\{\n\s*ghostBaseV10KMaybeResetDiagnosticsOnLaunch\(\)\n)',
        r'\1' + insert,
        core,
        count=1
    )
    if n != 1:
        raise SystemExit("[v1.0L] ERROR: failed to patch target snapshot detector")

old = '''        if data.id == requestedId {
            ghostBaseV10FRawRecord("historyProbeExactId")
        }
        if !data.message.isEmpty {
            ghostBaseV10FRawRecord("historyProbeWithText")
        }
'''

new = '''        if data.id == requestedId {
            ghostBaseV10FRawRecord("historyProbeExactId")
            ghostBaseV10LRecordExactHit(requestedId: requestedId, peerId: peerId, caseName: "message", id: data.id, peerFrom: ghostBaseV10IShapePeer(data.peerId), date: "\\(data.date)", text: data.message, media: data.media?.descriptionFields().0 ?? "none", action: "none")
        }
        if !data.message.isEmpty {
            ghostBaseV10FRawRecord("historyProbeWithText")
        }
        if ghostBaseV10LContainsTarget(data.message) {
            ghostBaseV10LRecord("targetHistoryHit")
            ghostBaseV10LSet("TargetMarker", ghostBaseV10LTargetMarker(data.message))
            ghostBaseV10LSet("TargetText", ghostBaseV10FRawPreview(data.message, limit: 180))
            ghostBaseV10LSetVerdictIfEmpty("TARGET_HISTORY_NON_EXACT")
        }
'''

core = replace_once(core, old, new, "patch exact message")

old = '''        if data.id == requestedId {
            ghostBaseV10FRawRecord("historyProbeExactEmptyId")
        }
'''

new = '''        if data.id == requestedId {
            ghostBaseV10FRawRecord("historyProbeExactEmptyId")
            ghostBaseV10LRecordExactHit(requestedId: requestedId, peerId: peerId, caseName: "messageEmpty", id: data.id, peerFrom: ghostBaseV10IShapePeer(data.peerId), date: "none", text: "", media: "none", action: "none")
        }
'''

core = replace_once(core, old, new, "patch exact messageEmpty")

old = '''        if data.id == requestedId {
            ghostBaseV10FRawRecord("historyProbeExactServiceId")
        }
'''

new = '''        if data.id == requestedId {
            ghostBaseV10FRawRecord("historyProbeExactServiceId")
            ghostBaseV10LRecordExactHit(requestedId: requestedId, peerId: peerId, caseName: "messageService", id: data.id, peerFrom: ghostBaseV10IShapePeer(data.peerId), date: "\\(data.date)", text: "", media: "none", action: data.action.descriptionFields().0)
        }
'''

core = replace_once(core, old, new, "patch exact service")

write(core_p, core)

if "v1.0L Target Verdict:" not in settings:
    summary = r'''v1.0L Target Verdict:
TargetVerdict: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "TargetVerdict") ?? "none")
TargetMarker: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "TargetMarker") ?? "none")
TargetSnapshotHit: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "targetSnapshotHit.Count"))
TargetHistoryHit: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "targetHistoryHit.Count"))
TargetExactHit: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "targetExactHit.Count"))
TargetText: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "TargetText") ?? "none")
TargetSnapshotText: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "TargetSnapshotText") ?? "none")

ExactHitCount: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "exactHitCount.Count"))
ExactHitMessage: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "exactHitMessage.Count"))
ExactHitEmpty: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "exactHitEmpty.Count"))
ExactHitService: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "exactHitService.Count"))
ExactHitWithText: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "exactHitWithText.Count"))
ExactHitWithoutText: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "exactHitWithoutText.Count"))

ExactHitRequestedId: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "ExactHitRequestedId") ?? "none")
ExactHitPeer: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "ExactHitPeer") ?? "none")
ExactHitCase: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "ExactHitCase") ?? "none")
ExactHitId: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "ExactHitId") ?? "none")
ExactHitTextLength: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "ExactHitTextLength") ?? "none")
ExactHitText: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "ExactHitText") ?? "none")
ExactHitMedia: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "ExactHitMedia") ?? "none")

ExactHitList:
\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "ExactHitList") ?? "none")

'''
    if "Raw Difference Snapshot Probe:" not in settings:
        raise SystemExit("[v1.0L] ERROR: Raw Difference Snapshot Probe anchor missing")
    settings = settings.replace("Raw Difference Snapshot Probe:", summary + "Raw Difference Snapshot Probe:", 1)

settings = settings.replace("Version: v1.0K", "Version: v1.0L")
write(settings_p, settings)

core = read(core_p)
settings = read(settings_p)

ensure(core, "GhostBase v1.0L Exact Target Classifier Probe", "v1.0L helper")
ensure(core, "ghostBaseV10LRecordExactHit", "exact recorder")
ensure(core, "targetSnapshotHit", "target snapshot detector")
ensure(core, "targetHistoryHit", "target history detector")
ensure(settings, "v1.0L Target Verdict:", "target verdict settings")
ensure(settings, "ExactHitList:", "exact list settings")
ensure(settings, "Version: v1.0L", "settings version")

print("[v1.0L] Exact Target Classifier Probe patch OK")
