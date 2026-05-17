from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_hide_typing_v05a.py")))

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramCore/Sources/Account/Account.swift").exists():
            return c
    raise SystemExit(f"cannot find source base from cwd={cwd}")

def must_replace(s: str, old: str, new: str, name: str) -> str:
    if old not in s:
        raise SystemExit(f"missing replacement point: {name}")
    return s.replace(old, new, 1)

BASE = find_base()
account_p = BASE / "submodules/TelegramCore/Sources/Account/Account.swift"
controller_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

controller = controller_p.read_text()
account = account_p.read_text()

controller = controller.replace("Version: v0.5A", "Version: v0.5B")

controller = controller.replace(
    "Profile Metrics affects the profile card after reopening a profile. Hide Typing is active when enabled. Other Ghost Mode toggles are saved for upcoming runtime modules.",
    "Profile Metrics affects the profile card after reopening a profile. Activity Ghost hides typing, recording, uploading, sticker, game and emoji activity when enabled."
)

controller = must_replace(controller,
    '    static let typingActions = "GhostBase.GhostMode.TypingActions"\n',
    '    static let typingActions = "GhostBase.GhostMode.TypingActions"\n'
    '    static let recordingActions = "GhostBase.GhostMode.HideRecording"\n'
    '    static let uploadingActions = "GhostBase.GhostMode.HideUploading"\n'
    '    static let stickerActivity = "GhostBase.GhostMode.HideStickerActivity"\n'
    '    static let gameActivity = "GhostBase.GhostMode.HideGameActivity"\n'
    '    static let emojiActivity = "GhostBase.GhostMode.HideEmojiActivity"\n',
    "keys"
)

controller = must_replace(controller,
    '    var typingActions: Bool\n',
    '    var typingActions: Bool\n'
    '    var recordingActions: Bool\n'
    '    var uploadingActions: Bool\n'
    '    var stickerActivity: Bool\n'
    '    var gameActivity: Bool\n'
    '    var emojiActivity: Bool\n',
    "state vars"
)

controller = must_replace(controller,
    '            typingActions: ghostBaseBool(GhostBaseKey.typingActions, defaultValue: false),\n',
    '            typingActions: ghostBaseBool(GhostBaseKey.typingActions, defaultValue: false),\n'
    '            recordingActions: ghostBaseBool(GhostBaseKey.recordingActions, defaultValue: false),\n'
    '            uploadingActions: ghostBaseBool(GhostBaseKey.uploadingActions, defaultValue: false),\n'
    '            stickerActivity: ghostBaseBool(GhostBaseKey.stickerActivity, defaultValue: false),\n'
    '            gameActivity: ghostBaseBool(GhostBaseKey.gameActivity, defaultValue: false),\n'
    '            emojiActivity: ghostBaseBool(GhostBaseKey.emojiActivity, defaultValue: false),\n',
    "state defaults"
)

controller = must_replace(controller,
    '        UserDefaults.standard.set(self.typingActions, forKey: GhostBaseKey.typingActions)\n',
    '        UserDefaults.standard.set(self.typingActions, forKey: GhostBaseKey.typingActions)\n'
    '        UserDefaults.standard.set(self.recordingActions, forKey: GhostBaseKey.recordingActions)\n'
    '        UserDefaults.standard.set(self.uploadingActions, forKey: GhostBaseKey.uploadingActions)\n'
    '        UserDefaults.standard.set(self.stickerActivity, forKey: GhostBaseKey.stickerActivity)\n'
    '        UserDefaults.standard.set(self.gameActivity, forKey: GhostBaseKey.gameActivity)\n'
    '        UserDefaults.standard.set(self.emojiActivity, forKey: GhostBaseKey.emojiActivity)\n',
    "state save"
)

old_entries = '''    entries.append(.toggle(ghost, 1, GhostBaseKey.readMessages, "Read Ghost", state.readMessages))
    entries.append(.toggle(ghost, 2, GhostBaseKey.typingActions, "Hide Typing", state.typingActions))
    entries.append(.toggle(ghost, 3, GhostBaseKey.presence, "Hide Online", state.presence))
    entries.append(.toggle(ghost, 4, GhostBaseKey.scheduledSend, "Scheduled Send", state.scheduledSend))
'''

new_entries = '''    entries.append(.toggle(ghost, 1, GhostBaseKey.readMessages, "Read Ghost", state.readMessages))
    entries.append(.toggle(ghost, 2, GhostBaseKey.typingActions, "Hide Typing", state.typingActions))
    entries.append(.toggle(ghost, 3, GhostBaseKey.recordingActions, "Hide Recording", state.recordingActions))
    entries.append(.toggle(ghost, 4, GhostBaseKey.uploadingActions, "Hide Uploading", state.uploadingActions))
    entries.append(.toggle(ghost, 5, GhostBaseKey.stickerActivity, "Hide Sticker Activity", state.stickerActivity))
    entries.append(.toggle(ghost, 6, GhostBaseKey.gameActivity, "Hide Game Activity", state.gameActivity))
    entries.append(.toggle(ghost, 7, GhostBaseKey.emojiActivity, "Hide Emoji Activity", state.emojiActivity))
    entries.append(.toggle(ghost, 8, GhostBaseKey.presence, "Hide Online", state.presence))
    entries.append(.toggle(ghost, 9, GhostBaseKey.scheduledSend, "Scheduled Send", state.scheduledSend))
'''

