#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
paths = [
    root / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift",
    root / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveInstantVideoNode/Sources/ChatMessageInteractiveInstantVideoNode.swift",
]
for path in paths:
    text = path.read_text(encoding="utf-8")
    if "GhostBase v1.1A TRANSCRIPTION1" not in text:
        raise SystemExit(f"[V11A verifier] transcription marker missing: {path}")
    if "transcribeAudio(messageId:" not in text:
        raise SystemExit(f"[V11A verifier] Official transcription call missing: {path}")
    section = text[text.index("private func transcribe()"):]
    if "SubscribeToPremium" in section[:3500]:
        raise SystemExit(f"[V11A verifier] local Premium refusal remains in transcribe(): {path}")
print("[V11A verifier] voice/round transcription UI and request paths OK")
