from pathlib import Path
import runpy

VERSION = "v0.8G"

ALLOW_CAPTURE = '(((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.AllowScreenshots") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.AllowScreenRecording") as? Bool) ?? true))'
ALLOW_ONETIME_CAPTURE_MESSAGE = '(((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeScreenshots") as? Bool) ?? false) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeScreenRecording") as? Bool) ?? false) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && message.id.peerId.namespace != Namespaces.Peer.SecretChat)'
ALLOW_ONETIME_CAPTURE_ITEM = '(((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeScreenshots") as? Bool) ?? false) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeScreenRecording") as? Bool) ?? false) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && item.message.id.peerId.namespace != Namespaces.Peer.SecretChat)'
ALLOW_ONETIME_SCREEN_RECORDING_MESSAGE = '(((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeScreenRecording") as? Bool) ?? false) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && message.id.peerId.namespace != Namespaces.Peer.SecretChat)'
ALLOW_ONETIME_SCREENSHOTS_STRONGSELF = '(((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeScreenshots") as? Bool) ?? false) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && strongSelf.messageId.peerId.namespace != Namespaces.Peer.SecretChat)'
ALLOW_ONETIME_SAVE_MESSAGE = '(((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && message.id.peerId.namespace != Namespaces.Peer.SecretChat && message.paidContent == nil)'

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramUI/Sources/Chat/ChatControllerOpenViewOnceMediaMessage.swift").exists():
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
    if before.rstrip() and not before.rstrip().endswith(","):
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

def replace_child_consistency(text: str, new_block: str, label: str) -> str:
    if "GhostBase v0.8G protected child consistency" in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    marker = "            // MARK: GhostBase v0.8F protected child consistency"
    start = text.find(marker)
    end_marker = "\n\n            return updated"
    end = text.find(end_marker, start)
    if start < 0 or end < 0:
        fail(label)
    return text[:start] + new_block.rstrip("\n") + text[end:]

BASE = find_base()

v08f_p = Path(__file__).with_name("apply_ghostbase_capture_complete_v08f.py")
if not v08f_p.exists():
    raise SystemExit(f"[{VERSION}] ERROR: missing prerequisite {v08f_p}")

settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
open_view_once_p = BASE / "submodules/TelegramUI/Sources/Chat/ChatControllerOpenViewOnceMediaMessage.swift"
secret_preview_p = BASE / "submodules/GalleryUI/Sources/SecretMediaPreviewController.swift"
gallery_p = BASE / "submodules/GalleryUI/Sources/GalleryController.swift"
instant_video_p = BASE / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveInstantVideoNode/Sources/ChatMessageInteractiveInstantVideoNode.swift"

settings_existing = settings_p.read_text(errors="ignore") if settings_p.exists() else ""
if "Version: v0.8G" in settings_existing and "GhostBase.ProtectedContent.OneTimeSave" in settings_existing:
    print(f"[{VERSION}] v0.8G already applied; skip prerequisite replay")
elif "Version: v0.8F" in settings_existing and "GhostBase v0.8F protected master cascade" in settings_existing:
    print(f"[{VERSION}] v0.8F chain already applied; skip prerequisite replay")
else:
    runpy.run_path(str(v08f_p))

settings = settings_p.read_text()
open_view_once = open_view_once_p.read_text()
secret_preview = secret_preview_p.read_text()
gallery = gallery_p.read_text()
instant_video = instant_video_p.read_text()

settings = settings.replace("Version: v0.8F", "Version: v0.8G")

settings = insert_after_line_contains(
    settings,
    "GhostBase.ProtectedContent.AllowScreenRecording",
    '''    static let oneTimeScreenshots = "GhostBase.ProtectedContent.OneTimeScreenshots"
    static let oneTimeScreenRecording = "GhostBase.ProtectedContent.OneTimeScreenRecording"
    static let oneTimeSave = "GhostBase.ProtectedContent.OneTimeSave"
''',
    "settings one-time keys"
)

