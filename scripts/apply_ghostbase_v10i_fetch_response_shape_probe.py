#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"
BASE = ROOT / "scripts/apply_ghostbase_v10h_fetch_race_probe.py"

def read(p):
    return Path(p).read_text()

def write(p, s):
    Path(p).write_text(s)

def ensure(s, needle, label):
    if needle not in s:
        raise SystemExit(f"[v1.0I] ERROR: missing {label}: {needle}")

def replace_once(s, old, new, label):
    if old in s:
        return s.replace(old, new, 1)
    if new in s:
        return s
    raise SystemExit(f"[v1.0I] ERROR: pattern not found: {label}")

print("[v1.0I] running base v1.0H patcher...")
subprocess.check_call([sys.executable, str(BASE)], cwd=str(ROOT))

core_p = SRC / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
settings_p = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

core = read(core_p)
settings = read(settings_p)

ensure(core, "GhostBase v1.0H Fetch Race Probe", "v1.0H helper")
ensure(core, "for apiMessage in apiMessages {", "fetch race loop")
ensure(settings, "LastFetchRaceText:", "fetch race settings")

helper_marker = "// MARK: GhostBase v1.0I Fetch Response Shape Probe"

if helper_marker not in core:
    helper = r'''
// MARK: GhostBase v1.0I Fetch Response Shape Probe
private func ghostBaseV10IShapePeer(_ peer: Api.Peer?) -> String {
    guard let peer = peer else {
        return "none"
    }

    switch peer {
    case let .peerUser(data):
        return "peerUser:\(data.userId)"
    case let .peerChat(data):
        return "peerChat:\(data.chatId)"
    case let .peerChannel(data):
        return "peerChannel:\(data.channelId)"
    }
}

private func ghostBaseV10IRecordFetchShape(_ apiMessage: Api.Message, source: String) {
    ghostBaseV10FRawRecord("fetchShapeSeen")
    ghostBaseV10FRawSet("LastFetchShapeSource", source)

    switch apiMessage {
    case let .message(data):
        ghostBaseV10FRawRecord("fetchShapeMessage")
        ghostBaseV10FRawSet("LastFetchShapeCase", "message")
        ghostBaseV10FRawSet("LastFetchShapeId", "\(data.id)")
        ghostBaseV10FRawSet("LastFetchShapeFlags", "\(data.flags)")
        ghostBaseV10FRawSet("LastFetchShapeFlags2", "\(data.flags2)")
        ghostBaseV10FRawSet("LastFetchShapePeer", ghostBaseV10IShapePeer(data.peerId))
        ghostBaseV10FRawSet("LastFetchShapeFrom", ghostBaseV10IShapePeer(data.fromId))
        ghostBaseV10FRawSet("LastFetchShapeDate", "\(data.date)")
        ghostBaseV10FRawSet("LastFetchShapeTextLength", "\(data.message.count)")
        ghostBaseV10FRawSet("LastFetchShapeTextPreview", ghostBaseV10FRawPreview(data.message))
        ghostBaseV10FRawSet("LastFetchShapeMedia", data.media?.descriptionFields().0 ?? "none")
        ghostBaseV10FRawSet("LastFetchShapeAction", "none")

    case let .messageEmpty(data):
        ghostBaseV10FRawRecord("fetchShapeMessageEmpty")
        ghostBaseV10FRawSet("LastFetchShapeCase", "messageEmpty")
        ghostBaseV10FRawSet("LastFetchShapeId", "\(data.id)")
        ghostBaseV10FRawSet("LastFetchShapeFlags", "\(data.flags)")
        ghostBaseV10FRawSet("LastFetchShapeFlags2", "none")
        ghostBaseV10FRawSet("LastFetchShapePeer", ghostBaseV10IShapePeer(data.peerId))
        ghostBaseV10FRawSet("LastFetchShapeFrom", "none")
        ghostBaseV10FRawSet("LastFetchShapeDate", "none")
        ghostBaseV10FRawSet("LastFetchShapeTextLength", "0")
        ghostBaseV10FRawSet("LastFetchShapeTextPreview", "none")
        ghostBaseV10FRawSet("LastFetchShapeMedia", "none")
        ghostBaseV10FRawSet("LastFetchShapeAction", "none")

    case let .messageService(data):
        ghostBaseV10FRawRecord("fetchShapeMessageService")
        ghostBaseV10FRawSet("LastFetchShapeCase", "messageService")
        ghostBaseV10FRawSet("LastFetchShapeId", "\(data.id)")
        ghostBaseV10FRawSet("LastFetchShapeFlags", "\(data.flags)")
        ghostBaseV10FRawSet("LastFetchShapeFlags2", "none")
        ghostBaseV10FRawSet("LastFetchShapePeer", ghostBaseV10IShapePeer(data.peerId))
        ghostBaseV10FRawSet("LastFetchShapeFrom", ghostBaseV10IShapePeer(data.fromId))
        ghostBaseV10FRawSet("LastFetchShapeDate", "\(data.date)")
        ghostBaseV10FRawSet("LastFetchShapeTextLength", "0")
        ghostBaseV10FRawSet("LastFetchShapeTextPreview", "none")
        ghostBaseV10FRawSet("LastFetchShapeMedia", "none")
        ghostBaseV10FRawSet("LastFetchShapeAction", data.action.descriptionFields().0)
    }
}

'''
    anchor = "// MARK: GhostBase v1.0H Fetch Race Probe"
    core = replace_once(core, anchor, helper + "\n" + anchor, "insert v1.0I helper")

