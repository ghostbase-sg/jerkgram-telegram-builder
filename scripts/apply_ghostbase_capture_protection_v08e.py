from pathlib import Path
import runpy

VERSION = "v0.8E"

ALLOW_CAPTURE = '(((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.AllowScreenshots") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.AllowScreenRecording") as? Bool) ?? true))'

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/GalleryUI/Sources/GalleryController.swift").exists():
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

def replace_all(text: str, old: str, new: str, label: str, min_count: int = 1) -> str:
    if new in text and old not in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    count = text.count(old)
    if count < min_count:
        fail(label)
    print(f"[{VERSION}] patch {label}: {count} replacement(s)")
    return text.replace(old, new)

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

def insert_update_cases_flexible(text: str, insertion: str, label: str) -> str:
    if insertion.strip() in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    switch_pos = text.find("switch key {")
    if switch_pos < 0:
        fail(label + " switch")
    read_pos = text.find("\n            case GhostBaseKey.readMessages:", switch_pos)
    if read_pos >= 0:
        return text[:read_pos] + "\n" + insertion.rstrip("\n") + text[read_pos:]
    default_pos = text.find("\n            default:", switch_pos)
    if default_pos >= 0:
        return text[:default_pos] + "\n" + insertion.rstrip("\n") + text[default_pos:]
    fail(label + " insert position")

BASE = find_base()

v08d_p = Path(__file__).with_name("apply_ghostbase_protected_chat_actions_v08d.py")
if not v08d_p.exists():
    raise SystemExit(f"[{VERSION}] ERROR: missing prerequisite {v08d_p}")

settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
gallery_p = BASE / "submodules/GalleryUI/Sources/GalleryController.swift"
chat_image_p = BASE / "submodules/GalleryUI/Sources/Items/ChatImageGalleryItem.swift"
interactive_media_p = BASE / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveMediaNode/Sources/ChatMessageInteractiveMediaNode.swift"
instant_video_p = BASE / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveInstantVideoNode/Sources/ChatMessageInteractiveInstantVideoNode.swift"
reply_info_p = BASE / "submodules/TelegramUI/Components/Chat/ChatMessageReplyInfoNode/Sources/ChatMessageReplyInfoNode.swift"
pinned_p = BASE / "submodules/TelegramUI/Sources/ChatPinnedMessageTitlePanelNode.swift"
shared_player_p = BASE / "submodules/TelegramUI/Sources/SharedMediaPlayer.swift"
chat_controller_p = BASE / "submodules/TelegramUI/Sources/ChatController.swift"

settings_existing = settings_p.read_text(errors="ignore") if settings_p.exists() else ""
if "Version: v0.8E" in settings_existing and "GhostBase.ProtectedContent.AllowScreenRecording" in settings_existing:
    print(f"[{VERSION}] v0.8E already applied; skip prerequisite replay")
elif "Version: v0.8D" in settings_existing and "GhostBase.ProtectedContent.ChatForward" in settings_existing:
    print(f"[{VERSION}] v0.8D chain already applied; skip prerequisite replay")
else:
    runpy.run_path(str(v08d_p))

settings = settings_p.read_text()
gallery = gallery_p.read_text()
chat_image = chat_image_p.read_text()
interactive_media = interactive_media_p.read_text()
instant_video = instant_video_p.read_text()
reply_info = reply_info_p.read_text()
pinned = pinned_p.read_text()
shared_player = shared_player_p.read_text()
chat_controller = chat_controller_p.read_text()

settings = settings.replace("Version: v0.8D", "Version: v0.8E")
settings = settings.replace(
    "Protected Chat Actions are active in v0.8D.",
    "Protected Chat Actions are active in v0.8D. Protected Capture bypass is active in v0.8E."
)

settings = insert_after_line_contains(
    settings,
    "GhostBase.ProtectedContent.ChatForward",
    '''    static let allowScreenshots = "GhostBase.ProtectedContent.AllowScreenshots"
    static let allowScreenRecording = "GhostBase.ProtectedContent.AllowScreenRecording"
''',
    "settings capture keys"
)

settings = insert_before_line_contains(
    settings,
    "static func load()",
    '''    var allowScreenshots: Bool
    var allowScreenRecording: Bool

''',
    "settings capture state vars"
)

settings = insert_args_before_state_init_close(
    settings,
    '''            allowScreenshots: ghostBaseBool(GhostBaseKey.allowScreenshots, defaultValue: true),
            allowScreenRecording: ghostBaseBool(GhostBaseKey.allowScreenRecording, defaultValue: true)''',
    "settings capture load"
)

