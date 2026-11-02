# BOTBRIDGE1 current API validation

Read-only source/API research, 2026-11-01. No production source modifications or full build. Files fetched through the primary GitHub connector at exact Telegram-iOS commit `279f89e4d4f63f17227bf877dc3d8990f22ecd58`, saved beneath `official-1312/` and checked against GitHub's Git blob SHA1. The six added records in `official-1312/PROVENANCE.json` identify exact bytes. Trailing newline introduced by scratch materialization was removed where necessary before hash verification.

## Exact evidence

| File | Git blob SHA1 |
| --- | --- |
| submodules/Postbox/Sources/Message.swift | a3a0bd715d60809d66295a05c7069b798195daee |
| submodules/Postbox/Sources/PostboxTransaction.swift | 940f559c706a1bdb6bfb9650b43986dc9b88c963 |
| submodules/Postbox/Sources/Postbox.swift | 5fdf8a8ded8f23c92592814e9072b6d4f8a0c5c1 |
| submodules/Postbox/Sources/MessageHistoryTable.swift | bbb1f8c321364e6ddf1dd64108c22ae3dd74fe81 |
| submodules/TelegramCore/Sources/ApiUtils/StoreMessage_Telegram.swift | 4f531ee97f460024dcde56a4e50240b8cfb19d91 |
| submodules/TelegramCore/Sources/SyncCore/SyncCore_AuthorizedAccountState.swift | 9ff2b9876353dfb8baeb952b1b745ba4830bf204 |

Correction to likely filename assumption: PostboxTransaction.swift is an internal transaction delta object; the public `Transaction` API is in **Postbox.swift**, not that file.

## StoreMessage construction and reference peers

Official `Message.swift:922` declares `public final class StoreMessage`, with public id, timestamp, flags, forwardInfo, authorId, attributes and media. `:939` defines the full MessageId initializer; `:975` defines StoreMessageId variant. Forward info at :502 exposes optional authorId, sourceId and sourceMessageId. MessageAttribute at :616 exposes associatedPeerIds, associatedMessageIds, associatedMediaIds and associatedStoryIds. The protocol defaults may be empty; do not assume every peer is covered by associatedPeerIds alone.

The current local `build177-source/.../ApiUtils/StoreMessage_Telegram.swift:1136` defines the required INTERNAL TelegramCore extension:

`convenience init?(apiMessage: Api.Message, accountPeerId: PeerId, peerIsForum: Bool, namespace: MessageId.Namespace = Namespaces.Message.Cloud)`

It creates a StoreMessage without invoking finalState/replay. Its local Git blob is `942e64e3585bc049efe437dce5e860342c846591`, intentionally different from stock. Inspected diff: only Jerkgram blocked-activity tag filtering helper and its two tag call sites differ. Preserve that modern conversion. The constructor may change namespace for quick-reply messages, so the bridge must filter resulting `.Id` namespace after conversion, even with the default Cloud argument.

Corresponding peer extraction can be precise and bounded:

1. Start with `apiMessagePeerIds(apiMessage)` from current conversion file :256. This includes chat, resolved author, forward author/saved peers, via bot/business bot, saved peer, contact user, mention-name users and service-action peers. It includes story reply peer, but normal-message reply-header peer extraction is NOT complete there.
2. Add StoreMessage `.Id.peerId`, authorId, forwardInfo.authorId/sourceId/sourceMessageId.peerId.
3. Add each attribute.associatedPeerIds and each attribute.associatedMessageIds.peerId; add associatedStoryIds peer IDs using the actual StoryId fields after compiler confirmation. Explicitly use `(attribute as? ReplyMessageAttribute)?.messageId.peerId` for reply target if needed; local constructor at :1228/:1594/:1636 demonstrates ReplyMessageAttribute(messageId:...) with explicit reply peer.
4. Inspect the Api.Message normal/service `replyTo` directly for `.messageReplyHeader`: add `replyToPeerId?.peerId`, and forward header `replyFrom` fromId/savedFromPeer/savedFromId peers. This avoids assuming quoted reply attributes retain all identifiers. For story header, add its peer. Existing ephemeral helper :424–468 demonstrates the precise API enum fields but is not itself called for normal messages.
5. Intersect this required set with response users/chats, filter `transaction.getPeer(id) == nil`, parse with `TelegramUser(user:)` / `parseTelegramGroupOrChannel(chat:)`, and insert absent peers only. Existing transaction peers win for forum status and metadata. A response may contain unrelated peers; inserting all absent response peers is bounded by page but broader than “corresponding peers”; prefer the reference-set intersection. Missing referenced peers not supplied by the response stay unresolved, with safe counts, without fetching dialogs or additional RPCs.

