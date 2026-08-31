#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
FORWARD = ROOT / "submodules/TelegramUI/Sources/ChatControllerForwardMessages.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_PROTECTED_FORWARD_LOCAL_COPY1"
SOURCE_PROTECTION_MARKER = "// MARK: Jerkgram v1.2M BUILD124_PROTECTED_FORWARD_SOURCE_CHANNEL1"
OLD_MARKER = "// MARK: Jerkgram v1.2L BUILD123_PORTABLE_FORWARD1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 protected forward] " + message)


def balanced_region(text: str, token: str) -> tuple[int, int]:
    start = text.find(token)
    require(start >= 0, f"token missing: {token}")
    brace = text.find("{", start + len(token))
    require(brace >= 0, f"opening brace missing: {token}")
    depth = 0
    in_string = False
    escaped = False
    i = brace
    while i < len(text):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1
    raise RuntimeError("[Build124 protected forward] unbalanced Swift region")


HELPER = r'''// MARK: Jerkgram v1.2M BUILD124_PROTECTED_FORWARD_LOCAL_COPY1
// MARK: Jerkgram v1.2M BUILD124_PROTECTED_FORWARD_SOURCE_CHANNEL1
private func jerkgramRequiresPortableForward(_ message: Message) -> Bool {
    if message.isCopyProtected() {
        return true
    }
    // A channel can send into a discussion/group as its author. In that form
    // Message.isCopyProtected() sees the destination peer, while the actual
    // copy restriction belongs to the channel author/source.
    if let sourcePeer = message.forwardInfo?.author ?? message.effectiveAuthor {
        return sourcePeer.isCopyProtectionEnabled
    }
    return false
}

private func jerkgramPortableForwardBaseMessage(
    _ message: Message,
    hideAuthor: Bool,
    threadId: Int64?,
    mediaReference: AnyMediaReference?
) -> EnqueueMessage {
    var text = message.text
    var entities = message.textEntitiesAttribute?.entities ?? []

    // Telegram's own forwarding UI resolves attribution from forwardInfo first
    // and then effectiveAuthor. For channel-authored posts the chat peer itself
    // is not necessarily the author we need to reproduce.
    if !hideAuthor, let author = message.forwardInfo?.author ?? message.effectiveAuthor ?? message.peers[message.id.peerId] {
        let sourcePeer = EnginePeer(author)
        let title = sourcePeer.compactDisplayTitle
        if !title.isEmpty {
            let prefix = text.isEmpty ? "" : "\n\n"
            let start = (text as NSString).length + (prefix as NSString).length
            text += prefix + "— " + title
            let titleStart = start + 2
            let titleEnd = titleStart + (title as NSString).length
            if let username = sourcePeer.addressName, !username.isEmpty {
                entities.append(MessageTextEntity(
                    range: titleStart ..< titleEnd,
                    type: .TextUrl(url: "https://t.me/\(username)")
                ))
            }
            entities.append(MessageTextEntity(range: titleStart ..< titleEnd, type: .Bold))
        }
    }

    var attributes: [MessageAttribute] = []
    if !entities.isEmpty {
        attributes.append(TextEntitiesMessageAttribute(entities: entities))
    }
    let embeddedFiles = (
        message.attributes.first(where: { $0 is EmbeddedMediaStickersMessageAttribute })
        as? EmbeddedMediaStickersMessageAttribute
    )?.files ?? []
    var inlineStickers: [MediaId: Media] = [:]
    for file in embeddedFiles {
        inlineStickers[file.fileId] = file
    }

    return .message(
        text: text,
        attributes: attributes,
        inlineStickers: inlineStickers,
        mediaReference: mediaReference,
        threadId: threadId,
        replyToMessageId: nil,
        replyToStoryId: nil,
        localGroupingKey: message.groupingKey,
        correlationId: nil,
        bubbleUpEmojiOrStickersets: []
    )
}

private func jerkgramProtectedResourceData(
    context: AccountContext,
    message: Message,
    mediaReference: AnyMediaReference,
    resource: TelegramMediaResource,
    userContentType: MediaResourceUserContentType,
    pathExtension: String?
) -> Signal<EngineMediaResource.ResourceData, NoError> {
    // Use the same public EngineResources fetch/data pair as Official Telegram's
    // SaveToCameraRoll path. The cloud reference stays alive only while fetching;
    // the outgoing message is created after a completed local path exists.
    return Signal { subscriber in
        let fetchDisposable = context.engine.resources.fetch(
            reference: mediaReference.resourceReference(resource),
            userLocation: .peer(message.id.peerId),
            userContentType: userContentType
        ).start()
        let dataDisposable = context.engine.resources.data(
            resource: EngineMediaResource(resource),
            pathExtension: pathExtension,
            waitUntilFetchStatus: true
        ).start(next: { data in
            if data.isComplete {
                subscriber.putNext(data)
                subscriber.putCompletion()
            }
        }, completed: {
            subscriber.putCompletion()
        })
        return ActionDisposable {
            fetchDisposable.dispose()
            dataDisposable.dispose()
        }
    }
    |> take(1)
}

private func jerkgramPortableForwardMessage(
    _ message: Message,
    hideAuthor: Bool,
    threadId: Int64?,
    context: AccountContext
) -> Signal<EnqueueMessage, NoError> {
    guard jerkgramRequiresPortableForward(message), let media = message.media.first else {
        let reference = message.media.first.map { AnyMediaReference.standalone(media: $0) }
        return .single(jerkgramPortableForwardBaseMessage(
            message,
            hideAuthor: hideAuthor,
            threadId: threadId,
            mediaReference: reference
        ))
    }

    if let file = media as? TelegramMediaFile {
        let sourceReference = AnyMediaReference.message(
            message: MessageReference(message),
            media: file
        )
        let pathExtension: String?
        if let fileName = file.fileName {
            let ext = (fileName as NSString).pathExtension
            pathExtension = ext.isEmpty ? nil : ext
        } else {
            pathExtension = nil
        }
        return jerkgramProtectedResourceData(
            context: context,
            message: message,
            mediaReference: sourceReference,
            resource: file.resource,
            userContentType: MediaResourceUserContentType(file: file),
            pathExtension: pathExtension
        )
        |> map { data -> EnqueueMessage in
            let localId = Int64.random(in: Int64.min ... Int64.max)
            let localResource = LocalFileReferenceMediaResource(
                localFilePath: data.path,
                randomId: localId
            )
            // Do not retain protected cloud thumbnail/alternative resources in
            // the outgoing file. Dimensions/duration/voice/video semantics live
            // in attributes and are preserved; Telegram regenerates upload media.
            let localFile = TelegramMediaFile(
                fileId: MediaId(namespace: Namespaces.Media.LocalFile, id: localId),
                partialReference: nil,
                resource: localResource,
                previewRepresentations: [],
                videoThumbnails: [],
                videoCover: nil,
                immediateThumbnailData: file.immediateThumbnailData,
                mimeType: file.mimeType,
                size: file.size,
                attributes: file.attributes,
                alternativeRepresentations: []
            )
            return jerkgramPortableForwardBaseMessage(
                message,
                hideAuthor: hideAuthor,
                threadId: threadId,
                mediaReference: .standalone(media: localFile)
            )
        }
    } else if let image = media as? TelegramMediaImage,
              let representation = largestImageRepresentation(image.representations) {
        let sourceReference = AnyMediaReference.message(
            message: MessageReference(message),
            media: image
        )
        return jerkgramProtectedResourceData(
            context: context,
            message: message,
            mediaReference: sourceReference,
            resource: representation.resource,
            userContentType: .image,
            pathExtension: "jpg"
        )
        |> map { data -> EnqueueMessage in
            let localId = Int64.random(in: Int64.min ... Int64.max)
            let localResource = LocalFileReferenceMediaResource(
                localFilePath: data.path,
                randomId: localId
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
                immediateThumbnailData: image.immediateThumbnailData,
                reference: nil,
                partialReference: nil,
                flags: image.flags
            )
            return jerkgramPortableForwardBaseMessage(
                message,
                hideAuthor: hideAuthor,
                threadId: threadId,
                mediaReference: .standalone(media: localImage)
            )
        }
    } else {
        // The red-failure regression is the protected upload-media path. Keep
        // existing portable semantics for non-upload message media.
        return .single(jerkgramPortableForwardBaseMessage(
            message,
            hideAuthor: hideAuthor,
            threadId: threadId,
            mediaReference: .standalone(media: media)
        ))
    }
}
'''


