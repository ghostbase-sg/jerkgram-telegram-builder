#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"
BASE = ROOT / "scripts/apply_ghostbase_v10i_fetch_response_shape_probe.py"

def read(p):
    return Path(p).read_text()

def write(p, s):
    Path(p).write_text(s)

def ensure(s, needle, label):
    if needle not in s:
        raise SystemExit(f"[v1.0J] ERROR: missing {label}: {needle}")

def replace_once(s, old, new, label):
    if old in s:
        return s.replace(old, new, 1)
    if new in s:
        return s
    raise SystemExit(f"[v1.0J] ERROR: pattern not found: {label}")

print("[v1.0J] running base v1.0I patcher...")
subprocess.check_call([sys.executable, str(BASE)], cwd=str(ROOT))

core_p = SRC / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
settings_p = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

core = read(core_p)
settings = read(settings_p)

ensure(core, "GhostBase v1.0I Fetch Response Shape Probe", "v1.0I marker")
ensure(core, "ghostBaseV10HFetchRaceProbe(accountPeerId:", "v1.0H fetch race helper")
ensure(core, "ghostBaseV10IRecordFetchShape", "v1.0I shape helper")
ensure(settings, "LastFetchShapeCase:", "v1.0I settings")

helper_marker = "// MARK: GhostBase v1.0J History Around Tombstone Probe"

