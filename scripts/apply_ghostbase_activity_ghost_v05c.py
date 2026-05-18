from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_activity_ghost_v05b.py")))

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramCore/Sources/State/ManagedLocalInputActivities.swift").exists():
            return c
    raise SystemExit(f"cannot find source base from cwd={cwd}")

BASE = find_base()

managed_p = BASE / "submodules/TelegramCore/Sources/State/ManagedLocalInputActivities.swift"
controller_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

managed = managed_p.read_text()
controller = controller_p.read_text()

controller = controller.replace("Version: v0.5B", "Version: v0.5C")
controller = controller.replace(
    "Activity Ghost hides typing, recording, uploading, sticker, game and emoji activity when enabled.",
    "Activity Ghost hides typing, recording, uploading, sticker, game and emoji activity when enabled. v0.5C adds a lower-layer activity guard."
)

controller_p.write_text(controller)
print("patched", controller_p)

marker = "private func requestActivity(postbox: Postbox, network: Network, accountPeerId: PeerId, peerId: PeerId, threadId: Int64?, activity: PeerInputActivity?) -> Signal<Void, NoError> {\n"

guard_block = '''    // MARK: GhostBase v0.5C Activity Ghost lower-layer guard
    if let activity = activity {
        let ghostBaseHideTyping = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.TypingActions") as? Bool) ?? false
        let ghostBaseHideRecording = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.HideRecording") as? Bool) ?? false
        let ghostBaseHideUploading = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.HideUploading") as? Bool) ?? false
        let ghostBaseHideStickerActivity = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.HideStickerActivity") as? Bool) ?? false
        let ghostBaseHideGameActivity = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.HideGameActivity") as? Bool) ?? false
        let ghostBaseHideEmojiActivity = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.HideEmojiActivity") as? Bool) ?? false

        let ghostBaseSuppressActivity: Bool
        switch activity {
        case .typingText:
            ghostBaseSuppressActivity = ghostBaseHideTyping
        case .recordingVoice, .recordingInstantVideo:
            ghostBaseSuppressActivity = ghostBaseHideRecording
        case .uploadingFile(_), .uploadingPhoto(_), .uploadingVideo(_), .uploadingInstantVideo(_):
            ghostBaseSuppressActivity = ghostBaseHideUploading
        case .choosingSticker:
            ghostBaseSuppressActivity = ghostBaseHideStickerActivity
        case .playingGame:
            ghostBaseSuppressActivity = ghostBaseHideGameActivity
        case .interactingWithEmoji(_, _, _), .seeingEmojiInteraction(_):
            ghostBaseSuppressActivity = ghostBaseHideEmojiActivity
        default:
            ghostBaseSuppressActivity = false
        }

        if ghostBaseSuppressActivity {
            return .complete()
        }
    }

'''

if marker not in managed:
    raise SystemExit("requestActivity function marker not found")

if "GhostBase v0.5C Activity Ghost lower-layer guard" not in managed:
    managed = managed.replace(marker, marker + guard_block, 1)

managed_p.write_text(managed)
print("patched", managed_p)

managed = managed_p.read_text()
controller = controller_p.read_text()

checks = [
    ("version", "Version: v0.5C" in controller),
    ("note", "lower-layer activity guard" in controller),
    ("guard", "GhostBase v0.5C Activity Ghost lower-layer guard" in managed),
    ("complete", "return .complete()" in managed),
    ("typing", "case .typingText:" in managed),
    ("recording", "case .recordingVoice, .recordingInstantVideo:" in managed),
    ("uploading", "case .uploadingFile(_), .uploadingPhoto(_), .uploadingVideo(_), .uploadingInstantVideo(_):" in managed),
    ("sticker", "case .choosingSticker:" in managed),
    ("game", "case .playingGame:" in managed),
    ("emoji", "case .interactingWithEmoji(_, _, _), .seeingEmojiInteraction(_):" in managed),
    ("recording key", "GhostBase.GhostMode.HideRecording" in managed),
    ("uploading key", "GhostBase.GhostMode.HideUploading" in managed),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print("FAILED:")
    for x in bad:
        print("-", x)
    raise SystemExit(1)

print("GhostBase Activity Ghost v0.5C lower-layer patch OK")
