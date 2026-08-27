#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
ATTRIBUTE = ROOT / "submodules/TelegramCore/Sources/SyncCore/GhostBaseMessageAttribute.swift"
STATE = ROOT / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
DELETE = ROOT / "submodules/TelegramCore/Sources/TelegramEngine/Messages/DeleteMessagesInteractively.swift"
MENU = ROOT / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"
FORWARD = ROOT / "submodules/TelegramUI/Sources/ChatControllerForwardMessages.swift"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build123 message fidelity] " + message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    require(text.count(old) == 1, f"{label}: expected one anchor, found {text.count(old)}")
    return text.replace(old, new, 1)


ATTRIBUTE_SOURCE = r'''import Foundation
import Postbox

// MARK: Jerkgram v1.2L BUILD123_MESSAGE_SNAPSHOT1
public final class GhostBaseEditEntitySnapshot: PostboxCoding {
    public let entities: [MessageTextEntity]
    public let inlineStickerFiles: [TelegramMediaFile]

    public init(entities: [MessageTextEntity], inlineStickerFiles: [TelegramMediaFile]) {
        self.entities = entities
        self.inlineStickerFiles = inlineStickerFiles
    }

    required public init(decoder: PostboxDecoder) {
        self.entities = decoder.decodeObjectArrayWithDecoderForKey("e")
        self.inlineStickerFiles = decoder.decodeObjectArrayWithDecoderForKey("f")
    }

    public func encode(_ encoder: PostboxEncoder) {
        encoder.encodeObjectArray(self.entities, forKey: "e")
        encoder.encodeObjectArray(self.inlineStickerFiles, forKey: "f")
    }
}

public final class GhostBaseMessageAttribute: MessageAttribute {
    public let originalText: String?
    public let originalEntities: [MessageTextEntity]
    public let editHistoryTexts: [String]
    public let editHistoryDates: [String]
    public let editHistoryEntities: [String]
    public let editHistorySnapshots: [GhostBaseEditEntitySnapshot]
    public let isDeleted: Bool
    public let deletedAt: Int32

    public init(
        originalText: String?,
        editHistoryTexts: [String],
        editHistoryDates: [String],
        isDeleted: Bool,
        deletedAt: Int32,
        originalEntities: [MessageTextEntity] = [],
        editHistoryEntities: [String] = [],
        editHistorySnapshots: [GhostBaseEditEntitySnapshot] = []
    ) {
        self.originalText = originalText
        self.originalEntities = originalEntities
        self.editHistoryTexts = editHistoryTexts
        self.editHistoryDates = editHistoryDates
        self.editHistoryEntities = editHistoryEntities
        self.editHistorySnapshots = editHistorySnapshots
        self.isDeleted = isDeleted
        self.deletedAt = deletedAt
    }

    required public init(decoder: PostboxDecoder) {
        self.originalText = decoder.decodeOptionalStringForKey("ot")
        self.originalEntities = decoder.decodeObjectArrayWithDecoderForKey("oe")
        self.editHistoryTexts = decoder.decodeStringArrayForKey("eht")
        self.editHistoryDates = decoder.decodeStringArrayForKey("ehd")
        self.editHistoryEntities = decoder.decodeStringArrayForKey("ehe")
        self.editHistorySnapshots = decoder.decodeObjectArrayWithDecoderForKey("ehs")
        self.isDeleted = decoder.decodeInt32ForKey("del", orElse: 0) != 0
        self.deletedAt = decoder.decodeInt32ForKey("dat", orElse: 0)
    }

    public func encode(_ encoder: PostboxEncoder) {
        if let originalText = self.originalText { encoder.encodeString(originalText, forKey: "ot") }
        encoder.encodeObjectArray(self.originalEntities, forKey: "oe")
        encoder.encodeStringArray(self.editHistoryTexts, forKey: "eht")
        encoder.encodeStringArray(self.editHistoryDates, forKey: "ehd")
        encoder.encodeStringArray(self.editHistoryEntities, forKey: "ehe")
        encoder.encodeObjectArray(self.editHistorySnapshots, forKey: "ehs")
        encoder.encodeInt32(self.isDeleted ? 1 : 0, forKey: "del")
        encoder.encodeInt32(self.deletedAt, forKey: "dat")
    }

    private static func encodeEntities(_ entities: [MessageTextEntity]) -> String {
        guard let data = try? JSONEncoder().encode(entities) else { return "" }
        return data.base64EncodedString()
    }

    public func entitiesForEditVersion(_ index: Int) -> [MessageTextEntity] {
        if index >= 0, index < self.editHistorySnapshots.count {
            return self.editHistorySnapshots[index].entities
        }
        guard index >= 0, index < self.editHistoryEntities.count,
              let data = Data(base64Encoded: self.editHistoryEntities[index]),
              let entities = try? JSONDecoder().decode([MessageTextEntity].self, from: data) else {
            return []
        }
        return entities
    }

    public func inlineStickerFilesForEditVersion(_ index: Int) -> [TelegramMediaFile] {
        guard index >= 0, index < self.editHistorySnapshots.count else { return [] }
        return self.editHistorySnapshots[index].inlineStickerFiles
    }

    public func withAddedEditVersion(text: String, date: Int32, entities: [MessageTextEntity] = [], inlineStickerFiles: [TelegramMediaFile] = []) -> GhostBaseMessageAttribute {
        var texts = self.editHistoryTexts
        var dates = self.editHistoryDates
        var entitySets = self.editHistoryEntities
        var snapshots = self.editHistorySnapshots
        let encodedEntities = Self.encodeEntities(entities)

        // Record text changes and entity-only edits (links, formatting, premium emoji).
        if texts.last != text || entitySets.last != encodedEntities {
            texts.append(text)
            dates.append(String(date))
            entitySets.append(encodedEntities)
            snapshots.append(GhostBaseEditEntitySnapshot(entities: entities, inlineStickerFiles: inlineStickerFiles))
            if texts.count > 30 {
                texts = Array(texts.suffix(30))
                dates = Array(dates.suffix(30))
                entitySets = Array(entitySets.suffix(30))
                snapshots = Array(snapshots.suffix(30))
            }
        }

        return GhostBaseMessageAttribute(
            originalText: self.originalText ?? text,
            editHistoryTexts: texts,
            editHistoryDates: dates,
            isDeleted: self.isDeleted,
            deletedAt: self.deletedAt,
            originalEntities: self.originalEntities.isEmpty ? entities : self.originalEntities,
            editHistoryEntities: entitySets,
            editHistorySnapshots: snapshots
        )
    }

    public func withUpdatedDeleted(isDeleted: Bool, deletedAt: Int32) -> GhostBaseMessageAttribute {
        return GhostBaseMessageAttribute(
            originalText: self.originalText,
            editHistoryTexts: self.editHistoryTexts,
            editHistoryDates: self.editHistoryDates,
            isDeleted: isDeleted,
            deletedAt: deletedAt,
            originalEntities: self.originalEntities,
            editHistoryEntities: self.editHistoryEntities,
            editHistorySnapshots: self.editHistorySnapshots
        )
    }
}
'''


