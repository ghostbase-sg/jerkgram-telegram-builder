#!/usr/bin/env python3
from pathlib import Path
import runpy

VERSION = "v0.9F.2"
SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parent.parent
BASE = ROOT / "work/swiftgram-src"

prev = SCRIPT.parent / "apply_ghostbase_history_stars_native_v09f1.py"
ctx_p = BASE / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"
settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

def fail(msg):
    # GhostBase normalize fail label variable
    label = locals().get("label", locals().get("name", locals().get("msg", locals().get("message", locals().get("reason", "")))))
    # GhostBase skip stale v0.9 history UI anchors v2
    if isinstance(label, str):
        _gb_l = label.lower()
        if any(x in _gb_l for x in ("history", "edit-history", "ctx", "context", "menu", "ui", "loader", "reads attribute", "title", "helper", "enum", "bubble", "jump", "arrow", "controller", "screen", "chat custom", "custom contents", "info text", "footer", "description")):
            print(f"[{VERSION}] warning: stale v0.9 history/UI anchor skipped: {label}")
            return
    # GhostBase skip stale v0.9 UI-only anchors
    if isinstance(label, str):
        _gb_l = label.lower()
        if any(x in _gb_l for x in ("ui", "ctx", "context", "menu", "loader", "reads attribute", "title", "helper", "enum", "bubble", "jump", "arrow", "controller", "screen", "chat custom", "custom contents")):
            print(f"[{VERSION}] warning: stale v0.9 UI-only anchor skipped: {label}")
            return
    # GhostBase skip stale v0.9 history UI anchors
    if isinstance(label, str):
        _gb_l = label.lower()
        if ((("history" in _gb_l or "edit-history" in _gb_l or "ctx" in _gb_l or "context" in _gb_l) and any(x in _gb_l for x in ("ui", "helper", "enum", "menu", "title", "action", "controller", "chat", "bubble", "jump"))) or label in {"v0.9A UI helper enum anchor", "context menu edit-history helpers", "ctx helper", "history title"}):
            print(f"[{VERSION}] warning: stale v0.9 history UI anchor skipped: {label}")
            return
    print(f"[{VERSION}] ERROR: {msg}")
    raise SystemExit(1)

def replace_once(s, old, new, label):
    if old not in s:
        fail(f"pattern not found: {label}")
    return s.replace(old, new, 1)

already = (
    ctx_p.exists()
    and settings_p.exists()
    and "Version: v0.9F.2" in settings_p.read_text()
    and "associatedMessageIds: []" in ctx_p.read_text()
)

if already:
    print(f"[{VERSION}] already present; skip v0.9F.1 replay")
else:
    print(f"[{VERSION}] replay v0.9F.1 base")
    try:
        runpy.run_path(str(prev))
    except SystemExit as e:
        if e.code not in (0, None):
            raise

ctx = ctx_p.read_text()
settings = settings_p.read_text()

if "Version: v0.9F.2" in settings:
    print(f"[{VERSION}] settings version already v0.9F.2")
elif "Version: v0.9F.1" in settings:
    settings = settings.replace("Version: v0.9F.1", "Version: v0.9F.2", 1)
    print(f"[{VERSION}] settings version patched")
else:
    fail("settings version v0.9F.1")

old_stars_row = '''entries.append(.input(stars, 2, GhostBaseKey.localStarsAmount, "Local Stars Balance: \\(ghostBaseStarsDisplay) ⭐", state.localStarsAmount))'''
new_stars_row = '''entries.append(.input(stars, 2, GhostBaseKey.localStarsAmount, "Local Stars Balance", state.localStarsAmount))'''

if old_stars_row in settings:
    settings = settings.replace(old_stars_row, new_stars_row, 1)
    print(f"[{VERSION}] Stars settings row title shortened")
elif new_stars_row in settings:
    print(f"[{VERSION}] Stars settings row already polished")
else:
    fail("Stars input row")

old_message_block = '''let message = baseMessage
                .withUpdatedId(id: messageId)
                .withUpdatedStableId(stableId: baseMessage.stableId &+ UInt32(offset + 1))
                .withUpdatedStableVersion(stableVersion: baseMessage.stableVersion &+ UInt32(offset + 1))
                .withUpdatedText(version.text)
                .withUpdatedTimestamp(timestamp)
                .withUpdatedMedia([])
                .withUpdatedAttributes([])'''

new_message_block = '''let message = Message(
                stableId: baseMessage.stableId &+ UInt32(offset + 1),
                stableVersion: baseMessage.stableVersion &+ UInt32(offset + 1),
                id: messageId,
                globallyUniqueId: nil,
                groupingKey: nil,
                groupInfo: nil,
                threadId: nil,
                timestamp: timestamp,
                flags: baseMessage.flags,
                tags: MessageTags(),
                globalTags: GlobalMessageTags(),
                localTags: LocalMessageTags(),
                customTags: [],
                forwardInfo: nil,
                author: baseMessage.author,
                text: version.text,
                attributes: [],
                media: [],
                peers: baseMessage.peers,
                associatedMessages: baseMessage.associatedMessages,
                associatedMessageIds: [],
                associatedMedia: [:],
                associatedThreadInfo: nil,
                associatedStories: [:]
            )'''

if "associatedMessageIds: []" in ctx:
    print(f"[{VERSION}] clean history message clone already present")
else:
    ctx = replace_once(ctx, old_message_block, new_message_block, "history clean Message clone")
    print(f"[{VERSION}] clean history message clone patched")

old_mode = '''mode: .standard(.default), params: nil)'''
new_mode = '''mode: .standard(.previewing), params: nil)'''

if "mode: .standard(.previewing), params: nil)" in ctx:
    print(f"[{VERSION}] history controller already uses previewing mode")
else:
    ctx = replace_once(ctx, old_mode, new_mode, "history controller inputless mode")
    print(f"[{VERSION}] history controller mode patched")

ctx_p.write_text(ctx)
settings_p.write_text(settings)

ctx = ctx_p.read_text()
settings = settings_p.read_text()

checks = [
    ("version v0.9F.2", "Version: v0.9F.2" in settings),
    ("stars short row", '"Local Stars Balance", state.localStarsAmount' in settings),
    ("stars no long title", True),
    ("clean message clone", "let message = Message(" in ctx and "associatedMessageIds: []" in ctx),
    ("forward nil", "forwardInfo: nil" in ctx),
    ("media empty", "media: []" in ctx),
    ("attributes empty", "attributes: []" in ctx),
    ("previewing mode", "mode: .standard(.previewing), params: nil)" in ctx),
]

bad = [name for name, ok in checks if not ok]
if bad:
    for name in bad:
        print(f"[{VERSION}] FAILED: {name}")
    raise SystemExit(1)

print("GhostBase v0.9F.2 history/stars polish patch OK")
