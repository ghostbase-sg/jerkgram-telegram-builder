import Foundation
// Deterministic UI/Postbox/transport boundaries. The ENTIRE production history
// coordinator, content types, delivery queue and page provider are inserted.
// Boundaries deliberately retain cancelled subscribers to test late callbacks.
public enum NoError: Error {}
public protocol Disposable { func dispose() }
final class ActionDisposable: Disposable {
    var action: (() -> Void)?
    init(_ action: @escaping () -> Void = {}) { self.action = action }
    func dispose() { let action = self.action; self.action = nil; action?() }
}
final class MetaDisposable: Disposable {
    private var current: Disposable?
    private var disposed = false
    func set(_ value: Disposable?) {
        if self.disposed { value?.dispose(); return }
        let old = self.current; self.current = value; old?.dispose()
    }
    func dispose() { self.disposed = true; self.set(nil); self.current?.dispose(); self.current = nil }
}
let EmptyDisposable: Disposable = ActionDisposable()
final class Subscriber<T, E: Error> {
    let next: (T) -> Void
    let completed: () -> Void
    init(next: @escaping (T) -> Void, completed: @escaping () -> Void) { self.next = next; self.completed = completed }
    func putNext(_ value: T) { self.next(value) }
    func putCompletion() { self.completed() }
}
public final class Signal<T, E: Error> {
    let generator: (Subscriber<T, E>) -> Disposable
    init(_ generator: @escaping (Subscriber<T, E>) -> Disposable) { self.generator = generator }
    func start(next: @escaping (T) -> Void, completed: @escaping () -> Void = {}) -> Disposable { return self.generator(Subscriber(next: next, completed: completed)) }
    static func single(_ value: T) -> Signal<T, E> { return Signal { subscriber in subscriber.putNext(value); return EmptyDisposable } }
}
final class Pipe<T> {
    var subscribers: [Subscriber<T, NoError>] = []
    var current: T?
    func signal() -> Signal<T, NoError> { return Signal { subscriber in
        self.subscribers.append(subscriber)
        if let value = self.current { subscriber.putNext(value) }
        return ActionDisposable() // Intentionally allow sends after disposal.
    } }
    func send(_ value: T) { self.current = value; for subscriber in self.subscribers { subscriber.putNext(value) } }
}
final class Promise<T> {
    let pipe = Pipe<T>()
    func set(_ signal: Signal<T, NoError>) { _ = signal.start(next: { self.pipe.send($0) }) }
    func get() -> Signal<T, NoError> { return self.pipe.signal() }
}
infix operator |> : AdditionPrecedence
func |> <T, U>(value: T, f: (T) -> U) -> U { return f(value) }
func deliverOnMainQueue<T>(_ signal: Signal<T, NoError>) -> Signal<T, NoError> { return signal }
public struct MessageId: Hashable { public let value: Int }
public struct MessageIndex: Comparable {
    public let id: MessageId
    public static func < (lhs: Self, rhs: Self) -> Bool { return lhs.id.value < rhs.id.value }
}
public final class Message {
    public let id: MessageId
    public let text: String
    public let index: MessageIndex
    public let timestamp: Int32 = 100
    public let threadId: Int64? = nil
    init(_ id: Int, _ text: String) { self.id = MessageId(value: id); self.index = MessageIndex(id: self.id); self.text = text }
}
public struct LocalSavedTag { let id: String }
public struct LocalSavedTagsCatalogue { let tags: [LocalSavedTag]; let revision: Int64 }
public enum LocalSavedTagsError: Error { case invalidPage, unavailable }
public enum LocalSavedTagsDirection: Equatable { case earlier, later }
public struct LocalSavedTagMessage: Equatable { let id: MessageId }
public struct LocalSavedTagsCursor: Equatable { let boundary: Int; let revision: Int64 }
public struct LocalSavedTagsPage {
    let messages: [LocalSavedTagMessage]
    let earlier: LocalSavedTagsCursor?
    let later: LocalSavedTagsCursor?
    let revision: Int64
}
/* EXACT_CONTENT_TYPES */
/* EXACT_DELIVERY */
public enum ViewUpdateType { case Initial, Generic }
struct MutableMessageHistoryEntryAttributes { init(authorIsContact: Bool) {} }
struct MessageHistoryEntry {
    let message: Message
    init(message: Message, isRead: Bool, location: Int?, monthLocation: Int?, attributes: MutableMessageHistoryEntryAttributes) { self.message = message }
}
struct MessageHistoryView {
    enum Namespaces { case all }
    let entries: [MessageHistoryEntry]
    init(tag: Int?, namespaces: Namespaces, entries: [MessageHistoryEntry], holeEarlier: Bool, holeLater: Bool, isLoading: Bool) { self.entries = entries }
}
enum PostboxViewKey: Hashable { case messages(Set<MessageId>) }
protocol PostboxView {}
final class MessagesView: PostboxView { let messages: [MessageId: Message]; init(_ messages: [MessageId: Message]) { self.messages = messages } }
struct CombinedView { let views: [PostboxViewKey: Any] }
final class Postbox {
    struct Observation { let ids: Set<MessageId>; let pipe: Pipe<CombinedView> }
    var observations: [Observation] = []
    var cache: [MessageId: Message] = [:]
    func combinedView(keys: [PostboxViewKey]) -> Signal<CombinedView, NoError> {
        guard keys.count == 1, case let .messages(ids) = keys[0] else { fatalError("unbounded view") }
        require(ids.count <= 135, "retained message observation exceeded135")
        let pipe = Pipe<CombinedView>()
        self.observations.append(Observation(ids: ids, pipe: pipe))
        pipe.current = CombinedView(views: [keys[0]: MessagesView(self.cache.filter { ids.contains($0.key) })])
        return pipe.signal()
    }
    func send(_ observation: Int, overrides: [MessageId: Message]? = nil) {
        let record = self.observations[observation]
        let messages = overrides ?? self.cache.filter { record.ids.contains($0.key) }
        record.pipe.send(CombinedView(views: [.messages(record.ids): MessagesView(messages)]))
    }
}
final class Account {
    let id = 7
    let peerId = 11
    let testingEnvironment = false
    let postbox = Postbox()
    var service: LocalSavedTagsService?
}
struct AccountContexts { let primary: AccountContext? }
final class PresentationStrings {}
struct PresentationData { let strings = PresentationStrings() }
final class Holder<T> {
    let value: T
    init(_ value: T) { self.value = value }
    func with<U>(_ f: (T) -> U) -> U { return f(self.value) }
}
final class SharedContext {
    let accounts = Pipe<AccountContexts>()
    var activeAccountContexts: Signal<AccountContexts, NoError> { return self.accounts.signal() }
    let currentPresentationData = Holder(PresentationData())
}
public protocol TelegramEngineDataItem { associatedtype Result }
protocol PostboxViewDataItem { associatedtype Result; var key: PostboxViewKey { get }; func extract(view: PostboxView) -> Result }
public final class EngineMessage {
    public typealias Id = MessageId
    private let message: Message
    public init(_ message: Message) { self.message = message }
    func _asMessage() -> Message { return self.message }
}
public enum TelegramEngine {
    public enum EngineData {
        public enum Item {
            public enum Messages {
                /* EXACT_ENGINE_MESSAGES_ITEM */
            }
        }
    }
}
// Engine subscription boundary: the exact upstream item above supplies its
// single batched key and extraction. Postbox and delivery remain deterministic.
final class EngineDataBoundary {
    let postbox: Postbox
    init(_ postbox: Postbox) { self.postbox = postbox }
    func subscribe(_ item: TelegramEngine.EngineData.Item.Messages.Messages) -> Signal<[MessageId: EngineMessage], NoError> {
        return Signal { subscriber in
            self.postbox.combinedView(keys: [item.key]).start(next: { view in
                subscriber.putNext(item.extract(view: view.views[item.key] as! PostboxView))
            })
        }
    }
}
final class EngineBoundary {
    let data: EngineDataBoundary
    init(_ postbox: Postbox) { self.data = EngineDataBoundary(postbox) }
}
final class AccountContext {
    let account = Account()
    let sharedContext = SharedContext()
    lazy var engine = EngineBoundary(self.account.postbox)
}
struct JerkgramSavedTagsStrings {
    init(_ strings: PresentationStrings) {}
    func text(_ en: String, _ ru: String) -> String { return en }
}
final class LocalSavedTagsService {
    struct Request { let cursor: LocalSavedTagsCursor?; let direction: LocalSavedTagsDirection; let subscriber: Subscriber<LocalSavedTagsPageEvent, NoError> }
    let delivery = LocalSavedTagsDelivery()
    let catalogue = Pipe<Result<LocalSavedTagsCatalogue, LocalSavedTagsError>>()
    var requests: [Request] = []
    init(account: Account) { account.service = self }
    func dispose() {}
    func catalogueUpdates() -> Signal<Result<LocalSavedTagsCatalogue, LocalSavedTagsError>, NoError> { return self.catalogue.signal() }
    func makePageProvider(tagId: String) -> LocalSavedTagsPageProvider { return LocalSavedTagsPageProvider(service: self, tagId: tagId) }
    fileprivate func bind<T>(_ signal: Signal<T, NoError>) -> Signal<T, NoError> { return signal }
    fileprivate func page(tagId: String, cursor: LocalSavedTagsCursor?, direction: LocalSavedTagsDirection) -> Signal<LocalSavedTagsPageEvent, NoError> {
        return Signal { subscriber in self.requests.append(Request(cursor: cursor, direction: direction, subscriber: subscriber)); return ActionDisposable() }
    }
}
/* EXACT_PAGE_PROVIDER */
/* EXACT_COORDINATOR */
func require(_ condition: Bool, _ message: String) { if !condition { fatalError(message) } }
func respond(_ service: LocalSavedTagsService, _ request: Int, _ context: AccountContext, newest: Int, unavailable: Set<Int> = [], revision: Int64 = 1) {
    let ids = Array(stride(from: newest, through: newest - 44, by: -1))
    let entries = ids.map { LocalSavedTagMessage(id: MessageId(value: $0)) }
    let rows = zip(ids, entries).map { id, entry -> LocalSavedTagsContentRow in
        let message: Message? = unavailable.contains(id) ? nil : Message(id, "caption-\(id)")
        if let message { context.account.postbox.cache[entry.id] = message }
        return LocalSavedTagsContentRow(entry: entry, message: message)
    }
    let page = LocalSavedTagsPage(messages: entries, earlier: LocalSavedTagsCursor(boundary: newest - 44, revision: revision), later: newest == 600 ? nil : LocalSavedTagsCursor(boundary: newest, revision: revision), revision: revision)
    service.requests[request].subscriber.putNext(.result(LocalSavedTagsContentPage(page: page, rows: rows, windows: [], earlier: page.earlier, later: page.later)))
}
let context = AccountContext()
context.sharedContext.accounts.current = AccountContexts(primary: context)
let history = JerkgramLocalSavedTagsHistory(context: context, tagId: "A", cleared: {})
let service = context.account.service!
var snapshots: [MessageHistoryView] = []
let observation = history.signal.start(next: { snapshots.append($0.0) })
service.catalogue.send(.success(LocalSavedTagsCatalogue(tags: [LocalSavedTag(id: "A")], revision: 1)))
respond(service, 0, context, newest: 600)
require(!context.account.postbox.observations.isEmpty, "retained IDs have no live observation")
let oldestObservation = context.account.postbox.observations.count - 1
for (request, newest) in [(1,555), (2,510), (3,465)] {
    require(history.loadBoundary(earlier: true), "missing indexed older boundary")
    respond(service, request, context, newest: newest, unavailable: newest == 465 ? [450] : [])
}
require(snapshots.last!.entries.count == 134, "unavailable membership was fabricated/dropped from bounds")
let viewCount = context.account.postbox.observations.count
let pageCount = service.requests.count
let edited = Message(465, "edited caption, same timestamp and thread")
context.account.postbox.cache[edited.id] = edited
context.account.postbox.send(viewCount - 1)
require(snapshots.last!.entries.first(where: { $0.message.id == edited.id })?.message.text == edited.text, "ordinary unchanged-metadata caption edit stayed stale")
require(service.requests.count == pageCount, "edit triggered page/catalogue work")
require(context.account.postbox.observations.count == viewCount, "same retained IDs recreated observation")
let beforeLate = snapshots.count
context.account.postbox.send(oldestObservation, overrides: [MessageId(value: 600): Message(600,"late evicted edit")])
require(snapshots.count == beforeLate, "late evicted-window observer published")
history.retry()
require(service.requests.last!.cursor == LocalSavedTagsCursor(boundary: 466, revision: 1), "unavailable older page retry jumped to newest/nil cursor")
require(service.requests.last!.direction == .earlier, "older retry direction changed")
respond(service, 4, context, newest: 465)
require(snapshots.last!.entries.count == 45 && snapshots.last!.entries.allSatisfy { (421...465).contains($0.message.id.value) }, "retry did not load the actual unavailable page IDs")
require(history.loadBoundary(earlier: true), "failed older request not admitted")
service.requests[5].subscriber.putNext(.failure(.unavailable))
history.retry()
require(service.requests[6].cursor == LocalSavedTagsCursor(boundary: 421, revision: 1), "failed older page retry jumped to newest")
respond(service, 6, context, newest: 420)
// Same IDs can reappear after a catalogue reset. The subscription generation,
// not merely set equality, must reject the first window's queued callback.
service.catalogue.send(.success(LocalSavedTagsCatalogue(tags: [LocalSavedTag(id: "A")], revision: 2)))
respond(service, 7, context, newest: 600, revision: 2)
let beforeRepeatedIdsLate = snapshots.count
context.account.postbox.send(oldestObservation, overrides: [MessageId(value: 600): Message(600,"obsolete same-ID generation")])
require(snapshots.count == beforeRepeatedIdsLate, "same-ID window accepted an obsolete observer generation")
let beforeDispose = snapshots.count
context.sharedContext.accounts.send(AccountContexts(primary: nil))
context.account.postbox.send(context.account.postbox.observations.count - 1)
service.requests[7].subscriber.putNext(.failure(.unavailable))
require(snapshots.count == beforeDispose, "account-disposed history published late observer/page update")
require(context.account.postbox.observations.allSatisfy { $0.ids.count <= 135 }, "observation escaped retained bound")
observation.dispose()
print("PASS exact full native coordinator ordinary edits / retained IDs / older retry / failed retry / eviction / account fences")
