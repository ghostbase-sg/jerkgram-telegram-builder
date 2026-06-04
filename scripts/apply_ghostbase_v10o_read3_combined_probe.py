#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/apply_ghostbase_v10n_sourcepeer_probe.py"

print("[v1.0O+READ3] applying base v1.0N...")
subprocess.check_call([sys.executable, str(BASE)], cwd=str(ROOT))

chat = ROOT / "work/swiftgram-src/submodules/TelegramUI/Sources/Chat/ChatControllerLoadDisplayNode.swift"
core_state = ROOT / "work/swiftgram-src/submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
readstats = ROOT / "work/swiftgram-src/submodules/TelegramCore/Sources/TelegramEngine/Messages/MessageReadStats.swift"
ctxmenu = ROOT / "work/swiftgram-src/submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"
settings = ROOT / "work/swiftgram-src/submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

def read(p):
    return p.read_text()

def write(p, s):
    p.write_text(s)

def need(s, needle, label):
    if needle not in s:
        raise SystemExit(f"[v1.0O+READ3] ERROR: missing {label}: {needle}")

print("[v1.0O+READ3] patching combined probe...")

# A1) SourcePeer UI capture: save persistent copy outside GhostBase.V10F.Raw.*.
s = read(chat)

old = '''    UserDefaults.standard.set(peerId.toInt64(), forKey: prefix + "NLastSourcePeerIdRaw")
    UserDefaults.standard.set("\\(peerId)", forKey: prefix + "NLastSourcePeerId")
    UserDefaults.standard.set(source, forKey: prefix + "NLastSourcePeerSource")
    UserDefaults.standard.set(Date().timeIntervalSince1970, forKey: prefix + "NLastSourcePeerSavedAt")
'''

new = '''    let ghostBaseSourcePeerRaw = peerId.toInt64()
    UserDefaults.standard.set(ghostBaseSourcePeerRaw, forKey: prefix + "NLastSourcePeerIdRaw")
    UserDefaults.standard.set("\\(peerId)", forKey: prefix + "NLastSourcePeerId")
    UserDefaults.standard.set(source, forKey: prefix + "NLastSourcePeerSource")
    UserDefaults.standard.set(Date().timeIntervalSince1970, forKey: prefix + "NLastSourcePeerSavedAt")

    // MARK: GhostBase v1.0O persistent SourcePeer candidate
    UserDefaults.standard.set(ghostBaseSourcePeerRaw, forKey: "GhostBase.V10O.Persistent.SourcePeerIdRaw")
    UserDefaults.standard.set("\\(peerId)", forKey: "GhostBase.V10O.Persistent.SourcePeerId")
    UserDefaults.standard.set(source, forKey: "GhostBase.V10O.Persistent.SourcePeerSource")
    UserDefaults.standard.set(Date().timeIntervalSince1970, forKey: "GhostBase.V10O.Persistent.SourcePeerSavedAt")
'''

if old not in s:
    raise SystemExit("[v1.0O+READ3] ERROR: SourcePeer UI save block not found")

s = s.replace(old, new, 1)
write(chat, s)

# A2) SourcePeer Core fallback: raw diagnostics may be reset on launch, persistent key must survive.
s = read(core_state)

old = 'let sourcePeerRaw = UserDefaults.standard.object(forKey: ghostBaseV10NRawKey("NLastSourcePeerIdRaw")) as? Int64'

new = '''let runtimeSourcePeerRaw = UserDefaults.standard.object(forKey: ghostBaseV10NRawKey("NLastSourcePeerIdRaw")) as? Int64
        let persistedSourcePeerRaw = UserDefaults.standard.object(forKey: "GhostBase.V10O.Persistent.SourcePeerIdRaw") as? Int64
        let sourcePeerRaw: Int64?

        if let runtimeSourcePeerRaw, runtimeSourcePeerRaw != 0 {
            sourcePeerRaw = runtimeSourcePeerRaw
            ghostBaseV10NSet("OSourcePeerCandidateStatus", "runtime")
        } else if let persistedSourcePeerRaw, persistedSourcePeerRaw != 0 {
            sourcePeerRaw = persistedSourcePeerRaw
            ghostBaseV10NSet("OSourcePeerCandidateStatus", "persisted")
        } else {
            sourcePeerRaw = nil
            ghostBaseV10NSet("OSourcePeerCandidateStatus", "missing")
        }

        ghostBaseV10NSet("OSourcePeerRuntimeRaw", "\\(runtimeSourcePeerRaw ?? 0)")
        ghostBaseV10NSet("OSourcePeerPersistedRaw", "\\(persistedSourcePeerRaw ?? 0)")
        ghostBaseV10NSet("OSourcePeerUsedRaw", "\\(sourcePeerRaw ?? 0)")'''

