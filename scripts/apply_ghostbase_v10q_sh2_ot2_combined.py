#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"
BASE = ROOT / "scripts/apply_ghostbase_v10p_sh1_ot1_combined.py"

def read(p): return Path(p).read_text()
def write(p, s): Path(p).write_text(s)

def ensure(s, needle, label):
    if needle not in s:
        raise SystemExit(f"[v1.0Q+SH2+OT2] ERROR: missing {label}: {needle}")

def replace_once(s, old, new, label):
    if old in s:
        return s.replace(old, new, 1)
    if new in s:
        return s
    raise SystemExit(f"[v1.0Q+SH2+OT2] ERROR: pattern not found: {label}")

print("[v1.0Q+SH2+OT2] running base v1.0P+SH1+OT1...")
subprocess.check_call([sys.executable, str(BASE)], cwd=str(ROOT))

core = SRC / "submodules/TelegramCore/Sources"
ui = SRC / "submodules/TelegramUI/Sources"

state_p = core / "State/AccountStateManagementUtils.swift"
standalone_p = core / "PendingMessages/StandaloneSendMessage.swift"
history_entries_p = ui / "ChatHistoryEntriesForView.swift"
settings_p = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

state = read(state_p)
standalone = read(standalone_p)
history_entries = read(history_entries_p)
settings = read(settings_p)

ensure(settings, "Version: v1.0P+SH1+OT1", "base version")
ensure(state, "case let .DeleteMessagesWithGlobalIds(ids):", "global delete case")
ensure(standalone, "public func standaloneSendEnqueueMessages(", "standalone send function")
ensure(history_entries, "if skipViewOnceMedia, let minAutoremoveOrClearTimeout = message.minAutoremoveOrClearTimeout", "view-once skip path")

if "GhostBase v1.0Q Raw Global Delete Trace" not in state:
    helper = r'''
// MARK: GhostBase v1.0Q Raw Global Delete Trace
private func ghostBaseV10QTraceRawGlobalDeleteIds<T>(_ ids: [T], mappedIds: [MessageId], source: String) {
    let d = UserDefaults.standard
    d.set(d.integer(forKey: "GhostBase.V10Q.RawDeleteEvents") + 1, forKey: "GhostBase.V10Q.RawDeleteEvents")
    d.set(source, forKey: "GhostBase.V10Q.LastRawDeleteSource")
    d.set(ids.count, forKey: "GhostBase.V10Q.LastRawDeleteIdCount")
    d.set(mappedIds.count, forKey: "GhostBase.V10Q.LastMappedDeleteIdCount")
    d.set(ids.map { "\($0)" }.joined(separator: ","), forKey: "GhostBase.V10Q.LastRawDeleteIds")
    d.set(mappedIds.map { "\($0)" }.joined(separator: ","), forKey: "GhostBase.V10Q.LastMappedDeleteIds")
    if mappedIds.isEmpty {
        d.set("RAW_IDS_NO_LOCAL_MAPPING", forKey: "GhostBase.V10Q.Verdict")
    } else {
        d.set("RAW_IDS_MAPPED", forKey: "GhostBase.V10Q.Verdict")
    }
}

'''
    at = state.find("// MARK: GhostBase v1.0P Pre-delete Shadow Trace")
    if at < 0:
        raise SystemExit("[v1.0Q+SH2+OT2] ERROR: v1.0P helper anchor not found")
    state = state[:at] + helper + state[at:]


# v1.0Q: flexible raw global delete ids injection
import re

case_anchor = "case let .DeleteMessagesWithGlobalIds(ids):"
case_i = state.find(case_anchor)
if case_i < 0:
    raise SystemExit("[v1.0Q+SH2+OT2] ERROR: DeleteMessagesWithGlobalIds case not found")

next_case_i = state.find("\n        case ", case_i + len(case_anchor))
if next_case_i < 0:
    next_case_i = min(len(state), case_i + 2500)

segment = state[case_i:next_case_i]

