import Foundation
/* REAL_POLICY */
struct PeerId: Hashable {
    struct Id: Hashable { let value: Int64; static func _internalFromInt64Value(_ v: Int64) -> Id { return Id(value: v) } }
    let namespace: Int; let id: Id
    func toInt64() -> Int64 { return id.value }
}
struct MessageId: Hashable { let peerId: PeerId; let namespace: Int; let id: Int32 }
struct StoryId { let peerId: PeerId }
enum Namespaces { enum Peer { static let CloudUser = 0, CloudGroup = 1, CloudChannel = 2 }; enum Message { static let Cloud = 0 } }
protocol Peer { var id: PeerId { get } }
struct TelegramUser: Peer { let id: PeerId; let botInfo: Int?; let marker: Int; init(id: PeerId, bot: Bool, marker: Int = 0) { self.id = id; botInfo = bot ? 1 : nil; self.marker = marker }; init(user: Api.User) { self = user.peer } }
struct TelegramChannel: Peer { struct Flags: OptionSet { let rawValue: Int; static let isForum = Flags(rawValue: 1) }; let id: PeerId; let flags: Flags }
struct AuthorizedAccountState { let peerId: PeerId; let isTestingEnvironment: Bool }
struct PreferencesEntry { let value: Any; init<T>(_ value: T) { self.value = value }; func get<T>(_ type: T.Type) -> T? { return value as? T } }
let botBridgeHistoryKey = 1
protocol MessageAttribute { var associatedPeerIds: [PeerId] { get }; var associatedMessageIds: [MessageId] { get }; var associatedStoryIds: [StoryId] { get } }
struct ReplyMessageAttribute: MessageAttribute { let messageId: MessageId; let associatedPeerIds: [PeerId] = []; let associatedMessageIds: [MessageId] = []; let associatedStoryIds: [StoryId] = [] }
struct StoreMessageForwardInfo { let authorId: PeerId?; let sourceId: PeerId?; let sourceMessageId: MessageId? }
enum StoreMessageId { case Id(MessageId), Partial }
final class StoreMessage {
    let id: StoreMessageId; let authorId: PeerId?; let forwardInfo: StoreMessageForwardInfo?; let attributes: [MessageAttribute]; let marker: Int
    init(id: MessageId, marker: Int = 0) { self.id = .Id(id); self.marker = marker; authorId = nil; forwardInfo = nil; attributes = [] }
    init?(apiMessage: Api.Message, accountPeerId: PeerId, peerIsForum: Bool) {
        switch apiMessage { case let .message(data), let .messageService(data): self.id = .Id(data.id); marker = data.marker; authorId = data.author; forwardInfo = nil; attributes = data.attributes
        default: return nil }
    }
}
enum Api {
    struct ApiPeer { let peerId: PeerId }
    struct User { let peer: TelegramUser }
    struct Chat { let peer: TelegramChannel }
    struct MessageData { let id: MessageId; let marker: Int; let author: PeerId?; let attributes: [MessageAttribute]; let replyTo: MessageReplyHeader?; var peerId: ApiPeer { return ApiPeer(peerId: id.peerId) } }
    enum Message { case message(MessageData), messageService(MessageData), empty }
    struct ReplyHeader { let replyToPeerId: ApiPeer?; let replyFrom: MessageFwdHeader? }
    struct StoryReply { let peer: ApiPeer }
    enum MessageReplyHeader { case messageReplyHeader(ReplyHeader), messageReplyStoryHeader(StoryReply) }
    struct FwdHeader { let fromId: ApiPeer?; let savedFromPeer: ApiPeer?; let savedFromId: ApiPeer? }
    enum MessageFwdHeader { case messageFwdHeader(FwdHeader) }
    struct DeleteMessages { let messages: [Int32] }
    struct DeleteChannelMessages { let messages: [Int32]; let channelId: Int64 }
    enum Update { case updateDeleteMessages(DeleteMessages), updateDeleteChannelMessages(DeleteChannelMessages), mutation }
}
func apiMessagePeerIds(_ message: Api.Message) -> [PeerId] {
    switch message { case let .message(data), let .messageService(data): return [data.id.peerId] + (data.author.map { [$0] } ?? [])
    default: return [] }
}
var chatParseCount = 0
func parseTelegramGroupOrChannel(chat: Api.Chat) -> Peer? { chatParseCount += 1; return chat.peer }
final class MessagesRemovedContext {
    var interactive = Set<MessageId>(), remote = Set<MessageId>()
    func synchronouslyIsMessageDeletedInteractively(ids: [MessageId]) -> [MessageId] { return ids.filter { interactive.contains($0) } }
    func synchronouslyIsMessageDeletedRemotely(ids: [MessageId]) -> [MessageId] { return ids.filter { remote.contains($0) } }
}
final class Transaction {
    var state: AuthorizedAccountState; var peers: [PeerId: Peer]; var messages: [MessageId: StoreMessage] = [:]; var progress: PreferencesEntry?
    var onMessageExists: (() -> Void)?
    var mutationCalls = 0; var progressWrites = 0; var callbacks = 0; var inclusion: [PeerId: String] = [:]
    init(state: AuthorizedAccountState, peers: [PeerId: Peer], progress: BotBridgeHistoryProgress) { self.state = state; self.peers = peers; self.progress = PreferencesEntry(progress) }
    func getState() -> Any? { return state }
    func getPeer(_ id: PeerId) -> Peer? { return peers[id] }
    func getPreferencesEntry(key: Int) -> PreferencesEntry? { return progress }
    func updatePreferencesEntry(key: Int, _ f: (PreferencesEntry?) -> PreferencesEntry?) { progressWrites += 1; progress = f(progress) }
    func messageExists(id: MessageId) -> Bool { onMessageExists?(); return messages[id] != nil }
    func updatePeersInternal(_ values: [Peer], update: (Peer?, Peer) -> Peer?) { mutationCalls += 1; for peer in values { peers[peer.id] = update(peers[peer.id], peer) } }
    func addHistoricalMessagesWithoutInteractiveActions(_ values: [StoreMessage]) -> [Int64: MessageId] { mutationCalls += 1; for message in values { if case let .Id(id) = message.id { messages[id] = message } }; return [:] }
}
// Existing inclusion algorithm is tested independently; this boundary sentinel
// proves exactly which newly stored messages the real storage helper passes to it.
func jerkgramIncludeBotMessagePeers(transaction: Transaction, accountPeerId: PeerId, messages: [StoreMessage]) {
    for message in messages { if case let .Id(id) = message.id, transaction.inclusion[id.peerId] == nil { transaction.inclusion[id.peerId] = "root" } }
}
/* REAL_STORAGE */
func peer(_ n: Int64, _ namespace: Int = 0) -> PeerId { return PeerId(namespace: namespace, id: ._internalFromInt64Value(n)) }
let account = peer(1), chat = peer(2), absent = peer(3), unrelated = peer(4)
func id(_ n: Int32, _ p: PeerId = peer(2)) -> MessageId { return MessageId(peerId: p, namespace: 0, id: n) }
func api(_ n: Int32, marker: Int = 1, author: PeerId? = nil) -> Api.Message { return .message(Api.MessageData(id: id(n), marker: marker, author: author, attributes: [], replyTo: nil)) }
let cursor = BotBridgeCursor(pts: 100, qts: 4, date: 20, seq: 6)
func reservation() -> BotBridgeHistoryProgress { var p = BotBridgeHistoryProgress(owner: 7, peer: 1, testing: false, generation: "g1"); _ = p.reserve(now: 1000); _ = p.acceptState(cursor, unread: 10, now: 1001); _ = p.reserve(now: 1002); return p }
func transaction(_ p: BotBridgeHistoryProgress) -> Transaction { return Transaction(state: AuthorizedAccountState(peerId: account, isTestingEnvironment: false), peers: [account: TelegramUser(id: account, bot: true), chat: TelegramUser(id: chat, bot: false, marker: 77)], progress: p) }
let expected = reservation(); let t = transaction(expected); let removed = MessagesRemovedContext(); let lifetime = BotBridgeLifetime(); let gate = BotBridgeOnceGate()
// Edited, live, and retained deleted-placeholder markers are intentionally opaque
// to the storage facade; existence alone must preserve them.
t.messages[id(1)] = StoreMessage(id: id(1), marker: 101)
t.messages[id(2)] = StoreMessage(id: id(2), marker: 102)
t.messages[id(3)] = StoreMessage(id: id(3), marker: -1)
t.inclusion[chat] = "archive/pinned/cutoff=17"
removed.interactive.insert(id(5)); removed.remote.insert(id(6))
private let page = BotBridgeHistoryPage(cursor: BotBridgeCursor(pts: 95, qts: 4, date: 21, seq: 6), final: false,
    messages: [api(1), api(2), api(3), api(4, author: absent), api(4), api(5), api(6), api(7), .empty],
    users: [Api.User(peer: TelegramUser(id: chat, bot: false, marker: 999)), Api.User(peer: TelegramUser(id: absent, bot: false)), Api.User(peer: TelegramUser(id: unrelated, bot: false))], chats: [],
    updates: [.updateDeleteMessages(Api.DeleteMessages(messages: [7])), .mutation], encryptedCount: 0)