count = s.count(old)
if count < 2:
    raise SystemExit(f"[v1.0O+READ3] ERROR: expected at least 2 SourcePeer raw reads, got {count}")

s = s.replace(old, new)
write(core_state, s)

# B1) READ3 runtime logging in MessageReadStats.swift.
s = read(readstats)

if "import Foundation" not in s:
    s = s.replace("import Postbox", "import Foundation\nimport Postbox", 1)

old = '''func _internal_messageReadStats(account: Account, id: MessageId) -> Signal<MessageReadStats?, NoError> {
    return account.postbox.transaction { transaction -> Peer? in
'''

new = '''func _internal_messageReadStats(account: Account, id: MessageId) -> Signal<MessageReadStats?, NoError> {
    UserDefaults.standard.set(id.peerId.toInt64(), forKey: "GhostBase.READ3.LastPeerIdRaw")
    UserDefaults.standard.set(id.id, forKey: "GhostBase.READ3.LastMessageId")
    UserDefaults.standard.set(Int(Date().timeIntervalSince1970), forKey: "GhostBase.READ3.LastRequestAt")
    UserDefaults.standard.set("started", forKey: "GhostBase.READ3.FinalVerdict")
    return account.postbox.transaction { transaction -> Peer? in
'''

if old not in s:
    raise SystemExit("[v1.0O+READ3] ERROR: MessageReadStats function header not found")

s = s.replace(old, new, 1)

old = '''            let readPeers: Signal<[(Int64, Int32)]?, NoError> = account.network.request(Api.functions.messages.getMessageReadParticipants(peer: inputPeer, msgId: id.id))
            |> map { result -> [(Int64, Int32)]? in
                var items: [(Int64, Int32)] = []
                for item in result {
'''

new = '''            UserDefaults.standard.set("getMessageReadParticipants", forKey: "GhostBase.READ3.LastApi")
            UserDefaults.standard.set("requesting", forKey: "GhostBase.READ3.FinalVerdict")

            let readPeers: Signal<[(Int64, Int32)]?, NoError> = account.network.request(Api.functions.messages.getMessageReadParticipants(peer: inputPeer, msgId: id.id))
            |> map { result -> [(Int64, Int32)]? in
                UserDefaults.standard.set(result.count, forKey: "GhostBase.READ3.ForcedApiRawCount")
                UserDefaults.standard.set("response", forKey: "GhostBase.READ3.LastResponse")
                var items: [(Int64, Int32)] = []
                for item in result {
'''

if old not in s:
    raise SystemExit("[v1.0O+READ3] ERROR: getMessageReadParticipants block not found")

s = s.replace(old, new, 1)

old = '''                return items
            }
            |> `catch` { _ -> Signal<[(Int64, Int32)]?, NoError> in
                return .single(nil)
            }
'''

new = '''                UserDefaults.standard.set(items.count, forKey: "GhostBase.READ3.ForcedCount")
                if let first = items.first {
                    UserDefaults.standard.set(first.0, forKey: "GhostBase.READ3.FirstUserId")
                    UserDefaults.standard.set(first.1, forKey: "GhostBase.READ3.FirstReadDate")
                }
                if items.isEmpty {
                    UserDefaults.standard.set("MESSAGE_NOT_READ_OR_EMPTY", forKey: "GhostBase.READ3.FinalVerdict")
                } else {
                    UserDefaults.standard.set("EXACT_READERS_FOUND", forKey: "GhostBase.READ3.FinalVerdict")
                }
                return items
            }
            |> `catch` { error -> Signal<[(Int64, Int32)]?, NoError> in
                UserDefaults.standard.set("\\(error)", forKey: "GhostBase.READ3.LastErrorRaw")
                UserDefaults.standard.set("RESTRICTED_BY_TELEGRAM_API_OR_ERROR", forKey: "GhostBase.READ3.FinalVerdict")
                return .single(nil)
            }
'''

