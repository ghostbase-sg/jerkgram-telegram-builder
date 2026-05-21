from pathlib import Path
import runpy

VERSION = "v0.8I"

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

BASE = find_base()

prev = Path(__file__).with_name("apply_ghostbase_safe_login_polish_v08h1.py")
if not prev.exists():
    raise SystemExit(f"[{VERSION}] ERROR: missing prerequisite {prev}")

settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
ctx_p = BASE / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"
img_p = BASE / "submodules/GalleryUI/Sources/Items/ChatImageGalleryItem.swift"
vid_p = BASE / "submodules/GalleryUI/Sources/Items/UniversalVideoGalleryItem.swift"

settings_existing = settings_p.read_text(errors="ignore") if settings_p.exists() else ""
if "Version: v0.8I" in settings_existing:
    print(f"[{VERSION}] v0.8I already applied; skip prerequisite replay")
elif "Version: v0.8H.1" in settings_existing:
    print(f"[{VERSION}] v0.8H.1 chain already applied; skip prerequisite replay")
else:
    runpy.run_path(str(prev))

settings = settings_p.read_text()
ctx = ctx_p.read_text()
img = img_p.read_text()
vid = vid_p.read_text()

# MARK: GhostBase v0.8I version
settings = settings.replace("Version: v0.8H.1", "Version: v0.8I")

# MARK: GhostBase v0.8I long press save for one-view/timed media
ctx = replace_once(
    ctx,
    '''        // MARK: GhostBase v0.8D chat save action gate
        let ghostBaseProtectedChatSave = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.ChatSave") as? Bool) ?? true))
        if resourceAvailable, !message.containsSecretMedia && (!isCopyProtected || ghostBaseProtectedChatSave) {''',
    '''        // MARK: GhostBase v0.8D chat save action gate
        let ghostBaseProtectedChatSave = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.ChatSave") as? Bool) ?? true))

        // MARK: GhostBase v0.8I one-time/timed media long-press save gate
        let ghostBaseTimedMediaSave = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat && message.paidContent == nil && message.minAutoremoveOrClearTimeout != nil)

        if resourceAvailable, (!message.containsSecretMedia || ghostBaseTimedMediaSave) && (!isCopyProtected || ghostBaseProtectedChatSave || ghostBaseTimedMediaSave) {''',
    "one-time/timed long press save gate"
)

# Do not write files yet. Later blocks add preview save and final checks.

# MARK: GhostBase v0.8I image preview save for one-view/timed media
img = replace_once(
    img,
    '''                let ghostBaseProtectedEnabled = ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true)
                let ghostBaseProtectedSave = ghostBaseProtectedEnabled && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.GallerySave") as? Bool) ?? true)
                let ghostBaseProtectedCopy = ghostBaseProtectedEnabled && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.GalleryCopy") as? Bool) ?? true)
                let ghostBaseProtectedOriginalAllowed = !message.isCopyProtected() && !self.peerIsCopyProtected

                if !self.isSecret && message.paidContent == nil, let media = self.contextAndMedia?.1, (ghostBaseProtectedSave || ghostBaseProtectedCopy || ghostBaseProtectedOriginalAllowed) {''',
    '''                let ghostBaseProtectedEnabled = ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true)
                let ghostBaseProtectedSave = ghostBaseProtectedEnabled && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.GallerySave") as? Bool) ?? true)
                let ghostBaseProtectedCopy = ghostBaseProtectedEnabled && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.GalleryCopy") as? Bool) ?? true)
                let ghostBaseProtectedOriginalAllowed = !message.isCopyProtected() && !self.peerIsCopyProtected

                // MARK: GhostBase v0.8I one-time/timed image preview save gate
                let ghostBaseTimedImageSave = ghostBaseProtectedEnabled && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat && message.paidContent == nil && message.minAutoremoveOrClearTimeout != nil

                if (!self.isSecret || ghostBaseTimedImageSave) && message.paidContent == nil, let media = self.contextAndMedia?.1, (ghostBaseProtectedSave || ghostBaseProtectedCopy || ghostBaseProtectedOriginalAllowed || ghostBaseTimedImageSave) {''',
    "image preview timed save gate"
)

img = replace_once(
    img,
    '''                    if ghostBaseProtectedSave || ghostBaseProtectedOriginalAllowed {''',
    '''                    if ghostBaseProtectedSave || ghostBaseProtectedOriginalAllowed || ghostBaseTimedImageSave {''',
    "image preview save action condition"
)

# MARK: GhostBase v0.8I video preview save for one-view/timed media

def ghostbase_close_nested_video_save_if(text: str, var_name: str, label: str, stop_marker: str) -> str:
    pos = text.find(var_name)
    if pos < 0:
        fail(label + " var")

    end = text.find(stop_marker, pos)
    if end < 0:
        end = len(text)

    already = '''                    })))
                    }
                }'''
    target = '''                    })))
                }'''

    segment = text[pos:end]
    if already in segment:
        print(f"[{VERSION}] already patched: {label} flexible close brace")
        return text

    idx = text.find(target, pos, end)
    if idx < 0:
        fail(label + " flexible close brace")

    print(f"[{VERSION}] patch {label} flexible close brace")
    return text[:idx] + already + text[idx + len(target):]

