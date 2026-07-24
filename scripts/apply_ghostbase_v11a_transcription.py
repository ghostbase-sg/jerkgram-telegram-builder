#!/usr/bin/env python3
import os
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
VOICE = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift"
ROUND = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveInstantVideoNode/Sources/ChatMessageInteractiveInstantVideoNode.swift"
for path in (VOICE, ROUND):
    if not path.is_file():
        raise SystemExit(f"[V11A TRANSCRIPTION] missing source: {path}")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"[V11A TRANSCRIPTION] {label} anchor count: {count}")
    return text.replace(old, new, 1)

voice = VOICE.read_text(encoding="utf-8")
marker_voice = "// MARK: GhostBase v1.1A TRANSCRIPTION1 voice unlock"
if marker_voice not in voice:
    display_start = voice.index("                var displayTranscribe = false\n", voice.index("let textFont = arguments.presentationData.messageFont"))
    display_end = voice.index("                let transcribedText =", display_start)
    new_display = """                var displayTranscribe = false
                // MARK: GhostBase v1.1A TRANSCRIPTION1 voice unlock
                if !Namespaces.Message.allNonRegular.contains(arguments.message.id.namespace) && arguments.message.id.peerId.namespace != Namespaces.Peer.SecretChat && !isViewOnceMessage && !arguments.presentationData.isPreview {
                    displayTranscribe = true
                }

"""
    voice = voice[:display_start] + new_display + voice[display_end:]

    start = voice.index("        if !context.isPremium, case .inProgress = self.audioTranscriptionState {")
    end = voice.index("        var shouldBeginTranscription = false", start)
    replacement = '''        // MARK: GhostBase v1.1A TRANSCRIPTION1 request without local Premium gate
        let presentationData = context.sharedContext.currentPresentationData.with { $0 }

'''
    voice = voice[:start] + replacement + voice[end:]

# TRANSCRIPTION1 removes the local Premium UI branch. Keep the generated Swift
# warning-clean under Telegram's warnings-as-errors build settings.
voice = voice.replace(
    "guard let arguments = self.arguments, let context = self.context, let message = self.message else {",
    "guard let context = self.context, let message = self.message else {",
    1,
)
voice = voice.replace("                var isConsumed: Bool?\n", "", 1)
voice = voice.replace("                        isConsumed = attribute.consumed\n", "", 1)
VOICE.write_text(voice, encoding="utf-8")

round_text = ROUND.read_text(encoding="utf-8")
marker_round = "// MARK: GhostBase v1.1A TRANSCRIPTION1 round-video unlock"
if marker_round not in round_text:
    display_start = round_text.index("                    var displayTranscribe = false\n", round_text.index("ChatMessageInteractiveInstantVideoNode"))
    display_end = round_text.index("                    if displayTranscribe, let durationBlurColor", display_start)
    new_display = """                    var displayTranscribe = false
                    // MARK: GhostBase v1.1A TRANSCRIPTION1 round-video unlock
                    if item.message.id.peerId.namespace != Namespaces.Peer.SecretChat && statusDisplayType == .free && !isViewOnceMessage && !item.presentationData.isPreview {
                        displayTranscribe = true
                    }

"""
    round_text = round_text[:display_start] + new_display + round_text[display_end:]

    start = round_text.index("        if !item.context.isPremium, case .inProgress = self.audioTranscriptionState {")
    end = round_text.index("        var shouldBeginTranscription = false", start)
    replacement = '''        // MARK: GhostBase v1.1A TRANSCRIPTION1 round request without local Premium gate
'''
    round_text = round_text[:start] + replacement + round_text[end:]
ROUND.write_text(round_text, encoding="utf-8")

for path, proofs in (
    (VOICE, (marker_voice, "displayTranscribe = true", "request without local Premium gate", "transcribeAudio(messageId:")),
    (ROUND, (marker_round, "displayTranscribe = true", "round request without local Premium gate", "transcribeAudio(messageId:")),
):
    updated = path.read_text(encoding="utf-8")
    for proof in proofs:
        if proof not in updated:
            raise SystemExit(f"[V11A TRANSCRIPTION] proof missing in {path.name}: {proof}")
print("[V11A] voice and round-video transcription buttons unlocked through Official engine")