if old not in s:
    raise SystemExit("[v1.0O+READ3] ERROR: readParticipants catch block not found")

s = s.replace(old, new, 1)
write(readstats, s)

# B2) READ3: force normal Telegram read-report item for large groups/megagroups.
s = read(ctxmenu)

anchor = '''private func canViewReadStats(message: Message, participantCount: Int?, isMessageRead: Bool, isPremium: Bool, appConfig: AppConfiguration) -> Bool {
'''

helper = r'''
// MARK: GhostBase READ3 force read reports in large groups/supergroups
private func ghostBaseREAD3ShouldForceReadStats(message: Message, participantCount: Int?, isMessageRead: Bool, appConfig: AppConfiguration) -> Bool {
    guard let peer = message.peers[message.id.peerId] else {
        return false
    }
    if message.id.namespace != Namespaces.Message.Cloud {
        return false
    }
    if message.flags.contains(.Incoming) {
        return false
    }
    if !isMessageRead {
        return false
    }

    var maxParticipantCount = 50
    if let data = appConfig.data, let value = data["chat_read_mark_size_threshold"] as? Double {
        maxParticipantCount = Int(value)
    }

    var shouldForce = false
    var peerType = "unknown"

    switch peer {
    case let channel as TelegramChannel:
        if case .broadcast = channel.info {
            peerType = "broadcast"
            shouldForce = false
        } else {
            peerType = "megagroup"
            if let participantCount = participantCount {
                shouldForce = participantCount > maxParticipantCount
            } else {
                shouldForce = true
            }
        }
    case let group as TelegramGroup:
        peerType = "group"
        shouldForce = group.participantCount > maxParticipantCount
    default:
        peerType = "other"
        shouldForce = false
    }

    if shouldForce {
        UserDefaults.standard.set(message.id.peerId.toInt64(), forKey: "GhostBase.READ3.UI.PeerIdRaw")
        UserDefaults.standard.set(message.id.id, forKey: "GhostBase.READ3.UI.MessageId")
        UserDefaults.standard.set(peerType, forKey: "GhostBase.READ3.UI.PeerType")
        UserDefaults.standard.set(participantCount ?? -1, forKey: "GhostBase.READ3.UI.ParticipantCount")
        UserDefaults.standard.set(maxParticipantCount, forKey: "GhostBase.READ3.UI.Threshold")
        UserDefaults.standard.set("forcedReadReportItem", forKey: "GhostBase.READ3.UI.Action")
    }

    return shouldForce
}

'''

if helper not in s:
    if anchor not in s:
        raise SystemExit("[v1.0O+READ3] ERROR: canViewReadStats anchor not found")
    s = s.replace(anchor, helper + anchor, 1)

old = '''        } else if let messageReadStatsAreHidden = infoSummaryData.messageReadStatsAreHidden, !messageReadStatsAreHidden {
            canViewStats = canViewReadStats(message: message, participantCount: infoSummaryData.participantCount, isMessageRead: isMessageRead, isPremium: isPremium, appConfig: appConfig)
        }
'''

new = '''        } else if let messageReadStatsAreHidden = infoSummaryData.messageReadStatsAreHidden, !messageReadStatsAreHidden {
            canViewStats = canViewReadStats(message: message, participantCount: infoSummaryData.participantCount, isMessageRead: isMessageRead, isPremium: isPremium, appConfig: appConfig)
            if !canViewStats && ghostBaseREAD3ShouldForceReadStats(message: message, participantCount: infoSummaryData.participantCount, isMessageRead: isMessageRead, appConfig: appConfig) {
                canViewStats = true
            }
        }
'''

if old not in s:
    raise SystemExit("[v1.0O+READ3] ERROR: canViewStats assignment block not found")

s = s.replace(old, new, 1)
write(ctxmenu, s)

# C) Settings diagnostics for v1.0O+READ3.
s = read(settings)

s = s.replace("Version: v1.0N", "Version: v1.0O+READ3")
s = s.replace("v1.0N SourcePeer Verdict:", "v1.0O SourcePeer Verdict:")

anchor = '''v1.0O SourcePeer Verdict:
NSourcePeerVerdict:'''

