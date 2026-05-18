from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_activity_ghost_v05c.py")))

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramCore/Sources/State/ManagedAccountPresence.swift").exists():
            return c
    raise SystemExit(f"cannot find source base from cwd={cwd}")

def must_replace(s: str, old: str, new: str, name: str) -> str:
    if old not in s:
        raise SystemExit(f"missing replacement point: {name}")
    return s.replace(old, new, 1)

BASE = find_base()

presence_p = BASE / "submodules/TelegramCore/Sources/State/ManagedAccountPresence.swift"
controller_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

presence = presence_p.read_text()
controller = controller_p.read_text()

controller = controller.replace("Version: v0.5C", "Version: v0.6A")
controller = controller.replace(
    "v0.5C adds a lower-layer activity guard.",
    "v0.5C adds a lower-layer activity guard. Hide Online is active in v0.6A."
)

old_presence_case = '''            case GhostBaseKey.presence:
                updated.presence = value
'''

new_presence_case = '''            case GhostBaseKey.presence:
                updated.presence = value
                if value {
                    context.account.shouldKeepOnlinePresence.set(.single(false))
                } else {
                    context.account.shouldKeepOnlinePresence.set(.single(false))
                    context.account.shouldKeepOnlinePresence.set(.single(true))
                }
'''

controller = must_replace(controller, old_presence_case, new_presence_case, "presence update case")
controller_p.write_text(controller)
print("patched", controller_p)

if "GhostBase v0.6A Hide Online runtime" not in presence:
    function_marker = "    private func updatePresence(_ isOnline: Bool) {"
    if function_marker not in presence:
        raise SystemExit("missing replacement point: updatePresence function")

    request_marker = "        let request: Signal<Api.Bool, MTRpcError>\n        if isOnline {"
    if request_marker not in presence:
        raise SystemExit("missing replacement point: updatePresence request branch")

    presence = presence.replace(
        function_marker,
        function_marker + """
        // MARK: GhostBase v0.6A Hide Online runtime
        let ghostBaseHideOnline = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.Presence") as? Bool) ?? false
        let effectiveIsOnline = ghostBaseHideOnline ? false : isOnline
""",
        1
    )
    presence = presence.replace(
        request_marker,
        "        let request: Signal<Api.Bool, MTRpcError>\n        if effectiveIsOnline {",
        1
    )

presence_p.write_text(presence)
print("patched", presence_p)

presence = presence_p.read_text()
controller = controller_p.read_text()

checks = [
    ("version", "Version: v0.6A" in controller),
    ("settings note", "Hide Online is active in v0.6A" in controller),
    ("presence key", "GhostBase.GhostMode.Presence" in presence),
    ("runtime marker", "GhostBase v0.6A Hide Online runtime" in presence),
    ("effective online", "let effectiveIsOnline = ghostBaseHideOnline ? false : isOnline" in presence),
    ("online request still present", "account.updateStatus(offline: .boolFalse)" in presence),
    ("offline request still present", "account.updateStatus(offline: .boolTrue)" in presence),
    ("instant false", "context.account.shouldKeepOnlinePresence.set(.single(false))" in controller),
    ("presence case", "case GhostBaseKey.presence:" in controller),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print("FAILED:")
    for x in bad:
        print("-", x)
    raise SystemExit(1)

print("GhostBase Hide Online v0.6A patch OK")
