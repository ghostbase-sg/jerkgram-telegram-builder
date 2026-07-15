#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

path = root / (
    "submodules/TelegramUI/Sources/Chat/"
    "ChatControllerMediaRecording.swift"
)

if not path.is_file():
    raise SystemExit(f"missing generated source: {path}")

text = path.read_text(encoding="utf-8")

marker = (
    "// MARK: GhostBase v1.0ZA scheduled voice "
    "direct send redirect"
)

def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[v1.0ZA voice] {message}")

if marker not in text:
    old_state = """        var sendImmediately = false
        if let _ = self.presentationInterfaceState.sendPaidMessageStars, case .send = action {
            updatedAction = .preview
            sendImmediately = true
        }
"""

    new_state = """        var sendImmediately = false
        var ghostBaseSendImmediatelyViewOnce = false

        if let _ = self.presentationInterfaceState.sendPaidMessageStars, case .send = action {
            updatedAction = .preview
            sendImmediately = true
        }

        let ghostBaseScheduledVoiceDirectSendEnabled = (
            UserDefaults.standard.object(
                forKey: "GhostBase.GhostMode.ScheduledSend"
            ) as? Bool
        ) ?? false

        if ghostBaseScheduledVoiceDirectSendEnabled,
           !isScheduledMessages,
           case let .send(viewOnce) = action {
            // MARK: GhostBase v1.0ZA scheduled voice direct send redirect
            updatedAction = .preview
            sendImmediately = true
            ghostBaseSendImmediatelyViewOnce = viewOnce
        }
"""

    require(
        old_state in text,
        "sendImmediately state anchor missing"
    )
    text = text.replace(old_state, new_state, 1)

    old_send = """                                        strongSelf.interfaceInteraction?.sendRecordedMedia(false, false)
"""

    new_send = """                                        strongSelf.interfaceInteraction?.sendRecordedMedia(
                                            false,
                                            ghostBaseSendImmediatelyViewOnce
                                        )
"""

    require(
        old_send in text,
        "sendRecordedMedia anchor missing"
    )
    text = text.replace(old_send, new_send, 1)

for proof in (
    marker,
    "ghostBaseScheduledVoiceDirectSendEnabled",
    "case let .send(viewOnce) = action",
    "updatedAction = .preview",
    "ghostBaseSendImmediatelyViewOnce = viewOnce",
    "ghostBaseSendImmediatelyViewOnce\n",
):
    require(proof in text, f"missing proof: {proof}")

path.write_text(text, encoding="utf-8")

print("[v1.0ZA] scheduled voice direct send redirected")
print("[v1.0ZA] direct send now uses preview/draft lifecycle")