if 'ghostBaseV10IRecordFetchShape(apiMessage, source: "FetchRaceGlobalDelete")' not in core:
    core = replace_once(
        core,
        '''        for apiMessage in apiMessages {
            var peerIsForum = false
''',
        '''        for apiMessage in apiMessages {
            ghostBaseV10IRecordFetchShape(apiMessage, source: "FetchRaceGlobalDelete")
            var peerIsForum = false
''',
        "insert fetch response shape recorder"
    )

write(core_p, core)

if "fetchShapeSeen:" not in settings:
    settings = replace_once(
        settings,
        '''fetchRaceError: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "fetchRaceError.Count"))
LastSnapshotSource:''',
        '''fetchRaceError: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "fetchRaceError.Count"))
fetchShapeSeen: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "fetchShapeSeen.Count"))
fetchShapeMessage: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "fetchShapeMessage.Count"))
fetchShapeMessageEmpty: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "fetchShapeMessageEmpty.Count"))
fetchShapeMessageService: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "fetchShapeMessageService.Count"))
LastSnapshotSource:''',
        "insert shape counters"
    )

if "LastFetchShapeCase:" not in settings:
    settings = replace_once(
        settings,
        '''LastFetchRaceError: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchRaceError") ?? "none")
LastDeleteSnapshotKey:''',
        '''LastFetchRaceError: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchRaceError") ?? "none")
LastFetchShapeSource: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchShapeSource") ?? "none")
LastFetchShapeCase: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchShapeCase") ?? "none")
LastFetchShapeId: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchShapeId") ?? "none")
LastFetchShapeFlags: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchShapeFlags") ?? "none")
LastFetchShapeFlags2: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchShapeFlags2") ?? "none")
LastFetchShapePeer: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchShapePeer") ?? "none")
LastFetchShapeFrom: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchShapeFrom") ?? "none")
LastFetchShapeDate: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchShapeDate") ?? "none")
LastFetchShapeTextLength: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchShapeTextLength") ?? "none")
LastFetchShapeTextPreview: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchShapeTextPreview") ?? "none")
LastFetchShapeMedia: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchShapeMedia") ?? "none")
LastFetchShapeAction: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchShapeAction") ?? "none")
LastDeleteSnapshotKey:''',
        "insert shape last fields"
    )

settings = settings.replace("Version: v1.0H", "Version: v1.0I")
write(settings_p, settings)

core = read(core_p)
settings = read(settings_p)

ensure(core, "GhostBase v1.0I Fetch Response Shape Probe", "shape helper marker")
ensure(core, 'ghostBaseV10IRecordFetchShape(apiMessage, source: "FetchRaceGlobalDelete")', "shape call")
ensure(settings, "fetchShapeMessageEmpty:", "shape settings counters")
ensure(settings, "LastFetchShapeCase:", "shape settings fields")
ensure(settings, "Version: v1.0I", "settings version")

print("[v1.0I] Fetch Response Shape Probe patch OK")
