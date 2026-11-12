import Foundation
func require(_ x: @autoclosure () -> Bool, _ why: String) { precondition(x(), why) }
protocol Disposable { func dispose() }
final class ActionDisposable: Disposable { let f: () -> Void; init(_ f: @escaping () -> Void) { self.f = f }; func dispose() { f() } }
final class MetaDisposable { var value: Disposable?; func set(_ value: Disposable?) { self.value?.dispose(); self.value = value } }
enum NoError: Error {}
final class Signal<T, E: Error> {
    let subscribe: (@escaping () -> Void) -> Disposable
    init(_ subscribe: @escaping (@escaping () -> Void) -> Disposable) { self.subscribe = subscribe }
    func start(completed: @escaping () -> Void) -> Disposable { subscribe(completed) }
}
final class Queue { func async(_ f: () -> Void) { f() } }
infix operator |> : AdditionPrecedence
func |> <A, B>(a: A, f: (A) -> B) -> B { f(a) }
func deliverOn<T, E: Error>(_ queue: Queue) -> (Signal<T, E>) -> Signal<T, E> { { $0 } }
struct UpdateGroup {}
struct MessageId {}
struct AccountFinalStateEvents {}
struct AccountFinalState {}
final class Timer { func invalidate() {} }
/* REAL_OPERATION_TYPES */
private final class Manager {
    var operations: [AccountStateManagerOperation] = []
    let operationDisposable = MetaDisposable()
    let queue = Queue()
    var operationTimer: Timer?
    var currentValidityMarker = 0
    var nextId: Int32 = 100
    func getNextId() -> Int32 { nextId += 1; return nextId }
    /* REAL_REPLACEMENT */
    // Exact production reset scheduling segment; update sink installation and
    // receipt-acknowledgement setup are intentionally outside this fixture.
    func reset() { queue.async {
        /* REAL_RESET_SCHEDULING */
    } }
    func startFirstOperation() {
        /* REAL_START_GUARDS */
        switch operation.content {
        /* REAL_CUSTOM_ACTIVATION */
        default: break // live poll stays running until the fixture completes it
        }
    }
    func finishLive() {
        require(operations.first!.isRunning, "running live work")
        operations.removeFirst(); startFirstOperation()
    }
    func customIds() -> [Int32] {
        operations.compactMap { if case let .custom(id, _) = $0.content { return id }; return nil }
    }
}
private let manager = Manager()
var starts = 0, disposed = 0, completions = 0
var complete: (() -> Void)?
let signal = Signal<Void, NoError> { done in starts += 1; complete = { completions += 1; done() }; return ActionDisposable { disposed += 1 } }
manager.operations = [AccountStateManagerOperation(content: .custom(7, signal))]
manager.startFirstOperation()
let original = manager.operations[0]
for _ in 0..<8 { manager.reset() }
require(manager.operations[0] === original && original.isRunning, "active identity survives exact replacement")
require(starts == 1 && disposed == 0 && manager.customIds() == [7], "reset neither resubscribes nor disposes active custom")
complete!()
require(completions == 1 && manager.customIds().isEmpty, "custom completion removes exactly once and starts live work")
manager.operations.append(AccountStateManagerOperation(content: .custom(8, signal)))
for _ in 0..<8 { manager.reset() }
require(manager.customIds() == [8] && starts == 1, "pending exact custom ID retained behind live poll")
manager.finishLive()
manager.finishLive() // running old poll plus the replacement poll precede pending custom
require(starts == 2 && manager.customIds() == [8], "pending custom starts once after live yield")
manager.reset(); require(starts == 2 && disposed == 0, "active second custom survives reset")
complete!(); require(completions == 2 && manager.customIds().isEmpty, "pending custom completes once")
print("PASS production manager reset scheduling replacement and custom activation")
