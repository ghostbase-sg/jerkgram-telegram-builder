from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_settings_toggles_v04a.py")))

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramCore/Sources/Account/Account.swift").exists():
            return c
    raise SystemExit(f"cannot find source base from cwd={cwd}")

BASE = find_base()

account_p = BASE / "submodules/TelegramCore/Sources/Account/Account.swift"
controller_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

if not account_p.exists():
    raise SystemExit(f"missing file: {account_p}")
if not controller_p.exists():
    raise SystemExit(f"missing file: {controller_p}")

controller = controller_p.read_text()

controller = controller.replace("Version: v0.4A", "Version: v0.5A")
controller = controller.replace('"Read Messages"', '"Read Ghost"')
controller = controller.replace('"Typing Actions"', '"Hide Typing"')
controller = controller.replace('"Presence"', '"Hide Online"')
controller = controller.replace(
    "Profile Metrics affects the profile card after reopening a profile. Ghost Mode toggles are saved for upcoming runtime modules.",
    "Profile Metrics affects the profile card after reopening a profile. Hide Typing is active when enabled. Other Ghost Mode toggles are saved for upcoming runtime modules."
)

old_master = '''            case GhostBaseKey.profileEnabled:
                updated.profileEnabled = value
                if value && !updated.showIds && !updated.showDCs && !updated.showRegistration {
                    updated.showIds = true
                    updated.showDCs = true
                    updated.showRegistration = true
                }
'''

new_master = '''            case GhostBaseKey.profileEnabled:
                updated.profileEnabled = value
                if value {
                    updated.showIds = true
                    updated.showDCs = true
                    updated.showRegistration = true
                } else {
                    updated.showIds = false
                    updated.showDCs = false
                    updated.showRegistration = false
                }
'''

if old_master not in controller:
    raise SystemExit("profileEnabled switch block not found")

controller = controller.replace(old_master, new_master, 1)

controller_p.write_text(controller)
print("patched", controller_p)

account = account_p.read_text()

start_marker = "    public func updateLocalInputActivity(peerId: PeerActivitySpace, activity: PeerInputActivity, isPresent: Bool) {\n"
end_marker = "    public func acquireLocalInputActivity(peerId: PeerActivitySpace, activity: PeerInputActivity) -> Disposable {\n"

if start_marker not in account:
    raise SystemExit("updateLocalInputActivity function not found")

start = account.index(start_marker)
end = account.index(end_marker, start)

new_func = '''    public func updateLocalInputActivity(peerId: PeerActivitySpace, activity: PeerInputActivity, isPresent: Bool) {
        // MARK: GhostBase v0.5A Hide Typing runtime
        let ghostBaseHideTyping = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.TypingActions") as? Bool) ?? false
        if ghostBaseHideTyping && isPresent && activity == .typingText {
            return
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
    ("version v0.5A", "Version: v0.5A" in controller),
    ("hide typing title", '"Hide Typing"' in controller),
    ("read ghost title", '"Read Ghost"' in controller),
    ("hide online title", '"Hide Online"' in controller),
    ("master off disables ids", "updated.showIds = false" in controller),
    ("master off disables dcs", "updated.showDCs = false" in controller),
    ("master off disables reg", "updated.showRegistration = false" in controller),
    ("hide typing marker", "GhostBase v0.5A Hide Typing runtime" in account),
    ("hide typing key", "GhostBase.GhostMode.TypingActions" in account),
    ("typing guard", "ghostBaseHideTyping && isPresent && activity == .typingText" in account),
    ("cancel still passes", "manager.removeActivity(chatPeerId: peerId, peerId: self.peerId, activity: activity)" in account),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print("FAILED:")
    for x in bad:
        print("-", x)
    raise SystemExit(1)

print("GhostBase Hide Typing v0.5A patch OK")
