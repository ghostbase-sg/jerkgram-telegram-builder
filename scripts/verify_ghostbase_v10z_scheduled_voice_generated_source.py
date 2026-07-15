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

text = path.read_text(encoding="utf-8")

def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[v1.0Z voice verifier] {message}")

for proof in [
    "GhostBase v1.0Z scheduled voice official lifecycle restore",
    "let ghostBaseScheduledVoiceEnabled",
    "let ghostBaseEffectiveScheduleTime: Int32?",
    "if let scheduleTime",
    "ghostBaseScheduledVoiceEnabled && !isScheduledMessages",
    "Int32(Date().timeIntervalSince1970) + 12",
    "scheduleTime: ghostBaseEffectiveScheduleTime",
    "self.chatDisplayNode.setupSendActionOnViewUpdate",
]:
    require(proof in text, f"missing proof: {proof}")

request_prefix = """    func requestAudioRecorder(beginWithTone: Bool, existingDraft: ChatInterfaceMediaDraftState.Audio? = nil) {
        if self.audioRecorderValue == nil {
"""

require(
    request_prefix in text,
    "official requestAudioRecorder prefix missing"
)

for forbidden in [
    "GhostBase v1.0T scheduled voice UI cleanup",
    "GhostBase v1.0U scheduled voice complete cleanup",
    "GhostBase v1.0W scheduled voice verdict",
    "GhostBase v1.0W scheduled voice post-enqueue cleanup",
    "GhostBase v1.0X scheduled voice UI routing",
    "GhostBase v1.0X scheduled voice immediate success cleanup",
    "GhostBase v1.0Y repeated scheduled voice reset",
    "ghostBaseRuntimeScheduledVoice",
    "ghostBaseVoiceWillBeScheduled",
    "ghostBaseVoiceWasScheduled",
]:
    require(
        forbidden not in text,
        f"legacy voice branch remains: {forbidden}"
    )

require(
    text.count(
        "let ghostBaseEffectiveScheduleTime: Int32?"
    ) == 1,
    "effective schedule state duplicated"
)

require(
    text.count(
        "GhostBase v1.0Z scheduled voice official lifecycle restore"
    ) == 1,
    "lifecycle restore duplicated"
)

print("[v1.0Z voice verifier] official recorder lifecycle OK")
print("[v1.0Z voice verifier] explicit scheduleTime routing OK")
print("[v1.0Z voice verifier] T/U/W/X/Y cleanup branches absent")
