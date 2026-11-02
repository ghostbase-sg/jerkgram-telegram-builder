// This fixture replaces queue/clock, transport I/O, and transaction scheduling.
// BotBridgeHistoryController, response adapter, policy, and storage are inserted
// verbatim from production. No history/reservation/import algorithm lives here.
/* SHARED_STORAGE_FACADES */

protocol Disposable { func dispose() }
struct EmptyDisposableValue: Disposable { func dispose() {} }
let EmptyDisposable = EmptyDisposableValue()
final class ActionDisposable: Disposable {
    private var action: (() -> Void)?
    init(_ action: @escaping () -> Void) { self.action = action }
    func dispose() { let action = self.action; self.action = nil; action?() }
}
final class MetaDisposable: Disposable {
    private var current: Disposable?; private var disposed = false
    func set(_ value: Disposable?) { if disposed { value?.dispose() } else { let old = current; current = value; old?.dispose() } }
    func dispose() { guard !disposed else { return }; disposed = true; let old = current; current = nil; old?.dispose() }
}
enum NoError: Error {}
struct RpcFailure: Error {}
final class Subscriber<T, E: Error> {
    let next: (T) -> Void; let error: (E) -> Void; let completion: () -> Void
    init(next: @escaping (T) -> Void, error: @escaping (E) -> Void, completed: @escaping () -> Void) { self.next = next; self.error = error; self.completion = completed }
    // Deliberately permit hostile late callbacks after disposal; the production
    // controller must reject them with its own lifetime/request gates.
    func putNext(_ value: T) { next(value) }
    func putError(_ value: E) { error(value) }
    func putCompletion() { completion() }
}
final class Signal<T, E: Error> {
    let generator: (Subscriber<T, E>) -> Disposable
    init(_ generator: @escaping (Subscriber<T, E>) -> Disposable) { self.generator = generator }
    func start(next: @escaping (T) -> Void = { _ in }, error: @escaping (E) -> Void = { _ in }, completed: @escaping () -> Void = {}) -> Disposable {
        return generator(Subscriber(next: next, error: error, completed: completed))
    }
}
infix operator |> : AdditionPrecedence
func |> <A, B>(value: A, transform: (A) -> B) -> B { return transform(value) }
func deliverOn<T, E: Error>(_ queue: Queue) -> (Signal<T, E>) -> Signal<T, E> {
    return { signal in Signal { subscriber in
        signal.start(next: { value in queue.async { subscriber.putNext(value) } }, error: { error in queue.async { subscriber.putError(error) } }, completed: { queue.async { subscriber.putCompletion() } })
    } }
}
final class Queue {
    var now: Double = 0
    var tasks: [() -> Void] = []
    var timers: [SwiftSignalKit.Timer] = []
    func async(_ f: @escaping () -> Void) { tasks.append(f) }
    func isCurrent() -> Bool { return true }
    @discardableResult func runOne() -> Bool { guard !tasks.isEmpty else { return false }; let f = tasks.removeFirst(); f(); return true }
    func drain() { var steps = 0; while runOne() { steps += 1; precondition(steps < 10000, "scheduler failed to quiesce") } }
    func advance(_ seconds: Double) {
        now += seconds
        for timer in timers where timer.active && timer.due <= now {
            timer.active = false
            async(timer.completion)
        }
        drain()
    }
}
enum SwiftSignalKit {
    final class Timer {
        let timeout: Double; let completion: () -> Void; let queue: Queue
        var due: Double = 0; var active = false
        init(timeout: Double, repeat: Bool, completion: @escaping () -> Void, queue: Queue) { precondition(!`repeat`); self.timeout = timeout; self.completion = completion; self.queue = queue }
        func start() { due = queue.now + timeout; active = true; queue.timers.append(self) }
        func invalidate() { active = false }
    }
}
// The custom-operation boundary has the same serial completion contract as the
// unchanged manager. It supplies no retry, cursor, reservation or storage logic.
final class ManagerFacade {
    let queue: Queue
    var operations: [() -> Void] = []
    var running = false
    var customStarts = 0, customCompletions = 0, modernRuns = 0
    init(_ queue: Queue) { self.queue = queue }
    func enqueue(_ signal: Signal<Void, NoError>) {
        operations.append { [unowned self] in
            customStarts += 1
            let _ = signal.start(completed: { [unowned self] in
                precondition(running, "custom operation completed more than once")
                running = false; customCompletions += 1
                queue.async { [unowned self] in pump() }
            })
        }
        queue.async { [unowned self] in pump() }
    }
    func modern(_ f: @escaping () -> Void = {}) {
        operations.append { [unowned self] in modernRuns += 1; f(); running = false; queue.async { [unowned self] in pump() } }
        queue.async { [unowned self] in pump() }
    }
    func pump() { guard !running, !operations.isEmpty else { return }; running = true; let op = operations.removeFirst(); op() }
}
final class Postbox {
    let value: Transaction; let queue: Queue
    var holdNext = false
    var held: [() -> Void] = []
    var executions = 0
    init(_ value: Transaction, _ queue: Queue) { self.value = value; self.queue = queue }
    func transaction<T>(_ f: @escaping (Transaction) -> T) -> Signal<T, NoError> {
        return Signal { subscriber in
            let action = { [self] in executions += 1; subscriber.putNext(f(value)); subscriber.putCompletion() }
            if self.holdNext { self.holdNext = false; self.held.append(action) } else { self.queue.async(action) }
            // Mirrors the inspected Postbox closure contract: disposal cannot
            // remove a suspended DB closure. It can still run after timeout.
            return EmptyDisposable
        }
    }
    func releaseHeld() { let values = held; held.removeAll(); for f in values { queue.async(f) } }
}
struct TestRequest<T> { let name: String; let cursor: BotBridgeCursor? }
extension Api {
    enum updates {
        struct StateData { let pts: Int32, qts: Int32, date: Int32, seq: Int32, unreadCount: Int32 }
        enum State { case state(StateData) }
        struct FinalData { let state: State; let newMessages: [Api.Message]; let users: [Api.User]; let chats: [Api.Chat]; let otherUpdates: [Api.Update]; let newEncryptedMessages: [Int] }
        struct SliceData { let intermediateState: State; let newMessages: [Api.Message]; let users: [Api.User]; let chats: [Api.Chat]; let otherUpdates: [Api.Update]; let newEncryptedMessages: [Int] }
        struct EmptyData { let date: Int32, seq: Int32 }
        enum Difference { case difference(FinalData), differenceSlice(SliceData), differenceEmpty(EmptyData), differenceTooLong(Int32) }
    }
    enum functions {
        enum updates {
            static func getState() -> TestRequest<Api.updates.State> { return TestRequest(name: "updates.getState", cursor: nil) }
            static func getDifference(flags: Int32, pts: Int32, ptsLimit: Int32?, ptsTotalLimit: Int32?, date: Int32, qts: Int32, qtsLimit: Int32?) -> TestRequest<Api.updates.Difference> {
                precondition(flags == 0 && ptsLimit == nil && ptsTotalLimit == nil && qtsLimit == nil)
                return TestRequest(name: "updates.getDifference", cursor: BotBridgeCursor(pts: pts, qts: qts, date: date, seq: 0))
            }
        }
    }
}
final class TransportRecord {
    let name: String; let cursor: BotBridgeCursor?; let response: (Any) -> Void; let error: () -> Void
    var disposals = 0
    init(name: String, cursor: BotBridgeCursor?, response: @escaping (Any) -> Void, error: @escaping () -> Void) { self.name = name; self.cursor = cursor; self.response = response; self.error = error }
}
final class Network {
    var requests: [TransportRecord] = []
    var onSubscribe: (() -> Void)?
    func request<T>(_ request: TestRequest<T>, automaticFloodWait: Bool) -> Signal<T, RpcFailure> {
        precondition(!automaticFloodWait)
        return Signal { subscriber in
            self.onSubscribe?()
            let record = TransportRecord(name: request.name, cursor: request.cursor, response: { subscriber.putNext($0 as! T) }, error: { subscriber.putError(RpcFailure()) })
            self.requests.append(record)
            return ActionDisposable { record.disposals += 1 }
        }
    }
}
/* REAL_CONTROLLER_AND_DEPENDENCIES */

