#!/usr/bin/env python3
from pathlib import Path
import runpy

VERSION = "v0.9F.3"
SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parent.parent
BASE = ROOT / "work/swiftgram-src"

prev = SCRIPT.parent / "apply_ghostbase_history_stars_polish_v09f2.py"

account_p = BASE / "submodules/AccountContext/Sources/AccountContext.swift"
kind_p = BASE / "submodules/AccountContext/Sources/ChatController.swift"
ctx_p = BASE / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"
settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
validation_p = BASE / "submodules/TelegramCore/Sources/State/HistoryViewStateValidation.swift"

switch_files = [
    BASE / "submodules/TelegramUI/Sources/Chat/UpdateChatPresentationInterfaceState.swift",
    BASE / "submodules/TelegramUI/Sources/Chat/ChatControllerLoadDisplayNode.swift",
    BASE / "submodules/TelegramUI/Sources/ChatControllerContentData.swift",
    BASE / "submodules/TelegramUI/Sources/ChatInterfaceTitlePanelNodes.swift",
    BASE / "submodules/TelegramUI/Sources/ChatInterfaceStateInputPanels.swift",
    BASE / "submodules/TelegramUI/Sources/ChatBusinessLinkTitlePanelNode.swift",
    BASE / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift",
    BASE / "submodules/TelegramUI/Sources/ChatControllerNode.swift",
    BASE / "submodules/TelegramUI/Sources/ChatInterfaceStateNavigationButtons.swift",
    BASE / "submodules/TelegramUI/Sources/ChatRestrictedInputPanelNode.swift",
    BASE / "submodules/TelegramUI/Sources/ChatController.swift",
    BASE / "submodules/TelegramUI/Sources/ChatInterfaceInputContexts.swift",
]

def fail(msg):
    print(f"[{VERSION}] ERROR: {msg}")
    raise SystemExit(1)

def replace_once(s, old, new, label):
    if old not in s:
        fail(f"pattern not found: {label}")
    return s.replace(old, new, 1)

already = (
    kind_p.exists()
    and ctx_p.exists()
    and settings_p.exists()
    and validation_p.exists()
    and "case ghostBaseEditHistory" in kind_p.read_text()
    and "let kind: ChatCustomContentsKind = .ghostBaseEditHistory" in ctx_p.read_text()
    and "chatLocation: .peer(id: messages[0].id.peerId)" in ctx_p.read_text()
    and "GhostBase v0.9F.3 channel history validation retention" in validation_p.read_text()
    and "Version: v0.9F.3" in settings_p.read_text()
)

if already:
    print(f"[{VERSION}] already present; skip v0.9F.2 replay")
else:
    print(f"[{VERSION}] replay v0.9F.2 base")
    try:
        runpy.run_path(str(prev))
    except SystemExit as e:
        if e.code not in (0, None):
            raise

for p in [account_p, kind_p, ctx_p, settings_p, validation_p] + switch_files:
    if not p.exists():
        fail(f"missing file: {p}")

kind = kind_p.read_text()
ctx = ctx_p.read_text()
settings = settings_p.read_text()
validation = validation_p.read_text()

if "case ghostBaseEditHistory" in kind:
    print(f"[{VERSION}] enum case already present")
else:
    kind = replace_once(
        kind,
        "    case hashTagSearch(publicPosts: Bool)\n",
        "    case hashTagSearch(publicPosts: Bool)\n    case ghostBaseEditHistory\n",
        "ChatCustomContentsKind.ghostBaseEditHistory"
    )
    print(f"[{VERSION}] enum case inserted")

old_kind = "    let kind: ChatCustomContentsKind = .hashTagSearch(publicPosts: false)"
new_kind = "    let kind: ChatCustomContentsKind = .ghostBaseEditHistory"

if new_kind in ctx:
    print(f"[{VERSION}] history kind already patched")
else:
    ctx = replace_once(ctx, old_kind, new_kind, "GhostBase history kind")
    print(f"[{VERSION}] history kind patched")

old_controller = "chatLocation: .customChatContents, subject: .customChatContents(contents: contents)"
new_controller = "chatLocation: .peer(id: messages[0].id.peerId), subject: .customChatContents(contents: contents)"

if new_controller in ctx:
    print(f"[{VERSION}] history controller peer location already patched")
