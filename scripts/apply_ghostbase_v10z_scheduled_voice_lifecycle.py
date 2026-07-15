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
    raise SystemExit(f"missing generated source: {path}")

text = path.read_text(encoding="utf-8")

marker = (
    "// MARK: GhostBase v1.0Z scheduled voice "
    "official lifecycle restore"
)

def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[v1.0Z voice] {message}")

if marker not in text:
    y_preflight = """        // MARK: GhostBase v1.0Y repeated scheduled voice reset
        if existingDraft == nil,
           self.presentationInterfaceState.inputTextPanelState.mediaRecordingState == nil,
           self.presentationInterfaceState.interfaceState.mediaDraftState == nil {
            self.recorderDataDisposable.set(nil)
            self.audioRecorder.set(.single(nil))
            self.recorderFeedback = nil
        }

"""

    require(
        y_preflight in text,
        "v1.0Y recorder preflight block missing"
    )
    text = text.replace(y_preflight, "", 1)

    routing_start_marker = (
        "            // MARK: GhostBase v1.0X "
        "scheduled voice UI routing\n"
    )
    attributes_anchor = (
        "            var attributes: "
        "[EngineMessage.Attribute] = []"
    )

    routing_start = text.find(routing_start_marker)
    require(routing_start >= 0, "v1.0X routing start missing")

    routing_end = text.find(
        attributes_anchor,
        routing_start
    )
    require(routing_end >= 0, "voice attributes anchor missing")

    official_setup = """            // MARK: GhostBase v1.0Z scheduled voice official lifecycle restore
            self.chatDisplayNode.setupSendActionOnViewUpdate({ [weak self] in
                if let strongSelf = self {
                    strongSelf.chatDisplayNode.collapseInput()

                    strongSelf.updateChatPresentationInterfaceState(animated: true, interactive: false, {
                        $0.updatedInterfaceState { $0.withUpdatedReplyMessageSubject(nil).withUpdatedMediaDraftState(nil).withUpdatedSendMessageEffect(nil).withUpdatedPostSuggestionState(nil) }
                    })

                    strongSelf.updateDownButtonVisibility()
                }
            }, nil)

"""

    text = (
        text[:routing_start]
        + official_setup
        + text[routing_end:]
    )

    old_transform = """            let effectiveSilentPosting = silentPosting ?? self.presentationInterfaceState.interfaceState.silentPosting
            let transformedMessages = self.transformEnqueueMessages(messages, silentPosting: effectiveSilentPosting, scheduleTime: scheduleTime, repeatPeriod: repeatPeriod, postpone: postpone)
"""

    new_transform = """            let effectiveSilentPosting = silentPosting ?? self.presentationInterfaceState.interfaceState.silentPosting

            let ghostBaseScheduledVoiceEnabled = (
                UserDefaults.standard.object(
                    forKey: "GhostBase.GhostMode.ScheduledSend"
                ) as? Bool
            ) ?? false

            let ghostBaseEffectiveScheduleTime: Int32?
            if let scheduleTime {
                ghostBaseEffectiveScheduleTime = scheduleTime
            } else if ghostBaseScheduledVoiceEnabled && !isScheduledMessages {
                ghostBaseEffectiveScheduleTime =
                    Int32(Date().timeIntervalSince1970) + 12
            } else {
                ghostBaseEffectiveScheduleTime = nil
            }

            let transformedMessages = self.transformEnqueueMessages(
                messages,
                silentPosting: effectiveSilentPosting,
                scheduleTime: ghostBaseEffectiveScheduleTime,
                repeatPeriod: repeatPeriod,
                postpone: postpone
            )
"""

    require(
        old_transform in text,
        "official transformEnqueueMessages anchor missing"
    )
    text = text.replace(old_transform, new_transform, 1)

    verdict_start_marker = (
        "            // MARK: GhostBase v1.0W "
        "scheduled voice verdict\n"
    )
    peer_guard = """            guard let peerId = self.chatLocation.peerId else {
                return
            }
"""

    verdict_start = text.find(verdict_start_marker)
    require(verdict_start >= 0, "v1.0W verdict block missing")

    verdict_end = text.find(peer_guard, verdict_start)
    require(verdict_end >= 0, "peer guard after verdict missing")

    text = (
        text[:verdict_start]
        + text[verdict_end:]
    )

    cleanup_start_marker = """            if ghostBaseVoiceWasScheduled {
                // MARK: GhostBase v1.0X scheduled voice immediate success cleanup
"""

    donate_anchor = (
        "            donateSendMessageIntent("
        "account: self.context.account"
    )

    cleanup_start = text.find(cleanup_start_marker)
    require(cleanup_start >= 0, "v1.0X cleanup block missing")

    cleanup_end = text.find(donate_anchor, cleanup_start)
    require(cleanup_end >= 0, "donate anchor after cleanup missing")

    text = (
        text[:cleanup_start]
        + text[cleanup_end:]
    )

required = [
    marker,
    "let ghostBaseScheduledVoiceEnabled",
    "let ghostBaseEffectiveScheduleTime: Int32?",
    "scheduleTime: ghostBaseEffectiveScheduleTime",
    "self.chatDisplayNode.setupSendActionOnViewUpdate",
    'forKey: "GhostBase.GhostMode.ScheduledSend"',
]

for value in required:
    require(value in text, f"missing proof: {value}")

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
    require(forbidden not in text, f"legacy voice code remains: {forbidden}")

official_request_prefix = """    func requestAudioRecorder(beginWithTone: Bool, existingDraft: ChatInterfaceMediaDraftState.Audio? = nil) {
        if self.audioRecorderValue == nil {
"""

require(
    official_request_prefix in text,
    "requestAudioRecorder lifecycle was not restored"
)

if dry_run:
    print(f"[DRY RUN] would update {path}")
else:
    path.write_text(text, encoding="utf-8")

print("[v1.0Z] official scheduled voice lifecycle restored")
print("[v1.0Z] GhostBase scheduleTime routed through official transform")
print("[v1.0Z] legacy T/U/W/X/Y voice cleanup removed")
