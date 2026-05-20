from pathlib import Path
import runpy
import re

VERSION = "v0.8D"

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift").exists():
            return c
    raise SystemExit(f"[{VERSION}] ERROR: cannot find source base from cwd={cwd}")

def clean(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"

def fail(label: str) -> None:
    raise SystemExit(f"[{VERSION}] ERROR: required anchor not found: {label}")

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    if old not in text:
        fail(label)
    return text.replace(old, new, 1)

def replace_after(text: str, marker: str, old: str, new: str, label: str) -> str:
    if new in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    start = text.find(marker)
    if start < 0:
        fail(label + " marker")
    pos = text.find(old, start)
    if pos < 0:
        fail(label)
    return text[:pos] + new + text[pos + len(old):]

def replace_before_marker(text: str, marker: str, old: str, new: str, label: str, window: int = 3000) -> str:
    if new in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    pos = text.find(marker)
    if pos < 0:
        fail(label + " marker")
    start = max(0, pos - window)
    local = text[start:pos]
    rel = local.rfind(old)
    if rel < 0:
        fail(label)
    abs_pos = start + rel
    return text[:abs_pos] + new + text[abs_pos + len(old):]

def patch_forward_insert_gate(text: str) -> str:
    if "GhostBase v0.8D chat forward action gate" in text:
        print(f"[{VERSION}] already patched: chat forward action gate")
        return text

    marker = "optionsMap[id]!.insert(.forward)"
    pos = text.find(marker)
    if pos < 0:
        fail("chat forward insert marker")

    start = max(0, pos - 2500)
    local = text[start:pos]
    rel = local.rfind("!isCopyProtected")
    if rel < 0:
        fail("chat forward !isCopyProtected gate")

    abs_pos = start + rel
    line_start = text.rfind("\n", 0, abs_pos) + 1
    indent = text[line_start:abs_pos]
    indent = indent[:len(indent) - len(indent.lstrip())]

    local_name = "ghostBaseProtectedChatForward"
    insert = (
        f"{indent}// MARK: GhostBase v0.8D chat forward action gate\n"
        f"{indent}let {local_name} = (((UserDefaults.standard.object(forKey: \"GhostBase.ProtectedContent.Enabled\") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: \"GhostBase.ProtectedContent.ChatForward\") as? Bool) ?? true) && !message.containsSecretMedia)\n"
    )

    text = text[:line_start] + insert + text[line_start:]
    abs_pos += len(insert)
    text = text[:abs_pos] + f"(!isCopyProtected || {local_name})" + text[abs_pos + len("!isCopyProtected"):]
    return text

def patch_share_button_gate(text: str, label: str) -> str:
    if "GhostBase v0.8D right-side protected share button" in text:
        print(f"[{VERSION}] already patched: {label}")
        return text

    pattern = re.compile(r'(?m)^(\s*)if\s+\(?item\.associatedData\.isCopyProtectionEnabled \|\| item\.message\.isCopyProtected\(\)\)?\s*\{')
    match = pattern.search(text)
    if not match:
        fail(label)

    indent = match.group(1)
    replacement = (
        f'{indent}// MARK: GhostBase v0.8D right-side protected share button\n'
        f'{indent}let ghostBaseProtectedChatForward = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.ChatForward") as? Bool) ?? true) && !item.message.containsSecretMedia && item.message.paidContent == nil)\n'
        f'{indent}if (item.associatedData.isCopyProtectionEnabled || item.message.isCopyProtected()) && !ghostBaseProtectedChatForward {{'
    )

    return text[:match.start()] + replacement + text[match.end():]

BASE = find_base()

v08c_p = Path(__file__).with_name("apply_ghostbase_protected_controls_v08c.py")
if not v08c_p.exists():
    raise SystemExit(f"[{VERSION}] ERROR: missing prerequisite {v08c_p}")

settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
share_p = BASE / "submodules/ShareController/Sources/ShareController.swift"
ctx_p = BASE / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"

bubble_p = BASE / "submodules/TelegramUI/Components/Chat/ChatMessageBubbleItemNode/Sources/ChatMessageBubbleItemNode.swift"
instant_p = BASE / "submodules/TelegramUI/Components/Chat/ChatMessageInstantVideoItemNode/Sources/ChatMessageInstantVideoItemNode.swift"
animated_p = BASE / "submodules/TelegramUI/Components/Chat/ChatMessageAnimatedStickerItemNode/Sources/ChatMessageAnimatedStickerItemNode.swift"
sticker_p = BASE / "submodules/TelegramUI/Components/Chat/ChatMessageStickerItemNode/Sources/ChatMessageStickerItemNode.swift"

settings_existing = settings_p.read_text(errors="ignore") if settings_p.exists() else ""

if "Version: v0.8D" in settings_existing and "GhostBase.ProtectedContent.ChatForward" in settings_existing:
    print(f"[{VERSION}] v0.8D already applied; skip prerequisite replay")
elif "Version: v0.8C" in settings_existing and "GhostBase.ProtectedContent.GalleryCopy" in settings_existing:
    print(f"[{VERSION}] v0.8C chain already applied; skip prerequisite replay")
else:
    runpy.run_path(str(v08c_p))

settings = settings_p.read_text()
share = share_p.read_text()
ctx = ctx_p.read_text()
bubble = bubble_p.read_text()
instant = instant_p.read_text()
animated = animated_p.read_text()
sticker = sticker_p.read_text()

settings = settings.replace("Version: v0.8C", "Version: v0.8D")
settings = settings.replace(
    "Protected Content Gallery Save/Share is active in v0.8C.",
    "Protected Content Gallery Save/Share is active in v0.8C. Protected Chat Actions are active in v0.8D."
)

def insert_after_line_contains(text: str, contains: str, insertion: str, label: str) -> str:
    if insertion.strip() in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if contains in line:
            lines[i + 1:i + 1] = insertion.rstrip("\n").splitlines()
            return "\n".join(lines) + "\n"
    fail(label)

def insert_before_line_contains(text: str, contains: str, insertion: str, label: str) -> str:
    if insertion.strip() in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if contains in line:
            lines[i:i] = insertion.rstrip("\n").splitlines()
            return "\n".join(lines) + "\n"
    fail(label)

def insert_args_before_state_init_close(text: str, insertion: str, label: str) -> str:
    if insertion.strip() in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    start = text.find("return GhostBaseSettingsState(")
    if start < 0:
        fail(label + " init start")
    depth = 0
    close = -1
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                close = i
                break
    if close < 0:
        fail(label + " init close")
    before = text[:close]
    after = text[close:]
    last_nl = before.rstrip().rfind("\n")
    if last_nl >= 0:
        line = before[last_nl + 1:].rstrip()
        if line and not line.endswith(","):
            before = before.rstrip() + ",\n"
    return before + insertion.rstrip("\n") + "\n" + after

def insert_before_func_end(text: str, func_marker: str, insertion: str, label: str) -> str:
    if insertion.strip() in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    start = text.find(func_marker)
    if start < 0:
        fail(label + " func start")
    brace = text.find("{", start)
    if brace < 0:
        fail(label + " func brace")
    depth = 0
    close = -1
    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                close = i
                break
    if close < 0:
        fail(label + " func close")
    return text[:close] + insertion.rstrip("\n") + "\n" + text[close:]

def insert_before_default_case_after(text: str, marker: str, insertion: str, label: str) -> str:
    if insertion.strip() in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    start = text.find(marker)
    if start < 0:
        fail(label + " marker")
    default_pos = text.find("\n            default:", start)
    if default_pos < 0:
        fail(label + " default")
    return text[:default_pos] + "\n" + insertion.rstrip("\n") + text[default_pos:]

settings = insert_after_line_contains(
    settings,
    "GhostBase.ProtectedContent.GalleryCopy",
    '''    static let chatSave = "GhostBase.ProtectedContent.ChatSave"
    static let chatCopy = "GhostBase.ProtectedContent.ChatCopy"
    static let chatForward = "GhostBase.ProtectedContent.ChatForward"
''',
    "settings chat action keys"
)

settings = insert_before_line_contains(
    settings,
    "static func load()",
    '''    var chatSave: Bool
    var chatCopy: Bool
    var chatForward: Bool

''',
    "settings chat action state vars"
)

settings = insert_args_before_state_init_close(
    settings,
    '''            chatSave: ghostBaseBool(GhostBaseKey.chatSave, defaultValue: true),
            chatCopy: ghostBaseBool(GhostBaseKey.chatCopy, defaultValue: true),
            chatForward: ghostBaseBool(GhostBaseKey.chatForward, defaultValue: true)''',
    "settings chat action load"
)

settings = insert_before_func_end(
    settings,
    "func save()",
    '''        UserDefaults.standard.set(self.chatSave, forKey: GhostBaseKey.chatSave)
        UserDefaults.standard.set(self.chatCopy, forKey: GhostBaseKey.chatCopy)
        UserDefaults.standard.set(self.chatForward, forKey: GhostBaseKey.chatForward)
''',
    "settings chat action save"
)

settings = insert_after_line_contains(
    settings,
    "Gallery Copy",
    '''    entries.append(.toggle(protected, 5, GhostBaseKey.chatSave, "Chat Save", state.chatSave))
    entries.append(.toggle(protected, 6, GhostBaseKey.chatCopy, "Chat Copy", state.chatCopy))
    entries.append(.toggle(protected, 7, GhostBaseKey.chatForward, "Chat Forward", state.chatForward))
''',
    "settings chat action entries"
)

def insert_update_cases_flexible(text: str, insertion: str, label: str) -> str:
    if insertion.strip() in text:
        print(f"[{VERSION}] already patched: {label}")
        return text

    switch_pos = text.find("switch key {")
    if switch_pos < 0:
        fail(label + " switch")

    # Best place: before Ghost Mode cases.
    read_pos = text.find("\n            case GhostBaseKey.readMessages:", switch_pos)
    if read_pos >= 0:
        return text[:read_pos] + "\n" + insertion.rstrip("\n") + text[read_pos:]

    # Fallback: before default in the same switch.
    default_pos = text.find("\n            default:", switch_pos)
    if default_pos >= 0:
        return text[:default_pos] + "\n" + insertion.rstrip("\n") + text[default_pos:]

    fail(label + " insert position")

settings = insert_update_cases_flexible(
    settings,
    "            case GhostBaseKey.chatSave:\n"
    "                updated.chatSave = value\n"
    "            case GhostBaseKey.chatCopy:\n"
    "                updated.chatCopy = value\n"
    "            case GhostBaseKey.chatForward:\n"
    "                updated.chatForward = value\n",
    "settings chat action update cases"
)

if "GhostBase v0.8D ShareController media scheduled safety" not in share:
    marker = "GhostBase v0.8C Internal ShareController Scheduled Send bridge"
    map_pos = share.find("return messages.map { message in", share.find(marker))
    if map_pos < 0:
        fail("ShareController enqueue map")
    insert_pos = map_pos + len("return messages.map { message in")
    insert = '''
                    // MARK: GhostBase v0.8D ShareController media scheduled safety
                    let ghostBaseCanScheduleShareMessage: Bool
                    switch message {
                    case let .message(text: _, attributes: _, inlineStickers: _, mediaReference: mediaReference, threadId: _, replyToMessageId: _, replyToStoryId: _, localGroupingKey: _, correlationId: _, bubbleUpEmojiOrStickersets: _):
                        ghostBaseCanScheduleShareMessage = mediaReference == nil
                    case .forward:
                        ghostBaseCanScheduleShareMessage = false
                    }
'''
    share = share[:insert_pos] + insert + share[insert_pos:]
else:
    print(f"[{VERSION}] already patched: ShareController media scheduled safety")

share = replace_after(
    share,
    "GhostBase v0.8D ShareController media scheduled safety",
    "                        if let ghostBaseShareScheduleTime {\n",
    "                        if ghostBaseCanScheduleShareMessage, let ghostBaseShareScheduleTime {\n",
    "ShareController schedule condition"
)

def patch_regex(text: str, pattern, repl_func, marker: str, label: str) -> str:
    if marker in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    m = pattern.search(text)
    if not m:
        fail(label)
    return text[:m.start()] + repl_func(m) + text[m.end():]

ctx = patch_regex(
    ctx,
    re.compile(r'(?m)^([ \t]*)if !isCopyProtected \{\n([ \t]*)actions\.append\(\.action\(ContextMenuActionItem\(text: chatPresentationInterfaceState\.strings\.Conversation_ContextMenuCopy,'),
    lambda m: (
        m.group(1) + '// MARK: GhostBase v0.8D chat copy action gate\n' +
        m.group(1) + 'let ghostBaseProtectedChatCopy = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.ChatCopy") as? Bool) ?? true) && !message.containsSecretMedia)\n' +
        m.group(1) + 'if !isCopyProtected || ghostBaseProtectedChatCopy {\n' +
        m.group(2) + 'actions.append(.action(ContextMenuActionItem(text: chatPresentationInterfaceState.strings.Conversation_ContextMenuCopy,'
    ),
    "GhostBase v0.8D chat copy action gate",
    "chat copy gate"
)

ctx = patch_regex(
    ctx,
    re.compile(r'(?m)^([ \t]*)if resourceAvailable, !message\.containsSecretMedia && !isCopyProtected \{'),
    lambda m: (
        m.group(1) + '// MARK: GhostBase v0.8D chat save action gate\n' +
        m.group(1) + 'let ghostBaseProtectedChatSave = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.ChatSave") as? Bool) ?? true))\n' +
        m.group(1) + 'if resourceAvailable, !message.containsSecretMedia && (!isCopyProtected || ghostBaseProtectedChatSave) {'
    ),
    "GhostBase v0.8D chat save action gate",
    "chat save gate"
)

ctx = patch_regex(
    ctx,
    re.compile(r'(?m)^([ \t]*)if !isCopyProtected \{\n([ \t]*)actions\.append\(\.action\(ContextMenuActionItem\(text: chatPresentationInterfaceState\.strings\.Conversation_ContextMenuForward,'),
    lambda m: (
        m.group(1) + '// MARK: GhostBase v0.8D chat forward menu gate\n' +
        m.group(1) + 'let ghostBaseProtectedChatForwardMenu = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.ChatForward") as? Bool) ?? true) && !message.containsSecretMedia && message.paidContent == nil)\n' +
        m.group(1) + 'if !isCopyProtected || ghostBaseProtectedChatForwardMenu {\n' +
        m.group(2) + 'actions.append(.action(ContextMenuActionItem(text: chatPresentationInterfaceState.strings.Conversation_ContextMenuForward,'
    ),
    "GhostBase v0.8D chat forward menu gate",
    "chat forward menu gate"
)

def patch_forward_available_gate(text: str) -> str:
    if "GhostBase v0.8D chat forward available gate" in text:
        print(f"[{VERSION}] already patched: chat forward available gate")
        return text

    allow = '(((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.ChatForward") as? Bool) ?? true))'

    old1 = "if message.id.peerId.namespace != Namespaces.Peer.SecretChat && !message.isCopyProtected() {"
    new1 = (
        '// MARK: GhostBase v0.8D chat forward action gate\n'
        '                            // MARK: GhostBase v0.8D chat forward available gate\n'
        f'                            if message.id.peerId.namespace != Namespaces.Peer.SecretChat && (!message.isCopyProtected() || {allow}) {{'
    )

    old2 = "if !isAction && !message.isCopyProtected() && !isShareProtected {"
    new2 = f"if !isAction && (!message.isCopyProtected() || {allow}) && !isShareProtected {{"

    old3 = "if !isScheduled && message.id.peerId.namespace != Namespaces.Peer.SecretChat && !message.containsSecretMedia && !isAction && !message.id.peerId.isReplies && !message.isCopyProtected() && !isShareProtected {"
    new3 = f"if !isScheduled && message.id.peerId.namespace != Namespaces.Peer.SecretChat && !message.containsSecretMedia && !isAction && !message.id.peerId.isReplies && (!message.isCopyProtected() || {allow}) && !isShareProtected {{"

    replacements = [
        ("chat forward channel gate", old1, new1),
        ("chat forward group gate", old2, new2),
        ("chat forward peer gate", old3, new3),
    ]

    for label, old, new in replacements:
        if old in text:
            text = text.replace(old, new, 1)
        elif new in text:
            print(f"[{VERSION}] already patched: {label}")
        else:
            fail(label)

    return text

ctx = patch_forward_available_gate(ctx)


bubble = patch_share_button_gate(bubble, "BubbleItem right-side share gate")
instant = patch_share_button_gate(instant, "InstantVideo right-side share gate")
animated = patch_share_button_gate(animated, "AnimatedSticker right-side share gate")
sticker = patch_share_button_gate(sticker, "Sticker right-side share gate")

settings_p.write_text(clean(settings))
share_p.write_text(clean(share))
ctx_p.write_text(clean(ctx))
bubble_p.write_text(clean(bubble))
instant_p.write_text(clean(instant))
animated_p.write_text(clean(animated))
sticker_p.write_text(clean(sticker))

settings = settings_p.read_text()
share = share_p.read_text()
ctx = ctx_p.read_text()
bubble = bubble_p.read_text()
instant = instant_p.read_text()
animated = animated_p.read_text()
sticker = sticker_p.read_text()

checks = [
    ("settings version", "Version: v0.8D" in settings),
    ("settings chat save key", "GhostBase.ProtectedContent.ChatSave" in settings),
    ("settings chat copy key", "GhostBase.ProtectedContent.ChatCopy" in settings),
    ("settings chat forward key", "GhostBase.ProtectedContent.ChatForward" in settings),
    ("settings chat entries", "Chat Save" in settings and "Chat Copy" in settings and "Chat Forward" in settings),

    ("share safety marker", "GhostBase v0.8D ShareController media scheduled safety" in share),
    ("share safety condition", "if ghostBaseCanScheduleShareMessage, let ghostBaseShareScheduleTime" in share),
    ("share no old broken syntax", "let ghostBaseShareScheduleTime: Int32? = (((" not in share),

    ("chat copy marker", "GhostBase v0.8D chat copy action gate" in ctx),
    ("chat save marker", "GhostBase v0.8D chat save action gate" in ctx),
    ("chat forward marker", "GhostBase v0.8D chat forward action gate" in ctx),

    ("bubble right-side marker", "GhostBase v0.8D right-side protected share button" in bubble),
    ("instant right-side marker", "GhostBase v0.8D right-side protected share button" in instant),
    ("animated right-side marker", "GhostBase v0.8D right-side protected share button" in animated),
    ("sticker right-side marker", "GhostBase v0.8D right-side protected share button" in sticker),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print(f"[{VERSION}] FAILED:")
    for name in bad:
        print("-", name)
    raise SystemExit(1)

print("GhostBase Protected Chat Actions v0.8D patch OK")
