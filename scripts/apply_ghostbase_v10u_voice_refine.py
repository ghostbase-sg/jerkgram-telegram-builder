#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "work/swiftgram-src/submodules/TelegramUI/Sources/Chat/ChatControllerMediaRecording.swift"

def need(value, message):
    if not value:
        raise RuntimeError(message)

need(FILE.is_file(), f"missing: {FILE}")
text = FILE.read_text()

marker = "GhostBase v1.0U scheduled voice runtime verdict"

if marker not in text:
    old = '''            let ghostBaseRuntimeScheduledVoice = ((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false) && scheduleTime == nil && !isScheduledMessages
'''

    new = '''            let ghostBaseRuntimeScheduledVoice = (
                scheduleTime != nil
                || ((UserDefaults.standard.object(
                    forKey: "GhostBase.GhostMode.ScheduledSend"
                ) as? Bool) ?? false)
            ) && !isScheduledMessages
'''

    need(old in text, "voice runtime anchor missing")
    text = text.replace(old, new, 1)

    old = '''            } else {
                transformedMessages = self.transformEnqueueMessages(messages)
            }

            guard let peerId = self.chatLocation.peerId else {
'''

    new = '''            } else {
                transformedMessages = self.transformEnqueueMessages(messages)
            }

            // MARK: GhostBase v1.0U scheduled voice runtime verdict
            let ghostBaseVoiceWasScheduled = transformedMessages.contains { message in
                switch message {
                case let .message(_, attributes, _, _, _, _, _, _, _, _):
                    return attributes.contains {
                        $0 is OutgoingScheduleInfoMessageAttribute
                    }
                case .forward:
                    return false
                }
            }

            guard let peerId = self.chatLocation.peerId else {
'''

    need(old in text, "transformed voice anchor missing")
    text = text.replace(old, new, 1)

    old = '''            if ghostBaseRuntimeScheduledVoice {
                // MARK: GhostBase v1.0U scheduled voice complete cleanup
'''

    new = '''            if ghostBaseVoiceWasScheduled {
                // MARK: GhostBase v1.0U scheduled voice complete cleanup
'''

    need(old in text, "voice cleanup verdict anchor missing")
    text = text.replace(old, new, 1)

FILE.write_text(text)
need(marker in text, "voice verdict marker missing")

print("[v1.0U] scheduled voice verdict refined")
