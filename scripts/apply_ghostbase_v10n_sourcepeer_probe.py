#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"
BASE = ROOT / "scripts/apply_ghostbase_v10m_current_target_lock_probe.py"

def read(p):
    return Path(p).read_text()

def write(p, s):
    Path(p).write_text(s)

def ensure(s, needle, label):
    if needle not in s:
        raise SystemExit(f"[v1.0N] ERROR: missing {label}: {needle}")

def replace_once(s, old, new, label):
    if old in s:
        return s.replace(old, new, 1)
    if new in s:
        return s
    raise SystemExit(f"[v1.0N] ERROR: pattern not found: {label}")

print("[v1.0N] running base v1.0M patcher...")
subprocess.check_call([sys.executable, str(BASE)], cwd=str(ROOT))

core_p = SRC / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
settings_p = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
chat_p = SRC / "submodules/TelegramUI/Sources/Chat/ChatControllerLoadDisplayNode.swift"

core = read(core_p)
settings = read(settings_p)
chat = read(chat_p)

ensure(core, "ghostBaseV10JHistoryAroundTombstoneProbe", "history probe")
ensure(settings, "Version: v1.0M", "settings v1.0M")
ensure(settings, "v1.0M Current Test Verdict:", "v1.0M block")
ensure(chat, "self.chatLocation.peerId", "chat source peer line")

ui_marker = "// MARK: GhostBase v1.0N SourcePeer UI Probe"

if ui_marker not in chat:
    helper = r'''
// MARK: GhostBase v1.0N SourcePeer UI Probe
private func ghostBaseV10NSaveSourcePeerId(_ peerId: PeerId, source: String) {
    let prefix = "GhostBase.V10F.Raw."
    UserDefaults.standard.set(peerId.toInt64(), forKey: prefix + "NLastSourcePeerIdRaw")
    UserDefaults.standard.set("\(peerId)", forKey: prefix + "NLastSourcePeerId")
    UserDefaults.standard.set(source, forKey: prefix + "NLastSourcePeerSource")
    UserDefaults.standard.set(Date().timeIntervalSince1970, forKey: prefix + "NLastSourcePeerSavedAt")
    let key = prefix + "nSourcePeerSaved.Count"
    UserDefaults.standard.set(UserDefaults.standard.integer(forKey: key) + 1, forKey: key)
}

'''
    # Insert after imports by placing before first final/private class extension marker if possible.
    if "private final class" in chat:
        chat = chat.replace("private final class", helper + "\nprivate final class", 1)
    elif "final class" in chat:
        chat = chat.replace("final class", helper + "\nfinal class", 1)
    else:
        # fallback: after imports area, before first extension
        chat = chat.replace("extension ChatControllerImpl", helper + "\nextension ChatControllerImpl", 1)

if "ghostBaseV10NSaveSourcePeerId(peerId" not in chat:
    # Safest patch: after the first `if let peerId = self.chatLocation.peerId {`
    old = "if let peerId = self.chatLocation.peerId {"
    new = '''if let peerId = self.chatLocation.peerId {
            ghostBaseV10NSaveSourcePeerId(peerId, source: "ChatControllerLoadDisplayNode")'''
    if old not in chat:
        raise SystemExit("[v1.0N] ERROR: no `if let peerId = self.chatLocation.peerId {` anchor")
    chat = chat.replace(old, new, 1)

write(chat_p, chat)

marker = "// MARK: GhostBase v1.0N SourcePeer Probe"

if marker not in core:
    helper = r'''
// MARK: GhostBase v1.0N SourcePeer Probe
private func ghostBaseV10NRawKey(_ key: String) -> String {
    return "GhostBase.V10F.Raw." + key
}

private func ghostBaseV10NSet(_ key: String, _ value: String) {
    UserDefaults.standard.set(value, forKey: ghostBaseV10NRawKey(key))
}

private func ghostBaseV10NRecord(_ name: String, amount: Int = 1) {
    guard amount > 0 else {
        return
    }
    let key = ghostBaseV10NRawKey(name + ".Count")
    UserDefaults.standard.set(UserDefaults.standard.integer(forKey: key) + amount, forKey: key)
}

private func ghostBaseV10NContainsTarget(_ text: String) -> Bool {
    return text.contains("N_D_") || text.contains("N_KEEP_")
}

private func ghostBaseV10NMarker(_ text: String) -> String {
    for part in text.components(separatedBy: CharacterSet.whitespacesAndNewlines) {
        if part.contains("N_D_") || part.contains("N_KEEP_") {
            return part
        }
    }
    return "none"
}

'''
    anchor = "// MARK: GhostBase v1.0M Current Target Lock Probe"
    core = replace_once(core, anchor, helper + "\n" + anchor, "insert v1.0N helper")

