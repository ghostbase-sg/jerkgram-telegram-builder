#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "work/swiftgram-src/submodules/TelegramUI/Sources/Chat/ChatControllerMediaRecording.swift"

text = path.read_text()

old = """            let _ = (enqueueMessages(account: self.context.account, peerId: peerId, messages: transformedMessages)
            |> deliverOnMainQueue).startStandalone(next: { [weak self] _ in
                if let strongSelf = self, strongSelf.presentationInterfaceState.subject != .scheduledMessages {
                    strongSelf.chatDisplayNode.historyNode.scrollToEndOfHistory()
                }
            })

            if ghostBaseVoiceWasScheduled {
"""

new = """            let _ = (enqueueMessages(account: self.context.account, peerId: peerId, messages: transformedMessages)
            |> deliverOnMainQueue).startStandalone(next: { [weak self] _ in
                guard let strongSelf = self else {
                    return
                }

                if strongSelf.presentationInterfaceState.subject != .scheduledMessages {
                    strongSelf.chatDisplayNode.historyNode.scrollToEndOfHistory()
                }

                if ghostBaseVoiceWasScheduled {
                    // MARK: GhostBase v1.0V scheduled voice native cleanup
                    strongSelf.deleteMediaRecording()
                    strongSelf.chatDisplayNode.collapseInput()

                    strongSelf.updateChatPresentationInterfaceState(
                        animated: true,
                        interactive: false,
                        {
                            $0.updatedInterfaceState {
                                $0.withUpdatedReplyMessageSubject(nil)
                                    .withUpdatedSendMessageEffect(nil)
                                    .withUpdatedPostSuggestionState(nil)
                            }.updatedInputTextPanelState { panelState in
                                panelState.withUpdatedMediaRecordingState(nil)
                            }
                        }
                    )
                }
            })

            if ghostBaseVoiceWasScheduled {
"""

if "GhostBase v1.0V scheduled voice native cleanup" in text:
    print("[v1.0V voice] already applied")
elif old not in text:
    raise RuntimeError("[v1.0V voice] enqueue anchor missing")
else:
    path.write_text(text.replace(old, new, 1))
    print("[v1.0V voice] native cleanup applied")

text = path.read_text()

import re

pattern = re.compile(
    r'\n[ \t]*if ghostBaseVoiceWasScheduled \{\n'
    r'[ \t]*// MARK: GhostBase v1\.0U scheduled voice complete cleanup'
    r'.*?'
    r'\n[ \t]*\}\n'
    r'(?=\n[ \t]*donateSendMessageIntent)',
    re.S
)

text, count = pattern.subn("\n", text, count=1)

if count != 0:
    path.write_text(text)
    print("[v1.0V voice] old premature cleanup removed")
else:
    print("[v1.0V voice] old cleanup already absent")