func check(_ condition: @autoclosure () -> Bool, _ message: String) { precondition(condition(), message) }
func peer(_ n: Int64) -> PeerId { return PeerId(namespace: 0, id: ._internalFromInt64Value(n)) }
let account = peer(1), destination = peer(2)
func messageId(_ n: Int32) -> MessageId { return MessageId(peerId: destination, namespace: 0, id: n) }
func apiMessage(_ n: Int32) -> Api.Message { return .message(Api.MessageData(id: messageId(n), marker: 8, author: nil, attributes: [], replyTo: nil)) }
func state(_ pts: Int32 = 100, unread: Int32 = 10, date: Int32 = 20) -> Api.updates.State { return .state(Api.updates.StateData(pts: pts, qts: 4, date: date, seq: 6, unreadCount: unread)) }
func difference(_ pts: Int32, slice: Bool = false, messages: [Api.Message] = [], updates: [Api.Update] = []) -> Api.updates.Difference {
    if slice { return .differenceSlice(Api.updates.SliceData(intermediateState: state(pts, date: 21), newMessages: messages, users: [], chats: [], otherUpdates: updates, newEncryptedMessages: [])) }
    return .difference(Api.updates.FinalData(state: state(pts, date: 21), newMessages: messages, users: [], chats: [], otherUpdates: updates, newEncryptedMessages: []))
}
final class Clock { var offset: Double = 1000 }
final class EventSink { var values: [BotBridgeHistoryEvent] = [] }
final class Host {
    let queue = Queue(); let clock = Clock(); let sink = EventSink()
    let network = Network(); let removed = MessagesRemovedContext()
    let transaction: Transaction
    let postbox: Postbox; let manager: ManagerFacade
    var lifetime = BotBridgeLifetime()
    var controller: BotBridgeHistoryController?
    init(bot: Bool = true, progress: BotBridgeHistoryProgress? = nil) {
        let initial = progress ?? BotBridgeHistoryProgress(owner: 7, peer: 1, testing: false, generation: "g1")
        transaction = Transaction(state: AuthorizedAccountState(peerId: account, isTestingEnvironment: false), peers: [account: TelegramUser(id: account, bot: bot), destination: TelegramUser(id: destination, bot: false)], progress: initial)
        postbox = Postbox(transaction, queue); manager = ManagerFacade(queue)
    }
    var progress: BotBridgeHistoryProgress { return transaction.progress!.get(BotBridgeHistoryProgress.self)! }
    func start() {
        let lifetime = self.lifetime
        guard let initial = jerkgramPrepareBotBridgeHistory(transaction: transaction, owner: 7, accountPeerId: account, lifetime: lifetime) else { return }
        let queue = self.queue, manager = self.manager, clock = self.clock, sink = self.sink
        controller = BotBridgeHistoryController(queue: queue, postbox: postbox, network: network, accountPeerId: account, initialProgress: initial, removed: removed, lifetime: lifetime, enqueue: { manager.enqueue($0) }, wall: { clock.offset + queue.now }, monotonic: { queue.now }, event: { sink.values.append($0) })
        controller!.start()
    }
    func crash() { controller = nil; queue.drain() }
    func restart() { lifetime = BotBridgeLifetime(); start(); queue.drain() }
    func reply(_ value: Any, at index: Int? = nil) { network.requests[index ?? (network.requests.count - 1)].response(value); queue.drain() }
    func seedToDifference() { start(); queue.drain(); reply(state()); check(network.requests.last?.name == "updates.getDifference", "state -> difference") }
    func finished(_ reason: BotBridgeHistoryReason) { check(progress.terminal == reason, "terminal reason \(reason)"); check(!manager.running && manager.customStarts == manager.customCompletions, "no custom operation leak") }
}