if helper_marker not in core:
    helper = r'''
// MARK: GhostBase v1.0J History Around Tombstone Probe
private func ghostBaseV10JRecordHistoryMessage(_ apiMessage: Api.Message, peerId: PeerId, requestedId: Int32, source: String) {
    ghostBaseV10FRawRecord("historyProbeMessageSeen")
    ghostBaseV10FRawSet("LastHistoryProbeSource", source)
    ghostBaseV10FRawSet("LastHistoryProbePeer", "\(peerId)")
    ghostBaseV10FRawSet("LastHistoryProbeRequestedId", "\(requestedId)")

    switch apiMessage {
    case let .message(data):
        ghostBaseV10FRawRecord("historyProbeMessage")
        ghostBaseV10FRawSet("LastHistoryProbeCase", "message")
        ghostBaseV10FRawSet("LastHistoryProbeId", "\(data.id)")
        ghostBaseV10FRawSet("LastHistoryProbePeerFromMessage", ghostBaseV10IShapePeer(data.peerId))
        ghostBaseV10FRawSet("LastHistoryProbeDate", "\(data.date)")
        ghostBaseV10FRawSet("LastHistoryProbeTextLength", "\(data.message.count)")
        ghostBaseV10FRawSet("LastHistoryProbeText", ghostBaseV10FRawPreview(data.message))
        ghostBaseV10FRawSet("LastHistoryProbeMedia", data.media?.descriptionFields().0 ?? "none")
        ghostBaseV10FRawSet("LastHistoryProbeAction", "none")
        if data.id == requestedId {
            ghostBaseV10FRawRecord("historyProbeExactId")
        }
        if !data.message.isEmpty {
            ghostBaseV10FRawRecord("historyProbeWithText")
        }

    case let .messageEmpty(data):
        ghostBaseV10FRawRecord("historyProbeMessageEmpty")
        ghostBaseV10FRawSet("LastHistoryProbeCase", "messageEmpty")
        ghostBaseV10FRawSet("LastHistoryProbeId", "\(data.id)")
        ghostBaseV10FRawSet("LastHistoryProbePeerFromMessage", ghostBaseV10IShapePeer(data.peerId))
        ghostBaseV10FRawSet("LastHistoryProbeDate", "none")
        ghostBaseV10FRawSet("LastHistoryProbeTextLength", "0")
        ghostBaseV10FRawSet("LastHistoryProbeText", "none")
        ghostBaseV10FRawSet("LastHistoryProbeMedia", "none")
        ghostBaseV10FRawSet("LastHistoryProbeAction", "none")
        if data.id == requestedId {
            ghostBaseV10FRawRecord("historyProbeExactEmptyId")
        }

    case let .messageService(data):
        ghostBaseV10FRawRecord("historyProbeMessageService")
        ghostBaseV10FRawSet("LastHistoryProbeCase", "messageService")
        ghostBaseV10FRawSet("LastHistoryProbeId", "\(data.id)")
        ghostBaseV10FRawSet("LastHistoryProbePeerFromMessage", ghostBaseV10IShapePeer(data.peerId))
        ghostBaseV10FRawSet("LastHistoryProbeDate", "\(data.date)")
        ghostBaseV10FRawSet("LastHistoryProbeTextLength", "0")
        ghostBaseV10FRawSet("LastHistoryProbeText", "none")
        ghostBaseV10FRawSet("LastHistoryProbeMedia", "none")
        ghostBaseV10FRawSet("LastHistoryProbeAction", data.action.descriptionFields().0)
        if data.id == requestedId {
            ghostBaseV10FRawRecord("historyProbeExactServiceId")
        }
    }
}
'''

    helper += r'''

private func ghostBaseV10JHistoryAroundTombstoneProbe(accountPeerId: PeerId, postbox: Postbox, network: Network, state: AccountMutableState, globalIds: [Int32], source: String) {
    guard !globalIds.isEmpty else {
        return
    }

    ghostBaseV10FRawRecord("historyProbeStarted")
    ghostBaseV10FRawRecord("historyProbeInputIds", amount: globalIds.count)
    ghostBaseV10FRawSet("LastHistoryProbeSource", source)
    ghostBaseV10FRawSet("LastHistoryProbeInputIdsCount", "\(globalIds.count)")
    ghostBaseV10FRawSet("LastHistoryProbeInputIds", globalIds.map { "\($0)" }.joined(separator: ","))

    let idsToProbe = Array(globalIds.prefix(4))
    let statePeerIds = Array(Set(Array(state.peers.keys) + Array(state.readInboxMaxIds.keys) + Array(state.storedMessagesByPeerIdAndTimestamp.keys) + Array(state.initialState.peerIds) + Array(state.initialState.channelStates.keys)))
    ghostBaseV10FRawSet("LastHistoryProbeStateCandidateCount", "\(statePeerIds.count)")

    let _ = fetchChatList(accountPeerId: accountPeerId, postbox: postbox, network: network, location: .general, upperBound: .absoluteUpperBound(), hash: 0, limit: 60).startStandalone(next: { fetched in
        var seen = Set<PeerId>()
        var candidates: [(PeerId, Api.InputPeer)] = []

        func addCandidate(peerId: PeerId, peer: Peer?) {
            if seen.contains(peerId) {
                return
            }
            guard let peer = peer, let inputPeer = apiInputPeer(peer) else {
                return
            }
            seen.insert(peerId)
            candidates.append((peerId, inputPeer))
        }

        if let fetched = fetched {
            ghostBaseV10FRawRecord("historyProbeChatListResponse")
            ghostBaseV10FRawSet("LastHistoryProbeChatListCount", "\(fetched.chatPeerIds.count)")
            for peerId in fetched.chatPeerIds {
                addCandidate(peerId: peerId, peer: fetched.peers.get(peerId))
            }
        } else {
            ghostBaseV10FRawRecord("historyProbeChatListNil")
            ghostBaseV10FRawSet("LastHistoryProbeChatListCount", "0")
        }

        for peerId in statePeerIds {
            addCandidate(peerId: peerId, peer: state.peers[peerId])
        }

        let limitedCandidates = Array(candidates.prefix(24))
        ghostBaseV10FRawRecord("historyProbeCandidatePeers", amount: limitedCandidates.count)
        ghostBaseV10FRawSet("LastHistoryProbeCandidateCount", "\(limitedCandidates.count)")
        ghostBaseV10FRawSet("LastHistoryProbeCandidatePeers", limitedCandidates.map { "\($0.0)" }.joined(separator: ","))

        if limitedCandidates.isEmpty {
            ghostBaseV10FRawRecord("historyProbeNoCandidates")
            return
        }

        for requestedId in idsToProbe {
            for (peerId, inputPeer) in limitedCandidates {
                ghostBaseV10FRawRecord("historyProbePeerTried")
                ghostBaseV10FRawSet("LastHistoryProbePeer", "\(peerId)")
                ghostBaseV10FRawSet("LastHistoryProbeRequestedId", "\(requestedId)")

                let signal = network.request(Api.functions.messages.getHistory(peer: inputPeer, offsetId: requestedId, offsetDate: 0, addOffset: -3, limit: 7, maxId: 0, minId: 0, hash: 0))
                |> map(Optional.init)
                |> `catch` { error -> Signal<Api.messages.Messages?, NoError> in
                    ghostBaseV10FRawRecord("historyProbeError")
                    ghostBaseV10FRawSet("LastHistoryProbeError", error.errorDescription)
                    ghostBaseV10FRawSet("LastHistoryProbePeer", "\(peerId)")
                    ghostBaseV10FRawSet("LastHistoryProbeRequestedId", "\(requestedId)")
                    return .single(nil)
                }

                let _ = signal.startStandalone(next: { result in
                    guard let result = result else {
                        ghostBaseV10FRawRecord("historyProbeNil")
                        return
                    }

                    var apiMessages: [Api.Message] = []
                    switch result {
                    case let .messages(data):
                        apiMessages = data.messages
                    case let .messagesSlice(data):
                        apiMessages = data.messages
                    case let .channelMessages(data):
                        apiMessages = data.messages
                    case .messagesNotModified:
                        break
                    }

                    ghostBaseV10FRawRecord("historyProbeResponse")
                    ghostBaseV10FRawSet("LastHistoryProbeApiMessageCount", "\(apiMessages.count)")
                    ghostBaseV10FRawSet("LastHistoryProbePeer", "\(peerId)")
                    ghostBaseV10FRawSet("LastHistoryProbeRequestedId", "\(requestedId)")

                    if apiMessages.isEmpty {
                        ghostBaseV10FRawRecord("historyProbeEmpty")
                        return
                    }

                    for apiMessage in apiMessages {
                        ghostBaseV10JRecordHistoryMessage(apiMessage, peerId: peerId, requestedId: requestedId, source: "HistoryAroundTombstone")
                    }
                })
            }
        }
    })
}

'''

    anchor = "// MARK: GhostBase v1.0I Fetch Response Shape Probe"
    core = replace_once(core, anchor, helper + "\n" + anchor, "insert v1.0J helper")