settings = insert_before_line_contains(
    settings,
    "static func load()",
    '''    var oneTimeScreenshots: Bool
    var oneTimeScreenRecording: Bool
    var oneTimeSave: Bool

''',
    "settings one-time state vars"
)

settings = insert_args_before_state_init_close(
    settings,
    '''            oneTimeScreenshots: ghostBaseBool(GhostBaseKey.oneTimeScreenshots, defaultValue: false),
            oneTimeScreenRecording: ghostBaseBool(GhostBaseKey.oneTimeScreenRecording, defaultValue: false),
            oneTimeSave: ghostBaseBool(GhostBaseKey.oneTimeSave, defaultValue: false)''',
    "settings one-time load"
)

settings = insert_before_func_end(
    settings,
    "func save()",
    '''        UserDefaults.standard.set(self.oneTimeScreenshots, forKey: GhostBaseKey.oneTimeScreenshots)
        UserDefaults.standard.set(self.oneTimeScreenRecording, forKey: GhostBaseKey.oneTimeScreenRecording)
        UserDefaults.standard.set(self.oneTimeSave, forKey: GhostBaseKey.oneTimeSave)
''',
    "settings one-time save"
)

settings = insert_after_line_contains(
    settings,
    "Allow Screen Recording",
    '''    entries.append(.toggle(protected, 10, GhostBaseKey.oneTimeScreenshots, "Allow One-Time Screenshots", state.oneTimeScreenshots))
    entries.append(.toggle(protected, 11, GhostBaseKey.oneTimeScreenRecording, "Allow One-Time Screen Recording", state.oneTimeScreenRecording))
    entries.append(.toggle(protected, 12, GhostBaseKey.oneTimeSave, "Allow One-Time Save", state.oneTimeSave))
''',
    "settings one-time entries"
)

settings = replace_case_block(
    settings,
    "GhostBaseKey.protectedEnabled",
    '''            case GhostBaseKey.protectedEnabled:
                // MARK: GhostBase v0.8G protected master cascade
                updated.protectedEnabled = value
                updated.protectedGalleryShare = value
                updated.protectedGallerySave = value
                updated.protectedGalleryCopy = value
                updated.chatSave = value
                updated.chatCopy = value
                updated.chatForward = value
                updated.allowScreenshots = value
                updated.allowScreenRecording = value
                updated.oneTimeScreenshots = value
                updated.oneTimeScreenRecording = value
                updated.oneTimeSave = value
''',
    "GhostBase v0.8G protected master cascade",
    "settings one-time master cascade"
)

settings = replace_case_block(
    settings,
    "GhostBaseKey.oneTimeScreenshots",
    '''            case GhostBaseKey.oneTimeScreenshots:
                updated.oneTimeScreenshots = value
            case GhostBaseKey.oneTimeScreenRecording:
                updated.oneTimeScreenRecording = value
            case GhostBaseKey.oneTimeSave:
                updated.oneTimeSave = value
''',
    "case GhostBaseKey.oneTimeScreenshots",
    "settings one-time update cases"
) if "case GhostBaseKey.oneTimeScreenshots:" in settings else insert_after_line_contains(
    settings,
    "case GhostBaseKey.allowScreenRecording:",
    '''            case GhostBaseKey.oneTimeScreenshots:
                updated.oneTimeScreenshots = value
            case GhostBaseKey.oneTimeScreenRecording:
                updated.oneTimeScreenRecording = value
            case GhostBaseKey.oneTimeSave:
                updated.oneTimeSave = value
''',
    "settings one-time update cases"
)

# MARK: GhostBase v0.8G fix malformed one-time update cases
broken_update_cases = """            case GhostBaseKey.allowScreenRecording:
            case GhostBaseKey.oneTimeScreenshots:
                updated.oneTimeScreenshots = value
            case GhostBaseKey.oneTimeScreenRecording:
                updated.oneTimeScreenRecording = value
            case GhostBaseKey.oneTimeSave:
                updated.oneTimeSave = value
                updated.allowScreenRecording = value
            case GhostBaseKey.readMessages:"""

