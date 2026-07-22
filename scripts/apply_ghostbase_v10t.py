#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"

MEDIA = (
    SRC
    / "submodules/TelegramUI/Sources/Chat"
    / "ChatControllerMediaRecording.swift"
)

def require(condition, message):
    if not condition:
        raise RuntimeError(f"[v1.0T] {message}")

def replace_once(text, old, new, label):
    require(old in text, f"missing anchor: {label}")
    return text.replace(old, new, 1)

require(MEDIA.is_file(), f"missing source: {MEDIA}")
media = MEDIA.read_text(encoding="utf-8")

marker = "GhostBase v1.0T scheduled voice UI cleanup"

if marker not in media:
    old = '''            self.chatDisplayNode.setupSendActionOnViewUpdate({ [weak self] in
                if let strongSelf = self {
                    strongSelf.chatDisplayNode.collapseInput()

                    strongSelf.updateChatPresentationInterfaceState(animated: true, interactive: false, {
                        $0.updatedInterfaceState { $0.withUpdatedReplyMessageSubject(nil).withUpdatedMediaDraftState(nil).withUpdatedSendMessageEffect(nil).withUpdatedPostSuggestionState(nil) }
                    })

                    strongSelf.updateDownButtonVisibility()
                }
            }, nil)
'''

    new = '''            // MARK: GhostBase v1.0T scheduled voice UI cleanup
            let ghostBaseRuntimeScheduledVoice = ((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false) && scheduleTime == nil && !isScheduledMessages

            if !ghostBaseRuntimeScheduledVoice {
                self.chatDisplayNode.setupSendActionOnViewUpdate({ [weak self] in
                    if let strongSelf = self {
                        strongSelf.chatDisplayNode.collapseInput()

                        strongSelf.updateChatPresentationInterfaceState(animated: true, interactive: false, {
                            $0.updatedInterfaceState { $0.withUpdatedReplyMessageSubject(nil).withUpdatedMediaDraftState(nil).withUpdatedSendMessageEffect(nil).withUpdatedPostSuggestionState(nil) }
                        })

                        strongSelf.updateDownButtonVisibility()
                    }
                }, nil)
            }
'''

    media = replace_once(
        media,
        old,
        new,
        "voice send-action transition"
    )

    old = '''            let _ = (enqueueMessages(account: self.context.account, peerId: peerId, messages: transformedMessages)
            |> deliverOnMainQueue).startStandalone(next: { [weak self] _ in
                if let strongSelf = self, strongSelf.presentationInterfaceState.subject != .scheduledMessages {
                    strongSelf.chatDisplayNode.historyNode.scrollToEndOfHistory()
                }
            })

            donateSendMessageIntent(account: self.context.account, sharedContext: self.context.sharedContext, intentContext: .chat, peerIds: [peerId])
'''

    new = '''            let _ = (enqueueMessages(account: self.context.account, peerId: peerId, messages: transformedMessages)
            |> deliverOnMainQueue).startStandalone(next: { [weak self] _ in
                if let strongSelf = self, strongSelf.presentationInterfaceState.subject != .scheduledMessages {
                    strongSelf.chatDisplayNode.historyNode.scrollToEndOfHistory()
                }
            })

            if ghostBaseRuntimeScheduledVoice {
                self.chatDisplayNode.collapseInput()

                self.updateChatPresentationInterfaceState(animated: true, interactive: false, {
                    $0.updatedInterfaceState {
                        $0.withUpdatedReplyMessageSubject(nil)
                            .withUpdatedMediaDraftState(nil)
                            .withUpdatedSendMessageEffect(nil)
                            .withUpdatedPostSuggestionState(nil)
                    }
                })

                self.updateDownButtonVisibility()

                UserDefaults.standard.set(
                    UserDefaults.standard.integer(
                        forKey: "GhostBase.V10T.VoiceScheduledUICleanup.Count"
                    ) + 1,
                    forKey: "GhostBase.V10T.VoiceScheduledUICleanup.Count"
                )
            }

            donateSendMessageIntent(account: self.context.account, sharedContext: self.context.sharedContext, intentContext: .chat, peerIds: [peerId])
'''

    media = replace_once(
        media,
        old,
        new,
        "voice cleanup after enqueue"
    )

MEDIA.write_text(media, encoding="utf-8")

require(
    marker in media,
    "voice cleanup marker missing"
)

print("[v1.0T] scheduled voice UI cleanup applied")

CHAT_LIST_STRINGS = (
    SRC
    / "submodules/ChatListUI/Sources/Node"
    / "ChatListItemStrings.swift"
)

require(
    CHAT_LIST_STRINGS.is_file(),
    f"missing source: {CHAT_LIST_STRINGS}"
)

chat_list_strings = CHAT_LIST_STRINGS.read_text(
    encoding="utf-8"
)

chat_list_marker = (
    "GhostBase v1.0T deleted chat-list preview filter"
)

if chat_list_marker not in chat_list_strings:
    chat_list_strings = replace_once(
        chat_list_strings,
        '''public func chatListItemStrings(strings: PresentationStrings, nameDisplayOrder: PresentationPersonNameOrder, dateTimeFormat: PresentationDateTimeFormat, contentSettings: ContentSettings, messages: [EngineMessage], chatPeer: EngineRenderedPeer, accountPeerId: EnginePeer.Id, enableMediaEmoji: Bool = true, isPeerGroup: Bool = false) -> (peer: EnginePeer?, hideAuthor: Bool, messageText: String, messageEntities: [MessageTextEntity], spoilers: [NSRange]?, customEmojiRanges: [(NSRange, ChatTextInputTextCustomEmojiAttribute)]?, richTextPreview: NSAttributedString?) {
    let peer: EnginePeer?
    
    let message = messages.last
''',
        '''public func chatListItemStrings(strings: PresentationStrings, nameDisplayOrder: PresentationPersonNameOrder, dateTimeFormat: PresentationDateTimeFormat, contentSettings: ContentSettings, messages originalMessages: [EngineMessage], chatPeer: EngineRenderedPeer, accountPeerId: EnginePeer.Id, enableMediaEmoji: Bool = true, isPeerGroup: Bool = false) -> (peer: EnginePeer?, hideAuthor: Bool, messageText: String, messageEntities: [MessageTextEntity], spoilers: [NSRange]?, customEmojiRanges: [(NSRange, ChatTextInputTextCustomEmojiAttribute)]?, richTextPreview: NSAttributedString?) {
    let peer: EnginePeer?

    // MARK: GhostBase v1.0T deleted chat-list preview filter
    let ghostBaseShowDeleted = ((UserDefaults.standard.object(
        forKey: "GhostBase.Messages.ShowDeleted"
    ) as? Bool) ?? true)

    let messages: [EngineMessage]
    if ghostBaseShowDeleted {
        messages = originalMessages
    } else {
        messages = originalMessages.filter { message in
            let ghostBaseAttribute = message._asMessage().attributes.first(
                where: { $0 is GhostBaseMessageAttribute }
            ) as? GhostBaseMessageAttribute

            return !(ghostBaseAttribute?.isDeleted ?? false)
        }
    }

    let message = messages.last
''',
        "chat-list filtered messages"
    )

CHAT_LIST_STRINGS.write_text(
    chat_list_strings,
    encoding="utf-8"
)

require(
    chat_list_marker in chat_list_strings,
    "chat-list filter marker missing"
)

print("[v1.0T] deleted chat-list preview filter applied")
