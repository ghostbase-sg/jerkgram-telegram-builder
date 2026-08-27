#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/TelegramUI/Sources/ChatControllerForwardMessages.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_PROTECTED_FORWARD_LOCAL_COPY1"
OLD_MARKER = "// MARK: Jerkgram v1.2L BUILD123_PORTABLE_FORWARD1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 protected forward] " + message)


HELPERS = r'''// MARK: Jerkgram v1.2M BUILD124_PROTECTED_FORWARD_LOCAL_COPY1
private func jerkgramProtectedForwardResourceData(
    context: AccountContext,
    reference: AnyMediaReference,
    resource: TelegramMediaResource,
    userContentType: MediaResourceUserContentType
) -> Signal<MediaResourceData, NoError> {
    return Signal { subscriber in
        let fetchDisposable = fetchedMediaResource(
            mediaBox: context.account.postbox.mediaBox,
            userLocation: .other,
            userContentType: userContentType,
            reference: reference.resourceReference(resource)
        ).start()
        let dataDisposable = context.account.postbox.mediaBox.resourceData(
            resource,
            option: .complete(waitUntilFetchStatus: true)
        ).start(next: { data in
            if data.complete {
                subscriber.putNext(data)
                subscriber.putCompletion()
            }
        })
        return ActionDisposable {
            fetchDisposable.dispose()
            dataDisposable.dispose()
        }
    }
    |> take(1)
}

private func jerkgramProtectedForwardMediaReference(
    context: AccountContext,
    message: Message
) -> Signal<AnyMediaReference?, NoError> {
    guard let media = message.media.first else {
        return .single(nil)
    }

    if let file = media as? TelegramMediaFile {
        let sourceReference = AnyMediaReference.message(
            message: MessageReference(message),
            media: file
        )
        return jerkgramProtectedForwardResourceData(
            context: context,
            reference: sourceReference,
            resource: file.resource,
            userContentType: MediaResourceUserContentType(file: file)
        )
        |> map { data -> AnyMediaReference? in
            let localId = Int64.random(in: Int64.min ... Int64.max)
            let localResource = LocalFileReferenceMediaResource(
                localFilePath: data.path,
                randomId: localId,
                isUniquelyReferencedTemporaryFile: false,
                size: data.size
            )
            let localFile = TelegramMediaFile(
                fileId: MediaId(namespace: Namespaces.Media.LocalFile, id: localId),
                partialReference: nil,
                resource: localResource,
                previewRepresentations: file.previewRepresentations,
                videoThumbnails: file.videoThumbnails,
                videoCover: file.videoCover,
                immediateThumbnailData: file.immediateThumbnailData,
                mimeType: file.mimeType,
                size: data.size,
                attributes: file.attributes,
                alternativeRepresentations: []
            )
            return AnyMediaReference.standalone(media: localFile)
        }
    } else if let image = media as? TelegramMediaImage, let representation = largestImageRepresentation(image.representations) {
        let sourceReference = AnyMediaReference.message(
            message: MessageReference(message),
            media: image
        )
        return jerkgramProtectedForwardResourceData(
            context: context,
            reference: sourceReference,
            resource: representation.resource,
            userContentType: .image
        )
        |> map { data -> AnyMediaReference? in
            let localId = Int64.random(in: Int64.min ... Int64.max)
            let localResource = LocalFileReferenceMediaResource(
                localFilePath: data.path,
                randomId: localId,
                isUniquelyReferencedTemporaryFile: false,
                size: data.size
            )
            let localRepresentation = TelegramMediaImageRepresentation(
                dimensions: representation.dimensions,
                resource: localResource,
                progressiveSizes: [],
                immediateThumbnailData: nil,
                hasVideo: false,
                isPersonal: false
            )
            let localImage = TelegramMediaImage(
                imageId: MediaId(namespace: Namespaces.Media.LocalImage, id: localId),
                representations: [localRepresentation],
                videoRepresentations: [],
                immediateThumbnailData: image.immediateThumbnailData,
                emojiMarkup: image.emojiMarkup,
                reference: nil,
                partialReference: nil,
                flags: image.flags,
                video: nil
            )
            return AnyMediaReference.standalone(media: localImage)
        }
    } else {
        return .single(AnyMediaReference.standalone(media: media))
    }
}

private func jerkgramPortableForwardMessage(
    context: AccountContext,
    _ message: Message,
    hideAuthor: Bool,
    threadId: Int64?
) -> Signal<EnqueueMessage, NoError> {
    var text = message.text
    var entities = message.textEntitiesAttribute?.entities ?? []

    if !hideAuthor, let author = message.forwardInfo?.author ?? message.effectiveAuthor {
        let sourcePeer = EnginePeer(author)
        let title = sourcePeer.compactDisplayTitle
        if !text.isEmpty {
            text += "\n\n"
        }
        let titleStart = (text as NSString).length
        text += title
        let titleEnd = (text as NSString).length
        if let username = sourcePeer.addressName, !username.isEmpty {
            entities.append(MessageTextEntity(range: titleStart ..< titleEnd, type: .TextUrl(url: "https://t.me/\(username)")))
        }
        entities.append(MessageTextEntity(range: titleStart ..< titleEnd, type: .Bold))
    }

    var attributes: [MessageAttribute] = []
    if !entities.isEmpty {
        attributes.append(TextEntitiesMessageAttribute(entities: entities))
    }

    return jerkgramProtectedForwardMediaReference(context: context, message: message)
    |> map { mediaReference -> EnqueueMessage in
        return .message(
            text: text,
            attributes: attributes,
            inlineStickers: [:],
            mediaReference: mediaReference,
            threadId: threadId,
            replyToMessageId: nil,
            replyToStoryId: nil,
            localGroupingKey: nil,
            correlationId: nil,
            bubbleUpEmojiOrStickersets: []
        )
    }
}

'''