old = '''        if let fetched = fetched {
            ghostBaseV10FRawRecord("historyProbeChatListResponse")
            ghostBaseV10FRawSet("LastHistoryProbeChatListCount", "\\(fetched.chatPeerIds.count)")
            for peerId in fetched.chatPeerIds {
                addCandidate(peerId: peerId, peer: fetched.peers.get(peerId))
            }
        } else {
'''

new = '''        let sourcePeerRaw = UserDefaults.standard.object(forKey: ghostBaseV10NRawKey("NLastSourcePeerIdRaw")) as? Int64
        if let sourcePeerRaw = sourcePeerRaw {
            let sourcePeerId = PeerId(sourcePeerRaw)
            ghostBaseV10NRecord("nSourcePeerPresent")
            ghostBaseV10NSet("NSourcePeerId", "\\(sourcePeerId)")
            ghostBaseV10NSet("NSourcePeerRaw", "\\(sourcePeerRaw)")

            if let sourcePeer = state.peers[sourcePeerId] {
                ghostBaseV10NRecord("nSourcePeerInStatePeers")
                addCandidate(peerId: sourcePeerId, peer: sourcePeer)
                ghostBaseV10NSet("NSourcePeerCandidateStatus", "addedFromStatePeers")
            } else {
                ghostBaseV10NRecord("nSourcePeerMissingFromStatePeers")
                ghostBaseV10NSet("NSourcePeerCandidateStatus", "missingFromStatePeers")
            }
        } else {
            ghostBaseV10NRecord("nSourcePeerMissing")
            ghostBaseV10NSet("NSourcePeerCandidateStatus", "missing")
        }

        if let fetched = fetched {
            ghostBaseV10FRawRecord("historyProbeChatListResponse")
            ghostBaseV10FRawSet("LastHistoryProbeChatListCount", "\\(fetched.chatPeerIds.count)")
            for peerId in fetched.chatPeerIds {
                addCandidate(peerId: peerId, peer: fetched.peers.get(peerId))
            }
        } else {
'''

core = replace_once(core, old, new, "insert source peer candidate before chatlist candidates")

old = '''                    for apiMessage in apiMessages {
                        ghostBaseV10JRecordHistoryMessage(apiMessage, peerId: peerId, requestedId: requestedId, source: "HistoryAroundTombstone")
                    }
'''

new = '''                    let sourcePeerRaw = UserDefaults.standard.object(forKey: ghostBaseV10NRawKey("NLastSourcePeerIdRaw")) as? Int64
                    let isSourcePeer = sourcePeerRaw != nil && peerId == PeerId(sourcePeerRaw!)

                    if isSourcePeer {
                        ghostBaseV10NRecord("nSourcePeerHistoryResponse")
                        ghostBaseV10NSet("NSourcePeerLastRequestedId", "\\(requestedId)")
                        ghostBaseV10NSet("NSourcePeerLastApiMessageCount", "\\(apiMessages.count)")
                    }

                    for apiMessage in apiMessages {
                        ghostBaseV10JRecordHistoryMessage(apiMessage, peerId: peerId, requestedId: requestedId, source: isSourcePeer ? "SourcePeerHistoryAroundTombstone" : "HistoryAroundTombstone")

                        if isSourcePeer {
                            switch apiMessage {
                            case let .message(data):
                                if data.id == requestedId {
                                    ghostBaseV10NRecord("nSourcePeerExactMessage")
                                    ghostBaseV10NSet("NSourcePeerExactTextLength", "\\(data.message.count)")
                                    ghostBaseV10NSet("NSourcePeerExactText", ghostBaseV10FRawPreview(data.message, limit: 180))
                                    if ghostBaseV10NContainsTarget(data.message) {
                                        ghostBaseV10NRecord("nSourcePeerTargetHit")
                                        ghostBaseV10NSet("NSourcePeerTargetMarker", ghostBaseV10NMarker(data.message))
                                        ghostBaseV10NSet("NSourcePeerTargetText", ghostBaseV10FRawPreview(data.message, limit: 180))
                                        ghostBaseV10NSet("NSourcePeerVerdict", "SOURCE_PEER_TARGET_TEXT")
                                    } else if data.message.isEmpty {
                                        ghostBaseV10NSet("NSourcePeerVerdict", "SOURCE_PEER_EXACT_EMPTY_TEXT")
                                    } else {
                                        ghostBaseV10NRecord("nSourcePeerExactNonTargetText")
                                        ghostBaseV10NSet("NSourcePeerVerdict", "SOURCE_PEER_EXACT_NON_TARGET_TEXT")
                                    }
                                } else if ghostBaseV10NContainsTarget(data.message) {
                                    ghostBaseV10NRecord("nSourcePeerNonExactTargetHit")
                                    ghostBaseV10NSet("NSourcePeerTargetMarker", ghostBaseV10NMarker(data.message))
                                    ghostBaseV10NSet("NSourcePeerTargetText", ghostBaseV10FRawPreview(data.message, limit: 180))
                                    ghostBaseV10NSet("NSourcePeerVerdict", "SOURCE_PEER_NON_EXACT_TARGET_TEXT")
                                }
                            case let .messageEmpty(data):
                                if data.id == requestedId {
                                    ghostBaseV10NRecord("nSourcePeerExactEmpty")
                                    ghostBaseV10NSet("NSourcePeerVerdict", "SOURCE_PEER_EXACT_MESSAGE_EMPTY")
                                }
                            case let .messageService(data):
                                if data.id == requestedId {
                                    ghostBaseV10NRecord("nSourcePeerExactService")
                                    ghostBaseV10NSet("NSourcePeerVerdict", "SOURCE_PEER_EXACT_SERVICE")
                                }
                            }
                        }
                    }
'''

