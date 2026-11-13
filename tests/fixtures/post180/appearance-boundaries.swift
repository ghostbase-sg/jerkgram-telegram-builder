// Only external scheduling/Postbox/peer boundaries are facades. The store and
// settings below are compiled verbatim; PreferencesEntry uses the pinned codec.
public enum NoError: Error {}
public protocol Disposable { func dispose() }
public final class ActionDisposable: Disposable {
    var action: (() -> Void)?
    init(_ action: @escaping () -> Void = {}) { self.action = action }
    public func dispose() { let f = action; action = nil; f?() }
}
public final class MetaDisposable: Disposable {
    var item: Disposable?
    public func set(_ value: Disposable?) { item?.dispose(); item = value }
    public func dispose() { set(nil) }
}
public final class Atomic<T> {
    var value: T
    public init(value: T) { self.value = value }
    public func with<R>(_ f: (T) -> R) -> R { f(value) }
    public func modify(_ f: (T) -> T) -> T { value = f(value); return value }
}
public final class Signal<T, E: Error> {
    let subscribe: (@escaping (T) -> Void) -> Disposable
    init(_ subscribe: @escaping (@escaping (T) -> Void) -> Disposable) { self.subscribe = subscribe }
    public func start(next: ((T) -> Void)? = nil) -> Disposable { subscribe(next ?? { _ in }) }
}
public final class ValuePromise<T: Equatable> {
    var value: T; var observers: [Int: (T) -> Void] = [:]; var serial = 0
    init(_ value: T, ignoreRepeated: Bool) { self.value = value }
    func set(_ next: T) { if value == next { return }; value = next; for f in Array(observers.values) { f(next) } }
    func get() -> Signal<T, NoError> {
        Signal { [self] next in
            serial += 1; let id = serial; observers[id] = next; next(value)
            return ActionDisposable { [weak self] in self?.observers.removeValue(forKey: id) }
        }
    }
}
infix operator |> : AdditionPrecedence
public func |> <A, B>(lhs: A, rhs: (A) -> B) -> B { rhs(lhs) }
public func deliverOnMainQueue<T>(_ signal: Signal<T, NoError>) -> Signal<T, NoError> { signal }
public func combineLatest<A, B>(_ a: Signal<A, NoError>, _ b: Signal<B, NoError>) -> Signal<(A, B), NoError> {
    Signal { next in
        var va: A?; var vb: B?
        let da = a.start(next: { v in va = v; if let vb { next((v, vb)) } })
        let db = b.start(next: { v in vb = v; if let va { next((va, v)) } })
        return ActionDisposable { da.dispose(); db.dispose() }
    }
}
public final class Queue { public static func mainQueue() -> Queue { Queue() } }
var wall: Double = 1000
public enum SwiftSignalKit {
    public final class Timer {
        static var live: [Timer] = []
        let deadline: Double; let completion: () -> Void; var valid = false
        public init(timeout: Double, repeat: Bool, completion: @escaping () -> Void, queue: Queue) { deadline = wall + timeout; self.completion = completion }
        public func start() { valid = true; Self.live.append(self) }
        public func invalidate() { valid = false; Self.live.removeAll { $0 === self } }
        static func advance(_ timestamp: Double) {
            wall = timestamp
            for timer in Array(live) where timer.valid && timer.deadline <= wall { timer.invalidate(); timer.completion() }
        }
    }
}
public struct PeerId: Hashable { let raw: Int64; public func toInt64() -> Int64 { raw } }
public protocol Peer: AnyObject { var id: PeerId { get } }
public struct PeerNameColor: Equatable { public let rawValue: Int32; public init(rawValue: Int32) { self.rawValue = rawValue } }
public enum PeerColor: Equatable { case preset(PeerNameColor) }
public struct PeerEmojiStatus: Equatable {
    public enum Content: Equatable { case emoji(fileId: Int64) }
    public let content: Content; public let expirationDate: Int32?
    public init(content: Content, expirationDate: Int32?) { self.content = content; self.expirationDate = expirationDate }
}
public final class TelegramUser: Peer, Equatable {
    static var copies = 0
    public let id: PeerId; public let botInfo: Bool?
    var emojiStatus: PeerEmojiStatus?; var nameColor: PeerColor?; var profileColor: PeerNameColor?; var reply: Int64?; var background: Int64?
    init(_ id: Int64, bot: Bool = false) { self.id = PeerId(raw: id); botInfo = bot ? true : nil }
    func clone() -> TelegramUser { Self.copies += 1; let u = TelegramUser(id.raw, bot: botInfo != nil); u.emojiStatus = emojiStatus; u.nameColor = nameColor; u.profileColor = profileColor; u.reply = reply; u.background = background; return u }
    public func withUpdatedEmojiStatus(_ s: PeerEmojiStatus?) -> TelegramUser { let u = clone(); u.emojiStatus = s; return u }
    public func withUpdatedNameColor(_ c: PeerColor) -> TelegramUser { let u = clone(); u.nameColor = c; return u }
    public func withUpdatedProfileColor(_ c: PeerNameColor?) -> TelegramUser { let u = clone(); u.profileColor = c; return u }
    public func withUpdatedBackgroundEmojiId(_ e: Int64?) -> TelegramUser { let u = clone(); u.reply = e; return u }
    public func withUpdatedProfileBackgroundEmojiId(_ e: Int64?) -> TelegramUser { let u = clone(); u.background = e; return u }
    public static func ==(a: TelegramUser, b: TelegramUser) -> Bool { a.id == b.id && a.botInfo == b.botInfo && a.emojiStatus == b.emojiStatus && a.nameColor == b.nameColor && a.profileColor == b.profileColor && a.reply == b.reply && a.background == b.background }
}
public enum EnginePeer: Equatable {
    case user(TelegramUser)
    public init(_ peer: Peer) { self = .user(peer as! TelegramUser) }
    public func _asPeer() -> Peer { switch self { case let .user(u): return u } }
}
public struct EngineRawMessage {
    public let id: Int64; public let text: String; public let peers: [PeerId: Peer]; public let author: Peer?
    public func withUpdatedPeers(_ p: [PeerId: Peer]) -> Self { Self(id: id, text: text, peers: p, author: author) }
    public func withUpdatedAuthor(_ p: Peer?) -> Self { Self(id: id, text: text, peers: peers, author: p) }
}
public final class AuthorizedAccountState { let peerId: PeerId; let isTestingEnvironment: Bool; init(_ peerId: PeerId, _ testing: Bool) { self.peerId = peerId; isTestingEnvironment = testing } }
public struct PreferencesView: Equatable {
    let values: [ValueBoxKey: PreferencesEntry]
    public static func ==(a: Self, b: Self) -> Bool { a.values.mapValues { $0.data } == b.values.mapValues { $0.data } }
}
public final class Transaction {
    let box: Postbox
    init(_ box: Postbox) { self.box = box }
    func getState() -> Any? { box.state }
    func getPeer(_ id: PeerId) -> Peer? { box.user.id == id ? box.user : nil }
    func updatePreferencesEntry(key: ValueBoxKey, _ update: (PreferencesEntry?) -> PreferencesEntry?) {
        var values = box.preferences.value.values; values[key] = update(values[key]); box.preferences.set(PreferencesView(values: values)); box.writes += 1
    }
}
public final class Postbox {
    let preferences = ValuePromise(PreferencesView(values: [:]), ignoreRepeated: true)
    let peer: ValuePromise<EnginePeer?>
    var user: TelegramUser; var state: AuthorizedAccountState?; var reads = 0; var writes = 0
    var pending: [() -> Void] = []
    init(_ user: TelegramUser, testing: Bool) { self.user = user; peer = ValuePromise(.user(user), ignoreRepeated: true); state = AuthorizedAccountState(user.id, testing) }
    func preferencesView(keys: [ValueBoxKey]) -> Signal<PreferencesView, NoError> { reads += 1; return preferences.get() }
    func transaction<T>(_ body: @escaping (Transaction) -> T) -> Signal<T, NoError> {
        Signal { [self] next in
            var cancelled = false
            pending.append { if !cancelled { next(body(Transaction(self))) } }
            return ActionDisposable { cancelled = true }
        }
    }
    func drain() { let jobs = pending; pending = []; for job in jobs { job() } }
}
public final class Account {
    public struct Id { let int64: Int64 }
    let id: Id; let peerId: PeerId; let testingEnvironment: Bool; let postbox: Postbox
    init(_ record: Int64, _ peer: Int64, bot: Bool = false, testing: Bool = false) { id = Id(int64: record); peerId = PeerId(raw: peer); testingEnvironment = testing; postbox = Postbox(TelegramUser(peer, bot: bot), testing: testing) }
}
public final class TelegramEngine {
    public enum EngineData { public enum Item { public enum Peer { public struct Peer { let id: PeerId } } } }
    final class DataAccess {
        let account: Account; init(_ account: Account) { self.account = account }
        func subscribe(_ item: EngineData.Item.Peer.Peer) -> Signal<EnginePeer?, NoError> { account.postbox.peer.get() }
    }
    let data: DataAccess
    public init(account: Account) { data = DataAccess(account) }
}
