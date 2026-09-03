#!/usr/bin/env python3
"""Build131: remove blocked authors from group histories before UI mapping.

The code intentionally runs only in Postbox transactions.  It never adds a
per-frame UI filter, a network request, or a UserDefaults lookup.
"""
from pathlib import Path
import os


ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", os.environ.get("JERKGRAM_SRC", "/root/gb_builder/work/swiftgram-src")))
BLOCKED = ROOT / "submodules/TelegramCore/Sources/TelegramEngine/Privacy/BlockedPeers.swift"
STATE = ROOT / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"


def require(condition, message):
    if not condition:
        raise RuntimeError(f"[Build131] {message}")


def replace_once(text, old, new, label):
    require(old in text, f"missing anchor: {label}")
    return text.replace(old, new, 1)


for path in (BLOCKED, STATE):
    require(path.is_file(), f"missing source: {path}")

blocked = BLOCKED.read_text(encoding="utf-8")
state = STATE.read_text(encoding="utf-8")

helper_marker = "JERKGRAM_BUILD131_BLOCKED_GROUP_AUTHOR_PURGE"
if helper_marker not in blocked:
    helper = '''// MARK: JERKGRAM_BUILD131_BLOCKED_GROUP_AUTHOR_PURGE
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
    import_anchor = "import MtProtoKit\n\n"
    require(import_anchor in blocked, "BlockedPeers import section")
    blocked = blocked.replace(import_anchor, import_anchor + helper, 1)

    anchor = '''                        if result != nil {
                            transaction.updatePeerCachedData(peerIds: Set([peerId]), update: { _, current in
                                let previous: CachedUserData
                                if let current = current as? CachedUserData {
                                    previous = current
                                } else {
                                    previous = CachedUserData()
                                }
                                return previous.withUpdatedIsBlocked(isBlocked)
                            })
                        }
'''
    replacement = '''                        if result != nil {
                            transaction.updatePeerCachedData(peerIds: Set([peerId]), update: { _, current in
                                let previous: CachedUserData
                                if let current = current as? CachedUserData {
                                    previous = current
                                } else {
                                    previous = CachedUserData()
                                }
                                return previous.withUpdatedIsBlocked(isBlocked)
                            })

                            if isBlocked {
                                jerkgramBuild131PurgeBlockedAuthorFromGroupHistories(transaction: transaction, authorId: peerId)
                            }
                        }
'''
    blocked = replace_once(blocked, anchor, replacement, "ordinary block completion")

state_marker = "JERKGRAM_BUILD131_BLOCKED_GROUP_INGRESS_GATE"
if state_marker not in state:
    helper = '''// MARK: JERKGRAM_BUILD131_BLOCKED_GROUP_INGRESS_GATE
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
    anchor = "func replayFinalState("
    require(anchor in state, "replayFinalState function")
    state = state.replace(anchor, helper + anchor, 1)

    old = '''            case let .AddMessages(messages, location):
                if case .UpperHistoryBlock = location {
                    for message in messages {
'''
    new = '''            case let .AddMessages(messagesValue, location):
                var messages = messagesValue

                // Drop before any thread/unread bookkeeping or Postbox insert.
                // Therefore blocked authors cannot create a local badge either.
                if case .UpperHistoryBlock = location {
                    messages.removeAll { message in
                        return jerkgramBuild131ShouldDropIncomingBlockedGroupMessage(transaction: transaction, message: message)
                    }
                }

                if case .UpperHistoryBlock = location {
                    for message in messages {
'''
    state = replace_once(state, old, new, "AddMessages ingress")
    state = replace_once(
        state,
        '''                var messages = messages
            
                if case .UpperHistoryBlock = location {
''',
        '''                if case .UpperHistoryBlock = location {
''',
        "duplicate AddMessages binding"
    )

BLOCKED.write_text(blocked, encoding="utf-8")
STATE.write_text(state, encoding="utf-8")

require(helper_marker in blocked, "block purge helper missing")
require("jerkgramBuild131PurgeBlockedAuthorFromGroupHistories(transaction: transaction, authorId: peerId)" in blocked, "block purge call missing")
require(state_marker in state, "ingress helper missing")
require("case let .AddMessages(messagesValue, location):" in state, "ingress binding missing")
require("messages.removeAll { message in" in state, "ingress filter missing")
print("[Build131] blocked group author core policy applied")