def replace_helper(text: str) -> str:
    token = "private func jerkgramPortableForwardMessage("
    require(text.count(token) == 1, f"portable helper owner count is {text.count(token)}")
    start, end = balanced_region(text, token)
    for marker in (MARKER, OLD_MARKER):
        marker_start = text.rfind(marker, 0, start)
        if marker_start >= 0:
            start = marker_start
            break
    return text[:start] + HELPER + text[end:]


def patch_portable_secret_chat_guard(text: str) -> str:
    guard = "message.id.peerId.namespace != Namespaces.Peer.SecretChat"
    if guard in text:
        return text

    anchor = "let canUsePortableCopy = messages.allSatisfy { message in\n"
    require(text.count(anchor) == 1, f"portable-copy gate count is {text.count(anchor)}")
    body_start = text.index(anchor) + len(anchor)
    body_content = body_start
    while body_content < len(text) and text[body_content] in " \t":
        body_content += 1
    require(body_content > body_start, "portable-copy gate body indentation missing")
    indent = text[body_start:body_content]
    return (
        text[:body_start]
        + indent + guard + "\n"
        + indent + "&& "
        + text[body_content:]
    )


def patch_portable_branch(text: str) -> str:
    variable_anchor = "var result: [EnqueueMessage] = []"
    require(text.count(variable_anchor) >= 1, "forward result owner missing")
    text = text.replace(
        variable_anchor,
        variable_anchor + "\n                        var jerkgramPortableMessagesSignal: Signal<[EnqueueMessage], NoError>?",
        1,
    )

    old_actual = '''result.append(contentsOf: messages.map {
                                jerkgramPortableForwardMessage($0, hideAuthor: hideAuthor, threadId: strongSelf.chatLocation.threadId)
                            })'''
    old_fixture = '''result.append(contentsOf: messages.map { message in
                jerkgramPortableForwardMessage(message, hideAuthor: hideAuthor, threadId: strongSelf.chatLocation.threadId)
            })'''
    if old_actual in text:
        old = old_actual
        indent = "                            "
    elif old_fixture in text:
        old = old_fixture
        indent = "            "
    else:
        raise RuntimeError("[Build124 protected forward] portable append branch missing")

    new = '''let jerkgramPrefixMessages = result
{indent}jerkgramPortableMessagesSignal = combineLatest(messages.map {{ message in
{indent}    jerkgramPortableForwardMessage(
{indent}        message,
{indent}        hideAuthor: hideAuthor,
{indent}        threadId: strongSelf.chatLocation.threadId,
{indent}        context: strongSelf.context
{indent}    )
{indent}}})
{indent}|> map {{ portableMessages in
{indent}    jerkgramPrefixMessages + portableMessages
{indent}}}'''.format(indent=indent)
    return text.replace(old, new, 1)