fixed_update_cases = """            case GhostBaseKey.allowScreenRecording:
                updated.allowScreenRecording = value
            case GhostBaseKey.oneTimeScreenshots:
                updated.oneTimeScreenshots = value
            case GhostBaseKey.oneTimeScreenRecording:
                updated.oneTimeScreenRecording = value
            case GhostBaseKey.oneTimeSave:
                updated.oneTimeSave = value
            case GhostBaseKey.readMessages:"""

if broken_update_cases in settings:
    settings = settings.replace(broken_update_cases, fixed_update_cases, 1)
elif "case GhostBaseKey.allowScreenRecording:\n            case GhostBaseKey.oneTimeScreenshots:" in settings:
    fail("settings malformed one-time update cases cleanup")


settings = replace_child_consistency(
    settings,
    '''            // MARK: GhostBase v0.8G protected child consistency
            if !updated.protectedGalleryShare && !updated.protectedGallerySave && !updated.protectedGalleryCopy && !updated.chatSave && !updated.chatCopy && !updated.chatForward && !updated.allowScreenshots && !updated.allowScreenRecording && !updated.oneTimeScreenshots && !updated.oneTimeScreenRecording && !updated.oneTimeSave {
                updated.protectedEnabled = false
            } else if updated.protectedGalleryShare || updated.protectedGallerySave || updated.protectedGalleryCopy || updated.chatSave || updated.chatCopy || updated.chatForward || updated.allowScreenshots || updated.allowScreenRecording || updated.oneTimeScreenshots || updated.oneTimeScreenRecording || updated.oneTimeSave {
                updated.protectedEnabled = true
            }''',
    "settings one-time child consistency"
)

open_view_once = replace_once(
    open_view_once,
    '''        if self.screenCaptureManager?.isRecordingActive == true {
            let controller = textAlertController(context: self.context, updatedPresentationData: self.updatedPresentationData, title: nil, text: self.presentationData.strings.Chat_PlayOnceMesasge_DisableScreenCapture, actions: [TextAlertAction(type: .defaultAction, title: self.presentationData.strings.Common_OK, action: {
            })])
            self.present(controller, in: .window(.root))
            return
        }''',
    f'''        // MARK: GhostBase v0.8G one-time screen recording gate
        let ghostBaseAllowOneTimeScreenRecording = {ALLOW_ONETIME_SCREEN_RECORDING_MESSAGE}
        if self.screenCaptureManager?.isRecordingActive == true && !ghostBaseAllowOneTimeScreenRecording {{
            let controller = textAlertController(context: self.context, updatedPresentationData: self.updatedPresentationData, title: nil, text: self.presentationData.strings.Chat_PlayOnceMesasge_DisableScreenCapture, actions: [TextAlertAction(type: .defaultAction, title: self.presentationData.strings.Common_OK, action: {{
            }})])
            self.present(controller, in: .window(.root))
            return
        }}''',
    "ChatControllerOpenViewOnceMediaMessage recording gate"
)

secret_preview = replace_once(
    secret_preview,
    '''                if let strongSelf = self, strongSelf.traceVisibility() {
                    if strongSelf.messageId.peerId.namespace == Namespaces.Peer.CloudUser {''',
    f'''                if let strongSelf = self, strongSelf.traceVisibility() {{
                    let ghostBaseAllowOneTimeScreenshots = {ALLOW_ONETIME_SCREENSHOTS_STRONGSELF}
                    if strongSelf.currentNodeMessageIsViewOnce && ghostBaseAllowOneTimeScreenshots {{
                        return
                    }}
                    if strongSelf.messageId.peerId.namespace == Namespaces.Peer.CloudUser {{''',
    "SecretMediaPreviewController screenshot event gate"
)

