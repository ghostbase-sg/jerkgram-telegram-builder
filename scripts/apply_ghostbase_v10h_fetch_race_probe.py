#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"
BASE = ROOT / "scripts/apply_ghostbase_v10g_global_delete_resolver_bridge.py"

def read(p):
    return Path(p).read_text()

def write(p, s):
    Path(p).write_text(s)

def ensure(s, needle, label):
    if needle not in s:
        raise SystemExit(f"[v1.0H] ERROR: missing {label}: {needle}")

def replace_once(s, old, new, label):
    if old in s:
        return s.replace(old, new, 1)
    if new in s:
        return s
    raise SystemExit(f"[v1.0H] ERROR: pattern not found: {label}")

print("[v1.0H] running base v1.0G patcher...")
subprocess.check_call([sys.executable, str(BASE)], cwd=str(ROOT))

core_p = SRC / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
settings_p = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

core = read(core_p)
settings = read(settings_p)

ensure(core, "Api.functions.messages.getMessages", "messages.getMessages available")
ensure(core, "ghostBaseV10FRawDeleteGlobalHit", "v1.0F raw helper")
ensure(core, "deleteGlobalResolverSeen", "v1.0G resolver")
ensure(settings, "Raw Difference Snapshot Probe:", "raw settings")

helper_marker = "// MARK: GhostBase v1.0H Fetch Race Probe"

if helper_marker not in core:
    helper = r'''
// MARK: GhostBase v1.0H Fetch Race Probe
private func ghostBaseV10HFetchRaceProbe(accountPeerId: PeerId, network: Network, state: AccountMutableState, globalIds: [Int32], source: String) {
    guard !globalIds.isEmpty else {
        return
    }

    ghostBaseV10FRawRecord("fetchRaceStarted")
    ghostBaseV10FRawRecord("fetchRaceIds", amount: globalIds.count)
    ghostBaseV10FRawSet("LastFetchRaceSource", source)
    ghostBaseV10FRawSet("LastFetchRaceIdsCount", "\(globalIds.count)")
    ghostBaseV10FRawSet("LastFetchRaceInputIds", globalIds.map { "\($0)" }.joined(separator: ","))

    let signal = network.request(Api.functions.messages.getMessages(id: globalIds.map { Api.InputMessage.inputMessageID(.init(id: $0)) }))
    |> map(Optional.init)
    |> `catch` { error -> Signal<Api.messages.Messages?, NoError> in
        ghostBaseV10FRawRecord("fetchRaceError")
        ghostBaseV10FRawSet("LastFetchRaceError", error.errorDescription)
        return .single(nil)
    }

    let _ = signal.startStandalone(next: { result in
        guard let result = result else {
            ghostBaseV10FRawRecord("fetchRaceNil")
            return
        }

        var apiMessages: [Api.Message] = []
        var chats: [Api.Chat] = []
        var users: [Api.User] = []

        switch result {
        case let .messages(data):
            apiMessages = data.messages
            chats = data.chats
            users = data.users
        case let .messagesSlice(data):
            apiMessages = data.messages
            chats = data.chats
            users = data.users
        case let .channelMessages(data):
            apiMessages = data.messages
            chats = data.chats
            users = data.users
        case .messagesNotModified:
            break
        }

        ghostBaseV10FRawRecord("fetchRaceResponse")
        ghostBaseV10FRawSet("LastFetchRaceApiMessageCount", "\(apiMessages.count)")
        ghostBaseV10FRawSet("LastFetchRaceChatsCount", "\(chats.count)")
        ghostBaseV10FRawSet("LastFetchRaceUsersCount", "\(users.count)")

        if apiMessages.isEmpty {
            ghostBaseV10FRawRecord("fetchRaceEmpty")
            return
        }

        for apiMessage in apiMessages {
            var peerIsForum = false
            if let peerId = apiMessage.peerId {
                peerIsForum = state.isPeerForum(peerId: peerId)
            }

            if let message = StoreMessage(apiMessage: apiMessage, accountPeerId: accountPeerId, peerIsForum: peerIsForum) {
                ghostBaseV10FRawRecord("fetchRaceStoreMessage")
                ghostBaseV10FRawSnapshot(message: message, source: "FetchRaceGlobalDelete")

                if !message.text.isEmpty {
                    ghostBaseV10FRawRecord("fetchRaceWithText")
                    ghostBaseV10FRawSet("LastFetchRaceText", ghostBaseV10FRawPreview(message.text))
                    if case let .Id(messageId) = message.id {
                        ghostBaseV10FRawSet("LastFetchRaceMessageKey", ghostBaseV10FRawMessageKey(messageId))
                    }
                } else {
                    ghostBaseV10FRawRecord("fetchRaceEmptyText")
                }
            } else {
                ghostBaseV10FRawRecord("fetchRaceStoreFail")
            }
        }
    })
}

'''
    anchor = "// MARK: GhostBase v1.0B Core Difference Diagnostics"
    core = replace_once(core, anchor, helper + "\n" + anchor, "insert v1.0H helper")