core = replace_once(core, old, new, "patch source peer hit detector")

if "v1.0N SourcePeer Verdict:" not in settings:
    summary = r'''v1.0N SourcePeer Verdict:
NSourcePeerVerdict: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "NSourcePeerVerdict") ?? "none")
NLastSourcePeerId: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "NLastSourcePeerId") ?? "none")
NLastSourcePeerIdRaw: \(ghostBaseRawDefaultsV10F.object(forKey: ghostBaseRawPrefixV10F + "NLastSourcePeerIdRaw") as? Int64 ?? 0)
NLastSourcePeerSource: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "NLastSourcePeerSource") ?? "none")
NSourcePeerSaved: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "nSourcePeerSaved.Count"))

NSourcePeerCandidateStatus: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "NSourcePeerCandidateStatus") ?? "none")
NSourcePeerPresent: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "nSourcePeerPresent.Count"))
NSourcePeerMissing: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "nSourcePeerMissing.Count"))
NSourcePeerInStatePeers: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "nSourcePeerInStatePeers.Count"))
NSourcePeerMissingFromStatePeers: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "nSourcePeerMissingFromStatePeers.Count"))

NSourcePeerHistoryResponse: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "nSourcePeerHistoryResponse.Count"))
NSourcePeerLastRequestedId: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "NSourcePeerLastRequestedId") ?? "none")
NSourcePeerLastApiMessageCount: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "NSourcePeerLastApiMessageCount") ?? "none")

NSourcePeerTargetHit: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "nSourcePeerTargetHit.Count"))
NSourcePeerNonExactTargetHit: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "nSourcePeerNonExactTargetHit.Count"))
NSourcePeerTargetMarker: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "NSourcePeerTargetMarker") ?? "none")
NSourcePeerTargetText: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "NSourcePeerTargetText") ?? "none")

NSourcePeerExactMessage: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "nSourcePeerExactMessage.Count"))
NSourcePeerExactEmpty: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "nSourcePeerExactEmpty.Count"))
NSourcePeerExactService: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "nSourcePeerExactService.Count"))
NSourcePeerExactTextLength: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "NSourcePeerExactTextLength") ?? "none")
NSourcePeerExactText: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "NSourcePeerExactText") ?? "none")

'''
    settings = settings.replace("v1.0M Current Test Verdict:", summary + "v1.0M Current Test Verdict:", 1)

settings = settings.replace("Version: v1.0M", "Version: v1.0N")
write(settings_p, settings)
write(core_p, core)

core = read(core_p)
settings = read(settings_p)
chat = read(chat_p)

ensure(chat, "ghostBaseV10NSaveSourcePeerId", "UI save helper")
ensure(chat, "NLastSourcePeerIdRaw", "UI raw peer save")
ensure(core, "GhostBase v1.0N SourcePeer Probe", "core helper")
ensure(core, "NSourcePeerVerdict", "source peer verdict")
ensure(core, "SOURCE_PEER_TARGET_TEXT", "target hit verdict")
ensure(settings, "v1.0N SourcePeer Verdict:", "settings sourcepeer block")
ensure(settings, "Version: v1.0N", "settings version")

print("[v1.0N] SourcePeer Probe patch OK")