PORTABLE_HELPER = r'''// MARK: Jerkgram v1.2L BUILD123_PORTABLE_FORWARD1
private func jerkgramPortableForwardMessage(
    _ message: Message,
    hideAuthor: Bool,
    threadId: Int64?
) -> EnqueueMessage {
    var text = message.text
    var entities = message.textEntitiesAttribute?.entities ?? []

    if !hideAuthor, let sourcePeer = message.peers[message.id.peerId].map(EnginePeer.init) {
        let title = sourcePeer.compactDisplayTitle
        if !title.isEmpty {
            let prefix = text.isEmpty ? "" : "\n\n"
            let start = (text as NSString).length + (prefix as NSString).length
            text += prefix + "— " + title
            let titleStart = start + 2
            let titleEnd = titleStart + (title as NSString).length
            if let username = sourcePeer.addressName, !username.isEmpty {
                entities.append(MessageTextEntity(range: titleStart ..< titleEnd, type: .TextUrl(url: "https://t.me/\(username)")))
            }
            entities.append(MessageTextEntity(range: titleStart ..< titleEnd, type: .Bold))
        }
    }

    var attributes: [MessageAttribute] = []
    if !entities.isEmpty { attributes.append(TextEntitiesMessageAttribute(entities: entities)) }
    let embeddedFiles = (message.attributes.first(where: { $0 is EmbeddedMediaStickersMessageAttribute }) as? EmbeddedMediaStickersMessageAttribute)?.files ?? []
    var inlineStickers: [MediaId: Media] = [:]
    for file in embeddedFiles { inlineStickers[file.fileId] = file }

    let mediaReference = message.media.first.map { AnyMediaReference.standalone(media: $0) }
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

'''