insert = '''v1.0O Persistent SourcePeer Candidate:
OSourcePeerPersistedRaw: \\(UserDefaults.standard.object(forKey: "GhostBase.V10O.Persistent.SourcePeerIdRaw") as? Int64 ?? 0)
OSourcePeerPersistedId: \\(UserDefaults.standard.string(forKey: "GhostBase.V10O.Persistent.SourcePeerId") ?? "none")
OSourcePeerPersistedSource: \\(UserDefaults.standard.string(forKey: "GhostBase.V10O.Persistent.SourcePeerSource") ?? "none")
OSourcePeerRuntimeRaw: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "OSourcePeerRuntimeRaw") ?? "none")
OSourcePeerPersistedRawLastUse: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "OSourcePeerPersistedRaw") ?? "none")
OSourcePeerUsedRaw: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "OSourcePeerUsedRaw") ?? "none")
OSourcePeerCandidateStatus: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "OSourcePeerCandidateStatus") ?? "none")

READ3 Runtime Probe:
R3UIPeerIdRaw: \\(UserDefaults.standard.object(forKey: "GhostBase.READ3.UI.PeerIdRaw") as? Int64 ?? 0)
R3UIMessageId: \\(UserDefaults.standard.object(forKey: "GhostBase.READ3.UI.MessageId") as? Int32 ?? 0)
R3UIPeerType: \\(UserDefaults.standard.string(forKey: "GhostBase.READ3.UI.PeerType") ?? "none")
R3UIParticipantCount: \\(UserDefaults.standard.object(forKey: "GhostBase.READ3.UI.ParticipantCount") as? Int ?? -2)
R3UIThreshold: \\(UserDefaults.standard.object(forKey: "GhostBase.READ3.UI.Threshold") as? Int ?? -1)
R3UIAction: \\(UserDefaults.standard.string(forKey: "GhostBase.READ3.UI.Action") ?? "none")
R3LastPeerIdRaw: \\(UserDefaults.standard.object(forKey: "GhostBase.READ3.LastPeerIdRaw") as? Int64 ?? 0)
R3LastMessageId: \\(UserDefaults.standard.object(forKey: "GhostBase.READ3.LastMessageId") as? Int32 ?? 0)
R3LastApi: \\(UserDefaults.standard.string(forKey: "GhostBase.READ3.LastApi") ?? "none")
R3LastResponse: \\(UserDefaults.standard.string(forKey: "GhostBase.READ3.LastResponse") ?? "none")
R3ForcedApiRawCount: \\(UserDefaults.standard.object(forKey: "GhostBase.READ3.ForcedApiRawCount") as? Int ?? -1)
R3ForcedCount: \\(UserDefaults.standard.object(forKey: "GhostBase.READ3.ForcedCount") as? Int ?? -1)
R3FirstUserId: \\(UserDefaults.standard.object(forKey: "GhostBase.READ3.FirstUserId") as? Int64 ?? 0)
R3FirstReadDate: \\(UserDefaults.standard.object(forKey: "GhostBase.READ3.FirstReadDate") as? Int32 ?? 0)
R3LastErrorRaw: \\(UserDefaults.standard.string(forKey: "GhostBase.READ3.LastErrorRaw") ?? "none")
R3FinalVerdict: \\(UserDefaults.standard.string(forKey: "GhostBase.READ3.FinalVerdict") ?? "none")

v1.0O SourcePeer Verdict:
NSourcePeerVerdict:'''

if anchor not in s:
    raise SystemExit("[v1.0O+READ3] ERROR: settings sourcepeer anchor not found")

s = s.replace(anchor, insert, 1)
write(settings, s)

for p, needle, label in [
    (chat, "GhostBase.V10O.Persistent.SourcePeerIdRaw", "persistent SourcePeer write"),
    (core_state, "OSourcePeerUsedRaw", "SourcePeer persistent fallback"),
    (readstats, "GhostBase.READ3.FinalVerdict", "READ3 MessageReadStats logging"),
    (ctxmenu, "ghostBaseREAD3ShouldForceReadStats", "READ3 UI unlock"),
    (settings, "Version: v1.0O+READ3", "combined version"),
    (settings, "READ3 Runtime Probe:", "READ3 settings block"),
]:
    need(read(p), needle, label)

print("[v1.0O+READ3] OK: combined probe applied")
