from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_scheduled_send_fix_v07b.py")))

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramUI/Sources/ChatControllerNode.swift").exists():
            return c
    raise SystemExit(f"cannot find source base from cwd={cwd}")

BASE = find_base()

node_p = BASE / "submodules/TelegramUI/Sources/ChatControllerNode.swift"
controller_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

node = node_p.read_text()
controller = controller_p.read_text()

controller = controller.replace("Version: v0.7B", "Version: v0.7C")
controller = controller.replace(
    "Scheduled Send is active in v0.7B.",
    "Scheduled Send is active in v0.7C."
)

old = '''                            state = state.withUpdatedComposeDisableUrlPreviews([])

                            return state
'''

new = '''                            state = state.withUpdatedComposeDisableUrlPreviews([])
                            state = state.withUpdatedComposeInputState(ChatTextInputState(inputText: NSAttributedString(string: "")))

                            return state
'''

if "GhostBase v0.7C Scheduled Send stronger compose clear" not in node:
    if old not in node:
        raise SystemExit("missing replacement point: v07B cleanup compose block")
    node = node.replace(old, '''                            // MARK: GhostBase v0.7C Scheduled Send stronger compose clear
''' + new, 1)

node_p.write_text(node)
controller_p.write_text(controller)

node = node_p.read_text()
controller = controller_p.read_text()

checks = [
    ("version", "Version: v0.7C" in controller),
    ("note", "Scheduled Send is active in v0.7C" in controller),
    ("v07b marker", "GhostBase v0.7B Scheduled Send input clear fix" in node),
    ("v07c marker", "GhostBase v0.7C Scheduled Send stronger compose clear" in node),
    ("compose clear", "withUpdatedComposeInputState(ChatTextInputState(inputText: NSAttributedString(string: \"\")))" in node),
    ("text clear", "textInputPanelNode.text = \"\"" in node),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print("FAILED:")
    for x in bad:
        print("-", x)
    raise SystemExit(1)

print("GhostBase Scheduled Send v0.7C patch OK")