else:
    ctx = replace_once(ctx, old_controller, new_controller, "history controller peer chatLocation")
    print(f"[{VERSION}] history controller peer location patched")

if "Version: v0.9F.3" in settings:
    print(f"[{VERSION}] settings version already v0.9F.3")
elif "Version: v0.9F.2" in settings:
    settings = settings.replace("Version: v0.9F.2", "Version: v0.9F.3", 1)
    print(f"[{VERSION}] settings version patched")
else:
    fail("settings version v0.9F.2")

# MARK: v0.9F.3 write ctx before switch patching
# Important for clean CI:
# ChatInterfaceStateContextMenus.swift is also in switch_files.
# Write history kind / peer-location changes before switch loop reads it.
ctx_p.write_text(ctx)

for p in switch_files:
    file_text = p.read_text()
    if "case .hashTagSearch, .ghostBaseEditHistory:" in file_text and "case .hashTagSearch:" not in file_text:
        print(f"[{VERSION}] switch already patched: {p.name}")
        continue

    count = file_text.count("case .hashTagSearch:")
    if count == 0:
        print(f"[{VERSION}] no plain switch case in: {p.name}")
        continue

    file_text = file_text.replace("case .hashTagSearch:", "case .hashTagSearch, .ghostBaseEditHistory:")
    p.write_text(file_text)
    print(f"[{VERSION}] patched {count} switch case(s): {p.name}")

# ChatInterfaceStateContextMenus.swift is also kept in `ctx`.
# Reload it after switch patching so the final ctx_p.write_text(ctx) does not revert switch edits.
ctx = ctx_p.read_text()

marker = "// MARK: GhostBase v0.9F.3 channel history validation retention"

old_delete_1 = '''                                } else {
                                    _internal_deleteMessages(transaction: transaction, mediaBox: postbox.mediaBox, ids: [id])
                                    Logger.shared.log("HistoryValidation", "deleting message \\(id) in \\(id.peerId)")
                                }'''

new_delete_1 = '''                                } else {
                                    // MARK: GhostBase v0.9F.3 channel history validation retention
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
                            // MARK: GhostBase v0.9F.3 channel history validation retention
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
    print(f"[{VERSION}] HistoryValidation retention already patched")
else:
    validation = replace_once(validation, old_delete_1, new_delete_1, "HistoryValidation normal delete retention")
    validation = replace_once(validation, old_delete_2, new_delete_2, "HistoryValidation thread delete retention")
    print(f"[{VERSION}] HistoryValidation retention patched")

kind_p.write_text(kind)
ctx_p.write_text(ctx)
settings_p.write_text(settings)
validation_p.write_text(validation)

kind = kind_p.read_text()
ctx = ctx_p.read_text()
settings = settings_p.read_text()
validation = validation_p.read_text()

bad = []

if "case ghostBaseEditHistory" not in kind:
    bad.append("enum ghostBaseEditHistory missing")
if "let kind: ChatCustomContentsKind = .ghostBaseEditHistory" not in ctx:
    bad.append("GhostBase history kind missing")
if ".hashTagSearch(publicPosts: false)" in ctx:
    bad.append("old GhostBase hashTagSearch kind still present")
if "chatLocation: .peer(id: messages[0].id.peerId)" not in ctx:
    bad.append("history peer chatLocation missing")
if "Version: v0.9F.3" not in settings:
    bad.append("settings version v0.9F.3 missing")
if marker not in validation:
    bad.append("HistoryValidation retention marker missing")
if "GhostBase keeping deleted message" not in validation:
    bad.append("HistoryValidation keep normal message missing")
if "GhostBase keeping deleted thread message" not in validation:
    bad.append("HistoryValidation keep thread message missing")

for p in switch_files:
    s = p.read_text()
    if "case .hashTagSearch:" in s:
        bad.append(f"plain hashTagSearch switch case left in {p.name}")

# Critical: search/jump if-blocks must remain hashTagSearch-only.
node = (BASE / "submodules/TelegramUI/Sources/ChatControllerNode.swift").read_text()
if "case .ghostBaseEditHistory = contents.kind" in node:
    bad.append("ghostBaseEditHistory accidentally added to hashTagSearch if-blocks")

if bad:
    for item in bad:
        print(f"[{VERSION}] FAILED: {item}")
    raise SystemExit(1)

print("GhostBase v0.9F.3 history UI + channel retention patch OK")
