#!/usr/bin/env python3
import os
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
VOICE = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift"
ROUND = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveInstantVideoNode/Sources/ChatMessageInteractiveInstantVideoNode.swift"
for p in (VOICE, ROUND):
    if not p.is_file():
        raise SystemExit(f"[V11B TRANSCRIPTION2] missing source: {p}")

voice = VOICE.read_text(encoding="utf-8")
round_text = ROUND.read_text(encoding="utf-8")
VM = "// MARK: GhostBase v1.1B TRANSCRIPTION2 local-first voice"
RM = "// MARK: GhostBase v1.1B TRANSCRIPTION2 round server-limit guard"
if VM not in voice:
    if "// MARK: GhostBase v1.1A TRANSCRIPTION1 voice unlock" not in voice:
        raise SystemExit("[V11B TRANSCRIPTION2] TRANSCRIPTION1 voice marker missing")
    old = "                if context.sharedContext.immediateExperimentalUISettings.localTranscription {\n"
    if voice.count(old) != 1:
        raise SystemExit(f"[V11B TRANSCRIPTION2] local transcription branch anchor count={voice.count(old)}")
    new = "                " + VM + "\n                if true {\n"
    voice = voice.replace(old, new, 1)
    # Make local failure visibly leave progress state and log the real limitation.
    old_nil = """                        } else {
                            strongSelf.audioTranscriptionState = .collapsed
                            strongSelf.requestUpdateLayout(true)
                        }
"""
    new_nil = """                        } else {
                            Logger.shared.log("GhostBase.Transcription2", "local voice transcription unavailable or media not downloaded")
                            strongSelf.audioTranscriptionState = .collapsed
                            strongSelf.requestUpdateLayout(true)
                        }
"""
    if voice.count(old_nil) < 1:
        raise SystemExit("[V11B TRANSCRIPTION2] local nil-result anchor missing")
    voice = voice.replace(old_nil, new_nil, 1)
    VOICE.write_text(voice, encoding="utf-8")

if RM not in round_text:
    if "// MARK: GhostBase v1.1A TRANSCRIPTION1 round-video unlock" not in round_text:
        raise SystemExit("[V11B TRANSCRIPTION2] TRANSCRIPTION1 round marker missing")
    anchor = "                self.transcribeDisposable = (item.context.engine.messages.transcribeAudio(messageId: item.message.id)\n"
    if round_text.count(anchor) != 1:
        raise SystemExit(f"[V11B TRANSCRIPTION2] round request anchor count={round_text.count(anchor)}")
    replacement = "                " + RM + "\n                Logger.shared.log(\"GhostBase.Transcription2\", \"round video still requires Official server transcription\")\n" + anchor
    round_text = round_text.replace(anchor, replacement, 1)
    ROUND.write_text(round_text, encoding="utf-8")

for p, proofs in ((VOICE, (VM, "if true {", "local voice transcription unavailable")), (ROUND, (RM, "round video still requires Official server transcription", "transcribeAudio(messageId:"))):
    value = p.read_text(encoding="utf-8")
    for proof in proofs:
        if proof not in value:
            raise SystemExit(f"[V11B TRANSCRIPTION2] proof missing in {p.name}: {proof}")
print("[V11B] TRANSCRIPTION2 applied: voice uses local-first path; round-video server dependency is explicit and unchanged")
