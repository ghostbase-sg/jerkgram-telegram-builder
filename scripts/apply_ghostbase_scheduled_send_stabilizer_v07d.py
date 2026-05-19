from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_scheduled_send_fix_v07c.py")))

VERSION = "v0.7D"

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramUI/Sources/ChatControllerNode.swift").exists():
            return c
    raise SystemExit(f"[{VERSION}] ERROR: cannot find source base from cwd={cwd}")

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"[{VERSION}] ERROR: required anchor not found: {label}")
    return text.replace(old, new, 1)

BASE = find_base()

node_p = BASE / "submodules/TelegramUI/Sources/ChatControllerNode.swift"
settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

node = node_p.read_text()
settings = settings_p.read_text()

settings = settings.replace("Version: v0.7C", "Version: v0.7D")
settings = settings.replace(
    "Scheduled Send is active in v0.7C.",
    "Scheduled Send is active in v0.7D."
)

required_marker = "GhostBase v0.7B Scheduled Send input clear fix"
if required_marker not in node:
    raise SystemExit(f"[{VERSION}] ERROR: v0.7B cleanup marker missing after v0.7C chain")

if "GhostBase v0.7D Scheduled Send stabilizer" not in node:
    anchor = '''                            state = state.withUpdatedComposeInputState(ChatTextInputState(inputText: NSAttributedString(string: "")))

                            return state
'''
    replacement = '''                            state = state.withUpdatedComposeInputState(ChatTextInputState(inputText: NSAttributedString(string: "")))

                            // MARK: GhostBase v0.7D Scheduled Send stabilizer
                            // Keep this patch intentionally narrow: scheduleTime runtime already works.
                            state = state.withUpdatedEffectiveInputState(ChatTextInputState(inputText: NSAttributedString(string: "")))

                            return state
'''
    node = replace_once(node, anchor, replacement, "v0.7C compose cleanup block")

node_p.write_text(node)
settings_p.write_text(settings)

node = node_p.read_text()
settings = settings_p.read_text()

checks = [
    ("settings version", "Version: v0.7D" in settings),
    ("settings note", "Scheduled Send is active in v0.7D" in settings),
    ("v07b marker", "GhostBase v0.7B Scheduled Send input clear fix" in node),
    ("v07c marker", "GhostBase v0.7C Scheduled Send stronger compose clear" in node),
    ("v07d marker", "GhostBase v0.7D Scheduled Send stabilizer" in node),
    ("compose clear", "withUpdatedComposeInputState(ChatTextInputState(inputText: NSAttributedString(string: \"\")))" in node),
    ("effective clear", "withUpdatedEffectiveInputState(ChatTextInputState(inputText: NSAttributedString(string: \"\")))" in node),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print(f"[{VERSION}] FAILED:")
    for name in bad:
        print("-", name)
    raise SystemExit(1)

print("GhostBase Scheduled Send v0.7D stabilizer patch OK")
