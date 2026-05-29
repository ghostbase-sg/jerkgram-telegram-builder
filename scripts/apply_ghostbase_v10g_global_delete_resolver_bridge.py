#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"
BASE = ROOT / "scripts/apply_ghostbase_v10f_raw_difference_snapshot_probe.py"

def read(p):
    return Path(p).read_text()

def write(p, s):
    Path(p).write_text(s)

def ensure(s, needle, label):
    if needle not in s:
        raise SystemExit(f"[v1.0G] ERROR: missing {label}: {needle}")

def replace_once(s, old, new, label):
    if old in s:
        return s.replace(old, new, 1)
    if new in s:
        return s
    raise SystemExit(f"[v1.0G] ERROR: pattern not found: {label}")

print("[v1.0G] running base v1.0F patcher...")
subprocess.check_call([sys.executable, str(BASE)], cwd=str(ROOT))

core_p = SRC / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
settings_p = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

core = read(core_p)
settings = read(settings_p)

ensure(core, "transaction.messageIdsForGlobalIds(ids)", "global resolver")
ensure(core, "ghostBaseV10FRawDeleteHit", "raw delete hit helper")
ensure(settings, "Raw Difference Snapshot Probe:", "raw settings section")

if 'ghostBaseV10FRawDeleteHit(messageIds: ghostBaseMessageIds, source: "ReplayDeleteGlobalIds")' not in core:
    core = replace_once(
        core,
        '''                let ghostBaseMessageIds = transaction.messageIdsForGlobalIds(ids)
                for id in ghostBaseMessageIds {
''',
        '''                let ghostBaseMessageIds = transaction.messageIdsForGlobalIds(ids)
                ghostBaseV10FRawRecord("deleteGlobalResolverSeen")
                ghostBaseV10FRawSet("LastDeleteGlobalInputIdsCount", "\\(ids.count)")
                ghostBaseV10FRawSet("LastDeleteGlobalResolvedIdsCount", "\\(ghostBaseMessageIds.count)")
                if ghostBaseMessageIds.isEmpty {
                    ghostBaseV10FRawRecord("deleteGlobalResolverMiss")
                } else {
                    ghostBaseV10FRawRecord("deleteGlobalResolvedIds", amount: ghostBaseMessageIds.count)
                    ghostBaseV10FRawDeleteHit(messageIds: ghostBaseMessageIds, source: "ReplayDeleteGlobalIds")
                }
                for id in ghostBaseMessageIds {
''',
        "insert global resolver bridge"
    )

if 'ghostBaseV10FRawRecord("deleteResolvedCurrentText")' not in core:
    core = replace_once(
        core,
        '''                    transaction.updateMessage(id, update: { currentMessage in
                        var updatedAttributes = currentMessage.attributes
''',
        '''                    transaction.updateMessage(id, update: { currentMessage in
                        let ghostBaseResolvedKey = ghostBaseV10FRawMessageKey(id)
                        if !currentMessage.text.isEmpty {
                            ghostBaseV10FRawRecord("deleteResolvedCurrentText")
                            ghostBaseV10FRawSet("LastDeleteResolvedText", ghostBaseV10FRawPreview(currentMessage.text))
                            ghostBaseV10FRawSet("LastDeleteResolvedKey", ghostBaseResolvedKey)
                            UserDefaults.standard.set(currentMessage.text, forKey: "GhostBase.V10F.Raw.Snapshot." + ghostBaseResolvedKey + ".text")
                            UserDefaults.standard.set("ReplayDeleteGlobalIdsCurrentText", forKey: "GhostBase.V10F.Raw.Snapshot." + ghostBaseResolvedKey + ".source")
                            ghostBaseV10FRawDeleteHit(messageIds: [id], source: "ReplayDeleteGlobalIdsCurrentText")
                        }
                        var updatedAttributes = currentMessage.attributes
''',
        "insert current message text capture"
    )

write(core_p, core)

if "deleteGlobalResolverSeen:" not in settings:
    settings = replace_once(
        settings,
        '''deleteGlobalSnapshotMiss: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "deleteGlobalSnapshotMiss.Count"))
LastSnapshotSource:''',
        '''deleteGlobalSnapshotMiss: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "deleteGlobalSnapshotMiss.Count"))
deleteGlobalResolverSeen: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "deleteGlobalResolverSeen.Count"))
deleteGlobalResolvedIds: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "deleteGlobalResolvedIds.Count"))
deleteGlobalResolverMiss: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "deleteGlobalResolverMiss.Count"))
deleteResolvedCurrentText: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "deleteResolvedCurrentText.Count"))
LastSnapshotSource:''',
        "insert resolver counters settings"
    )

if "LastDeleteGlobalResolvedIdsCount:" not in settings:
    settings = replace_once(
        settings,
        '''LastDeleteGlobalIdsCount: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastDeleteGlobalIdsCount") ?? "none")
LastDeleteSnapshotKey:''',
        '''LastDeleteGlobalIdsCount: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastDeleteGlobalIdsCount") ?? "none")
LastDeleteGlobalInputIdsCount: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastDeleteGlobalInputIdsCount") ?? "none")
LastDeleteGlobalResolvedIdsCount: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastDeleteGlobalResolvedIdsCount") ?? "none")
LastDeleteResolvedKey: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastDeleteResolvedKey") ?? "none")
LastDeleteResolvedText: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastDeleteResolvedText") ?? "none")
LastDeleteSnapshotKey:''',
        "insert resolver last settings"
    )

settings = settings.replace("Version: v1.0F", "Version: v1.0G")
write(settings_p, settings)

core = read(core_p)
settings = read(settings_p)

ensure(core, 'ghostBaseV10FRawDeleteHit(messageIds: ghostBaseMessageIds, source: "ReplayDeleteGlobalIds")', "resolver delete hit")
ensure(core, 'ghostBaseV10FRawRecord("deleteResolvedCurrentText")', "current text capture")
ensure(core, 'LastDeleteGlobalResolvedIdsCount', "resolved count set")
ensure(settings, "deleteGlobalResolverSeen:", "resolver settings counter")
ensure(settings, "LastDeleteGlobalResolvedIdsCount:", "resolver settings last")
ensure(settings, "Version: v1.0G", "settings version")

print("[v1.0G] Global Delete Resolver Bridge patch OK")