def patch_attribute() -> None:
    text = ATTRIBUTE.read_text(encoding="utf-8")
    if "BUILD123_MESSAGE_SNAPSHOT1" not in text:
        ATTRIBUTE.write_text(ATTRIBUTE_SOURCE, encoding="utf-8")


def patch_capture() -> None:
    text = STATE.read_text(encoding="utf-8")
    if "BUILD123_ENTITY_HISTORY_CAPTURE1" in text:
        return
    old = '''                    if ghostBaseSaveEditHistory,
                       previousMessage.text != message.text {'''
    new = '''                    let previousEntities = previousMessage.textEntitiesAttribute?.entities ?? []
                    let updatedEntities = (message.attributes.first(where: { $0 is TextEntitiesMessageAttribute }) as? TextEntitiesMessageAttribute)?.entities ?? []
                    let previousInlineStickerFiles = (previousMessage.attributes.first(where: { $0 is EmbeddedMediaStickersMessageAttribute }) as? EmbeddedMediaStickersMessageAttribute)?.files ?? []
                    // MARK: Jerkgram v1.2L BUILD123_ENTITY_HISTORY_CAPTURE1
                    // Capture text transitions and entity-only edits.
                    if ghostBaseSaveEditHistory,
                       previousMessage.text != message.text || previousEntities != updatedEntities {'''
    text = replace_once(text, old, new, "entity-only edits gate")
    old_call = '''                        if let updatedAttribute = attribute?.withAddedEditVersion(
                            text: previousMessage.text,
                            date: previousVersionDate
                        ) {'''
    new_call = '''                        if let updatedAttribute = attribute?.withAddedEditVersion(
                            text: previousMessage.text,
                            date: previousVersionDate,
                            entities: previousEntities,
                            inlineStickerFiles: previousInlineStickerFiles
                        ) {'''
    text = replace_once(text, old_call, new_call, "history entity snapshot")
    STATE.write_text(text, encoding="utf-8")


def patch_deleted_entities() -> None:
    text = STATE.read_text(encoding="utf-8")
    marker = "BUILD123_DELETED_ENTITY_SNAPSHOT1"
    if marker not in text:
        deletion_old = '''                                originalText: originalText,
                                editHistoryTexts: [],
                                editHistoryDates: [],
                                isDeleted: false,
                                deletedAt: 0
                            )'''
        deletion_new = '''                                originalText: originalText,
                                editHistoryTexts: [],
                                editHistoryDates: [],
                                isDeleted: false,
                                deletedAt: 0,
                                // MARK: Jerkgram v1.2L BUILD123_DELETED_ENTITY_SNAPSHOT1
                                originalEntities: currentMessage.textEntitiesAttribute?.entities ?? []
                            )'''
        text = replace_once(text, deletion_old, deletion_new, "server deletion snapshot")
        history_old = '''                                originalText: previousMessage.text,
                                editHistoryTexts: [],
                                editHistoryDates: [],
                                isDeleted: false,
                                deletedAt: 0
                            )'''
        history_new = '''                                originalText: previousMessage.text,
                                editHistoryTexts: [],
                                editHistoryDates: [],
                                isDeleted: false,
                                deletedAt: 0,
                                // MARK: Jerkgram v1.2L BUILD123_DELETED_ENTITY_SNAPSHOT1
                                originalEntities: previousEntities
                            )'''
        text = replace_once(text, history_old, history_new, "edit history original entity snapshot")
        STATE.write_text(text, encoding="utf-8")

    text = DELETE.read_text(encoding="utf-8")
    if marker not in text:
        old = '''                        updatedAttributes.append(GhostBaseMessageAttribute(originalText: currentMessage.text, editHistoryTexts: [], editHistoryDates: [], isDeleted: true, deletedAt: currentMessage.timestamp))'''
        new = '''                        // MARK: Jerkgram v1.2L BUILD123_DELETED_ENTITY_SNAPSHOT1
                        updatedAttributes.append(GhostBaseMessageAttribute(
                            originalText: currentMessage.text,
                            editHistoryTexts: [],
                            editHistoryDates: [],
                            isDeleted: true,
                            deletedAt: currentMessage.timestamp,
                            originalEntities: currentMessage.textEntitiesAttribute?.entities ?? []
                        ))'''
        text = replace_once(text, old, new, "interactive deletion snapshot")
        DELETE.write_text(text, encoding="utf-8")


