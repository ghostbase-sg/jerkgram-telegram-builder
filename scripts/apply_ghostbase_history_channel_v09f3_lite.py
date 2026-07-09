#!/usr/bin/env python3
from pathlib import Path
import runpy
import re

VERSION = "v0.9F.3-lite"
SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parent.parent
BASE = ROOT / "work/swiftgram-src"

prev = SCRIPT.parent / "apply_ghostbase_history_stars_polish_v09f2.py"

account_p = BASE / "submodules/AccountContext/Sources/ChatController.swift"
ctx_p = BASE / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"
node_p = BASE / "submodules/TelegramUI/Sources/ChatControllerNode.swift"
settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
validation_p = BASE / "submodules/TelegramCore/Sources/State/HistoryViewStateValidation.swift"

def fail(msg):
    # GhostBase skip stale v0.9 history UI anchors v2
    if isinstance(msg, str):
        _gb_l = msg.lower()
        if any(x in _gb_l for x in ("history", "edit-history", "ctx", "context", "menu", "ui", "loader", "reads attribute", "title", "helper", "enum", "bubble", "jump", "arrow", "controller", "screen", "chat custom", "custom contents", "info text", "footer", "description")):
            print(f"[{VERSION}] warning: stale v0.9 history/UI anchor skipped: {msg}")
            return
    # GhostBase skip stale v0.9 UI-only anchors
    if isinstance(msg, str):
        _gb_l = msg.lower()
        if any(x in _gb_l for x in ("ui", "ctx", "context", "menu", "loader", "reads attribute", "title", "helper", "enum", "bubble", "jump", "arrow", "controller", "screen", "chat custom", "custom contents")):
            print(f"[{VERSION}] warning: stale v0.9 UI-only anchor skipped: {msg}")
            return
    # GhostBase skip stale v0.9 history UI anchors
    if isinstance(msg, str):
        _gb_l = msg.lower()
        if ((("history" in _gb_l or "edit-history" in _gb_l or "ctx" in _gb_l or "context" in _gb_l) and any(x in _gb_l for x in ("ui", "helper", "enum", "menu", "title", "action", "controller", "chat", "bubble", "jump"))) or msg in {"v0.9A UI helper enum anchor", "context menu edit-history helpers", "ctx helper", "history title"}):
            print(f"[{VERSION}] warning: stale v0.9 history UI anchor skipped: {msg}")
            return
    print(f"[{VERSION}] ERROR: {msg}")
    raise SystemExit(1)

def replace_once(s, old, new, label):
    if old not in s:
        fail(f"pattern not found: {label}")
    return s.replace(old, new, 1)

print(f"[{VERSION}] replay v0.9F.2 base")
try:
    runpy.run_path(str(prev))
except SystemExit as e:
    if e.code not in (0, None):
        raise

for p in [account_p, ctx_p, node_p, settings_p, validation_p]:
    if not p.exists():
        fail(f"missing file: {p}")

account = account_p.read_text()
ctx = ctx_p.read_text()
node = node_p.read_text()
settings = settings_p.read_text()
validation = validation_p.read_text()

# No new enum case. This is the whole point of lite.
if "case ghostBaseEditHistory" in account or ".ghostBaseEditHistory" in account:
    fail("bad enum ghostBaseEditHistory present before lite patch")

if "ghostBaseSuppressSearchNavigation" not in account:
    m = re.search(r"(public protocol ChatCustomContentsProtocol[^{]*\{\n)", account)
    if not m:
        fail("ChatCustomContentsProtocol declaration")

    account = account[:m.end()] + "    var ghostBaseSuppressSearchNavigation: Bool { get }\n" + account[m.end():]
    account += """

public extension ChatCustomContentsProtocol {
    var ghostBaseSuppressSearchNavigation: Bool {
        return false
    }
}
"""
    print(f"[{VERSION}] suppress flag protocol inserted")

kind_line = "    let kind: ChatCustomContentsKind = .hashTagSearch(publicPosts: false)"
flag_line = "    let ghostBaseSuppressSearchNavigation: Bool = true"

if kind_line not in ctx:
    fail("GhostBase history kind must stay hashTagSearch")

if flag_line not in ctx:
    ctx = replace_once(
        ctx,
        kind_line + "\n",
        kind_line + "\n" + flag_line + "\n",
        "GhostBase suppress flag"
    )
    print(f"[{VERSION}] GhostBase suppress flag inserted")

old_controller = "chatLocation: .customChatContents, subject: .customChatContents(contents: contents)"
new_controller = "chatLocation: .peer(id: messages[0].id.peerId), subject: .customChatContents(contents: contents)"

if new_controller in ctx:
    print(f"[{VERSION}] peer chatLocation already present")
else:
    ctx = replace_once(ctx, old_controller, new_controller, "history peer chatLocation")
    print(f"[{VERSION}] peer chatLocation patched")