if 'ghostBaseV10HFetchRaceProbe(accountPeerId: accountPeerId, network: network, state: updatedState, globalIds: updateDeleteMessagesData.messages, source: "UpdateDeleteMessages")' not in core:
    core = replace_once(
        core,
        '''                ghostBaseV10FRawDeleteGlobalHit(globalIds: updateDeleteMessagesData.messages, source: "UpdateDeleteMessages")
                updatedState.deleteMessagesWithGlobalIds(updateDeleteMessagesData.messages)
''',
        '''                ghostBaseV10FRawDeleteGlobalHit(globalIds: updateDeleteMessagesData.messages, source: "UpdateDeleteMessages")
                ghostBaseV10HFetchRaceProbe(accountPeerId: accountPeerId, network: network, state: updatedState, globalIds: updateDeleteMessagesData.messages, source: "UpdateDeleteMessages")
                updatedState.deleteMessagesWithGlobalIds(updateDeleteMessagesData.messages)
''',
        "insert fetch race call"
    )

write(core_p, core)

if "fetchRaceStarted:" not in settings:
    settings = replace_once(
        settings,
        '''deleteResolvedCurrentText: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "deleteResolvedCurrentText.Count"))
LastSnapshotSource:''',
        '''deleteResolvedCurrentText: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "deleteResolvedCurrentText.Count"))
fetchRaceStarted: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "fetchRaceStarted.Count"))
fetchRaceIds: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "fetchRaceIds.Count"))
fetchRaceResponse: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "fetchRaceResponse.Count"))
fetchRaceEmpty: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "fetchRaceEmpty.Count"))
fetchRaceWithText: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "fetchRaceWithText.Count"))
fetchRaceStoreMessage: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "fetchRaceStoreMessage.Count"))
fetchRaceError: \\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "fetchRaceError.Count"))
LastSnapshotSource:''',
        "insert fetch race counters"
    )

if "LastFetchRaceText:" not in settings:
    settings = replace_once(
        settings,
        '''LastDeleteResolvedText: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastDeleteResolvedText") ?? "none")
LastDeleteSnapshotKey:''',
        '''LastDeleteResolvedText: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastDeleteResolvedText") ?? "none")
LastFetchRaceSource: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchRaceSource") ?? "none")
LastFetchRaceIdsCount: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchRaceIdsCount") ?? "none")
LastFetchRaceApiMessageCount: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchRaceApiMessageCount") ?? "none")
LastFetchRaceMessageKey: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchRaceMessageKey") ?? "none")
LastFetchRaceText: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchRaceText") ?? "none")
LastFetchRaceError: \\(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastFetchRaceError") ?? "none")
LastDeleteSnapshotKey:''',
        "insert fetch race last fields"
    )

settings = settings.replace("Version: v1.0G", "Version: v1.0H")
write(settings_p, settings)

core = read(core_p)
settings = read(settings_p)

ensure(core, "GhostBase v1.0H Fetch Race Probe", "helper marker")
ensure(core, "Api.functions.messages.getMessages(id: globalIds.map", "fetch api call")
ensure(core, "ghostBaseV10HFetchRaceProbe(accountPeerId:", "fetch call")
ensure(settings, "fetchRaceStarted:", "settings fetch counters")
ensure(settings, "LastFetchRaceText:", "settings fetch text")
ensure(settings, "Version: v1.0H", "settings version")

print("[v1.0H] Fetch Race Probe patch OK")