There is no need to materialize the entire mutable account state to discover these references. The account bot peer itself must already be present and verified; never replace it with response data.

## Exact Transaction APIs and .Random

All of the following are public in fetched `Postbox.swift`:

- :46 `addMessages(_ messages: [StoreMessage], location: AddMessagesLocation) -> [Int64: MessageId]`
- :55 `messageExists(id: MessageId) -> Bool`
- :272 `getState() -> PostboxCoding?`
- :321 `getPeer(_ id: PeerId) -> Peer?`
- :351 `updatePeersInternal(_ peers: [Peer], update: (Peer?, Peer) -> Peer?)`
- :764 `filterStoredMessageIds(_ messageIds: Set<MessageId>) -> Set<MessageId>`
- :858 `getPreferencesEntry(key: ValueBoxKey) -> PreferencesEntry?`
- :868 `updatePreferencesEntry(key: ValueBoxKey, _ f: (PreferencesEntry?) -> PreferencesEntry?)`

`Postbox.swift:2194` implements addMessages; :2201 switches explicitly on `.Random` and `.UpperHistoryBlock`. `.Random` does not remove history holes, whereas UpperHistoryBlock removes holes above the earliest message. Therefore `.Random` is both valid API and the correct conservative insertion mode for sparse legacy backlog. Do not infer contiguous history completeness.

IMPORTANT LIMIT: even direct addMessages runs installed message actions and installed store-or-update actions (:2223–2234). It updates ordinary Postbox indexes and pending actions through MessageHistoryTable. Direct insertion is narrower than generic final-state replay, but it is not a proof of zero indirect side effects. Audit installed callbacks for account-local imported historical messages before asserting that storage cannot trigger any follow-up network work. Retain source-level bridge RPC allowlist and runtime diagnostics to detect unexpected work. This refines the earlier design note's “side-effect-free” intent.

## Account and session validation available today

`SyncCore_AuthorizedAccountState.swift:72–77` exposes isTestingEnvironment, masterDatacenterId, peerId, optional state tuple and invalidatedChannels. A page transaction can require:

- `transaction.getState() as? AuthorizedAccountState` succeeds;
- authorized.peerId equals expected accountPeerId;
- isTestingEnvironment equals captured environment;
- `transaction.getPeer(accountPeerId) as? TelegramUser` has botInfo;
- persisted bridge version/owner/generation/cursor matches request snapshot;
- process-local importer cancellation/instance token still valid.

`Account/Account.swift:385–387` demonstrates authorizedState fields used to construct the current Network and Account. Manager `Impl` has accountPeerId, Postbox and Network (:192–195). Capturing the existing objects plus an importer lifetime token binds a running request to that manager/account instance.

There is NO authentication-session generation field in AuthorizedAccountState. peerId/environment/masterDatacenterId are not session identity; do not claim otherwise. Master DC can legitimately change and should not be used as a permanent generation. A new nonsecret generation/epoch must be persisted by the current account lifecycle when a new authorization record is created, or a validated existing Account record identity plus explicit progress invalidation on reauthorization must be used. A random importer token alone protects in-process callbacks, but cannot distinguish relogin across process restarts. Final plan must state this lifecycle dependency explicitly and audit logout/removal/reauthorization paths. Do not derive identity from or persist auth keys/tokens.

## Preference-key collision scope

Search of the entire supplied `build177-source` snapshot and saved official evidence found no occurrence of `0x4A470002`, lowercase equivalent, or decimal equivalent. Current `SyncCore_Namespaces.swift:374` uses `0x4A470001` for jerkgramDefaultFolderOrder; 0x4A470002 is the proposed next key.

This is a scoped assurance: build177-source is a selective snapshot, not a full generated checkout, and not every third-party module was obtained. The full generated TelegramCore namespaces and all local plugin preference definitions must be scanned immediately before reserving 0x4A470002. No global uniqueness guarantee is claimed from the selective tree. Postbox preference isolation is per account; one key suffices for that account's versioned bridge progress.

## Verification status

Six fetched file hashes match GitHub blob identity exactly. Public storage signatures, direct converter access, .Random semantics, reference extraction and absence of existing session epoch were inspected. No full build or implementation performed. Remaining implementation gates are full-tree key collision scan, selected session-epoch lifecycle source, installed Postbox action audit and durable deleted-message/tombstone policy.
