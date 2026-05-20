from pathlib import Path
import runpy

VERSION = "v0.8F"

ALLOW_CAPTURE = '(((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.AllowScreenshots") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.AllowScreenRecording") as? Bool) ?? true))'

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramUI/Sources/ChatController.swift").exists():
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

def replace_case_block(text: str, case_key: str, new_block: str, marker: str, label: str) -> str:
    if marker in text:
        print(f"[{VERSION}] already patched: {label}")
        return text

    start = text.find(f"            case {case_key}:")
    if start < 0:
        fail(label + " start")

    next_case = text.find("\n            case GhostBaseKey.", start + 1)
    default_case = text.find("\n            default:", start + 1)

    candidates = [p for p in [next_case, default_case] if p >= 0]
    if not candidates:
        fail(label + " end")

    end = min(candidates)
    return text[:start] + new_block.rstrip("\n") + text[end:]

def insert_before_update_return(text: str, insertion: str, label: str) -> str:
    if insertion.strip() in text:
        print(f"[{VERSION}] already patched: {label}")
        return text

    marker = "            return updated\n        }\n    })"
    pos = text.find(marker)
    if pos < 0:
        fail(label)

    return text[:pos] + insertion.rstrip("\n") + "\n\n" + text[pos:]

BASE = find_base()

v08e_p = Path(__file__).with_name("apply_ghostbase_capture_protection_v08e.py")
if not v08e_p.exists():
    raise SystemExit(f"[{VERSION}] ERROR: missing prerequisite {v08e_p}")

settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
chat_controller_p = BASE / "submodules/TelegramUI/Sources/ChatController.swift"
chat_node_p = BASE / "submodules/TelegramUI/Sources/ChatControllerNode.swift"
story_content_p = BASE / "submodules/TelegramUI/Components/Stories/StoryContainerScreen/Sources/StoryItemContentComponent.swift"
story_pane_p = BASE / "submodules/TelegramUI/Components/PeerInfo/PeerInfoVisualMediaPaneNode/Sources/PeerInfoStoryPaneNode.swift"

settings_existing = settings_p.read_text(errors="ignore") if settings_p.exists() else ""

if "Version: v0.8F" in settings_existing and "GhostBase v0.8F protected master cascade" in settings_existing:
    print(f"[{VERSION}] v0.8F already applied; skip prerequisite replay")
elif "Version: v0.8E" in settings_existing and "GhostBase.ProtectedContent.AllowScreenRecording" in settings_existing:
    print(f"[{VERSION}] v0.8E chain already applied; skip prerequisite replay")
else:
    runpy.run_path(str(v08e_p))

settings = settings_p.read_text()
chat_controller = chat_controller_p.read_text()
chat_node = chat_node_p.read_text()
story_content = story_content_p.read_text()
story_pane = story_pane_p.read_text()

settings = settings.replace("Version: v0.8E", "Version: v0.8F")
settings = settings.replace(
    "Protected Capture bypass is active in v0.8E.",
    "Protected Capture bypass is active in v0.8E. v0.8F completes protected capture with owner-enabled channels and stories."
)

settings = replace_case_block(
    settings,
    "GhostBaseKey.protectedEnabled",
    '''            case GhostBaseKey.protectedEnabled:
                // MARK: GhostBase v0.8F protected master cascade
                updated.protectedEnabled = value
                updated.galleryShare = value
                updated.gallerySave = value
                updated.galleryCopy = value
                updated.chatSave = value
                updated.chatCopy = value
                updated.chatForward = value
                updated.allowScreenshots = value
                updated.allowScreenRecording = value
''',
    "GhostBase v0.8F protected master cascade",
    "settings protected master cascade"
)

settings = insert_before_update_return(
    settings,
    '''            // MARK: GhostBase v0.8F protected child consistency
            if !updated.galleryShare && !updated.gallerySave && !updated.galleryCopy && !updated.chatSave && !updated.chatCopy && !updated.chatForward && !updated.allowScreenshots && !updated.allowScreenRecording {
                updated.protectedEnabled = false
            } else if updated.galleryShare || updated.gallerySave || updated.galleryCopy || updated.chatSave || updated.chatCopy || updated.chatForward || updated.allowScreenshots || updated.allowScreenRecording {
                updated.protectedEnabled = true
            }''',
    "settings protected child consistency"
)

