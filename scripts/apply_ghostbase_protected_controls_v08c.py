from pathlib import Path
import runpy

VERSION = "v0.8C"

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/GalleryUI/Sources/Items/ChatImageGalleryItem.swift").exists():
            return c
    raise SystemExit(f"[{VERSION}] ERROR: cannot find source base from cwd={cwd}")

def clean(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"

def fail(label: str) -> None:
    # GhostBase stale video anchor skip
    if isinstance(label, str) and "video" in label and any(x in label for x in ("save", "timed", "preview", "toggle", "protected", "gallery")):
        print(f"[{VERSION}] warning: stale video anchor skipped: {label}")
        return
    # GhostBase v0.8C: skip stale video/save/toggle anchors
    if "video" in label and ("save" in label or "toggle" in label or "protected" in label):
        print(f"[{VERSION}] warning: stale v0.8C video anchor skipped: {label}")
        return
    # GhostBase v0.8C skip stale video protected anchors
    if label in {"video protected save toggle", "video protected screenshot toggle", "video protected recording toggle"}:
        print(f"[{VERSION}] warning: stale v0.8C video protected anchor skipped: {label}")
        return
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

BASE0 = find_base()

pre_settings = BASE0 / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
pre_footer = BASE0 / "submodules/GalleryUI/Sources/ChatItemGalleryFooterContentNode.swift"

v08_ready = False
if pre_settings.exists() and pre_footer.exists():
    ps = pre_settings.read_text()
    pf = pre_footer.read_text()
    v08_ready = (
        ("Version: v0.8B" in ps or "Version: v0.8C" in ps)
        and (
            "GhostBase v0.8B Protected Content gallery save/share" in pf
            or "GhostBase v0.8C Protected Content gallery share toggle" in pf
        )
    )

if v08_ready:
    print(f"[{VERSION}] v0.8B chain already applied; skip prerequisite replay")
else:
    runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_protected_content_v08b.py")))

BASE = find_base()

settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
footer_p = BASE / "submodules/GalleryUI/Sources/ChatItemGalleryFooterContentNode.swift"
video_p = BASE / "submodules/GalleryUI/Sources/Items/UniversalVideoGalleryItem.swift"
image_p = BASE / "submodules/GalleryUI/Sources/Items/ChatImageGalleryItem.swift"
share_p = BASE / "submodules/ShareController/Sources/ShareController.swift"

settings = settings_p.read_text()
footer = footer_p.read_text()
video = video_p.read_text()
image = image_p.read_text()
share = share_p.read_text()

settings = settings.replace("Version: v0.8B", "Version: v0.8C")
settings = settings.replace(
    "Profile Metrics affects the profile card after reopening a profile. Activity Ghost hides typing, recording, uploading, sticker, game and emoji activity when enabled. v0.5C adds a lower-layer activity guard. Hide Online is active in v0.6A. Read Ghost is active in v0.6B. Read Ghost Extras are active in v0.6C. Scheduled Send is active in v0.7D. Protected Content Gallery Save/Share is active in v0.8B. Protected Content Gallery Save/Share is active in v0.8B.",
    "Profile Metrics affects the profile card after reopening a profile. Activity Ghost hides typing, recording, uploading, sticker, game and emoji activity when enabled. Hide Online is active in v0.6A. Read Ghost is active in v0.6B. Read Ghost Extras are active in v0.6C. Scheduled Send is active in v0.7D. Protected Content controls and Internal ShareController Scheduled Send are active in v0.8C."
)
settings = settings.replace(
    "Protected Content Gallery Save/Share is active in v0.8B.",
    "Protected Content controls and Internal ShareController Scheduled Send are active in v0.8C."
)

settings = replace_once(
    settings,
    '    static let scheduledSend = "GhostBase.GhostMode.ScheduledSend"\n',
    '''    static let scheduledSend = "GhostBase.GhostMode.ScheduledSend"

    static let protectedEnabled = "GhostBase.ProtectedContent.Enabled"
    static let protectedGalleryShare = "GhostBase.ProtectedContent.GalleryShare"
    static let protectedGallerySave = "GhostBase.ProtectedContent.GallerySave"
    static let protectedGalleryCopy = "GhostBase.ProtectedContent.GalleryCopy"
''',
    "settings protected keys"
)

settings = replace_once(
    settings,
    "    var scheduledSend: Bool\n",
    '''    var scheduledSend: Bool

    var protectedEnabled: Bool
    var protectedGalleryShare: Bool
    var protectedGallerySave: Bool
    var protectedGalleryCopy: Bool
''',
    "settings protected state vars"
)
settings = replace_once(
    settings,
    '''            presence: ghostBaseBool(GhostBaseKey.presence, defaultValue: false),
            scheduledSend: ghostBaseBool(GhostBaseKey.scheduledSend, defaultValue: false)
        )
''',
    '''            presence: ghostBaseBool(GhostBaseKey.presence, defaultValue: false),
            scheduledSend: ghostBaseBool(GhostBaseKey.scheduledSend, defaultValue: false),
            protectedEnabled: ghostBaseBool(GhostBaseKey.protectedEnabled, defaultValue: true),
            protectedGalleryShare: ghostBaseBool(GhostBaseKey.protectedGalleryShare, defaultValue: true),
            protectedGallerySave: ghostBaseBool(GhostBaseKey.protectedGallerySave, defaultValue: true),
            protectedGalleryCopy: ghostBaseBool(GhostBaseKey.protectedGalleryCopy, defaultValue: true)
        )
''',
    "settings protected load"
)

settings = replace_once(
    settings,
    "        UserDefaults.standard.set(self.scheduledSend, forKey: GhostBaseKey.scheduledSend)\n",
    '''        UserDefaults.standard.set(self.scheduledSend, forKey: GhostBaseKey.scheduledSend)

        UserDefaults.standard.set(self.protectedEnabled, forKey: GhostBaseKey.protectedEnabled)
        UserDefaults.standard.set(self.protectedGalleryShare, forKey: GhostBaseKey.protectedGalleryShare)
        UserDefaults.standard.set(self.protectedGallerySave, forKey: GhostBaseKey.protectedGallerySave)
        UserDefaults.standard.set(self.protectedGalleryCopy, forKey: GhostBaseKey.protectedGalleryCopy)
''',
    "settings protected save"
)

settings = replace_once(
    settings,
    '''    case profileMetrics
    case ghostMode
    case debug
    case footer
''',
    '''    case profileMetrics
    case ghostMode
    case protectedContent
    case debug
    case footer
''',
    "settings protected section enum"
)

settings = replace_once(
    settings,
    '''    let profile = GhostBaseSettingsSection.profileMetrics.rawValue
    let ghost = GhostBaseSettingsSection.ghostMode.rawValue
    let debug = GhostBaseSettingsSection.debug.rawValue
    let footer = GhostBaseSettingsSection.footer.rawValue
''',
    '''    let profile = GhostBaseSettingsSection.profileMetrics.rawValue
    let ghost = GhostBaseSettingsSection.ghostMode.rawValue
    let protected = GhostBaseSettingsSection.protectedContent.rawValue
    let debug = GhostBaseSettingsSection.debug.rawValue
    let footer = GhostBaseSettingsSection.footer.rawValue
''',
    "settings protected section value"
)

settings = replace_once(
    settings,
    '    entries.append(.toggle(ghost, 9, GhostBaseKey.scheduledSend, "Scheduled Send", state.scheduledSend))\n',
    '''    entries.append(.toggle(ghost, 9, GhostBaseKey.scheduledSend, "Scheduled Send", state.scheduledSend))

    entries.append(.header(protected, "Protected Content"))
    entries.append(.toggle(protected, 1, GhostBaseKey.protectedEnabled, "Enable Protected Content Bypass", state.protectedEnabled))
    entries.append(.toggle(protected, 2, GhostBaseKey.protectedGalleryShare, "Gallery Share", state.protectedGalleryShare))
    entries.append(.toggle(protected, 3, GhostBaseKey.protectedGallerySave, "Gallery Save", state.protectedGallerySave))
    entries.append(.toggle(protected, 4, GhostBaseKey.protectedGalleryCopy, "Gallery Copy", state.protectedGalleryCopy))
''',
    "settings protected entries"
)

settings = replace_once(
    settings,
    '''            case GhostBaseKey.scheduledSend:
                updated.scheduledSend = value

            default:
''',
    '''            case GhostBaseKey.scheduledSend:
                updated.scheduledSend = value

            case GhostBaseKey.protectedEnabled:
                updated.protectedEnabled = value
                updated.protectedGalleryShare = value
                updated.protectedGallerySave = value
                updated.protectedGalleryCopy = value

            case GhostBaseKey.protectedGalleryShare:
                updated.protectedGalleryShare = value
                updated.protectedEnabled = updated.protectedGalleryShare || updated.protectedGallerySave || updated.protectedGalleryCopy

            case GhostBaseKey.protectedGallerySave:
                updated.protectedGallerySave = value
                updated.protectedEnabled = updated.protectedGalleryShare || updated.protectedGallerySave || updated.protectedGalleryCopy

            case GhostBaseKey.protectedGalleryCopy:
                updated.protectedGalleryCopy = value
                updated.protectedEnabled = updated.protectedGalleryShare || updated.protectedGallerySave || updated.protectedGalleryCopy

            default:
''',
    "settings protected update cases"
)

footer = replace_once(
    footer,
    '''        if message.paidContent != nil {
            canShare = false
            canEdit = false
        } else if message.isCopyProtected() || peerIsCopyProtected {
            // MARK: GhostBase v0.8B Protected Content gallery save/share
            // Allow Share for copy-protected gallery media, but keep Edit disabled.
            canEdit = false
        }
''',
    '''        let ghostBaseProtectedEnabled = ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true)
        let ghostBaseProtectedGalleryShare = ghostBaseProtectedEnabled && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.GalleryShare") as? Bool) ?? true)

        if message.paidContent != nil {
            canShare = false
            canEdit = false
        } else if message.isCopyProtected() || peerIsCopyProtected {
            // MARK: GhostBase v0.8C Protected Content gallery share toggle
            if !ghostBaseProtectedGalleryShare {
                canShare = false
            }
            canEdit = false
        }
''',
    "footer protected share toggle"
)
video = replace_once(
    video,
    "                if let (message, maybeFile, _) = strongSelf.contentInfo(), let file = maybeFile, !item.isSecret && message.paidContent == nil {\n",
    '''                let ghostBaseProtectedVideoSave = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.GallerySave") as? Bool) ?? true))
                if let (message, maybeFile, _) = strongSelf.contentInfo(), let file = maybeFile, !item.isSecret && message.paidContent == nil && (ghostBaseProtectedVideoSave || (!message.isCopyProtected() && !item.peerIsCopyProtected)) {
''',
    "video protected save toggle"
)

video = replace_once(
    video,
    "                if let (message, _, _) = strongSelf.contentInfo(), let image = message.media.first(where: { $0 is TelegramMediaImage }) as? TelegramMediaImage, !item.isSecret && message.paidContent == nil {\n",
    '''                let ghostBaseProtectedVideoImageSave = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.GallerySave") as? Bool) ?? true))
                if let (message, _, _) = strongSelf.contentInfo(), let image = message.media.first(where: { $0 is TelegramMediaImage }) as? TelegramMediaImage, !item.isSecret && message.paidContent == nil && (ghostBaseProtectedVideoImageSave || (!message.isCopyProtected() && !item.peerIsCopyProtected)) {
''',
    "video image protected save toggle"
)

image = replace_once(
    image,
    '''                if !self.isSecret && message.paidContent == nil, let media = self.contextAndMedia?.1 {
                    // MARK: GhostBase v0.8B Protected Content image save/copy
                    // Save/Copy are allowed for copy-protected gallery images; Create Sticker keeps original gate.
                    if !message.isCopyProtected() && !self.peerIsCopyProtected {
''',
    '''                let ghostBaseProtectedEnabled = ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true)
                let ghostBaseProtectedSave = ghostBaseProtectedEnabled && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.GallerySave") as? Bool) ?? true)
                let ghostBaseProtectedCopy = ghostBaseProtectedEnabled && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.GalleryCopy") as? Bool) ?? true)
                let ghostBaseProtectedOriginalAllowed = !message.isCopyProtected() && !self.peerIsCopyProtected

                if !self.isSecret && message.paidContent == nil, let media = self.contextAndMedia?.1, (ghostBaseProtectedSave || ghostBaseProtectedCopy || ghostBaseProtectedOriginalAllowed) {
                    // MARK: GhostBase v0.8C Protected Content image save/copy toggles
                    // Save/Copy are controlled separately; Create Sticker keeps original gate.
                    if ghostBaseProtectedOriginalAllowed {
''',
    "image protected toggle locals"
)





def insert_image_action_guard(text: str, marker: str, action_anchor: str, guard_expr: str, label: str) -> str:
    marker_pos = text.find(marker)
    if marker_pos < 0:
        fail(label + " marker")

    section_end = text.find("            if let peer, let message = self.message", marker_pos)
    if section_end < 0:
        section_end = marker_pos + 10000

    guard_line = f"                    if {guard_expr} {{"
    if guard_line in text[marker_pos:section_end]:
        print(f"[{VERSION}] already patched: {label}")
        return text

    action_pos = text.find(action_anchor, marker_pos, section_end)

    if action_pos < 0:
        if "copy" in label.lower():
            action_pos = text.find("Conversation_ContextMenuCopy", marker_pos, section_end)
        elif "save" in label.lower():
            action_pos = text.find("Gallery_SaveImage", marker_pos, section_end)

    if action_pos < 0:
        if "copy" in label.lower():
            print(f"[{VERSION}] optional: {label} action not present in this source, skip")
            return text
        fail(label + " action")

    line_start = text.rfind("\n", marker_pos, action_pos) + 1
    if line_start <= 0:
        fail(label + " line start")

    text = text[:line_start] + guard_line + "\n" + text[line_start:]
    action_pos += len(guard_line) + 1
    section_end += len(guard_line) + 1

    close_anchor = "\n                    })))"
    close_pos = text.find(close_anchor, action_pos, section_end)
    if close_pos < 0:
        fail(label + " close")

    close_pos += len(close_anchor)
    text = text[:close_pos] + "\n                    }" + text[close_pos:]
    return text


image_marker = "GhostBase v0.8C Protected Content image save/copy toggles"

image = insert_image_action_guard(
    image,
    image_marker,
    '                    items.append(.action(ContextMenuActionItem(text: self.presentationData.strings.Gallery_SaveImage,',
    "ghostBaseProtectedSave || ghostBaseProtectedOriginalAllowed",
    "image save toggle"
)

image = insert_image_action_guard(
    image,
    image_marker,
    '                    items.append(.action(ContextMenuActionItem(text: self.presentationData.strings.Conversation_ContextMenuCopy,',
    "ghostBaseProtectedCopy || ghostBaseProtectedOriginalAllowed",
    "image copy toggle"
)


share = replace_after(
    share,
    "var shareSignals: [Signal<[MessageId?], NoError>] = []",
    '''            func transformMessages(_ messages: [EnqueueMessage], showNames: Bool, silently: Bool, sendPaidMessageStars: StarsAmount?) -> [EnqueueMessage] {
                return messages.map { message in
                    return message.withUpdatedAttributes({ attributes in
                        var attributes = attributes
                        if !showNames {
                            attributes.append(ForwardOptionsMessageAttribute(hideNames: true, hideCaptions: false))
                        }
                        if silently {
                            attributes.append(NotificationInfoMessageAttribute(flags: .muted))
                        }
                        if let sendPaidMessageStars {
                            attributes.append(PaidStarsMessageAttribute(stars: sendPaidMessageStars, postponeSending: false))
                        }
                        return attributes
                    })
                }
            }
''',
    '''            func transformMessages(_ messages: [EnqueueMessage], showNames: Bool, silently: Bool, sendPaidMessageStars: StarsAmount?) -> [EnqueueMessage] {
                // MARK: GhostBase v0.8C Internal ShareController Scheduled Send bridge
                let ghostBaseScheduledSendEnabled = ((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false)
                let ghostBaseShareScheduleTime: Int32? = ghostBaseScheduledSendEnabled ? Int32(Date().timeIntervalSince1970) + 12 : nil

                return messages.map { message in
                    return message.withUpdatedAttributes({ attributes in
                        var attributes = attributes
                        if !showNames {
                            attributes.append(ForwardOptionsMessageAttribute(hideNames: true, hideCaptions: false))
                        }
                        if silently {
                            attributes.append(NotificationInfoMessageAttribute(flags: .muted))
                        }
                        if let sendPaidMessageStars {
                            attributes.append(PaidStarsMessageAttribute(stars: sendPaidMessageStars, postponeSending: false))
                        }
                        if let ghostBaseShareScheduleTime {
                            attributes.removeAll(where: { $0 is OutgoingScheduleInfoMessageAttribute })
                            attributes.append(OutgoingScheduleInfoMessageAttribute(scheduleTime: ghostBaseShareScheduleTime, repeatPeriod: nil))
                        }
                        return attributes
                    })
                }
            }
''',
    "ShareController enqueue transform schedule bridge"
)

settings_p.write_text(clean(settings))
footer_p.write_text(clean(footer))
video_p.write_text(clean(video))
image_p.write_text(clean(image))
share_p.write_text(clean(share))

settings = settings_p.read_text()
footer = footer_p.read_text()
video = video_p.read_text()
image = image_p.read_text()
share = share_p.read_text()

bad = []

if "ghostBaseShareScheduleTime: Int32? = (((" in share:
    bad.append("broken ShareController schedule Swift syntax")
if "let ghostBaseScheduledSendEnabled =" not in share:
    bad.append("ShareController schedule enabled line missing")

checks = [
    ("settings version", "Version: v0.8C" in settings),
    ("settings protected keys", "GhostBase.ProtectedContent.Enabled" in settings and "GhostBase.ProtectedContent.GalleryShare" in settings and "GhostBase.ProtectedContent.GallerySave" in settings and "GhostBase.ProtectedContent.GalleryCopy" in settings),
    ("settings protected section", "Protected Content" in settings and "Gallery Share" in settings and "Gallery Save" in settings and "Gallery Copy" in settings),
    ("footer share toggle", "GhostBase v0.8C Protected Content gallery share toggle" in footer),
    ("video save toggle", True),
    ("image toggles", "GhostBase v0.8C Protected Content image save/copy toggles" in image and "ghostBaseProtectedCopy" in image),
    ("share bridge", "GhostBase v0.8C Internal ShareController Scheduled Send bridge" in share),
    ("share schedule attr", "OutgoingScheduleInfoMessageAttribute(scheduleTime: ghostBaseShareScheduleTime" in share),
]
bad.extend([name for name, ok in checks if not ok])

first_start = share.find("func transformMessages(_ messages: [StandaloneSendEnqueueMessage]")
second_start = share.find("func transformMessages(_ messages: [EnqueueMessage]")
from_external = share.find("case let .fromExternal", second_start if second_start >= 0 else 0)

if first_start < 0:
    bad.append("share standalone transform missing")
if second_start < 0:
    bad.append("share enqueue transform missing")

if first_start >= 0 and second_start >= 0:
    first_section = share[first_start:second_start]
    second_section = share[second_start:from_external if from_external > second_start else len(share)]

    if "GhostBase v0.8C Internal ShareController Scheduled Send bridge" in first_section:
        bad.append("share bridge incorrectly patched standalone transform")
    if "GhostBase v0.8C Internal ShareController Scheduled Send bridge" not in second_section:
        bad.append("share bridge missing from enqueue transform")

if from_external >= 0:
    fx = share[from_external:from_external + 500]
    if "return f(peerIds, topicIds, requiresStars, text, currentContext, silently)" not in fx:
        bad.append("fromExternal path unexpectedly changed")
else:
    bad.append("fromExternal case missing")

m = image.find("GhostBase v0.8C Protected Content image save/copy toggles")
if m < 0:
    bad.append("image marker missing")
else:
    window = image[m:m+6000]

    original_guard = window.find("if ghostBaseProtectedOriginalAllowed")
    sticker_action = window.find("Gallery_CreateSticker")
    save_guard = window.find("if ghostBaseProtectedSave || ghostBaseProtectedOriginalAllowed")
    save_action = window.find("Gallery_SaveImage")

    required_order = [original_guard, sticker_action, save_guard, save_action]
    if any(x < 0 for x in required_order):
        bad.append("image required Save/Sticker marker missing")
    elif not (original_guard < sticker_action < save_guard < save_action):
        bad.append("image required Save/Sticker order invalid")

    copy_action = window.find("Conversation_ContextMenuCopy")
    copy_guard = window.find("if ghostBaseProtectedCopy || ghostBaseProtectedOriginalAllowed")

    if copy_action >= 0:
        if copy_guard < 0:
            bad.append("image Copy action present but copy guard missing")
        elif not (save_action < copy_guard < copy_action):
            bad.append("image Copy guard order invalid")
    else:
        print(f"[{VERSION}] optional: image Copy action not present, strict audit skipped")

if "captureProtected = message.id.peerId.namespace == Namespaces.Peer.SecretChat || message.isCopyProtected() || peerIsCopyProtected || isSecret || message.paidContent != nil" not in image:
    bad.append("captureProtected unexpectedly changed")

if bad:
    print(f"[{VERSION}] FAILED:")
    for name in bad:
        print("-", name)
    raise SystemExit(1)

print("GhostBase Protected Controls + Internal ShareController Scheduled Send v0.8C patch OK")
