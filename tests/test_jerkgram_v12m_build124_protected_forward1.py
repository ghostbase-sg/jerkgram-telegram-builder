from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts/apply_jerkgram_v12m_build124_protected_forward1.py"


class Build124ProtectedForwardTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_protected_forward", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self) -> str:
        return '''// MARK: Jerkgram v1.2L BUILD123_PORTABLE_FORWARD1
private func jerkgramPortableForwardMessage(
    _ message: Message,
    hideAuthor: Bool,
    threadId: Int64?
) -> EnqueueMessage {
    var text = message.text
    var entities = message.textEntitiesAttribute?.entities ?? []

    if !hideAuthor, let sourcePeer = message.peers[message.id.peerId].map(EnginePeer.init) {
        let title = sourcePeer.compactDisplayTitle
        if !text.isEmpty {
            text += "\\n\\n"
        }
        let titleStart = (text as NSString).length
        text += title
        let titleEnd = (text as NSString).length
        if let username = sourcePeer.addressName, !username.isEmpty {
            entities.append(MessageTextEntity(range: titleStart ..< titleEnd, type: .TextUrl(url: "https://t.me/\\(username)")))
        }
        entities.append(MessageTextEntity(range: titleStart ..< titleEnd, type: .Bold))
    }

    var attributes: [MessageAttribute] = []
    if !entities.isEmpty {
        attributes.append(TextEntitiesMessageAttribute(entities: entities))
    }
    let mediaReference = message.media.first.map { AnyMediaReference.standalone(media: $0) }
    return .message(text: text, attributes: attributes, inlineStickers: [:], mediaReference: mediaReference, threadId: threadId, replyToMessageId: nil, replyToStoryId: nil, localGroupingKey: nil, correlationId: nil, bubbleUpEmojiOrStickersets: [])
}

extension ChatControllerImpl {
    func demo(messages: [Message], mode: ForwardMode) {
        var result: [EnqueueMessage] = []
        let hideAuthor = forwardOptions?.hideNames == true
        let canUsePortableCopy = messages.allSatisfy { message in
            message.id.peerId.namespace != Namespaces.Peer.SecretChat
        }
        if canUsePortableCopy && (hideAuthor || messages.contains(where: { $0.isCopyProtected() })) {
            result.append(contentsOf: messages.map { message in
                jerkgramPortableForwardMessage(message, hideAuthor: hideAuthor, threadId: strongSelf.chatLocation.threadId)
            })
        } else {
            result.append(contentsOf: messages.map { message -> EnqueueMessage in
                return .forward(source: message.id, threadId: nil, grouping: .auto, attributes: attributes, correlationId: nil)
            })
        }

        let commit: ([EnqueueMessage]) -> Void = { result in
            consume(result)
        }

        switch mode {
        case .generic:
            commit(result)
        case .silent:
            let transformedMessages = strongSelf.transformEnqueueMessages(result, silentPosting: true)
            commit(transformedMessages)
        case .schedule:
            strongSelf.presentScheduleTimePicker(completion: { [weak self] timeResult in
                if let strongSelf = self {
                    let transformedMessages = strongSelf.transformEnqueueMessages(result, silentPosting: timeResult.silentPosting, scheduleTime: timeResult.time, repeatPeriod: timeResult.repeatPeriod)
                    commit(transformedMessages)
                }
            })
        case .whenOnline:
            let transformedMessages = strongSelf.transformEnqueueMessages(result, silentPosting: strongSelf.presentationInterfaceState.interfaceState.silentPosting, scheduleTime: scheduleWhenOnlineTimestamp)
            commit(transformedMessages)
        }
    }
}
'''

    def test_protected_media_becomes_fresh_local_upload(self):
        module = self.load_patch()
        result = module.patch_text(self.fixture())
        self.assertIn("BUILD124_PROTECTED_FORWARD_LOCAL_COPY1", result)
        self.assertIn("LocalFileReferenceMediaResource", result)
        self.assertIn("Namespaces.Media.LocalFile", result)
        self.assertIn("Namespaces.Media.LocalImage", result)
        self.assertIn("context.engine.resources.fetch", result)
        self.assertIn("waitUntilFetchStatus: true", result)
        self.assertNotIn("let mediaReference = message.media.first.map { AnyMediaReference.standalone(media: $0) }", result)

    def test_channel_author_uses_telegram_author_semantics(self):
        module = self.load_patch()
        result = module.patch_text(self.fixture())
        self.assertIn("message.forwardInfo?.author ?? message.effectiveAuthor", result)
        self.assertNotIn("message.peers[message.id.peerId].map(EnginePeer.init)", result)
        self.assertIn('https://t.me/\\(username)', result)

    def test_hide_author_path_still_omits_attribution(self):
        module = self.load_patch()
        result = module.patch_text(self.fixture())
        self.assertIn("if !hideAuthor, let author = message.forwardInfo?.author ?? message.effectiveAuthor", result)

    def test_portable_copy_waits_for_media_before_commit(self):
        module = self.load_patch()
        result = module.patch_text(self.fixture())
        self.assertIn("var jerkgramPortableMessagesSignal: Signal<[EnqueueMessage], NoError>?", result)
        self.assertIn("combineLatest(messages.map", result)
        self.assertIn("context: strongSelf.context", result)
        self.assertIn("let commitResolved", result)
        self.assertIn("if let jerkgramPortableMessagesSignal", result)
        self.assertIn("deliverOnMainQueue", result)
        self.assertLess(result.index("jerkgramPortableMessagesSignal"), result.index("let commitResolved"))

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_text(self.fixture())
        self.assertEqual(once, module.patch_text(once))
        self.assertEqual(once.count("BUILD124_PROTECTED_FORWARD_LOCAL_COPY1"), 1)


if __name__ == "__main__":
    unittest.main()