vid = replace_once(
    vid,
    '''                let ghostBaseProtectedVideoSave = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.GallerySave") as? Bool) ?? true))
                if let (message, maybeFile, _) = strongSelf.contentInfo(), let file = maybeFile, !item.isSecret && message.paidContent == nil && (ghostBaseProtectedVideoSave || (!message.isCopyProtected() && !item.peerIsCopyProtected)) {''',
    '''                let ghostBaseProtectedVideoSave = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.GallerySave") as? Bool) ?? true))
                // MARK: GhostBase v0.8I one-time/timed video preview save gate
                if let (message, maybeFile, _) = strongSelf.contentInfo(), let file = maybeFile {
                    let ghostBaseTimedVideoSave = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat && message.paidContent == nil && message.minAutoremoveOrClearTimeout != nil)
                    if (!item.isSecret || ghostBaseTimedVideoSave) && message.paidContent == nil && (ghostBaseProtectedVideoSave || (!message.isCopyProtected() && !item.peerIsCopyProtected) || ghostBaseTimedVideoSave) {''',
    "video preview timed save gate"
)

vid = ghostbase_close_nested_video_save_if(
    vid,
    "ghostBaseTimedVideoSave",
    "video preview timed save",
    "\n\n                let ghostBaseProtectedVideoImageSave"
)

vid = replace_once(
    vid,
    '''                let ghostBaseProtectedVideoImageSave = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.GallerySave") as? Bool) ?? true))
                if let (message, _, _) = strongSelf.contentInfo(), let image = message.media.first(where: { $0 is TelegramMediaImage }) as? TelegramMediaImage, !item.isSecret && message.paidContent == nil && (ghostBaseProtectedVideoImageSave || (!message.isCopyProtected() && !item.peerIsCopyProtected)) {''',
    '''                let ghostBaseProtectedVideoImageSave = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.GallerySave") as? Bool) ?? true))
                if let (message, _, _) = strongSelf.contentInfo(), let image = message.media.first(where: { $0 is TelegramMediaImage }) as? TelegramMediaImage {
                    let ghostBaseTimedVideoImageSave = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat && message.paidContent == nil && message.minAutoremoveOrClearTimeout != nil)
                    if (!item.isSecret || ghostBaseTimedVideoImageSave) && message.paidContent == nil && (ghostBaseProtectedVideoImageSave || (!message.isCopyProtected() && !item.peerIsCopyProtected) || ghostBaseTimedVideoImageSave) {''',
    "video image preview timed save gate"
)

vid = ghostbase_close_nested_video_save_if(
    vid,
    "ghostBaseTimedVideoImageSave",
    "video image preview timed save",
    "\n\n                // MARK:"
)

# MARK: GhostBase v0.8I final write/check
settings_p.write_text(clean(settings))
ctx_p.write_text(clean(ctx))
img_p.write_text(clean(img))
vid_p.write_text(clean(vid))

settings = settings_p.read_text()
ctx = ctx_p.read_text()
img = img_p.read_text()
vid = vid_p.read_text()

checks = [
    ("version", "Version: v0.8I" in settings and "Version: v0.8H.1" not in settings),
    ("no unsupported stars dismiss arg", "dismissKeyboardOnEnter" not in settings),
    ("long press timed save", "GhostBase v0.8I one-time/timed media long-press save gate" in ctx and "ghostBaseTimedMediaSave" in ctx),
    ("image preview timed save", "GhostBase v0.8I one-time/timed image preview save gate" in img and "ghostBaseTimedImageSave" in img),
    ("video preview timed save", "GhostBase v0.8I one-time/timed video preview save gate" in vid and "ghostBaseTimedVideoSave" in vid),
    ("video image preview timed save", "ghostBaseTimedVideoImageSave" in vid),
]

for generated_text, generated_label in [
    (ctx, "context menu"),
    (img, "image preview"),
    (vid, "video preview"),
]:
    for line in generated_text.splitlines():
        if "ghostBaseTimedMediaSave =" in line or "ghostBaseTimedImageSave =" in line or "ghostBaseTimedVideoSave =" in line or "ghostBaseTimedVideoImageSave =" in line:
            balance = line.count("(") - line.count(")")
            if balance != 0:
                raise SystemExit(f"[{VERSION}] FAILED: unbalanced generated Swift line in {generated_label}: {line}")

bad = [name for name, ok in checks if not ok]
if bad:
    print(f"[{VERSION}] FAILED:")
    for name in bad:
        print("-", name)
    raise SystemExit(1)

print("GhostBase One-Time Timed Save v0.8I patch OK")