settings = insert_before_func_end(
    settings,
    "func save()",
    '''        UserDefaults.standard.set(self.allowScreenshots, forKey: GhostBaseKey.allowScreenshots)
        UserDefaults.standard.set(self.allowScreenRecording, forKey: GhostBaseKey.allowScreenRecording)
''',
    "settings capture save"
)

settings = insert_after_line_contains(
    settings,
    "Chat Forward",
    '''    entries.append(.toggle(protected, 8, GhostBaseKey.allowScreenshots, "Allow Screenshots", state.allowScreenshots))
    entries.append(.toggle(protected, 9, GhostBaseKey.allowScreenRecording, "Allow Screen Recording", state.allowScreenRecording))
''',
    "settings capture entries"
)

settings = insert_update_cases_flexible(
    settings,
    '''            case GhostBaseKey.allowScreenshots:
                updated.allowScreenshots = value
            case GhostBaseKey.allowScreenRecording:
                updated.allowScreenRecording = value
''',
    "settings capture update cases"
)

gallery = replace_all(
    gallery,
    "let captureProtected = message.isCopyProtected() || message.containsSecretMedia || message.minAutoremoveOrClearTimeout == viewOnceTimeout || message.paidContent != nil || peerIsCopyProtected",
    f"let captureProtected = message.containsSecretMedia || message.minAutoremoveOrClearTimeout == viewOnceTimeout || message.paidContent != nil || (!{ALLOW_CAPTURE} && (message.isCopyProtected() || peerIsCopyProtected))",
    "GalleryController regular media captureProtected",
    min_count=2
)

gallery = replace_all(
    gallery,
    "captureProtected: message.isCopyProtected() || message.containsSecretMedia || peerIsCopyProtected",
    f"captureProtected: message.containsSecretMedia || (!{ALLOW_CAPTURE} && (message.isCopyProtected() || peerIsCopyProtected))",
    "GalleryController webpage video captureProtected",
    min_count=2
)

chat_image = replace_once(
    chat_image,
    "self.imageNode.captureProtected = message.id.peerId.namespace == Namespaces.Peer.SecretChat || message.isCopyProtected() || peerIsCopyProtected || isSecret || message.paidContent != nil",
    f"self.imageNode.captureProtected = message.id.peerId.namespace == Namespaces.Peer.SecretChat || isSecret || message.paidContent != nil || (!{ALLOW_CAPTURE} && (message.isCopyProtected() || peerIsCopyProtected))",
    "ChatImageGalleryItem image captureProtected"
)

interactive_media = replace_all(
    interactive_media,
    "captureProtected: associatedData.isCopyProtectionEnabled || message.isCopyProtected() || isExtendedMedia,",
    f"captureProtected: isExtendedMedia || (!{ALLOW_CAPTURE} && (associatedData.isCopyProtectionEnabled || message.isCopyProtected())),",
    "ChatMessageInteractiveMediaNode video captureProtected",
    min_count=1
)

interactive_media = replace_once(
    interactive_media,
    "strongSelf.imageNode.captureProtected = associatedData.isCopyProtectionEnabled || message.isCopyProtected() || isExtendedMedia",
    f"strongSelf.imageNode.captureProtected = isExtendedMedia || (!{ALLOW_CAPTURE} && (associatedData.isCopyProtectionEnabled || message.isCopyProtected()))",
    "ChatMessageInteractiveMediaNode image captureProtected"
)

instant_video = replace_once(
    instant_video,
    "captureProtected: item.associatedData.isCopyProtectionEnabled || item.message.isCopyProtected(),",
    f"captureProtected: isViewOnceMessage || (!{ALLOW_CAPTURE} && (item.associatedData.isCopyProtectionEnabled || item.message.isCopyProtected())),",
    "ChatMessageInteractiveInstantVideoNode captureProtected"
)

reply_info = replace_once(
    reply_info,
    "node.imageNode?.captureProtected = arguments.associatedData.isCopyProtectionEnabled || message.isCopyProtected()",
    f"node.imageNode?.captureProtected = !{ALLOW_CAPTURE} && (arguments.associatedData.isCopyProtectionEnabled || message.isCopyProtected())",
    "ChatMessageReplyInfoNode captureProtected"
)

pinned = replace_once(
    pinned,
    "self.captureProtected = interfaceState.copyProtectionEnabled || interfaceState.myCopyProtectionEnabled",
    f"self.captureProtected = !{ALLOW_CAPTURE} && (interfaceState.copyProtectionEnabled || interfaceState.myCopyProtectionEnabled)",
    "ChatPinnedMessageTitlePanelNode captureProtected"
)

