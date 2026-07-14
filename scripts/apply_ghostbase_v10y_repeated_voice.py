#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))
dry_run = os.environ.get("GHOSTBASE_DRY_RUN") == "1"

path = root / (
    "submodules/TelegramUI/Sources/Chat/"
    "ChatControllerMediaRecording.swift"
)

if not path.is_file():
    raise SystemExit(f"missing source: {path}")

text = path.read_text(encoding="utf-8")

def once(source: str, old: str, new: str, label: str) -> str:
    if new in source:
        return source
    if old not in source:
        raise SystemExit(f"anchor not found: {label}")
    return source.replace(old, new, 1)

text = once(
    text,
    """    func requestAudioRecorder(beginWithTone: Bool, existingDraft: ChatInterfaceMediaDraftState.Audio? = nil) {
        if self.audioRecorderValue == nil {
""",
    """    func requestAudioRecorder(beginWithTone: Bool, existingDraft: ChatInterfaceMediaDraftState.Audio? = nil) {
        // MARK: GhostBase v1.0Y repeated scheduled voice reset
        if existingDraft == nil,
           self.presentationInterfaceState.inputTextPanelState.mediaRecordingState == nil,
           self.presentationInterfaceState.interfaceState.mediaDraftState == nil {
            self.recorderDataDisposable.set(nil)
            self.audioRecorder.set(.single(nil))
            self.recorderFeedback = nil
        }

        if self.audioRecorderValue == nil {
""",
    "audio recorder preflight reset"
)

text = once(
    text,
    """                self.recorderDataDisposable.set(nil)

                self.chatDisplayNode.collapseInput()
""",
    """                self.recorderDataDisposable.set(nil)
                self.audioRecorder.set(.single(nil))
                self.recorderFeedback = nil
                self.chatDisplayNode.updateRecordedMediaDeleted(false)

                self.chatDisplayNode.collapseInput()
""",
    "scheduled voice final reset"
)

required = [
    "GhostBase v1.0Y repeated scheduled voice reset",
    "self.audioRecorder.set(.single(nil))",
    "self.recorderFeedback = nil",
    "self.chatDisplayNode.updateRecordedMediaDeleted(false)",
    "GhostBase v1.0X scheduled voice immediate success cleanup"
]

for value in required:
    if value not in text:
        raise SystemExit(f"missing generated proof: {value}")

if dry_run:
    print(f"[DRY RUN] would update {path}")
else:
    path.write_text(text, encoding="utf-8")

print("[v1.0Y] repeated scheduled voice anchors OK")