call = 'ghostBaseV10JHistoryAroundTombstoneProbe(accountPeerId: accountPeerId, postbox: postbox, network: network, state: updatedState, globalIds: updateDeleteMessagesData.messages, source: "UpdateDeleteMessages")'

if call not in core:
    core = replace_once(
        core,
        '''                ghostBaseV10HFetchRaceProbe(accountPeerId: accountPeerId, network: network, state: updatedState, globalIds: updateDeleteMessagesData.messages, source: "UpdateDeleteMessages")
                updatedState.deleteMessagesWithGlobalIds(updateDeleteMessagesData.messages)
''',
        '''                ghostBaseV10HFetchRaceProbe(accountPeerId: accountPeerId, network: network, state: updatedState, globalIds: updateDeleteMessagesData.messages, source: "UpdateDeleteMessages")
                ghostBaseV10JHistoryAroundTombstoneProbe(accountPeerId: accountPeerId, postbox: postbox, network: network, state: updatedState, globalIds: updateDeleteMessagesData.messages, source: "UpdateDeleteMessages")
                updatedState.deleteMessagesWithGlobalIds(updateDeleteMessagesData.messages)
''',
        "insert v1.0J call"
    )

write(core_p, core)

if "historyProbeStarted:" not in settings:
    settings = replace_once(
        settings,
        r'''fetchShapeMessageService: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "fetchShapeMessageService.Count"))
LastSnapshotSource:''',
        r'''fetchShapeMessageService: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "fetchShapeMessageService.Count"))
historyProbeStarted: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "historyProbeStarted.Count"))
historyProbeInputIds: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "historyProbeInputIds.Count"))
historyProbeChatListResponse: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "historyProbeChatListResponse.Count"))
historyProbeCandidatePeers: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "historyProbeCandidatePeers.Count"))
historyProbeNoCandidates: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "historyProbeNoCandidates.Count"))
historyProbePeerTried: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "historyProbePeerTried.Count"))
historyProbeResponse: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "historyProbeResponse.Count"))
historyProbeEmpty: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "historyProbeEmpty.Count"))
historyProbeMessage: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "historyProbeMessage.Count"))
historyProbeMessageEmpty: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "historyProbeMessageEmpty.Count"))
historyProbeMessageService: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "historyProbeMessageService.Count"))
historyProbeExactId: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "historyProbeExactId.Count"))
historyProbeExactEmptyId: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "historyProbeExactEmptyId.Count"))
historyProbeWithText: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "historyProbeWithText.Count"))
historyProbeError: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "historyProbeError.Count"))
LastSnapshotSource:''',
        "insert history counters"
    )