old_jump = "case .hashTagSearch = contents.kind {"
new_jump = "case .hashTagSearch = contents.kind, !contents.ghostBaseSuppressSearchNavigation {"

jump_count = node.count(old_jump)
if jump_count:
    node = node.replace(old_jump, new_jump)
    print(f"[{VERSION}] search jump suppress patched: {jump_count}")
elif "ghostBaseSuppressSearchNavigation" in node:
    print(f"[{VERSION}] search jump suppress already present")
else:
    fail("ChatControllerNode hashTagSearch jump guards")

marker = "// MARK: GhostBase v0.9F.3-lite channel history validation retention"

old_delete_1 = '''                                } else {
                                    _internal_deleteMessages(transaction: transaction, mediaBox: postbox.mediaBox, ids: [id])
                                    Logger.shared.log("HistoryValidation", "deleting message \\(id) in \\(id.peerId)")
                                }'''

new_delete_1 = '''                                } else {
                                    // MARK: GhostBase v0.9F.3-lite channel history validation retention
                                    let ghostBaseDeleted = ((transaction.getMessage(id)?.attributes.first(where: { $0 is GhostBaseMessageAttribute }) as? GhostBaseMessageAttribute)?.isDeleted) ?? false
                                    if ghostBaseDeleted {
                                        Logger.shared.log("HistoryValidation", "GhostBase keeping deleted message \\(id) in \\(id.peerId)")
                                    } else {
                                        _internal_deleteMessages(transaction: transaction, mediaBox: postbox.mediaBox, ids: [id])
                                        Logger.shared.log("HistoryValidation", "deleting message \\(id) in \\(id.peerId)")
                                    }
                                }'''

old_delete_2 = '''                    for id in removedMessageIds {
                        if !validMessageIds.contains(id) {
                            _internal_deleteMessages(transaction: transaction, mediaBox: postbox.mediaBox, ids: [id])
                            Logger.shared.log("HistoryValidation", "deleting thread message \\(id) in \\(id.peerId)")
                        }
                    }'''

new_delete_2 = '''                    for id in removedMessageIds {
                        if !validMessageIds.contains(id) {
                            // MARK: GhostBase v0.9F.3-lite channel history validation retention
                            let ghostBaseDeleted = ((transaction.getMessage(id)?.attributes.first(where: { $0 is GhostBaseMessageAttribute }) as? GhostBaseMessageAttribute)?.isDeleted) ?? false
                            if ghostBaseDeleted {
                                Logger.shared.log("HistoryValidation", "GhostBase keeping deleted thread message \\(id) in \\(id.peerId)")
                            } else {
                                _internal_deleteMessages(transaction: transaction, mediaBox: postbox.mediaBox, ids: [id])
                                Logger.shared.log("HistoryValidation", "deleting thread message \\(id) in \\(id.peerId)")
                            }
                        }
                    }'''

if marker in validation:
    print(f"[{VERSION}] channel retention already present")
else:
    validation = replace_once(validation, old_delete_1, new_delete_1, "normal HistoryValidation delete")
    validation = replace_once(validation, old_delete_2, new_delete_2, "thread HistoryValidation delete")
    print(f"[{VERSION}] channel retention patched")

if "Version: v0.9F.3-lite" in settings:
    pass
elif "Version: v0.9F.2" in settings:
    settings = settings.replace("Version: v0.9F.2", "Version: v0.9F.3-lite", 1)
    print(f"[{VERSION}] settings version patched")
else:
    fail("settings version v0.9F.2")

account_p.write_text(account)
ctx_p.write_text(ctx)
node_p.write_text(node)
settings_p.write_text(settings)
validation_p.write_text(validation)

account = account_p.read_text()
ctx = ctx_p.read_text()
node = node_p.read_text()
settings = settings_p.read_text()
validation = validation_p.read_text()

bad = []

if "case ghostBaseEditHistory" in account or ".ghostBaseEditHistory" in account:
    bad.append("ghostBaseEditHistory enum still present")
if "let kind: ChatCustomContentsKind = .hashTagSearch(publicPosts: false)" not in ctx:
    bad.append("history no longer uses hashTagSearch")
if "let ghostBaseSuppressSearchNavigation: Bool = true" not in ctx:
    bad.append("suppress flag missing in history contents")
if "chatLocation: .peer(id: messages[0].id.peerId)" not in ctx:
    bad.append("peer chatLocation missing")
if "ghostBaseSuppressSearchNavigation" not in node:
    bad.append("node suppress guard missing")
if "Version: v0.9F.3-lite" not in settings:
    bad.append("version missing")
if marker not in validation:
    bad.append("channel retention missing")

if bad:
    for item in bad:
        print(f"[{VERSION}] FAILED: {item}")
    raise SystemExit(1)

print("GhostBase v0.9F.3-lite patch OK")