let result = importBotBridgeHistoryPage(transaction: t, page: page, expected: expected, accountPeerId: account, removed: removed, now: 1003, lifetime: lifetime, requestGate: gate)!
precondition(result.terminal == nil && result.committedPages == 1 && result.inserted == 1 && result.deletions == 1)
precondition(t.messages.count == 4 && t.messages[id(1)]?.marker == 101 && t.messages[id(2)]?.marker == 102 && t.messages[id(3)]?.marker == -1)
precondition(t.messages[id(4)] != nil && t.messages[id(5)] == nil && t.messages[id(6)] == nil && t.messages[id(7)] == nil)
precondition((t.peers[chat] as? TelegramUser)?.marker == 77 && t.peers[absent] != nil && t.peers[unrelated] == nil)
precondition(t.inclusion[chat] == "archive/pinned/cutoff=17" && t.state.peerId == account && t.callbacks == 0)
precondition(t.progress?.get(BotBridgeHistoryProgress.self) == result)
let staleCalls = t.mutationCalls
precondition(importBotBridgeHistoryPage(transaction: t, page: page, expected: expected, accountPeerId: account, removed: removed, now: 1004, lifetime: lifetime, requestGate: gate) == nil && t.mutationCalls == staleCalls)
let cancelled = transaction(expected); let dead = BotBridgeLifetime(); dead.cancel()
precondition(importBotBridgeHistoryPage(transaction: cancelled, page: page, expected: expected, accountPeerId: account, removed: removed, now: 1004, lifetime: dead, requestGate: gate) == nil && cancelled.mutationCalls == 0)
let ordinary = transaction(expected); ordinary.peers[account] = TelegramUser(id: account, bot: false)
precondition(importBotBridgeHistoryPage(transaction: ordinary, page: page, expected: expected, accountPeerId: account, removed: removed, now: 1004, lifetime: lifetime, requestGate: gate) == nil && ordinary.mutationCalls == 0)
let oversized = transaction(expected)
private let bigPage = BotBridgeHistoryPage(cursor: page.cursor, final: false, messages: page.messages, users: [], chats: [], updates: Array(repeating: .mutation, count: 10001), encryptedCount: 0)
precondition(importBotBridgeHistoryPage(transaction: oversized, page: bigPage, expected: expected, accountPeerId: account, removed: removed, now: 1004, lifetime: lifetime, requestGate: gate)?.terminal == .limit && oversized.mutationCalls == 0)
let nested = transaction(expected)
private let nestedPage = BotBridgeHistoryPage(cursor: page.cursor, final: false, messages: page.messages, users: [], chats: [], updates: [.updateDeleteMessages(Api.DeleteMessages(messages: Array(repeating: 7, count: 20001)))], encryptedCount: 0)
precondition(importBotBridgeHistoryPage(transaction: nested, page: nestedPage, expected: expected, accountPeerId: account, removed: removed, now: 1004, lifetime: lifetime, requestGate: gate)?.terminal == .limit && nested.mutationCalls == 0)
let aggregate = transaction(expected)
private let aggregatePage = BotBridgeHistoryPage(cursor: page.cursor, final: false, messages: page.messages, users: [], chats: [], updates: [.updateDeleteMessages(Api.DeleteMessages(messages: Array(repeating: 7, count: 10001))), .updateDeleteMessages(Api.DeleteMessages(messages: Array(repeating: 8, count: 10000)))], encryptedCount: 0)
precondition(importBotBridgeHistoryPage(transaction: aggregate, page: aggregatePage, expected: expected, accountPeerId: account, removed: removed, now: 1004, lifetime: lifetime, requestGate: gate)?.terminal == .limit && aggregate.mutationCalls == 0)
let conversion = transaction(expected)
let manyChats = (0..<10000).map { Api.Chat(peer: TelegramChannel(id: peer(Int64($0 + 10), 2), flags: [])) }
let manyMessages = (0..<5000).map { Api.Message.message(Api.MessageData(id: id(Int32($0 + 100), peer(999999)), marker: 1, author: nil, attributes: [], replyTo: nil)) } // absent cloud-user destination cannot match chats
private let conversionPage = BotBridgeHistoryPage(cursor: page.cursor, final: true, messages: manyMessages, users: [], chats: manyChats, updates: [], encryptedCount: 0)
chatParseCount = 0
precondition(importBotBridgeHistoryPage(transaction: conversion, page: conversionPage, expected: expected, accountPeerId: account, removed: removed, now: 1004, lifetime: lifetime, requestGate: gate)?.inserted == 5000)
precondition(chatParseCount == manyChats.count, "each bounded response chat converted exactly once")
print("PASS real storage helper: existing/live/edited/placeholder preservation, duplicates, missing peers, deletion exclusions, unrelated updates, generation/token guards, bounds, atomic progress")