if "LastHistoryProbeCase:" not in settings:
    settings = replace_once(
        settings,
        r'''LastFetchShapeAction: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchShapeAction") ?? "none")
LastDeleteSnapshotKey:''',
        r'''LastFetchShapeAction: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchShapeAction") ?? "none")
LastHistoryProbeInputIdsCount: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastHistoryProbeInputIdsCount") ?? "none")
LastHistoryProbeStateCandidateCount: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastHistoryProbeStateCandidateCount") ?? "none")
LastHistoryProbeChatListCount: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastHistoryProbeChatListCount") ?? "none")
LastHistoryProbeCandidateCount: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastHistoryProbeCandidateCount") ?? "none")
LastHistoryProbeCandidatePeers: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastHistoryProbeCandidatePeers") ?? "none")
LastHistoryProbePeer: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastHistoryProbePeer") ?? "none")
LastHistoryProbeRequestedId: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastHistoryProbeRequestedId") ?? "none")
LastHistoryProbeApiMessageCount: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastHistoryProbeApiMessageCount") ?? "none")
LastHistoryProbeCase: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastHistoryProbeCase") ?? "none")
LastHistoryProbeId: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastHistoryProbeId") ?? "none")
LastHistoryProbePeerFromMessage: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastHistoryProbePeerFromMessage") ?? "none")
LastHistoryProbeDate: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastHistoryProbeDate") ?? "none")
LastHistoryProbeTextLength: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastHistoryProbeTextLength") ?? "none")
LastHistoryProbeText: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastHistoryProbeText") ?? "none")
LastHistoryProbeMedia: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastHistoryProbeMedia") ?? "none")
LastHistoryProbeAction: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastHistoryProbeAction") ?? "none")
LastHistoryProbeError: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastHistoryProbeError") ?? "none")
LastDeleteSnapshotKey:''',
        "insert history fields"
    )

settings = settings.replace("Version: v1.0I", "Version: v1.0J")
write(settings_p, settings)

core = read(core_p)
settings = read(settings_p)

ensure(core, "GhostBase v1.0J History Around Tombstone Probe", "v1.0J helper marker")
ensure(core, "ghostBaseV10JHistoryAroundTombstoneProbe(accountPeerId:", "v1.0J call")
ensure(core, "Api.functions.messages.getHistory(peer:", "getHistory call")
ensure(settings, "historyProbeStarted:", "history counters")
ensure(settings, "LastHistoryProbeCase:", "history fields")
ensure(settings, "Version: v1.0J", "settings version")

print("[v1.0J] History Around Tombstone Probe patch OK")