if "ghostBaseV10QTraceRawGlobalDeleteIds" not in segment:
    m = re.search(r'(?m)^([ \t]*)let\s+([A-Za-z0-9_]+)\s*=\s*transaction\.messageIdsForGlobalIds\(ids\).*$', segment)
    if m:
        indent = m.group(1)
        local_var = m.group(2)
        line_end = case_i + m.end()
        inject = f'\n{indent}ghostBaseV10QTraceRawGlobalDeleteIds(ids, mappedIds: {local_var}, source: "DeleteMessagesWithGlobalIds")'
        state = state[:line_end] + inject + state[line_end:]
    else:
        insert_at = state.find("\n", case_i)
        if insert_at < 0:
            raise SystemExit("[v1.0Q+SH2+OT2] ERROR: cannot inject after DeleteMessagesWithGlobalIds line")
        inject = '\n            ghostBaseV10QTraceRawGlobalDeleteIds(ids, mappedIds: [], source: "DeleteMessagesWithGlobalIds")'
        state = state[:insert_at] + inject + state[insert_at:]

write(state_p, state)


if "GhostBase v1.0Q+SH2 Standalone Scheduled Send" not in standalone:
    helper = r'''
// MARK: GhostBase v1.0Q+SH2 Standalone Scheduled Send
private func ghostBaseSH2ApplyStandaloneSchedule(peerId: PeerId, attributes: inout [MessageAttribute]) {
    let d = UserDefaults.standard
    let enabled = ((d.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false)
    if !enabled {
        return
    }
    if attributes.contains(where: { $0 is OutgoingScheduleInfoMessageAttribute }) {
        return
    }
    let scheduleTime = Int32(Date().timeIntervalSince1970) + 12
    attributes.append(OutgoingScheduleInfoMessageAttribute(scheduleTime: scheduleTime, repeatPeriod: nil))
    d.set(d.integer(forKey: "GhostBase.SH2.StandaloneScheduledIntercept.Count") + 1, forKey: "GhostBase.SH2.StandaloneScheduledIntercept.Count")
    d.set("\(peerId)", forKey: "GhostBase.SH2.LastStandalonePeerId")
    d.set(Int(scheduleTime), forKey: "GhostBase.SH2.LastStandaloneScheduleTime")
}

'''
    idx = standalone.find("public func standaloneSendEnqueueMessages(")
    if idx < 0:
        raise SystemExit("[v1.0Q+SH2+OT2] ERROR: standalone function anchor not found")
    standalone = standalone[:idx] + helper + standalone[idx:]

old = '''        var attributes: [MessageAttribute] = []
        var text: String = ""'''

new = '''        var attributes: [MessageAttribute] = []
        ghostBaseSH2ApplyStandaloneSchedule(peerId: peerId, attributes: &attributes)
        var text: String = ""'''

standalone = replace_once(standalone, old, new, "SH2 apply standalone schedule")
write(standalone_p, standalone)

old = '''        if skipViewOnceMedia, let minAutoremoveOrClearTimeout = message.minAutoremoveOrClearTimeout {
            if minAutoremoveOrClearTimeout <= 60 {
                continue loop
            }
        }'''

new = '''        if skipViewOnceMedia, let minAutoremoveOrClearTimeout = message.minAutoremoveOrClearTimeout {
            let ghostBaseOT2KeepViewOnceVisible = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat)
            if minAutoremoveOrClearTimeout <= 60 {
                if ghostBaseOT2KeepViewOnceVisible {
                    UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "GhostBase.OT2.ViewOnceVisibleKeep.Count") + 1, forKey: "GhostBase.OT2.ViewOnceVisibleKeep.Count")
                    UserDefaults.standard.set("\\(message.id)", forKey: "GhostBase.OT2.LastViewOnceVisibleId")
                } else {
                    continue loop
                }
            }
        }'''

history_entries = replace_once(history_entries, old, new, "OT2 keep view-once visible in history")
write(history_entries_p, history_entries)