secret_preview = replace_once(
    secret_preview,
    '''                let entry = GalleryEntry(entry: MessageHistoryEntry(message: message, isRead: false, location: nil, monthLocation: nil, attributes: MutableMessageHistoryEntryAttributes(authorIsContact: false)))
                guard let item = galleryItemForEntry(context: self.context, presentationData: self.presentationData, entry: entry, streamVideos: false, hideControls: true, isSecret: true, playbackRate: { nil }, peerIsCopyProtected: true, tempFilePath: tempFilePath, playbackCompleted: { [weak self] in''',
    f'''                // MARK: GhostBase v0.8G one-time save gate
                let ghostBaseAllowOneTimeSave = {ALLOW_ONETIME_SAVE_MESSAGE}
                let entry = GalleryEntry(entry: MessageHistoryEntry(message: message, isRead: false, location: nil, monthLocation: nil, attributes: MutableMessageHistoryEntryAttributes(authorIsContact: false)))
                guard let item = galleryItemForEntry(context: self.context, presentationData: self.presentationData, entry: entry, streamVideos: false, hideControls: !ghostBaseAllowOneTimeSave, isSecret: !ghostBaseAllowOneTimeSave, playbackRate: {{ nil }}, peerIsCopyProtected: !ghostBaseAllowOneTimeSave, tempFilePath: tempFilePath, playbackCompleted: {{ [weak self] in''',
    "SecretMediaPreviewController one-time save gallery gate"
)

gallery = replace_all(
    gallery,
    f"let captureProtected = message.containsSecretMedia || message.minAutoremoveOrClearTimeout == viewOnceTimeout || message.paidContent != nil || (!{ALLOW_CAPTURE} && (message.isCopyProtected() || peerIsCopyProtected))",
    f"let captureProtected = (message.containsSecretMedia && message.minAutoremoveOrClearTimeout != viewOnceTimeout) || (message.minAutoremoveOrClearTimeout == viewOnceTimeout && !{ALLOW_ONETIME_CAPTURE_MESSAGE}) || message.paidContent != nil || (!{ALLOW_CAPTURE} && (message.isCopyProtected() || peerIsCopyProtected))",
    "GalleryController one-time captureProtected",
    min_count=2
)

instant_video = replace_once(
    instant_video,
    f"captureProtected: isViewOnceMessage || (!{ALLOW_CAPTURE} && (item.associatedData.isCopyProtectionEnabled || item.message.isCopyProtected())),",
    f"captureProtected: (isViewOnceMessage && !{ALLOW_ONETIME_CAPTURE_ITEM}) || (!{ALLOW_CAPTURE} && (item.associatedData.isCopyProtectionEnabled || item.message.isCopyProtected())),",
    "ChatMessageInteractiveInstantVideoNode one-time captureProtected"
)

settings_p.write_text(clean(settings))
open_view_once_p.write_text(clean(open_view_once))
secret_preview_p.write_text(clean(secret_preview))
gallery_p.write_text(clean(gallery))
instant_video_p.write_text(clean(instant_video))

settings = settings_p.read_text()
open_view_once = open_view_once_p.read_text()
secret_preview = secret_preview_p.read_text()
gallery = gallery_p.read_text()
instant_video = instant_video_p.read_text()