controller = must_replace(controller, old_entries, new_entries, "ghost entries")

needle_cases = '''            case GhostBaseKey.typingActions:
                updated.typingActions = value
'''

insert_cases = '''            case GhostBaseKey.recordingActions:
                updated.recordingActions = value
            case GhostBaseKey.uploadingActions:
                updated.uploadingActions = value
            case GhostBaseKey.stickerActivity:
                updated.stickerActivity = value
            case GhostBaseKey.gameActivity:
                updated.gameActivity = value
            case GhostBaseKey.emojiActivity:
                updated.emojiActivity = value
'''

if "case GhostBaseKey.recordingActions:" not in controller:
    controller = must_replace(controller, needle_cases, needle_cases + insert_cases, "ghost update cases")
controller_p.write_text(controller)
print("patched", controller_p)

start_marker = "    public func updateLocalInputActivity(peerId: PeerActivitySpace, activity: PeerInputActivity, isPresent: Bool) {\n"
end_marker = "    public func acquireLocalInputActivity(peerId: PeerActivitySpace, activity: PeerInputActivity) -> Disposable {\n"

if start_marker not in account:
    raise SystemExit("updateLocalInputActivity function not found")

start = account.index(start_marker)
end = account.index(end_marker, start)

new_func = '''    public func updateLocalInputActivity(peerId: PeerActivitySpace, activity: PeerInputActivity, isPresent: Bool) {
        // MARK: GhostBase v0.5B Activity Ghost runtime
        if isPresent {
            let ghostBaseHideTyping = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.TypingActions") as? Bool) ?? false
            let ghostBaseHideRecording = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.HideRecording") as? Bool) ?? false
            let ghostBaseHideUploading = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.HideUploading") as? Bool) ?? false
            let ghostBaseHideStickerActivity = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.HideStickerActivity") as? Bool) ?? false
            let ghostBaseHideGameActivity = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.HideGameActivity") as? Bool) ?? false
            let ghostBaseHideEmojiActivity = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.HideEmojiActivity") as? Bool) ?? false

            switch activity {
            case .typingText:
                if ghostBaseHideTyping { return }
            case .recordingVoice, .recordingInstantVideo:
                if ghostBaseHideRecording { return }
            case .uploadingFile(_), .uploadingPhoto(_), .uploadingVideo(_), .uploadingInstantVideo(_):
                if ghostBaseHideUploading { return }
            case .choosingSticker:
                if ghostBaseHideStickerActivity { return }
            case .playingGame:
                if ghostBaseHideGameActivity { return }
            case .interactingWithEmoji(_, _, _), .seeingEmojiInteraction(_):
                if ghostBaseHideEmojiActivity { return }
            default:
                break
            }
        }

        self.localInputActivityManager.transaction { manager in
            if isPresent {
                manager.addActivity(chatPeerId: peerId, peerId: self.peerId, activity: activity)
            } else {
                manager.removeActivity(chatPeerId: peerId, peerId: self.peerId, activity: activity)
            }
        }
    }
    
'''

account = account[:start] + new_func + account[end:]
account_p.write_text(account)
print("patched", account_p)

controller = controller_p.read_text()
account = account_p.read_text()

checks = [
    ("version", "Version: v0.5B" in controller),
    ("recording ui", '"Hide Recording"' in controller),
    ("uploading ui", '"Hide Uploading"' in controller),
    ("sticker ui", '"Hide Sticker Activity"' in controller),
    ("game ui", '"Hide Game Activity"' in controller),
    ("emoji ui", '"Hide Emoji Activity"' in controller),
    ("runtime", "GhostBase v0.5B Activity Ghost runtime" in account),
    ("typing", "case .typingText:" in account),
    ("recording", "case .recordingVoice, .recordingInstantVideo:" in account),
    ("uploading", "case .uploadingFile(_), .uploadingPhoto(_), .uploadingVideo(_), .uploadingInstantVideo(_):" in account),
    ("sticker", "case .choosingSticker:" in account),
    ("game", "case .playingGame:" in account),
    ("emoji", "case .interactingWithEmoji(_, _, _), .seeingEmojiInteraction(_):" in account),
    ("cancel passes", "manager.removeActivity(chatPeerId: peerId, peerId: self.peerId, activity: activity)" in account),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print("FAILED:")
    for x in bad:
        print("-", x)
    raise SystemExit(1)

print("GhostBase Activity Ghost v0.5B patch OK")