chat_controller = replace_once(
    chat_controller,
    "                copyProtected: self.presentationInterfaceState.copyProtectionEnabled || self.presentationInterfaceState.myCopyProtectionEnabled,",
    f"                copyProtected: !{ALLOW_CAPTURE} && (self.presentationInterfaceState.copyProtectionEnabled || self.presentationInterfaceState.myCopyProtectionEnabled),",
    "ChatController copyProtected owner-enabled gate"
)

chat_controller = replace_once(
    chat_controller,
    "            let disableScreenshots = isSecret || (!ghostBaseAllowCapture && strongSelf.presentationInterfaceState.copyProtectionEnabled)",
    "            let disableScreenshots = isSecret || (!ghostBaseAllowCapture && (strongSelf.presentationInterfaceState.copyProtectionEnabled || strongSelf.presentationInterfaceState.myCopyProtectionEnabled))",
    "ChatController pinch owner myCopyProtection gate"
)

chat_node = replace_once(
    chat_node,
    "        let isSecret = self.chatPresentationInterfaceState.copyProtectionEnabled || self.chatLocation.peerId?.namespace == Namespaces.Peer.SecretChat || self.chatLocation.peerId?.isVerificationCodes == true",
    f'''        // MARK: GhostBase v0.8F owner-enabled protected capture gate
        let ghostBaseAllowCapture = {ALLOW_CAPTURE}
        let isSecret = self.chatLocation.peerId?.namespace == Namespaces.Peer.SecretChat || self.chatLocation.peerId?.isVerificationCodes == true || (!ghostBaseAllowCapture && self.chatPresentationInterfaceState.copyProtectionEnabled)''',
    "ChatControllerNode owner-enabled title/panel gate"
)

story_content = replace_all(
    story_content,
    "captureProtected: component.item.isForwardingDisabled,",
    f"captureProtected: !{ALLOW_CAPTURE} && component.item.isForwardingDisabled,",
    "StoryItemContentComponent video captureProtected",
    min_count=1
)

story_content = replace_all(
    story_content,
    "isCaptureProtected: component.item.isForwardingDisabled,",
    f"isCaptureProtected: !{ALLOW_CAPTURE} && component.item.isForwardingDisabled,",
    "StoryItemContentComponent image/overlay captureProtected",
    min_count=3
)

story_pane = replace_once(
    story_pane,
    "        if let item = item as? VisualMediaItem, item.story.isForwardingDisabled {",
    f"        if let item = item as? VisualMediaItem, item.story.isForwardingDisabled && !{ALLOW_CAPTURE} {{",
    "PeerInfoStoryPaneNode story layer captureProtected"
)

settings_p.write_text(clean(settings))
chat_controller_p.write_text(clean(chat_controller))
chat_node_p.write_text(clean(chat_node))
story_content_p.write_text(clean(story_content))
story_pane_p.write_text(clean(story_pane))

settings = settings_p.read_text()
chat_controller = chat_controller_p.read_text()
chat_node = chat_node_p.read_text()
story_content = story_content_p.read_text()
story_pane = story_pane_p.read_text()

checks = [
    ("settings version", "Version: v0.8F" in settings),
    ("settings master cascade", "GhostBase v0.8F protected master cascade" in settings),
    ("settings child consistency", "GhostBase v0.8F protected child consistency" in settings),
    ("settings capture toggles preserved", "Allow Screenshots" in settings and "Allow Screen Recording" in settings),

    ("chat controller owner copyProtected", "copyProtected: !" in chat_controller and "myCopyProtectionEnabled" in chat_controller),
    ("chat controller pinch myCopy", "presentationInterfaceState.myCopyProtectionEnabled" in chat_controller and "GhostBase v0.8E protected capture pinch bypass" in chat_controller),

    ("chat node owner gate", "GhostBase v0.8F owner-enabled protected capture gate" in chat_node),
    ("chat node keeps SecretChat", "Namespaces.Peer.SecretChat" in chat_node),
    ("chat node keeps verification codes", "isVerificationCodes" in chat_node),

    ("story video allow capture", "captureProtected: !" in story_content and "component.item.isForwardingDisabled" in story_content),
    ("story image overlay allow capture", "isCaptureProtected: !" in story_content and "component.item.isForwardingDisabled" in story_content),
    ("peerinfo story allow capture", "item.story.isForwardingDisabled && !" in story_pane),

    ("screenCaptureManager untouched", "ScreenCaptureDetectionManager(check:" in chat_controller),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print(f"[{VERSION}] FAILED:")
    for name in bad:
        print("-", name)
    raise SystemExit(1)

print("GhostBase Protected Capture Complete v0.8F patch OK")
