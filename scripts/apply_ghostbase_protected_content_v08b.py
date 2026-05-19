from pathlib import Path
import runpy

VERSION = "v0.8B"

runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_scheduled_send_stabilizer_v07d.py")))

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/GalleryUI/Sources/Items/ChatImageGalleryItem.swift").exists():
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

BASE = find_base()

settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
footer_p = BASE / "submodules/GalleryUI/Sources/ChatItemGalleryFooterContentNode.swift"
video_p = BASE / "submodules/GalleryUI/Sources/Items/UniversalVideoGalleryItem.swift"
image_p = BASE / "submodules/GalleryUI/Sources/Items/ChatImageGalleryItem.swift"

settings = settings_p.read_text()
footer = footer_p.read_text()
video = video_p.read_text()
image = image_p.read_text()

settings = settings.replace("Version: v0.7D", "Version: v0.8B")
settings = settings.replace(
    "Scheduled Send is active in v0.7D.",
    "Scheduled Send is active in v0.7D. Protected Content Gallery Save/Share is active in v0.8B."
)

footer = replace_once(
    footer,
    '''        if message.isCopyProtected() || peerIsCopyProtected || message.paidContent != nil {
            canShare = false
            canEdit = false
        }
''',
    '''        if message.paidContent != nil {
            canShare = false
            canEdit = false
        } else if message.isCopyProtected() || peerIsCopyProtected {
            // MARK: GhostBase v0.8B Protected Content gallery save/share
            // Allow Share for copy-protected gallery media, but keep Edit disabled.
            canEdit = false
        }
''',
    "footer share gate"
)

if "let isSecret: Bool" not in video and "isSecret: Bool" not in video:
    fail("UniversalVideoGalleryItem isSecret field")

video = replace_once(
    video,
    "                if let (message, maybeFile, _) = strongSelf.contentInfo(), let file = maybeFile, !message.isCopyProtected() && !item.peerIsCopyProtected && message.paidContent == nil {\n",
    "                if let (message, maybeFile, _) = strongSelf.contentInfo(), let file = maybeFile, !item.isSecret && message.paidContent == nil {\n",
    "video save gate"
)

video = replace_once(
    video,
    "                if let (message, _, _) = strongSelf.contentInfo(), let image = message.media.first(where: { $0 is TelegramMediaImage }) as? TelegramMediaImage, !message.isCopyProtected() && !item.peerIsCopyProtected && message.paidContent == nil {\n",
    "                if let (message, _, _) = strongSelf.contentInfo(), let image = message.media.first(where: { $0 is TelegramMediaImage }) as? TelegramMediaImage, !item.isSecret && message.paidContent == nil {\n",
    "video item image save gate"
)

image = replace_once(
    image,
    "                if !message.isCopyProtected() && !self.peerIsCopyProtected && message.paidContent == nil, let media = self.contextAndMedia?.1 {\n",
    '''                if !self.isSecret && message.paidContent == nil, let media = self.contextAndMedia?.1 {
                    // MARK: GhostBase v0.8B Protected Content image save/copy
                    // Save/Copy are allowed for copy-protected gallery images; Create Sticker keeps original gate.
                    if !message.isCopyProtected() && !self.peerIsCopyProtected {
''',
    "image save/copy outer gate"
)

image = replace_after(
    image,
    "GhostBase v0.8B Protected Content image save/copy",
    '''                    })))
                    
                    items.append(.action(ContextMenuActionItem(text: self.presentationData.strings.Gallery_SaveImage,''',
    '''                    })))
                    }
                    
                    items.append(.action(ContextMenuActionItem(text: self.presentationData.strings.Gallery_SaveImage,''',
    "image create sticker close gate"
)

settings_p.write_text(clean(settings))
footer_p.write_text(clean(footer))
video_p.write_text(clean(video))
image_p.write_text(clean(image))

settings = settings_p.read_text()
footer = footer_p.read_text()
video = video_p.read_text()
image = image_p.read_text()

checks = [
    ("settings v08b", "Version: v0.8B" in settings),
    ("settings note", "Protected Content Gallery Save/Share is active in v0.8B" in settings),
    ("footer marker", "GhostBase v0.8B Protected Content gallery save/share" in footer),
    ("footer paid still blocks", "if message.paidContent != nil" in footer),
    ("video save gate", "let file = maybeFile, !item.isSecret && message.paidContent == nil" in video),
    ("video image save gate", "as? TelegramMediaImage, !item.isSecret && message.paidContent == nil" in video),
    ("image marker", "GhostBase v0.8B Protected Content image save/copy" in image),
    ("image secret still blocks", "if !self.isSecret && message.paidContent == nil, let media" in image),
    ("image sticker still gated", "if !message.isCopyProtected() && !self.peerIsCopyProtected" in image),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print(f"[{VERSION}] FAILED:")
    for name in bad:
        print("-", name)
    raise SystemExit(1)

print("GhostBase Protected Content Gallery Save/Share v0.8B patch OK")
