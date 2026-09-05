#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

SETTINGS = Path("submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift")
ATTRIBUTE = Path("submodules/TelegramCore/Sources/SyncCore/GhostBaseMessageAttribute.swift")
BLOCKED = Path("submodules/TelegramCore/Sources/TelegramEngine/Privacy/BlockedPeers.swift")
STATE = Path("submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift")
HISTORY = Path("submodules/TelegramUI/Sources/ChatHistoryEntriesForView.swift")
POSTBOX = Path("submodules/Postbox/Sources/Postbox.swift")


def fail(message: str) -> None:
    print(f"[build132-blocked-messages] FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(root: Path, rel: Path) -> str:
    path = root / rel
    if not path.is_file():
        fail(f"missing exact owner: {rel}")
    return path.read_text(encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        fail(f"expected one anchor for {label}, found {count}")
    return text.replace(old, new, 1)


def patch_attribute(text: str) -> str:
    marker = "// MARK: JERKGRAM_BUILD132_BLOCKED_HIDDEN_ATTRIBUTE"
    if marker in text:
        return text

    text = replace_once(
        text,
        "    public let deletedAt: Int32\n",
        "    public let deletedAt: Int32\n    // MARK: JERKGRAM_BUILD132_BLOCKED_HIDDEN_ATTRIBUTE\n    public let isBlockedHidden: Bool\n",
        "blocked-hidden property",
    )
    text = replace_once(
        text,
        "    public init(originalText: String?, editHistoryTexts: [String], editHistoryDates: [String], isDeleted: Bool, deletedAt: Int32) {\n",
        "    public init(originalText: String?, editHistoryTexts: [String], editHistoryDates: [String], isDeleted: Bool, deletedAt: Int32, isBlockedHidden: Bool = false) {\n",
        "blocked-hidden initializer",
    )
    text = replace_once(
        text,
        "        self.deletedAt = deletedAt\n    }\n\n    required public init(decoder: PostboxDecoder) {\n",
        "        self.deletedAt = deletedAt\n        self.isBlockedHidden = isBlockedHidden\n    }\n\n    required public init(decoder: PostboxDecoder) {\n",
        "blocked-hidden initializer assignment",
    )
    text = replace_once(
        text,
        '        self.deletedAt = decoder.decodeInt32ForKey("dat", orElse: 0)\n',
        '        self.deletedAt = decoder.decodeInt32ForKey("dat", orElse: 0)\n        self.isBlockedHidden = decoder.decodeInt32ForKey("ibh", orElse: 0) != 0\n',
        "blocked-hidden decode",
    )
    text = replace_once(
        text,
        '        encoder.encodeInt32(self.deletedAt, forKey: "dat")\n',
        '        encoder.encodeInt32(self.deletedAt, forKey: "dat")\n        encoder.encodeInt32(self.isBlockedHidden ? 1 : 0, forKey: "ibh")\n',
        "blocked-hidden encode",
    )
    text = replace_once(
        text,
        "            deletedAt: self.deletedAt\n        )\n    }\n\n    public func withUpdatedDeleted",
        "            deletedAt: self.deletedAt,\n            isBlockedHidden: self.isBlockedHidden\n        )\n    }\n\n    public func withUpdatedDeleted",
        "preserve blocked-hidden in edit-history helper",
    )
    text = replace_once(
        text,
        "            deletedAt: deletedAt\n        )\n    }\n}",
        "            deletedAt: deletedAt,\n            isBlockedHidden: self.isBlockedHidden\n        )\n    }\n\n    public func withUpdatedBlockedHidden(isBlockedHidden: Bool) -> GhostBaseMessageAttribute {\n        return GhostBaseMessageAttribute(\n            originalText: self.originalText,\n            editHistoryTexts: self.editHistoryTexts,\n            editHistoryDates: self.editHistoryDates,\n            isDeleted: self.isDeleted,\n            deletedAt: self.deletedAt,\n            isBlockedHidden: isBlockedHidden\n        )\n    }\n}",
        "blocked-hidden updater",
    )
    return text


def patch_settings(text: str) -> str:
    marker = "// MARK: JERKGRAM_BUILD132_HIDE_BLOCKED_MESSAGES_SETTING"
    if marker in text:
        return text

    text = replace_once(
        text,
        '    static let showEditHistory = "GhostBase.Messages.ShowEditHistory"\n',
        '    static let showEditHistory = "GhostBase.Messages.ShowEditHistory"\n\n    // MARK: JERKGRAM_BUILD132_HIDE_BLOCKED_MESSAGES_SETTING\n    static let hideBlockedMessages = "GhostBase.Messages.HideBlockedMessages"\n',
        "settings key",
    )
    text = replace_once(
        text,
        "    var showEditHistory: Bool\n",
        "    var showEditHistory: Bool\n    var hideBlockedMessages: Bool\n",
        "settings state property",
    )
    text = replace_once(
        text,
        "            showEditHistory: ghostBaseBool(GhostBaseKey.showEditHistory, defaultValue: true),\n",
        "            showEditHistory: ghostBaseBool(GhostBaseKey.showEditHistory, defaultValue: true),\n            hideBlockedMessages: ghostBaseBool(GhostBaseKey.hideBlockedMessages, defaultValue: true),\n",
        "settings state load",
    )
    text = replace_once(
        text,
        "        UserDefaults.standard.set(self.showEditHistory, forKey: GhostBaseKey.showEditHistory)\n",
        "        UserDefaults.standard.set(self.showEditHistory, forKey: GhostBaseKey.showEditHistory)\n        UserDefaults.standard.set(self.hideBlockedMessages, forKey: GhostBaseKey.hideBlockedMessages)\n",
        "settings state save",
    )
    text = replace_once(
        text,
        '            .info(1, "Выключение функций не удаляет уже сохранённые данные.")\n',
        '''            .toggle(
                1,
                90,
                GhostBaseKey.hideBlockedMessages,
                "Скрывать сообщения заблокированных",
                state.hideBlockedMessages
            ),
            .info(1, "Выключение функций не удаляет уже сохранённые данные.")
''',
        "Messages hide-blocked toggle row",
    )
    text = replace_once(
        text,
        '''            case GhostBaseKey.showEditHistory:
                updated.showEditHistory = value
''',
        '''            case GhostBaseKey.showEditHistory:
                updated.showEditHistory = value

            case GhostBaseKey.hideBlockedMessages:
                updated.hideBlockedMessages = value
                UserDefaults.standard.set(value, forKey: GhostBaseKey.hideBlockedMessages)
''',
        "settings toggle handler",
    )
    return text


OLD_BLOCKED_HELPER = '''// MARK: JERKGRAM_BUILD131_BLOCKED_GROUP_AUTHOR_PURGE
// This is a one-shot, indexed Postbox operation invoked after a successful
// ordinary contacts.block call.  It deliberately excludes direct dialogs.
func jerkgramBuild131IsGroupOrSupergroup(_ peer: Peer) -> Bool {
    if peer is TelegramGroup {
        return true
    }
    if let channel = peer as? TelegramChannel, case .group = channel.info {
        return true
    }
    return false
}

private func jerkgramBuild131PurgeBlockedAuthorFromGroupHistories(transaction: Transaction, authorId: PeerId) {
    guard authorId.namespace == Namespaces.Peer.CloudUser else {
        return
    }

    // chatListGetAllPeerIds is bounded by known dialogs; message selection is
    // performed by Postbox's allIndicesWithAuthor index, not by UI scans.
    for peerId in transaction.chatListGetAllPeerIds() {
        guard let peer = transaction.getPeer(peerId), jerkgramBuild131IsGroupOrSupergroup(peer) else {
            continue
        }
        transaction.removeAllMessagesWithAuthor(
            peerId,
            authorId: authorId,
            namespace: Namespaces.Message.Cloud,
            forEachMedia: nil
        )
    }
}

'''

NEW_BLOCKED_HELPER = '''// MARK: JERKGRAM_BUILD132_BLOCKED_MESSAGE_INVALIDATION
// Blocked messages stay in Postbox. Block/unblock only flips a local message
// attribute through Postbox's existing author index, which invalidates history
// views immediately without a full-history scan or destructive deletion.
func jerkgramBuild132IsGroupOrSupergroup(_ peer: Peer) -> Bool {
    if peer is TelegramGroup {
        return true
    }
    if let channel = peer as? TelegramChannel, case .group = channel.info {
        return true
    }
    return false
}

private func jerkgramBuild132UpdateBlockedAuthorVisibility(transaction: Transaction, authorId: PeerId, hidden: Bool) {
    guard authorId.namespace == Namespaces.Peer.CloudUser else {
        return
    }

    for peerId in transaction.chatListGetAllPeerIds() {
        guard let peer = transaction.getPeer(peerId), jerkgramBuild132IsGroupOrSupergroup(peer) else {
            continue
        }

        let messageIds = transaction.jerkgramMessageIdsWithAuthor(
            peerId,
            authorId: authorId,
            namespace: Namespaces.Message.Cloud
        )
        for messageId in messageIds {
            transaction.updateMessage(messageId, update: { currentMessage in
                var updatedAttributes = currentMessage.attributes
                if let index = updatedAttributes.firstIndex(where: { $0 is GhostBaseMessageAttribute }), let attribute = updatedAttributes[index] as? GhostBaseMessageAttribute {
                    updatedAttributes[index] = attribute.withUpdatedBlockedHidden(isBlockedHidden: hidden)
                } else {
                    updatedAttributes.append(
                        GhostBaseMessageAttribute(
                            originalText: currentMessage.text.isEmpty ? nil : currentMessage.text,
                            editHistoryTexts: [],
                            editHistoryDates: [],
                            isDeleted: false,
                            deletedAt: 0,
                            isBlockedHidden: hidden
                        )
                    )
                }

                let storeForwardInfo = currentMessage.forwardInfo.flatMap(StoreMessageForwardInfo.init)
                return .update(
                    StoreMessage(
                        id: currentMessage.id,
                        customStableId: nil,
                        globallyUniqueId: currentMessage.globallyUniqueId,
                        groupingKey: currentMessage.groupingKey,
                        threadId: currentMessage.threadId,
                        timestamp: currentMessage.timestamp,
                        flags: StoreMessageFlags(currentMessage.flags),
                        tags: currentMessage.tags,
                        globalTags: currentMessage.globalTags,
                        localTags: currentMessage.localTags,
                        forwardInfo: storeForwardInfo,
                        authorId: currentMessage.author?.id,
                        text: currentMessage.text,
                        attributes: updatedAttributes,
                        media: currentMessage.media
                    )
                )
            })
        }
    }
}

'''

OLD_BLOCK_CALL = '''
                            if isBlocked {
                                jerkgramBuild131PurgeBlockedAuthorFromGroupHistories(transaction: transaction, authorId: peerId)
                            }'''
NEW_BLOCK_CALL = '''
                            jerkgramBuild132UpdateBlockedAuthorVisibility(
                                transaction: transaction,
                                authorId: peerId,
                                hidden: isBlocked
                            )'''


def patch_blocked(text: str) -> str:
    if "JERKGRAM_BUILD132_BLOCKED_MESSAGE_INVALIDATION" not in text:
        text = replace_once(text, OLD_BLOCKED_HELPER, NEW_BLOCKED_HELPER, "replace destructive blocked-author helper")
    if "hidden: isBlocked" not in text:
        text = replace_once(text, OLD_BLOCK_CALL, NEW_BLOCK_CALL, "block/unblock invalidation call")
    return text


OLD_STATE_HELPER = '''// MARK: JERKGRAM_BUILD131_BLOCKED_GROUP_INGRESS_GATE
// Hot-path work is constant and transaction-local: one peer lookup and one
// cached-user lookup.  The UI never rechecks this policy while scrolling.
private func jerkgramBuild131ShouldDropIncomingBlockedGroupMessage(transaction: Transaction, message: StoreMessage) -> Bool {
    guard message.id.namespace == Namespaces.Message.Cloud,
          message.flags.contains(.Incoming),
          let authorId = message.authorId,
          authorId.namespace == Namespaces.Peer.CloudUser,
          let chatPeer = transaction.getPeer(message.id.peerId)
    else {
        return false
    }

    guard jerkgramBuild131IsGroupOrSupergroup(chatPeer) else {
        return false
    }

    return (transaction.getPeerCachedData(peerId: authorId) as? CachedUserData)?.isBlocked == true
}

'''

NEW_STATE_HELPER = '''// MARK: JERKGRAM_BUILD132_BLOCKED_MESSAGE_INGRESS_ANNOTATION
// New blocked-author group messages are stored normally. We annotate them
// before insertion so they can be hidden/revealed reversibly in the UI.
private func jerkgramBuild132MarkIncomingBlockedGroupMessage(transaction: Transaction, message: StoreMessage) -> StoreMessage {
    guard message.id.namespace == Namespaces.Message.Cloud,
          message.flags.contains(.Incoming),
          let authorId = message.authorId,
          authorId.namespace == Namespaces.Peer.CloudUser,
          let chatPeer = transaction.getPeer(message.id.peerId),
          jerkgramBuild132IsGroupOrSupergroup(chatPeer),
          (transaction.getPeerCachedData(peerId: authorId) as? CachedUserData)?.isBlocked == true
    else {
        return message
    }

    var updatedAttributes = message.attributes
    if let index = updatedAttributes.firstIndex(where: { $0 is GhostBaseMessageAttribute }), let attribute = updatedAttributes[index] as? GhostBaseMessageAttribute {
        updatedAttributes[index] = attribute.withUpdatedBlockedHidden(isBlockedHidden: true)
    } else {
        updatedAttributes.append(
            GhostBaseMessageAttribute(
                originalText: message.text.isEmpty ? nil : message.text,
                editHistoryTexts: [],
                editHistoryDates: [],
                isDeleted: false,
                deletedAt: 0,
                isBlockedHidden: true
            )
        )
    }

    return StoreMessage(
        id: message.id,
        customStableId: nil,
        globallyUniqueId: message.globallyUniqueId,
        groupingKey: message.groupingKey,
        threadId: message.threadId,
        timestamp: message.timestamp,
        flags: message.flags,
        tags: message.tags,
        globalTags: message.globalTags,
        localTags: message.localTags,
        forwardInfo: message.forwardInfo,
        authorId: message.authorId,
        text: message.text,
        attributes: updatedAttributes,
        media: message.media
    )
}

'''

OLD_INGRESS = '''            case let .AddMessages(messagesValue, location):
                var messages = messagesValue

                // Drop before any thread/unread bookkeeping or Postbox insert.
                // Therefore blocked authors cannot create a local badge either.
                if case .UpperHistoryBlock = location {
                    messages.removeAll { message in
                        return jerkgramBuild131ShouldDropIncomingBlockedGroupMessage(transaction: transaction, message: message)
                    }
                }

                if case .UpperHistoryBlock = location {
'''

NEW_INGRESS = '''            case let .AddMessages(messagesValue, location):
                var messages = messagesValue

                if case .UpperHistoryBlock = location {
                    messages = messages.map { message in
                        jerkgramBuild132MarkIncomingBlockedGroupMessage(
                            transaction: transaction,
                            message: message
                        )
                    }
                }

                if case .UpperHistoryBlock = location {
'''


def patch_state(text: str) -> str:
    if "JERKGRAM_BUILD132_BLOCKED_MESSAGE_INGRESS_ANNOTATION" not in text:
        text = replace_once(text, OLD_STATE_HELPER, NEW_STATE_HELPER, "replace ingress drop helper")
    if "jerkgramBuild132MarkIncomingBlockedGroupMessage(" not in text[text.find("case let .AddMessages"):]:
        text = replace_once(text, OLD_INGRESS, NEW_INGRESS, "replace ingress drop with annotation")
    return text


def patch_history(text: str) -> str:
    marker = "// MARK: JERKGRAM_BUILD132_BLOCKED_MESSAGE_HISTORY_FILTER"
    if marker in text:
        return text
    anchor = '''    loop: for entry in view.entries {
        var message = entry.message
        var isRead = entry.isRead
'''
    replacement = '''    loop: for entry in view.entries {
        var message = entry.message
        var isRead = entry.isRead

        // MARK: JERKGRAM_BUILD132_BLOCKED_MESSAGE_HISTORY_FILTER
        if UserDefaults.standard.bool(forKey: "GhostBase.Messages.HideBlockedMessages"),
           ((message.attributes.first(where: { $0 is GhostBaseMessageAttribute }) as? GhostBaseMessageAttribute)?.isBlockedHidden ?? false) {
            continue loop
        }
'''
    return replace_once(text, anchor, replacement, "chat history blocked-message visibility")


def patch_postbox(text: str) -> str:
    marker = "// MARK: JERKGRAM_BUILD132_MESSAGE_IDS_WITH_AUTHOR"
    if marker in text:
        return text
    anchor = '''    public func removeAllMessagesWithAuthor(_ peerId: PeerId, authorId: PeerId, namespace: MessageId.Namespace, forEachMedia: ((Media) -> Void)?) {
'''
    helper = '''    // MARK: JERKGRAM_BUILD132_MESSAGE_IDS_WITH_AUTHOR
    public func jerkgramMessageIdsWithAuthor(_ peerId: PeerId, authorId: PeerId, namespace: MessageId.Namespace) -> [MessageId] {
        assert(!self.disposed)
        if let postbox = self.postbox {
            return postbox.messageHistoryTable.allIndicesWithAuthor(
                peerId: peerId,
                authorId: authorId,
                namespace: namespace
            ).map(\\.id)
        } else {
            return []
        }
    }

'''
    return replace_once(text, anchor, helper + anchor, "Postbox author-index bridge")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: apply_build132_blocked_messages_visibility.py <materialized-source-root>")
    root = Path(sys.argv[1]).expanduser().resolve()

    owners = (SETTINGS, ATTRIBUTE, BLOCKED, STATE, HISTORY, POSTBOX)
    originals = {rel: read(root, rel) for rel in owners}

    # Prepare every transform in memory before writing anything.
    patched = {
        SETTINGS: patch_settings(originals[SETTINGS]),
        ATTRIBUTE: patch_attribute(originals[ATTRIBUTE]),
        BLOCKED: patch_blocked(originals[BLOCKED]),
        STATE: patch_state(originals[STATE]),
        HISTORY: patch_history(originals[HISTORY]),
        POSTBOX: patch_postbox(originals[POSTBOX]),
    }

    # Final destructive-policy guard before any materialized write.
    for rel in (BLOCKED, STATE):
        for token in (
            "JERKGRAM_BUILD131_BLOCKED_GROUP_AUTHOR_PURGE",
            "jerkgramBuild131PurgeBlockedAuthorFromGroupHistories",
            "JERKGRAM_BUILD131_BLOCKED_GROUP_INGRESS_GATE",
            "jerkgramBuild131ShouldDropIncomingBlockedGroupMessage",
        ):
            if token in patched[rel]:
                fail(f"destructive Build131 token survived in {rel}: {token}")

    changed = []
    for rel in owners:
        if patched[rel] != originals[rel]:
            (root / rel).write_text(patched[rel], encoding="utf-8")
            changed.append(str(rel))

    if changed:
        print("[build132-blocked-messages] patched")
        for rel in changed:
            print(f"  {rel}")
    else:
        print("[build132-blocked-messages] already applied")


if __name__ == "__main__":
    main()
