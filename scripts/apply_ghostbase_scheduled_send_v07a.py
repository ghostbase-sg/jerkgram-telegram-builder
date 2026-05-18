from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_read_ghost_extras_v06c.py")))

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramUI/Sources/ChatController.swift").exists():
            return c
    raise SystemExit(f"cannot find source base from cwd={cwd}")

BASE = find_base()

chat_p = BASE / "submodules/TelegramUI/Sources/ChatController.swift"
controller_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

chat = chat_p.read_text()
controller = controller_p.read_text()

controller = controller.replace("Version: v0.6C", "Version: v0.7A")
controller = controller.replace(
    "Read Ghost Extras are active in v0.6C.",
    "Read Ghost Extras are active in v0.6C. Scheduled Send is active in v0.7A."
)

controller_p.write_text(controller)
print("patched", controller_p)

function_marker = "    func transformEnqueueMessages(_ messages: [EnqueueMessage], silentPosting: Bool, scheduleTime: Int32? = nil, repeatPeriod: Int32? = nil, postpone: Bool = false) -> [EnqueueMessage] {\n"

insert_block = '''        // MARK: GhostBase v0.7A Scheduled Send runtime
        let ghostBaseScheduledSendEnabled = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false
        let ghostBaseScheduleBaseTime = Int32(Date().timeIntervalSince1970) + 12
        let ghostBaseIsScheduledMessages: Bool
        if case .scheduledMessages = self.presentationInterfaceState.subject {
            ghostBaseIsScheduledMessages = true
        } else {
            ghostBaseIsScheduledMessages = false
        }

'''

if "GhostBase v0.7A Scheduled Send runtime" not in chat:
    if function_marker not in chat:
        raise SystemExit("missing replacement point: transformEnqueueMessages function")
    chat = chat.replace(function_marker, function_marker + insert_block, 1)

old = '''            return message.withUpdatedAttributes { attributes in
                var attributes = attributes
'''

new = '''            return message.withUpdatedAttributes { attributes in
                var attributes = attributes
                
                let ghostBaseHasExistingSchedule = attributes.contains(where: { $0 is OutgoingScheduleInfoMessageAttribute })
                let ghostBaseEffectiveScheduleTime: Int32? = (ghostBaseScheduledSendEnabled && scheduleTime == nil && !ghostBaseHasExistingSchedule && !ghostBaseIsScheduledMessages) ? ghostBaseScheduleBaseTime : scheduleTime
'''

if "ghostBaseEffectiveScheduleTime" not in chat:
    if old not in chat:
        raise SystemExit("missing replacement point: attributes block")
    chat = chat.replace(old, new, 1)

chat = chat.replace(
    "if silentPosting || scheduleTime != nil {",
    "if silentPosting || ghostBaseEffectiveScheduleTime != nil {",
    1
)
chat = chat.replace(
    "else if let _ = scheduleTime, attributes[i] is OutgoingScheduleInfoMessageAttribute {",
    "else if let _ = ghostBaseEffectiveScheduleTime, attributes[i] is OutgoingScheduleInfoMessageAttribute {",
    1
)
chat = chat.replace(
    "if let scheduleTime {\n                         attributes.append(OutgoingScheduleInfoMessageAttribute(scheduleTime: scheduleTime, repeatPeriod: repeatPeriod))\n                    }",
    "if let ghostBaseEffectiveScheduleTime {\n                         attributes.append(OutgoingScheduleInfoMessageAttribute(scheduleTime: ghostBaseEffectiveScheduleTime, repeatPeriod: repeatPeriod))\n                    }",
    1
)

chat_p.write_text(chat)
print("patched", chat_p)

chat = chat_p.read_text()
controller = controller_p.read_text()

checks = [
    ("version", "Version: v0.7A" in controller),
    ("settings note", "Scheduled Send is active in v0.7A" in controller),
    ("runtime marker", "GhostBase v0.7A Scheduled Send runtime" in chat),
    ("settings key", "GhostBase.GhostMode.ScheduledSend" in chat),
    ("base delay", "+ 12" in chat),
    ("effective time", "ghostBaseEffectiveScheduleTime" in chat),
    ("skip existing", "ghostBaseHasExistingSchedule" in chat),
    ("skip scheduled screen", "ghostBaseIsScheduledMessages" in chat),
    ("schedule attribute", "OutgoingScheduleInfoMessageAttribute(scheduleTime: ghostBaseEffectiveScheduleTime" in chat),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print("FAILED:")
    for x in bad:
        print("-", x)
    raise SystemExit(1)

print("GhostBase Scheduled Send v0.7A patch OK")
