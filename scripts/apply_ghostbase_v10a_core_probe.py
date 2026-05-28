#!/usr/bin/env python3
from pathlib import Path
import runpy
import re

VERSION = "v1.0A"
ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "work/swiftgram-src"

prev = ROOT / "scripts/apply_ghostbase_history_stars_polish_v09f2.py"

asm_p = BASE / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
hv_p = BASE / "submodules/TelegramCore/Sources/State/HistoryViewStateValidation.swift"
settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
ctx_p = BASE / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"

def die(msg):
    raise SystemExit(f"[{VERSION}] ERROR: {msg}")

def once(s, old, new, name):
    if old not in s:
        die(f"pattern not found: {name}")
    return s.replace(old, new, 1)

print(f"[{VERSION}] replay v0.9F.2 base; v0.9F.3-lite history UI intentionally skipped")
runpy.run_path(str(prev), run_name="__main__")

asm = asm_p.read_text()
hv = hv_p.read_text()
settings = settings_p.read_text()
ctx = ctx_p.read_text()

for bad in [
    "case ghostBaseEditHistory",
    ".ghostBaseEditHistory",
    "ghostBaseSuppressSearchNavigation",
    "chatLocation: .peer(id: messages[0].id.peerId)",
]:
    if bad in ctx:
        die(f"bad history UI survived: {bad}")

probes = [
    (
        'case let .updateDeleteChannelMessages(updateDeleteChannelMessagesData):\n',
        'case let .updateDeleteChannelMessages(updateDeleteChannelMessagesData):\n                Logger.shared.log("GhostBaseV10A", "updateDeleteChannelMessages channelId=\\(updateDeleteChannelMessagesData.channelId) count=\\(updateDeleteChannelMessagesData.messages.count) pts=\\(updateDeleteChannelMessagesData.pts)")\n',
        "delete channel"
    ),
    (
        'case let .updateEditChannelMessage(updateEditChannelMessageData):\n',
        'case let .updateEditChannelMessage(updateEditChannelMessageData):\n                Logger.shared.log("GhostBaseV10A", "updateEditChannelMessage pts=\\(updateEditChannelMessageData.pts)")\n',
        "edit channel"
    ),
    (
        'case let .updateDeleteMessages(updateDeleteMessagesData):\n                updatedState.deleteMessagesWithGlobalIds(updateDeleteMessagesData.messages)',
        'case let .updateDeleteMessages(updateDeleteMessagesData):\n                Logger.shared.log("GhostBaseV10A", "updateDeleteMessages count=\\(updateDeleteMessagesData.messages.count)")\n                updatedState.deleteMessagesWithGlobalIds(updateDeleteMessagesData.messages)',
        "delete global"
    ),
    (
        'case let .updateEditMessage(updateEditMessageData):\n',
        'case let .updateEditMessage(updateEditMessageData):\n                Logger.shared.log("GhostBaseV10A", "updateEditMessage")\n',
        "edit global"
    ),
    (
        'case let .updateNewChannelMessage(updateNewChannelMessageData):\n',
        'case let .updateNewChannelMessage(updateNewChannelMessageData):\n                Logger.shared.log("GhostBaseV10A", "updateNewChannelMessage")\n',
        "new channel"
    ),
    (
        'case let .updateNewMessage(updateNewMessageData):\n',
        'case let .updateNewMessage(updateNewMessageData):\n                Logger.shared.log("GhostBaseV10A", "updateNewMessage")\n',
        "new global"
    ),
]

for old, new, name in probes:
    if new not in asm:
        asm = once(asm, old, new, f"probe {name}")


