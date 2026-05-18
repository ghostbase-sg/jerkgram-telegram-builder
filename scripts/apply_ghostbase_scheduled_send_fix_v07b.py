from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_scheduled_send_v07a.py")))

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

controller = controller.replace("Version: v0.7A", "Version: v0.7B")
controller = controller.replace(
    "Scheduled Send is active in v0.7A.",
    "Scheduled Send is active in v0.7B."
)

node_p.write_text(node)
controller_p.write_text(controller)

print("patched", controller_p)

marker = '''                    self.sendMessages(messages, silentPosting, scheduleTime, repeatPeriod, messages.count > 1, postpone)
'''

insert = '''                    self.sendMessages(messages, silentPosting, scheduleTime, repeatPeriod, messages.count > 1, postpone)

                    // MARK: GhostBase v0.7B Scheduled Send input clear fix
                    let ghostBaseScheduledSendEnabled = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false

                    if ghostBaseScheduledSendEnabled && scheduleTime == nil {
                        self.collapseInput()

                        self.ignoreUpdateHeight = true

                        if let textInputPanelNode = self.inputPanelNode as? ChatTextInputPanelNode {
                            textInputPanelNode.text = ""
                        }

                        self.requestUpdateChatInterfaceState(.immediate, overrideThreadId == nil, { state in
                            var state = state

                            state = state.withUpdatedReplyMessageSubject(nil)
                            state = state.withUpdatedSendMessageEffect(nil)

                            state = state.withUpdatedForwardMessageIds(nil)
                            state = state.withUpdatedForwardOptionsState(nil)

                            state = state.withUpdatedComposeDisableUrlPreviews([])

                            return state
                        })

                        self.ignoreUpdateHeight = false
                    }
'''

if "GhostBase v0.7B Scheduled Send input clear fix" not in node:
    if marker not in node:
        raise SystemExit("missing replacement point: sendMessages call")
    node = node.replace(marker, insert, 1)

node_p.write_text(node)
print("patched", node_p)

node = node_p.read_text()
controller = controller_p.read_text()

checks = [
    ("version", "Version: v0.7B" in controller),
    ("runtime marker", "GhostBase v0.7B Scheduled Send input clear fix" in node),
    ("settings key", "GhostBase.GhostMode.ScheduledSend" in node),
    ("text clear", 'textInputPanelNode.text = ""' in node),
    ("reply clear", "withUpdatedReplyMessageSubject(nil)" in node),
    ("forward clear", "withUpdatedForwardMessageIds(nil)" in node),
    ("preview clear", "withUpdatedComposeDisableUrlPreviews([])" in node),
]

bad = [name for name, ok in checks if not ok]

if bad:
    print("FAILED:")
    for x in bad:
        print("-", x)
    raise SystemExit(1)

print("GhostBase Scheduled Send v0.7B patch OK")