// R1: suspended reservation cannot hold modern processing; stale DB closure has
// no mutation or dispatch when later released, even though disposal cannot remove it.
do {
    let h = Host(); h.postbox.holdNext = true; h.start(); h.manager.modern(); h.queue.drain()
    check(h.network.requests.isEmpty && h.manager.running && h.postbox.held.count == 1, "reservation held")
    h.queue.advance(10)
    check(h.manager.modernRuns == 1 && !h.manager.running, "watchdog released serialized manager")
    check(!h.progress.reservedState && h.progress.terminal == .timeout, "no reservation was granted")
    let writes = h.transaction.progressWrites, mutations = h.transaction.mutationCalls
    h.postbox.releaseHeld(); h.queue.drain()
    check(h.transaction.progressWrites == writes && h.transaction.mutationCalls == mutations && h.network.requests.isEmpty, "stale reservation cannot mutate or dispatch")
    h.finished(.timeout)
}
// Time already spent awaiting reservation is not renewed at dispatch.
do {
    let h = Host(); h.postbox.holdNext = true; h.start(); h.queue.drain(); h.queue.advance(9)
    h.postbox.releaseHeld(); h.queue.drain(); check(h.network.requests.count == 1, "reservation dispatched within existing lease")
    h.queue.advance(1); h.finished(.timeout)
    check(h.network.requests[0].disposals == 1, "reservation did not renew watchdog")
}
// Confirmed bot, exact candidate request, durable reserve-before-subscribe.
do {
    let h = Host()
    h.network.onSubscribe = {
        check(h.progress.reservedState, "state reservation committed before subscription")
        if h.network.requests.count == 1 { check(h.progress.reservedPages == 1, "difference reservation committed before subscription") }
    }
    h.seedToDifference()
    check(h.network.requests[1].cursor?.pts == 90 && h.network.requests[1].cursor?.qts == 4 && h.network.requests[1].cursor?.date == 20, "candidate request")
    h.reply(difference(100, messages: [apiMessage(1)])); h.finished(.completed)
    check(h.transaction.messages[messageId(1)] != nil && h.progress.inserted == 1, "first payload consumed")
}
do {
    let h = Host(bot: false); let writes = h.transaction.progressWrites
    h.start(); h.queue.drain()
    check(h.controller == nil && h.network.requests.isEmpty && h.manager.customStarts == 0 && h.transaction.progressWrites == writes, "ordinary user fast path")
}
// Empty/deduplicated slice continues; queued modern operation executes before the
// next request and its live content, state and inclusion are preserved.
do {
    let h = Host(); h.seedToDifference()
    h.transaction.messages[messageId(1)] = StoreMessage(id: messageId(1), marker: 99)
    h.transaction.inclusion[destination] = "archive/pinned/cutoff=17"
    h.manager.modern { h.transaction.messages[messageId(2)] = StoreMessage(id: messageId(2), marker: 111) }
    h.reply(difference(95, slice: true, messages: [apiMessage(1)]))
    check(h.manager.modernRuns == 1 && h.network.requests.count == 3 && h.progress.inserted == 0, "dedup slice yields then continues")
    h.reply(difference(100, messages: [apiMessage(1), apiMessage(2), apiMessage(3)])); h.finished(.completed)
    check(h.transaction.messages[messageId(1)]?.marker == 99 && h.transaction.messages[messageId(2)]?.marker == 111 && h.transaction.messages[messageId(3)] != nil, "live content wins")
    check(h.transaction.inclusion[destination] == "archive/pinned/cutoff=17" && h.transaction.state.peerId == account, "inclusion and authorization untouched")
}
do {
    let h = Host(); h.seedToDifference(); h.reply(difference(95, slice: true))
    check(h.network.requests.count == 3 && h.progress.terminal == nil, "zero-message progressing slice continues")
    h.reply(Api.updates.Difference.differenceEmpty(Api.updates.EmptyData(date: 22, seq: 6))); h.finished(.completed)
}
do { let h = Host(); h.seedToDifference(); h.reply(Api.updates.Difference.differenceTooLong(500)); h.finished(.tooLong); check(h.transaction.mutationCalls == 0, "tooLong no reset/import") }
do { let h = Host(); h.seedToDifference(); h.reply(difference(90, slice: true, messages: [apiMessage(1)])); h.finished(.nonadvancing); check(h.transaction.mutationCalls == 0, "nonadvancing no mutation") }
do { let h = Host(); h.seedToDifference(); h.reply(difference(89, messages: [apiMessage(1)])); h.finished(.nonadvancing); check(h.transaction.mutationCalls == 0, "regressing final response rejected") }
do { let h = Host(); h.start(); h.queue.drain(); h.reply(state(unread: 0)); h.finished(.noCandidate); check(h.network.requests.count == 1, "no candidate no difference") }
// Hanging request, error, cancellation, late callbacks, and replacement.
do {
    let h = Host(); h.start(); h.queue.drain(); h.manager.modern(); h.queue.advance(10)
    h.finished(.timeout); check(h.network.requests[0].disposals == 1 && h.manager.modernRuns == 1, "timeout owns transport and releases manager")
    h.reply(state(), at: 0); check(h.network.requests.count == 1 && h.progress.original == nil, "late state ignored")
}
do { let h = Host(); h.start(); h.queue.drain(); h.network.requests[0].error(); h.queue.drain(); h.finished(.rpcError); check(h.network.requests.count == 1 && h.network.requests[0].disposals == 1, "error no retry") }
do {
    let h = Host(); h.start(); h.controller!.cancel(reason: .cancelled); h.queue.drain()
    check(h.network.requests.isEmpty, "cancel queued operation before activation"); h.finished(.cancelled)
}
do {
    let h = Host(); h.seedToDifference(); h.controller!.cancel(reason: .cancelled); h.queue.drain()
    h.reply(difference(100, messages: [apiMessage(1)])); h.finished(.cancelled)
    check(h.transaction.messages.isEmpty && h.network.requests[1].disposals == 1, "cancel inflight rejects late page")
}
do {
    let h = Host(); h.seedToDifference(); h.postbox.holdNext = true; h.reply(difference(100, messages: [apiMessage(1)]))
    check(h.postbox.held.count == 1, "response waiting to commit")
    h.controller!.cancel(reason: .cancelled); h.queue.drain(); h.postbox.releaseHeld(); h.queue.drain()
    h.finished(.cancelled); check(h.transaction.messages.isEmpty, "cancel before transaction excludes mutation")
}
do {
    let h = Host(); h.seedToDifference(); h.postbox.holdNext = true
    h.reply(difference(100, messages: [apiMessage(1)])); h.manager.modern(); h.queue.advance(10)
    h.finished(.timeout); check(h.manager.modernRuns == 1, "suspended page commit cannot hold manager")
    h.postbox.releaseHeld(); h.queue.drain()
    check(h.transaction.messages.isEmpty && h.progress.committedPages == 0, "late suspended page commit cannot mutate")
}
// Cancellation during the executing transaction invalidates the token before
// the manager queue hop, matching the public manager cancellation boundary.
do {
    let h = Host(); h.seedToDifference()
    h.transaction.onMessageExists = {
        h.lifetime.cancel()
        h.queue.async { h.controller!.cancel(reason: .cancelled) }
    }
    h.reply(difference(100, messages: [apiMessage(1)])); h.finished(.cancelled)
    check(h.transaction.mutationCalls == 0 && h.transaction.messages.isEmpty, "cancel during transaction before mutation")
}
do {
    let h = Host(); h.seedToDifference(); h.reply(difference(100, messages: [apiMessage(1)])); h.finished(.completed)
    let completions = h.manager.customCompletions
    h.controller!.cancel(reason: .cancelled); h.queue.drain(); h.finished(.completed)
    check(h.manager.customCompletions == completions && h.network.requests[1].disposals == 1, "cancel after commit cannot double-finish or overwrite terminal")
    h.crash(); h.restart(); h.finished(.completed)
    check(h.network.requests.count == 2, "completed generation does not automatically rerun")
}
do {
    let h = Host(); h.seedToDifference()
    let replacement = BotBridgeHistoryProgress(owner: 7, peer: 1, testing: false, generation: "replacement")
    h.transaction.progress = PreferencesEntry(replacement)
    h.reply(difference(100, messages: [apiMessage(1)]))
    check(h.progress == replacement && h.transaction.messages.isEmpty && !h.manager.running, "old generation cannot mutate replacement")
}
do {
    let a = Host(), b = Host(); a.seedToDifference(); b.seedToDifference()
    a.controller!.cancel(reason: .loggedOut); a.queue.drain()
    b.reply(difference(100, messages: [apiMessage(2)])); b.finished(.completed); a.finished(.loggedOut)
    check(a.transaction.messages.isEmpty && b.transaction.messages.count == 1, "account lifetimes isolated")
}
// Crash after reservation commit but before dispatch. No fresh getState window.
do {
    let h = Host(); h.start()
    while !h.progress.reservedState { check(h.queue.runOne(), "reservation must commit") }
    check(h.network.requests.isEmpty, "crash point before dispatch")
    h.crash(); h.restart(); h.finished(.interruptedState)
    check(h.network.requests.isEmpty && h.progress.reservedState, "interrupted getState budget consumed")
}
// Crash with page response before commit: repeats same cursor, consumes another
// reservation, old suspended transaction cannot commit into restarted controller.
do {
    let h = Host(); h.seedToDifference(); let oldCursor = h.progress.next
    h.postbox.holdNext = true; h.reply(difference(100, messages: [apiMessage(1)])); h.crash(); h.restart()
    check(h.progress.reservedPages == 2 && h.progress.next == oldCursor, "resume response-before-commit budget")
    h.postbox.releaseHeld(); h.queue.drain(); check(h.transaction.messages.isEmpty, "old page transaction closed")
    h.reply(difference(100, messages: [apiMessage(1)])); h.finished(.completed)
    check(h.progress.inserted == 1, "page imported once")
}
// Crash after page commit but before callback: resumes next stored cursor.
do {
    let h = Host(); h.seedToDifference()
    h.network.requests.last!.response(difference(95, slice: true, messages: [apiMessage(1)]))
    while h.progress.committedPages == 0 { check(h.queue.runOne(), "page commit must run") }
    h.crash(); h.restart()
    check(h.network.requests.last?.cursor?.pts == 95 && h.progress.reservedPages == 2, "after-commit resume advances")
    h.reply(difference(100, messages: [apiMessage(1)])); h.finished(.completed)
    check(h.progress.inserted == 1 && h.transaction.messages.count == 1, "repeat payload preserves import")
}
// Persisted reservation/deadline caps are not renewed by a new controller.
do {
    var p = BotBridgeHistoryProgress(owner: 7, peer: 1, testing: false, generation: "g1")
    _ = p.reserve(now: 1000); _ = p.acceptState(BotBridgeCursor(pts: 100, qts: 4, date: 20, seq: 6), unread: 10, now: 1000)
    p.reservedPages = 31; p.committedPages = 31
    let h = Host(progress: p); h.start(); h.queue.drain(); h.reply(difference(95, slice: true)); h.finished(.limit)
    check(h.network.requests.count == 1 && h.progress.reservedPages == 32, "32 pages cap")
}
do {
    var p = BotBridgeHistoryProgress(owner: 7, peer: 1, testing: false, generation: "g1")
    _ = p.reserve(now: 1000); _ = p.acceptState(BotBridgeCursor(pts: 100, qts: 4, date: 20, seq: 6), unread: 10, now: 1000)
    let h = Host(progress: p); h.clock.offset = 1115; h.start(); h.queue.drain()
    check(h.progress.deadline == 1120 && h.network.requests.count == 1, "resume original deadline")
    h.queue.advance(5); h.finished(.deadline)
    check(h.network.requests[0].disposals == 1 && h.progress.deadline == 1120, "remaining generation time bounds active request")
}
do {
    var p = BotBridgeHistoryProgress(owner: 7, peer: 1, testing: false, generation: "g1"); _ = p.reserve(now: 1000)
    let h = Host(progress: p); h.clock.offset = 1120; h.start(); h.queue.drain(); h.finished(.deadline)
    check(h.network.requests.isEmpty, "deadline before reservation dispatch")
}
do {
    var p = BotBridgeHistoryProgress(owner: 7, peer: 1, testing: false, generation: "g1"); _ = p.reserve(now: 1000)
    let h = Host(progress: p); h.clock.offset = 999; h.start(); h.queue.drain(); h.finished(.clockChanged)
    check(h.network.requests.isEmpty, "backward clock stops")
}
do {
    let h = Host(); h.seedToDifference(); h.reply(difference(100, messages: [apiMessage(1)], updates: Array(repeating: .mutation, count: 10001)))
    h.finished(.limit); check(h.transaction.messages.isEmpty, "oversize adapter payload rejected before mutation")
}
print("PASS unchanged production controller + response adapter: suspended reservation watchdog, sequencing, shapes, interleaving, disposal, cancellation, late work, generation/account isolation, crash/resume and finite bounds")
