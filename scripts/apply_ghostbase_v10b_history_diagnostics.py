#!/usr/bin/env python3
from pathlib import Path
import runpy
import re

VERSION = "v1.0B"
ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "work/swiftgram-src"

prev = ROOT / "scripts/apply_ghostbase_v10a_core_probe.py"

acc_p = BASE / "submodules/AccountContext/Sources/ChatController.swift"
ctx_p = BASE / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"
bubble_p = BASE / "submodules/TelegramUI/Components/Chat/ChatMessageBubbleItemNode/Sources/ChatMessageBubbleItemNode.swift"
share_p = BASE / "submodules/TelegramUI/Components/Chat/ChatMessageShareButton/Sources/ChatMessageShareButton.swift"
asm_p = BASE / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

def die(msg):
    raise SystemExit(f"[{VERSION}] ERROR: {msg}")

def once(s, old, new, name):
    if old not in s:
        die(f"pattern not found: {name}")
    return s.replace(old, new, 1)

print(f"[{VERSION}] replay v1.0A base")
runpy.run_path(str(prev), run_name="__main__")

acc = acc_p.read_text()
ctx = ctx_p.read_text()
bubble = bubble_p.read_text()
share = share_p.read_text()
asm = asm_p.read_text()
settings = settings_p.read_text()

# MARK: v1.0B history jump suppression flag
if "var ghostBaseSuppressSearchJump: Bool { get }" not in acc:
    acc = once(
        acc,
        "var messageLimit: Int? { get }\n    \n    func enqueueMessages",
        "var messageLimit: Int? { get }\n    var ghostBaseSuppressSearchJump: Bool { get }\n    \n    func enqueueMessages",
        "protocol suppress flag"
    )

if "public extension ChatCustomContentsProtocol {\n    var ghostBaseSuppressSearchJump: Bool" not in acc:
    acc = once(
        acc,
        "public enum ChatHistoryListDisplayHeaders {",
        "public extension ChatCustomContentsProtocol {\n    var ghostBaseSuppressSearchJump: Bool {\n        return false\n    }\n}\n\npublic enum ChatHistoryListDisplayHeaders {",
        "protocol suppress default"
    )

if "let ghostBaseSuppressSearchJump: Bool = true" not in ctx:
    ctx = once(
        ctx,
        "private final class GhostBaseEditHistoryChatContents: ChatCustomContentsProtocol {\n    let kind: ChatCustomContentsKind = .hashTagSearch(publicPosts: false)",
        "private final class GhostBaseEditHistoryChatContents: ChatCustomContentsProtocol {\n    let kind: ChatCustomContentsKind = .hashTagSearch(publicPosts: false)\n    let ghostBaseSuppressSearchJump: Bool = true",
        "history contents suppress flag"
    )

old = "if incoming, case let .customChatContents(contents) = item.associatedData.subject, case .hashTagSearch = contents.kind {\n            needsShareButton = true"
new = "if incoming, case let .customChatContents(contents) = item.associatedData.subject, case .hashTagSearch = contents.kind, !contents.ghostBaseSuppressSearchJump {\n            needsShareButton = true"

if new not in bubble:
    bubble = once(bubble, old, new, "bubble needsShareButton suppress")

old = "} else if case let .customChatContents(contents) = subject, case .hashTagSearch = contents.kind {\n                updatedIconImage = PresentationResourcesChat.chatFreeNavigateButtonIcon"
new = "} else if case let .customChatContents(contents) = subject, case .hashTagSearch = contents.kind, !contents.ghostBaseSuppressSearchJump {\n                updatedIconImage = PresentationResourcesChat.chatFreeNavigateButtonIcon"

if new not in share:
    share = once(share, old, new, "share button icon suppress")

helper = '''// MARK: GhostBase v1.0B Core Difference Diagnostics
private func ghostBaseV10BRecordCoreEvent(_ name: String) {
    let defaults = UserDefaults.standard
    let prefix = "GhostBase.V10B.Core."
    let countKey = prefix + name + ".Count"
    defaults.set(defaults.integer(forKey: countKey) + 1, forKey: countKey)
    defaults.set(defaults.integer(forKey: prefix + "Total") + 1, forKey: prefix + "Total")
    defaults.set(name, forKey: prefix + "Last")
    defaults.set(Int(Date().timeIntervalSince1970), forKey: prefix + "LastTime")
}

'''

if "ghostBaseV10BRecordCoreEvent" not in asm:
    asm = once(asm, "import EncryptionProvider\n\n", "import EncryptionProvider\n\n" + helper, "core diagnostics helper")

