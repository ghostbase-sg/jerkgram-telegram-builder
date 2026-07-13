#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / (
    "work/swiftgram-src/submodules/TelegramUI/Sources/Chat/"
    "ChatControllerMediaRecording.swift"
)

text = path.read_text()
marker = "GhostBase v1.0V scheduled voice native cleanup"

if marker in text:
    print("[v1.0V voice] already applied")
else:
    pattern = re.compile(
        r'''(?P<start>
            let\ _\ =\ \(enqueueMessages\(
            account:\ self\.context\.account,\ 
            peerId:\ peerId,\ 
            messages:\ transformedMessages
            \)
            \n[ \t]*\|>\ deliverOnMainQueue
            \)\.startStandalone\(next:\ \{\ \[weak\ self\]\ _\ in
        )
        .*?
        (?P<end>
            \n[ \t]*\}\)
        )
        ''',
        re.X | re.S
    )

    match = pattern.search(text)
    if match is None:
        raise RuntimeError(
            "[v1.0V voice] enqueue callback not found"
        )

    replacement = match.group("start") + '''
                guard let strongSelf = self else {
                    return
                }

                if strongSelf.presentationInterfaceState.subject != .scheduledMessages {
                    strongSelf.chatDisplayNode.historyNode.scrollToEndOfHistory()
                }

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
                }''' + match.group("end")

    text = (
        text[:match.start()]
        + replacement
        + text[match.end():]
    )

    path.write_text(text)
    print("[v1.0V voice] native cleanup applied")

text = path.read_text()

old_cleanup = re.compile(
    r'''
    \n[ \t]*if\ ghostBaseVoiceWasScheduled\ \{
    \n[ \t]*//\ MARK:\ GhostBase\ v1\.0U
    \ scheduled\ voice\ complete\ cleanup
    .*?
    \n[ \t]*\}
    (?=\n[ \t]*donateSendMessageIntent)
    ''',
    re.X | re.S
)

text, count = old_cleanup.subn("\n", text, count=1)

if count:
    path.write_text(text)
    print("[v1.0V voice] old premature cleanup removed")
else:
    print("[v1.0V voice] old premature cleanup absent")