checks = [
    ("settings version", "Version: v0.8G" in settings),
    ("settings one-time keys", "GhostBase.ProtectedContent.OneTimeScreenshots" in settings and "GhostBase.ProtectedContent.OneTimeScreenRecording" in settings and "GhostBase.ProtectedContent.OneTimeSave" in settings),
    ("settings one-time entries", "Allow One-Time Screenshots" in settings and "Allow One-Time Screen Recording" in settings and "Allow One-Time Save" in settings),
    ("settings one-time cascade", "GhostBase v0.8G protected master cascade" in settings and "oneTimeSave" in settings),
    ("settings update cases well-formed", "case GhostBaseKey.allowScreenRecording:\n                updated.allowScreenRecording = value\n            case GhostBaseKey.oneTimeScreenshots:" in settings and "updated.oneTimeSave = value\n                updated.allowScreenRecording = value" not in settings),

    ("open guard marker", "GhostBase v0.8G one-time screen recording gate" in open_view_once),
    ("open guard keeps secret", "message.id.peerId.namespace != Namespaces.Peer.SecretChat" in open_view_once),

    ("secret screenshot marker", "GhostBase v0.8G one-time save gate" in secret_preview and "ghostBaseAllowOneTimeScreenshots" in secret_preview),
    ("secret save gate", "hideControls: !ghostBaseAllowOneTimeSave" in secret_preview and "peerIsCopyProtected: !ghostBaseAllowOneTimeSave" in secret_preview),

    ("gallery one-time capture", "message.minAutoremoveOrClearTimeout == viewOnceTimeout && !" in gallery),
    ("gallery keeps paid", "message.paidContent != nil" in gallery),

    ("instant one-time capture", "captureProtected: (isViewOnceMessage && !" in instant_video),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print(f"[{VERSION}] FAILED:")
    for name in bad:
        print("-", name)
    raise SystemExit(1)


# MARK: GhostBase v0.8G generated Swift syntax guard
def _paren_balance(text: str) -> int:
    balance = 0
    for ch in text:
        if ch == "(":
            balance += 1
        elif ch == ")":
            balance -= 1
    return balance

def _require_balanced_line(path, needle: str, label: str) -> None:
    text = path.read_text()
    for line in text.splitlines():
        if needle in line:
            balance = _paren_balance(line)
            if balance != 0:
                raise SystemExit(f"[{VERSION}] FAILED: unbalanced generated Swift line ({label}) in {path}: {line}")
            return
    raise SystemExit(f"[{VERSION}] FAILED: generated Swift line not found ({label}) in {path}")

def _require_balanced_capture_segment(path, label: str) -> None:
    text = path.read_text()
    for line in text.splitlines():
        if "captureProtected:" in line and "GhostBase.ProtectedContent.OneTimeScreenshots" in line:
            segment = line.split("captureProtected:", 1)[1]
            if ", storeAfterDownload" in segment:
                segment = segment.split(", storeAfterDownload", 1)[0]
            balance = _paren_balance(segment)
            if balance != 0:
                raise SystemExit(f"[{VERSION}] FAILED: unbalanced captureProtected segment ({label}) in {path}: {segment}")
            return
    raise SystemExit(f"[{VERSION}] FAILED: captureProtected segment not found ({label}) in {path}")

_require_balanced_line(secret_preview_p, "let ghostBaseAllowOneTimeSave =", "one-time save")
_require_balanced_line(open_view_once_p, "let ghostBaseAllowOneTimeScreenRecording =", "one-time screen recording")
_require_balanced_capture_segment(instant_video_p, "instant video one-time captureProtected")

settings_text = settings_p.read_text()
good_cases = """case GhostBaseKey.allowScreenRecording:
                updated.allowScreenRecording = value
            case GhostBaseKey.oneTimeScreenshots:
                updated.oneTimeScreenshots = value
            case GhostBaseKey.oneTimeScreenRecording:
                updated.oneTimeScreenRecording = value
            case GhostBaseKey.oneTimeSave:
                updated.oneTimeSave = value"""

bad_cases_1 = """case GhostBaseKey.allowScreenRecording:
            case GhostBaseKey.oneTimeScreenshots:"""

bad_cases_2 = """updated.oneTimeSave = value
                updated.allowScreenRecording = value"""

if good_cases not in settings_text:
    raise SystemExit(f"[{VERSION}] FAILED: good one-time update cases block not found")
if bad_cases_1 in settings_text or bad_cases_2 in settings_text:
    raise SystemExit(f"[{VERSION}] FAILED: malformed one-time update cases")


print("GhostBase One-Time Media v0.8G patch OK")