if "v1.0Q Raw Delete Mapping:" not in settings:
    block = r'''v1.0Q Raw Delete Mapping:
QRawDeleteEvents: \(UserDefaults.standard.integer(forKey: "GhostBase.V10Q.RawDeleteEvents"))
QLastRawDeleteSource: \(UserDefaults.standard.string(forKey: "GhostBase.V10Q.LastRawDeleteSource") ?? "none")
QLastRawDeleteIdCount: \(UserDefaults.standard.integer(forKey: "GhostBase.V10Q.LastRawDeleteIdCount"))
QLastMappedDeleteIdCount: \(UserDefaults.standard.integer(forKey: "GhostBase.V10Q.LastMappedDeleteIdCount"))
QLastRawDeleteIds: \(UserDefaults.standard.string(forKey: "GhostBase.V10Q.LastRawDeleteIds") ?? "none")
QLastMappedDeleteIds: \(UserDefaults.standard.string(forKey: "GhostBase.V10Q.LastMappedDeleteIds") ?? "none")
QVerdict: \(UserDefaults.standard.string(forKey: "GhostBase.V10Q.Verdict") ?? "none")

SH2 Standalone Share Scheduled:
SH2StandaloneScheduledIntercept: \(UserDefaults.standard.integer(forKey: "GhostBase.SH2.StandaloneScheduledIntercept.Count"))
SH2LastStandalonePeerId: \(UserDefaults.standard.string(forKey: "GhostBase.SH2.LastStandalonePeerId") ?? "none")
SH2LastStandaloneScheduleTime: \(UserDefaults.standard.integer(forKey: "GhostBase.SH2.LastStandaloneScheduleTime"))

OT2 ViewOnce Visual Keep:
OT2ViewOnceVisibleKeep: \(UserDefaults.standard.integer(forKey: "GhostBase.OT2.ViewOnceVisibleKeep.Count"))
OT2LastViewOnceVisibleId: \(UserDefaults.standard.string(forKey: "GhostBase.OT2.LastViewOnceVisibleId") ?? "none")

'''
    settings = settings.replace("v1.0P Pre-delete Shadow Trace:", block + "v1.0P Pre-delete Shadow Trace:", 1)

settings = settings.replace("Version: v1.0P+SH1+OT1", "Version: v1.0Q+SH2+OT2")
write(settings_p, settings)

state = read(state_p)
standalone = read(standalone_p)
history_entries = read(history_entries_p)
settings = read(settings_p)

ensure(state, "GhostBase v1.0Q Raw Global Delete Trace", "Q helper")
ensure(state, "ghostBaseV10QTraceRawGlobalDeleteIds", "Q call")
ensure(standalone, "GhostBase v1.0Q+SH2 Standalone Scheduled Send", "SH2 helper")
ensure(standalone, "ghostBaseSH2ApplyStandaloneSchedule(peerId: peerId", "SH2 call")
ensure(history_entries, "GhostBase.OT2.ViewOnceVisibleKeep.Count", "OT2 visible keep")
ensure(settings, "v1.0Q Raw Delete Mapping:", "Q settings")
ensure(settings, "SH2 Standalone Share Scheduled:", "SH2 settings")
ensure(settings, "OT2 ViewOnce Visual Keep:", "OT2 settings")
ensure(settings, "Version: v1.0Q+SH2+OT2", "version")

print("[v1.0Q+SH2+OT2] patch OK")

# MARK: GhostBase Telegram 12.8 SwiftCompile cleanup
ctxmenu_128 = ROOT / "work/swiftgram-src/submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"

if ctxmenu_128.exists():
    s128 = ctxmenu_128.read_text()

    # v0.9 edit-history UI uses raw Postbox message types on Telegram 12.8.
    if "private func ghostBaseEditHistoryKey(_ id: MessageId)" in s128:
        if "import Postbox" not in s128:
            s128 = s128.replace("import Foundation\n", "import Foundation\nimport Postbox\n", 1)
        if "import TelegramCore" not in s128:
            s128 = s128.replace("import Postbox\n", "import Postbox\nimport TelegramCore\n", 1)

    old_map = "    |> map { data, updatingMessageMedia, infoSummaryData, appConfig, isMessageRead, messageViewsPrivacyTips, availableReactions, translationSettings, loggingSettings, notificationSoundList, accountPeer -> ContextController.Items in"
    new_map = "    |> map { args -> ContextController.Items in\n        let (data, updatingMessageMedia, infoSummaryData, appConfig, isMessageRead, messageViewsPrivacyTips, availableReactions, translationSettings, loggingSettings, notificationSoundList, accountPeer) = args"

    if old_map in s128:
        s128 = s128.replace(old_map, new_map, 1)
        print("[v1.0Q+SH2+OT2] patched Telegram 12.8 tuple map closure in ChatInterfaceStateContextMenus")

    ctxmenu_128.write_text(s128)