shared_player = replace_once(
    shared_player,
    "case let .telegramFile(fileReference, _, _):\n                                        let videoNode = OverlayInstantVideoNode(",
    "case let .telegramFile(fileReference, _, isViewOnce):\n                                        let videoNode = OverlayInstantVideoNode(",
    "SharedMediaPlayer expose isViewOnce"
)

shared_player = replace_once(
    shared_player,
    "captureProtected: item.message.isCopyProtected(),",
    f"captureProtected: isViewOnce || (!{ALLOW_CAPTURE} && item.message.isCopyProtected()),",
    "SharedMediaPlayer overlay instant video captureProtected"
)

chat_controller = replace_once(
    chat_controller,
    '''            let isSecret = strongSelf.presentationInterfaceState.copyProtectionEnabled || strongSelf.chatLocation.peerId?.namespace == Namespaces.Peer.SecretChat
            let pinchController = makePinchController(sourceNode: sourceNode, disableScreenshots: isSecret, getContentAreaInScreenSpace: {''',
    f'''            // MARK: GhostBase v0.8E protected capture pinch bypass
            let ghostBaseAllowCapture = {ALLOW_CAPTURE}
            let isSecret = strongSelf.chatLocation.peerId?.namespace == Namespaces.Peer.SecretChat
            let disableScreenshots = isSecret || (!ghostBaseAllowCapture && strongSelf.presentationInterfaceState.copyProtectionEnabled)
            let pinchController = makePinchController(sourceNode: sourceNode, disableScreenshots: disableScreenshots, getContentAreaInScreenSpace: {{''',
    "ChatController pinch disableScreenshots"
)

settings_p.write_text(clean(settings))
gallery_p.write_text(clean(gallery))
chat_image_p.write_text(clean(chat_image))
interactive_media_p.write_text(clean(interactive_media))
instant_video_p.write_text(clean(instant_video))
reply_info_p.write_text(clean(reply_info))
pinned_p.write_text(clean(pinned))
shared_player_p.write_text(clean(shared_player))
chat_controller_p.write_text(clean(chat_controller))

settings = settings_p.read_text()
gallery = gallery_p.read_text()
chat_image = chat_image_p.read_text()
interactive_media = interactive_media_p.read_text()
instant_video = instant_video_p.read_text()
reply_info = reply_info_p.read_text()
pinned = pinned_p.read_text()
shared_player = shared_player_p.read_text()
chat_controller = chat_controller_p.read_text()

checks = [
    ("settings version", "Version: v0.8E" in settings),
    ("settings allow screenshots", "GhostBase.ProtectedContent.AllowScreenshots" in settings and "Allow Screenshots" in settings),
    ("settings allow recording", "GhostBase.ProtectedContent.AllowScreenRecording" in settings and "Allow Screen Recording" in settings),

    ("gallery keeps view once", "message.minAutoremoveOrClearTimeout == viewOnceTimeout" in gallery),
    ("gallery keeps paid", "message.paidContent != nil" in gallery),
    ("gallery has allow capture", "GhostBase.ProtectedContent.AllowScreenRecording" in gallery),

    ("image keeps secret", "message.id.peerId.namespace == Namespaces.Peer.SecretChat" in chat_image and "isSecret" in chat_image),
    ("image keeps paid", "message.paidContent != nil" in chat_image),
    ("image has allow capture", "GhostBase.ProtectedContent.AllowScreenRecording" in chat_image),

    ("interactive keeps extended", "isExtendedMedia ||" in interactive_media),
    ("interactive has allow capture", "GhostBase.ProtectedContent.AllowScreenRecording" in interactive_media),

    ("instant keeps view once", "captureProtected: isViewOnceMessage ||" in instant_video),
    ("shared keeps view once", "case let .telegramFile(fileReference, _, isViewOnce):" in shared_player and "captureProtected: isViewOnce ||" in shared_player),

    ("reply has allow capture", "GhostBase.ProtectedContent.AllowScreenRecording" in reply_info),
    ("pinned has allow capture", "GhostBase.ProtectedContent.AllowScreenRecording" in pinned),
    ("pinch keeps secret", "let isSecret = strongSelf.chatLocation.peerId?.namespace == Namespaces.Peer.SecretChat" in chat_controller),
    ("pinch has allow capture", "GhostBase v0.8E protected capture pinch bypass" in chat_controller),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print(f"[{VERSION}] FAILED:")
    for name in bad:
        print("-", name)
    raise SystemExit(1)

print("GhostBase Protected Capture v0.8E patch OK")
