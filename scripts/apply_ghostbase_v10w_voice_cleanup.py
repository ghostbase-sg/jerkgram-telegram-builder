#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / (
    "work/swiftgram-src/submodules/TelegramUI/Sources/Chat/"
    "ChatControllerMediaRecording.swift"
)

text = FILE.read_text()
marker = "GhostBase v1.0W scheduled voice post-enqueue cleanup"

if marker in text:
    print("[v1.0W voice] already applied")
    raise SystemExit

anchor = '''            guard let peerId = self.chatLocation.peerId else {
                return
            }
'''

insert = '''            // MARK: GhostBase v1.0W scheduled voice verdict
            let ghostBaseVoiceWasScheduled = transformedMessages.contains { message in
                switch message {
                case let .message(_, attributes, _, _, _, _, _, _, _, _):
                    return attributes.contains {
                        $0 is OutgoingScheduleInfoMessageAttribute
                    }
                case .forward:
                    return false
                }
            }

            guard let peerId = self.chatLocation.peerId else {
                return
            }
'''

if anchor not in text:
    raise RuntimeError("[v1.0W voice] peerId anchor missing")

text = text.replace(anchor, insert, 1)

old_callback = '''            let _ = (enqueueMessages(account: self.context.account, peerId: peerId, messages: transformedMessages)
            |> deliverOnMainQueue).startStandalone(next: { [weak self] _ in
                if let strongSelf = self, strongSelf.presentationInterfaceState.subject != .scheduledMessages {
                    strongSelf.chatDisplayNode.historyNode.scrollToEndOfHistory()
                }
            })
'''

new_callback = '''            let _ = (enqueueMessages(account: self.context.account, peerId: peerId, messages: transformedMessages)
            |> deliverOnMainQueue).startStandalone(next: { [weak self] _ in
                guard let strongSelf = self else {
                    return
                }

                if strongSelf.presentationInterfaceState.subject != .scheduledMessages {
                    strongSelf.chatDisplayNode.historyNode.scrollToEndOfHistory()
                }

                if ghostBaseVoiceWasScheduled {
                    // MARK: GhostBase v1.0W scheduled voice post-enqueue cleanup
                    strongSelf.audioRecorderStatusDisposable?.dispose()
                    strongSelf.audioRecorderStatusDisposable = nil

                    strongSelf.deleteMediaRecording()
                    strongSelf.chatDisplayNode.collapseInput()

                    strongSelf.updateChatPresentationInterfaceState(
                        animated: true,
                        interactive: false,
                        {
                            $0.updatedInterfaceState {
                                $0.withUpdatedReplyMessageSubject(nil)
                                    .withUpdatedMediaDraftState(nil)
                                    .withUpdatedSendMessageEffect(nil)
                                    .withUpdatedPostSuggestionState(nil)
                            }.updatedInputTextPanelState { panelState in
                                panelState.withUpdatedMediaRecordingState(nil)
                            }
                        }
                    )
                }
            })
'''

if old_callback not in text:
    raise RuntimeError("[v1.0W voice] enqueue callback anchor missing")

text = text.replace(old_callback, new_callback, 1)

pattern = re.compile(
    r'\n[ \t]*if ghostBaseRuntimeScheduledVoice \{\n'
    r'[ \t]*// MARK: GhostBase v1\.0U scheduled voice complete cleanup'
    r'.*?'
    r'\n[ \t]*\}\n'
    r'(?=\n[ \t]*donateSendMessageIntent)',
    re.S
)

text, count = pattern.subn("\n", text, count=1)

if count != 1:
    raise RuntimeError("[v1.0W voice] old v1.0U cleanup block missing")

FILE.write_text(text)
print("[v1.0W voice] post-enqueue native cleanup applied")