events = [
    ('Logger.shared.log("GhostBaseV10A", "updateDeleteMessages count=\\(updateDeleteMessagesData.messages.count)")',
     'Logger.shared.log("GhostBaseV10A", "updateDeleteMessages count=\\(updateDeleteMessagesData.messages.count)")\n                ghostBaseV10BRecordCoreEvent("deleteMessages")'),
    ('Logger.shared.log("GhostBaseV10A", "updateEditMessage")',
     'Logger.shared.log("GhostBaseV10A", "updateEditMessage")\n                ghostBaseV10BRecordCoreEvent("editMessage")'),
    ('Logger.shared.log("GhostBaseV10A", "updateNewMessage")',
     'Logger.shared.log("GhostBaseV10A", "updateNewMessage")\n                ghostBaseV10BRecordCoreEvent("newMessage")'),
    ('Logger.shared.log("GhostBaseV10A", "APPLY updateNewChannelMessage pts=\\(updateNewChannelMessageData.pts)")',
     'Logger.shared.log("GhostBaseV10A", "APPLY updateNewChannelMessage pts=\\(updateNewChannelMessageData.pts)")\n                ghostBaseV10BRecordCoreEvent("newChannelMessage")'),
    ('Logger.shared.log("GhostBaseV10A", "updateDeleteChannelMessages channelId=\\(updateDeleteChannelMessagesData.channelId) count=\\(updateDeleteChannelMessagesData.messages.count) pts=\\(updateDeleteChannelMessagesData.pts)")',
     'Logger.shared.log("GhostBaseV10A", "updateDeleteChannelMessages channelId=\\(updateDeleteChannelMessagesData.channelId) count=\\(updateDeleteChannelMessagesData.messages.count) pts=\\(updateDeleteChannelMessagesData.pts)")\n                ghostBaseV10BRecordCoreEvent("deleteChannelMessages")'),
    ('Logger.shared.log("GhostBaseV10A", "updateEditChannelMessage pts=\\(updateEditChannelMessageData.pts)")',
     'Logger.shared.log("GhostBaseV10A", "updateEditChannelMessage pts=\\(updateEditChannelMessageData.pts)")\n                ghostBaseV10BRecordCoreEvent("editChannelMessage")'),
]

for old, new in events:
    if new not in asm:
        asm = once(asm, old, new, "core event counter")

diag = '''    let ghostBaseCorePrefix = "GhostBase.V10B.Core."
    let ghostBaseCoreDefaults = UserDefaults.standard
    let ghostBaseCoreTotal = ghostBaseCoreDefaults.integer(forKey: ghostBaseCorePrefix + "Total")
    let ghostBaseCoreLast = ghostBaseCoreDefaults.string(forKey: ghostBaseCorePrefix + "Last") ?? "none"
    let ghostBaseCoreLastTime = ghostBaseCoreDefaults.integer(forKey: ghostBaseCorePrefix + "LastTime")

    entries.append(.info(debug, """
Core Difference Probe:
Total: \\(ghostBaseCoreTotal)
Last: \\(ghostBaseCoreLast) @ \\(ghostBaseCoreLastTime)
newMessage: \\(ghostBaseCoreDefaults.integer(forKey: ghostBaseCorePrefix + "newMessage.Count"))
deleteMessages: \\(ghostBaseCoreDefaults.integer(forKey: ghostBaseCorePrefix + "deleteMessages.Count"))
editMessage: \\(ghostBaseCoreDefaults.integer(forKey: ghostBaseCorePrefix + "editMessage.Count"))
newChannelMessage: \\(ghostBaseCoreDefaults.integer(forKey: ghostBaseCorePrefix + "newChannelMessage.Count"))
deleteChannelMessages: \\(ghostBaseCoreDefaults.integer(forKey: ghostBaseCorePrefix + "deleteChannelMessages.Count"))
editChannelMessage: \\(ghostBaseCoreDefaults.integer(forKey: ghostBaseCorePrefix + "editChannelMessage.Count"))
"""))

'''

if "Core Difference Probe:" not in settings:
    settings = once(
        settings,
        '    entries.append(.header(debug, "Debug"))\n',
        '    entries.append(.header(debug, "Debug"))\n' + diag,
        "debug diagnostics insert"
    )

settings = re.sub(r"Version: v[0-9A-Za-z.\\-]+", "Version: v1.0B", settings, count=1)

acc_p.write_text(acc)
ctx_p.write_text(ctx)
bubble_p.write_text(bubble)
share_p.write_text(share)
asm_p.write_text(asm)
settings_p.write_text(settings)

bad = []
if "let ghostBaseSuppressSearchJump: Bool = true" not in ctx_p.read_text():
    bad.append("history suppress flag missing")
if "needsShareButton = true" not in bubble_p.read_text() or "ghostBaseSuppressSearchJump" not in bubble_p.read_text():
    bad.append("bubble suppress patch missing")
if "Core Difference Probe:" not in settings_p.read_text():
    bad.append("settings diagnostics missing")
if "Version: v1.0B" not in settings_p.read_text():
    bad.append("version v1.0B missing")
if "ghostBaseV10BRecordCoreEvent" not in asm_p.read_text():
    bad.append("core diagnostics helper missing")

if bad:
    for item in bad:
        print(f"[{VERSION}] FAILED: {item}")
    raise SystemExit(1)

print("GhostBase v1.0B history diagnostics patch OK")