def patch_commit_resolution(text: str) -> str:
    # balanced_region searches for the opening brace after the token. Keep the
    # brace out of the token so it owns the switch, not the nested schedule closure.
    token = "switch mode"
    require(text.count(token) == 1, f"forward mode switch count is {text.count(token)}")
    switch_start, switch_end = balanced_region(text, token)
    line_start = text.rfind("\n", 0, switch_start) + 1
    indent = text[line_start:switch_start]
    require(indent.strip() == "", "forward mode indentation detection failed")
    switch_region = text[switch_start:switch_end]
    switch_region = switch_region.replace("commit(result)", "commit(resolvedResult)")
    switch_region = switch_region.replace(
        "transformEnqueueMessages(result,",
        "transformEnqueueMessages(resolvedResult,",
    )
    nested = "\n".join(("    " + line if line else line) for line in switch_region.split("\n"))
    replacement = (
        "let commitResolved: ([EnqueueMessage]) -> Void = { resolvedResult in\n"
        + indent + nested
        + "\n" + indent + "}\n"
        + indent + "if let jerkgramPortableMessagesSignal {\n"
        + indent + "    let _ = (jerkgramPortableMessagesSignal\n"
        + indent + "    |> deliverOnMainQueue).startStandalone(next: { resolvedMessages in\n"
        + indent + "        commitResolved(resolvedMessages)\n"
        + indent + "    })\n"
        + indent + "} else {\n"
        + indent + "    commitResolved(result)\n"
        + indent + "}"
    )
    return text[:switch_start] + replacement + text[switch_end:]


def patch_text(text: str) -> str:
    if SOURCE_PROTECTION_MARKER in text:
        return text
    upgrading_existing_build124_owner = MARKER in text
    require(
        "BUILD123_PORTABLE_FORWARD1" in text or MARKER in text,
        "Build123/Build124 portable forward prerequisite missing",
    )
    text = replace_helper(text)
    if not upgrading_existing_build124_owner:
        text = patch_portable_secret_chat_guard(text)
        text = patch_portable_branch(text)
        text = patch_commit_resolution(text)
    require(text.count("messages.contains(where: { $0.isCopyProtected() })") == 1, "portable trigger owner missing")
    text = text.replace(
        "messages.contains(where: { $0.isCopyProtected() })",
        "messages.contains(where: { jerkgramRequiresPortableForward($0) })",
        1,
    )
    for proof in (
        MARKER,
        "LocalFileReferenceMediaResource",
        "Namespaces.Media.LocalFile",
        "Namespaces.Media.LocalImage",
        "context.engine.resources.fetch",
        "waitUntilFetchStatus: true",
        "message.forwardInfo?.author ?? message.effectiveAuthor",
        "jerkgramRequiresPortableForward",
        "sourcePeer.isCopyProtectionEnabled",
        "message.id.peerId.namespace != Namespaces.Peer.SecretChat",
        "var jerkgramPortableMessagesSignal: Signal<[EnqueueMessage], NoError>?",
        "let commitResolved",
    ):
        require(proof in text, f"proof missing: {proof}")
    require(
        "let mediaReference = message.media.first.map { AnyMediaReference.standalone(media: $0) }" not in text,
        "Build123 protected cloud media owner survived",
    )
    return text


def main() -> None:
    require(FORWARD.is_file(), f"missing materialized source: {FORWARD}")
    source = FORWARD.read_text(encoding="utf-8")
    FORWARD.write_text(patch_text(source), encoding="utf-8")
    print("[Build124 protected forward] GREEN")
    print("[Build124 protected forward] protected file/photo forwards wait for a complete local resource and re-upload a fresh media id")


if __name__ == "__main__":
    main()