def patch_history_ui() -> None:
    # The existing user-facing action is «Переслать без автора»; Build123
    # changes its capability gate and send path without duplicating the row.
    text = MENU.read_text(encoding="utf-8")
    if "BUILD123_HISTORY_ENTITIES1" in text:
        if "BUILD123_PORTABLE_MENU_RESTRICTIONS1" not in text:
            old_gate = '''        if ghostBaseForwardWithoutAuthor,
           messages.allSatisfy({ $0.id.peerId.namespace != Namespaces.Peer.SecretChat }) {
            // data.messageActions.options.contains(.forward) survived portable gate'''
            new_gate = '''        // MARK: Jerkgram v1.2L BUILD123_PORTABLE_MENU_RESTRICTIONS1
        if ghostBaseForwardWithoutAuthor,
           messages.allSatisfy({ message in
               message.id.peerId.namespace != Namespaces.Peer.SecretChat
               && !message.media.contains(where: {
                   $0 is TelegramMediaPaidContent
                   || $0 is TelegramMediaAction
                   || $0 is TelegramMediaExpiredContent
               })
           }) {
            // data.messageActions.options.contains(.forward) survived portable gate'''
            text = replace_once(text, old_gate, new_gate, "portable context-menu restrictions")
            MENU.write_text(text, encoding="utf-8")
        return
    text = replace_once(
        text,
        '''private struct GhostBaseEditHistoryVersion: Equatable {
    let index: Int
    let text: String
    let timestamp: Double
}''',
        '''// MARK: Jerkgram v1.2L BUILD123_HISTORY_ENTITIES1
private struct GhostBaseEditHistoryVersion: Equatable {
    let index: Int
    let text: String
    let timestamp: Double
    let entities: [MessageTextEntity]
    let inlineStickerFiles: [TelegramMediaFile]
}''',
        "history version entities",
    )
    text = text.replace(
        "GhostBaseEditHistoryVersion(index: index, text: text, timestamp: timestamp)",
        "GhostBaseEditHistoryVersion(index: index, text: text, timestamp: timestamp, entities: [], inlineStickerFiles: [])",
    )
    old = "result.append(GhostBaseEditHistoryVersion(index: result.count, text: text, timestamp: timestamp))"
    new = "result.append(GhostBaseEditHistoryVersion(index: result.count, text: text, timestamp: timestamp, entities: attribute.entitiesForEditVersion(index), inlineStickerFiles: attribute.inlineStickerFilesForEditVersion(index)))"
    text = replace_once(text, old, new, "attribute history entities")
    text = text.replace(
        "GhostBaseEditHistoryVersion(index: result.count, text: originalText, timestamp: 0.0)",
        "GhostBaseEditHistoryVersion(index: result.count, text: originalText, timestamp: 0.0, entities: attribute.originalEntities, inlineStickerFiles: [])",
    )
    old_current = '''            text: message.text,
            timestamp: Double(message.timestamp)
        ))'''
    new_current = '''            text: message.text,
            timestamp: Double((message.attributes.first(where: { $0 is EditedMessageAttribute }) as? EditedMessageAttribute)?.date ?? message.timestamp),
            entities: message.textEntitiesAttribute?.entities ?? [],
            inlineStickerFiles: (message.attributes.first(where: { $0 is EmbeddedMediaStickersMessageAttribute }) as? EmbeddedMediaStickersMessageAttribute)?.files ?? []
        ))'''
    text = replace_once(text, old_current, new_current, "current history timestamp/entities")
    old_attributes = "                attributes: [],\n                media: [],"
    new_attributes = '''                attributes: {
                    var attributes: [MessageAttribute] = []
                    if !version.entities.isEmpty {
                        attributes.append(TextEntitiesMessageAttribute(entities: version.entities))
                    }
                    if !version.inlineStickerFiles.isEmpty {
                        attributes.append(EmbeddedMediaStickersMessageAttribute(files: version.inlineStickerFiles))
                    }
                    return attributes
                }(),
                media: [],'''
    text = replace_once(text, old_attributes, new_attributes, "history rendered entities")
    old_gate = '''        if ghostBaseForwardWithoutAuthor,
           data.messageActions.options.contains(.forward) {'''
    new_gate = '''        // MARK: Jerkgram v1.2L BUILD123_PORTABLE_MENU_RESTRICTIONS1
        if ghostBaseForwardWithoutAuthor,
           messages.allSatisfy({ message in
               message.id.peerId.namespace != Namespaces.Peer.SecretChat
               && !message.media.contains(where: {
                   $0 is TelegramMediaPaidContent
                   || $0 is TelegramMediaAction
                   || $0 is TelegramMediaExpiredContent
               })
           }) {
            // data.messageActions.options.contains(.forward) survived portable gate'''
    text = replace_once(text, old_gate, new_gate, "portable context-menu gate")
    MENU.write_text(text, encoding="utf-8")


