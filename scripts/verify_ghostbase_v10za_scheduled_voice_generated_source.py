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
        raise SystemExit(f"[v1.0ZA voice verifier] {message}")

for proof in (
    "GhostBase v1.0ZA scheduled voice direct send redirect",
    "let ghostBaseScheduledVoiceDirectSendEnabled",
    "case let .send(viewOnce) = action",
    "updatedAction = .preview",
    "sendImmediately = true",
    "ghostBaseSendImmediatelyViewOnce = viewOnce",
    "ghostBaseSendImmediatelyViewOnce\n",
):
    require(proof in text, f"missing proof: {proof}")

require(
    text.count(
        "GhostBase v1.0ZA scheduled voice direct send redirect"
    ) == 1,
    "redirect duplicated"
)

require(
    "GhostBase v1.0X scheduled voice immediate success cleanup"
    not in text,
    "legacy cleanup returned"
)

print("[v1.0ZA voice verifier] direct send redirect OK")
print("[v1.0ZA voice verifier] locked and held send share one path")