# v1.0A: optional apply-lifecycle probes for channel updates.
# If exact anchors exist, mark the real apply path too.
channel_apply_probes = [
    (
        'case let .updateNewChannelMessage(updateNewChannelMessageData):\n                let (apiMessage, pts, ptsCount) = (updateNewChannelMessageData.message, updateNewChannelMessageData.pts, updateNewChannelMessageData.ptsCount)',
        'case let .updateNewChannelMessage(updateNewChannelMessageData):\n                Logger.shared.log("GhostBaseV10A", "APPLY updateNewChannelMessage pts=\\(updateNewChannelMessageData.pts)")\n                let (apiMessage, pts, ptsCount) = (updateNewChannelMessageData.message, updateNewChannelMessageData.pts, updateNewChannelMessageData.ptsCount)',
        "apply new channel"
    ),
]

for old, new, name in channel_apply_probes:
    if new not in asm and old in asm:
        asm = asm.replace(old, new, 1)
        print(f"[{VERSION}] patched optional probe: {name}")


marker = "// MARK: GhostBase v1.0A channel retention"

old1 = '''                                } else {
                                    _internal_deleteMessages(transaction: transaction, mediaBox: postbox.mediaBox, ids: [id])
                                    Logger.shared.log("HistoryValidation", "deleting message \\(id) in \\(id.peerId)")
                                }'''

new1 = '''                                } else {
                                    // MARK: GhostBase v1.0A channel retention
                                    let ghostBaseDeleted = ((transaction.getMessage(id)?.attributes.first(where: { $0 is GhostBaseMessageAttribute }) as? GhostBaseMessageAttribute)?.isDeleted) ?? false
                                    if ghostBaseDeleted {
                                        Logger.shared.log("HistoryValidation", "GhostBase keeping deleted message \\(id) in \\(id.peerId)")
                                    } else {
                                        _internal_deleteMessages(transaction: transaction, mediaBox: postbox.mediaBox, ids: [id])
                                        Logger.shared.log("HistoryValidation", "deleting message \\(id) in \\(id.peerId)")
                                    }
                                }'''

old2 = '''                    for id in removedMessageIds {
                        if !validMessageIds.contains(id) {
                            _internal_deleteMessages(transaction: transaction, mediaBox: postbox.mediaBox, ids: [id])
                            Logger.shared.log("HistoryValidation", "deleting thread message \\(id) in \\(id.peerId)")
                        }
                    }'''

new2 = '''                    for id in removedMessageIds {
                        if !validMessageIds.contains(id) {
                            // MARK: GhostBase v1.0A channel retention
                            let ghostBaseDeleted = ((transaction.getMessage(id)?.attributes.first(where: { $0 is GhostBaseMessageAttribute }) as? GhostBaseMessageAttribute)?.isDeleted) ?? false
                            if ghostBaseDeleted {
                                Logger.shared.log("HistoryValidation", "GhostBase keeping deleted thread message \\(id) in \\(id.peerId)")
                            } else {
                                _internal_deleteMessages(transaction: transaction, mediaBox: postbox.mediaBox, ids: [id])
                                Logger.shared.log("HistoryValidation", "deleting thread message \\(id) in \\(id.peerId)")
                            }
                        }
                    }'''

if marker not in hv:
    hv = once(hv, old1, new1, "retention normal")
    hv = once(hv, old2, new2, "retention thread")

settings = re.sub(r"Version: v[0-9A-Za-z.\-]+", "Version: v1.0A", settings, count=1)

asm_p.write_text(asm)
hv_p.write_text(hv)
settings_p.write_text(settings)

asm = asm_p.read_text()
hv = hv_p.read_text()
settings = settings_p.read_text()
ctx = ctx_p.read_text()

for need, text in [
    ("GhostBaseV10A", asm),
    ("GhostBase v1.0A channel retention", hv),
    ("Version: v1.0A", settings),
]:
    if need not in text:
        die(f"missing {need}")

for bad in [
    "case ghostBaseEditHistory",
    ".ghostBaseEditHistory",
    "ghostBaseSuppressSearchNavigation",
    "chatLocation: .peer(id: messages[0].id.peerId)",
]:
    if bad in ctx:
        die(f"bad history UI survived after patch: {bad}")

if "Version: v1.0A." in settings:
    die("bad version suffix, expected exact Version: v1.0A")

print("GhostBase v1.0A core probe patch OK")