def patch_forward_send() -> None:
    text = FORWARD.read_text(encoding="utf-8")
    if "BUILD123_PORTABLE_FORWARD1" in text:
        if "canUsePortableCopy" not in text:
            old = '''                        let hideAuthor = forwardOptions?.hideNames == true || options?.hideNames == true
                        if hideAuthor || messages.contains(where: { $0.isCopyProtected() }) {'''
            new = '''                        let hideAuthor = forwardOptions?.hideNames == true || options?.hideNames == true
                        let canUsePortableCopy = messages.allSatisfy { message in
                            !message.media.contains(where: {
                                $0 is TelegramMediaPaidContent
                                || $0 is TelegramMediaAction
                                || $0 is TelegramMediaExpiredContent
                            })
                        }
                        if canUsePortableCopy && (hideAuthor || messages.contains(where: { $0.isCopyProtected() })) {'''
            text = replace_once(text, old, new, "portable forward restrictions")
            FORWARD.write_text(text, encoding="utf-8")
        return
    anchor = "extension ChatControllerImpl {"
    require(text.count(anchor) == 1, "forward extension anchor")
    text = text.replace(anchor, PORTABLE_HELPER + anchor, 1)
    old = '''                        result.append(contentsOf: messages.map { message -> EnqueueMessage in
                            return .forward(source: message.id, threadId: nil, grouping: .auto, attributes: attributes, correlationId: nil)
                        })'''
    new = '''                        let hideAuthor = forwardOptions?.hideNames == true || options?.hideNames == true
                        let canUsePortableCopy = messages.allSatisfy { message in
                            !message.media.contains(where: {
                                $0 is TelegramMediaPaidContent
                                || $0 is TelegramMediaAction
                                || $0 is TelegramMediaExpiredContent
                            })
                        }
                        if canUsePortableCopy && (hideAuthor || messages.contains(where: { $0.isCopyProtected() })) {
                            result.append(contentsOf: messages.map {
                                jerkgramPortableForwardMessage($0, hideAuthor: hideAuthor, threadId: strongSelf.chatLocation.threadId)
                            })
                        } else {
                            result.append(contentsOf: messages.map { message -> EnqueueMessage in
                                return .forward(source: message.id, threadId: nil, grouping: .auto, attributes: attributes, correlationId: nil)
                            })
                        }'''
    text = replace_once(text, old, new, "portable forward commit")
    FORWARD.write_text(text, encoding="utf-8")


def main() -> None:
    patch_attribute()
    patch_capture()
    patch_deleted_entities()
    patch_history_ui()
    patch_forward_send()
    print("[Build123 message fidelity] GREEN")


if __name__ == "__main__":
    main()