OLD_PORTABLE_BRANCH = r'''                        let hideAuthor = forwardOptions?.hideNames == true
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
'''

NEW_PORTABLE_BRANCH = r'''                        var jerkgramPortableMessagesSignal: Signal<[EnqueueMessage], NoError>?
                        let hideAuthor = forwardOptions?.hideNames == true
                        let canUsePortableCopy = messages.allSatisfy { message in
                            message.id.peerId.namespace != Namespaces.Peer.SecretChat
                        }
                        if canUsePortableCopy && (hideAuthor || messages.contains(where: { $0.isCopyProtected() })) {
                            jerkgramPortableMessagesSignal = combineLatest(messages.map { message in
                                jerkgramPortableForwardMessage(
                                    context: strongSelf.context,
                                    message,
                                    hideAuthor: hideAuthor,
                                    threadId: strongSelf.chatLocation.threadId
                                )
                            })
                        } else {
                            result.append(contentsOf: messages.map { message -> EnqueueMessage in
                                return .forward(source: message.id, threadId: nil, grouping: .auto, attributes: attributes, correlationId: nil)
                            })
                        }
'''

OLD_MODE_SWITCH = r'''                        switch mode {
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
'''

NEW_MODE_SWITCH = r'''                        let commitResolved: ([EnqueueMessage]) -> Void = { resolvedResult in
                            switch mode {
                            case .generic:
                                commit(resolvedResult)
                            case .silent:
                                let transformedMessages = strongSelf.transformEnqueueMessages(resolvedResult, silentPosting: true)
                                commit(transformedMessages)
                            case .schedule:
                                strongSelf.presentScheduleTimePicker(completion: { [weak self] timeResult in
                                    if let strongSelf = self {
                                        let transformedMessages = strongSelf.transformEnqueueMessages(resolvedResult, silentPosting: timeResult.silentPosting, scheduleTime: timeResult.time, repeatPeriod: timeResult.repeatPeriod)
                                        commit(transformedMessages)
                                    }
                                })
                            case .whenOnline:
                                let transformedMessages = strongSelf.transformEnqueueMessages(resolvedResult, silentPosting: strongSelf.presentationInterfaceState.interfaceState.silentPosting, scheduleTime: scheduleWhenOnlineTimestamp)
                                commit(transformedMessages)
                            }
                        }

                        if let jerkgramPortableMessagesSignal {
                            let baseResult = result
                            let _ = (jerkgramPortableMessagesSignal
                            |> deliverOnMainQueue).startStandalone(next: { portableMessages in
                                commitResolved(baseResult + portableMessages)
                            })
                        } else {
                            commitResolved(result)
                        }
'''


def patch_text(text: str) -> str:
    if MARKER in text:
        return text

    require(OLD_MARKER in text, "Build123 portable-forward marker missing")
    require(text.count("extension ChatControllerImpl {") >= 1, "ChatControllerImpl extension missing")
    helper_start = text.index(OLD_MARKER)
    extension_start = text.index("extension ChatControllerImpl {", helper_start)
    old_helper = text[helper_start:extension_start]
    require("private func jerkgramPortableForwardMessage(" in old_helper, "Build123 portable helper missing")
    require("let mediaReference = message.media.first.map { AnyMediaReference.standalone(media: $0) }" in old_helper, "Build123 original-cloud media owner missing")

    if "import Postbox\n" not in text:
        require("import Foundation\n" in text, "Foundation import missing")
        text = text.replace("import Foundation\n", "import Foundation\nimport Postbox\n", 1)
        helper_start = text.index(OLD_MARKER)
        extension_start = text.index("extension ChatControllerImpl {", helper_start)
        old_helper = text[helper_start:extension_start]

    text = text[:helper_start] + HELPERS + text[extension_start:]

    require(text.count(OLD_PORTABLE_BRANCH) == 1, f"expected one Build123 portable branch, found {text.count(OLD_PORTABLE_BRANCH)}")
    text = text.replace(OLD_PORTABLE_BRANCH, NEW_PORTABLE_BRANCH, 1)

    require(text.count(OLD_MODE_SWITCH) == 1, f"expected one forwarding mode switch, found {text.count(OLD_MODE_SWITCH)}")
    text = text.replace(OLD_MODE_SWITCH, NEW_MODE_SWITCH, 1)

    require(MARKER in text, "Build124 marker was not installed")
    require("message.forwardInfo?.author ?? message.effectiveAuthor" in text, "correct author semantics missing")
    require("LocalFileReferenceMediaResource" in text, "fresh local resource missing")
    require("jerkgramPortableMessagesSignal" in text, "async portable forwarding missing")
    return text


def main() -> None:
    require(TARGET.is_file(), f"target missing: {TARGET}")
    original = TARGET.read_text(encoding="utf-8")
    updated = patch_text(original)
    TARGET.write_text(updated, encoding="utf-8")
    print("[Build124 protected forward] GREEN")
    print("[Build124 protected forward] protected file/photo forwards are fetched and re-enqueued as fresh local uploads")


if __name__ == "__main__":
    main()
