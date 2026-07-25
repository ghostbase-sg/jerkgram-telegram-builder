#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
voice = (root / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift").read_text(encoding="utf-8")
round_text = (root / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveInstantVideoNode/Sources/ChatMessageInteractiveInstantVideoNode.swift").read_text(encoding="utf-8")
checks = [
    ("voice local-first marker", "GhostBase v1.1B TRANSCRIPTION2 local-first voice" in voice),
    ("voice local engine", "transcribeAudio(path:" in voice),
    ("round server marker", "GhostBase v1.1B TRANSCRIPTION2 round server-limit guard" in round_text),
    ("round official request", "engine.messages.transcribeAudio(messageId:" in round_text),
]
failed = [name for name, ok in checks if not ok]
if failed:
    raise SystemExit("TRANSCRIPTION2 verify failed: " + ", ".join(failed))
print("TRANSCRIPTION2 VERIFY OK")
