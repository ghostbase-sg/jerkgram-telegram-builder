import Foundation

// Deterministic Signal/queue boundary. Production bind/dispose/provider bodies
// are injected unchanged. Delayed sends deliberately remain possible after
// upstream disposal, so production generation checks must reject them.
public enum NoError: Error {}
public protocol Disposable { func dispose() }
final class ActionDisposable: Disposable {
    private var action: (() -> Void)?
    init(_ action: @escaping () -> Void) { self.action = action }
    func dispose() { let action = self.action; self.action = nil; action?() }
}
final class MetaDisposable: Disposable {
    private var current: Disposable?
    private var disposed = false
    func set(_ value: Disposable) {
        if disposed { value.dispose(); return }
        let previous = current; current = value; previous?.dispose()
    }
    func dispose() { disposed = true; let value = current; current = nil; value?.dispose() }
}
let EmptyDisposable: Disposable = ActionDisposable({})
final class Subscriber<T, E: Error> {
    let next: (T) -> Void
    let completed: () -> Void
    let beforeNext: (() -> Void)?
    let beforeCompleted: (() -> Void)?
    init(next: @escaping (T) -> Void, completed: @escaping () -> Void, beforeNext: (() -> Void)? = nil, beforeCompleted: (() -> Void)? = nil) {
        self.next = next; self.completed = completed; self.beforeNext = beforeNext; self.beforeCompleted = beforeCompleted
    }
    func putNext(_ value: T) { beforeNext?(); next(value) }
    func putCompletion() { beforeCompleted?(); completed() }
}
public final class Signal<T, E: Error> {
    let generator: (Subscriber<T,E>) -> Disposable
    init(_ generator: @escaping (Subscriber<T,E>) -> Disposable) { self.generator = generator }
    func start(next: @escaping (T) -> Void = { _ in }, completed: @escaping () -> Void = {}, beforeNext: (() -> Void)? = nil, beforeCompleted: (() -> Void)? = nil) -> Disposable {
        return generator(Subscriber(next: next, completed: completed, beforeNext: beforeNext, beforeCompleted: beforeCompleted))
    }
}
infix operator |> : AdditionPrecedence
func |> <T, R>(value: T, f: (T) -> R) -> R { f(value) }
func deliverOn<T>(_ queue: FixtureQueue) -> (Signal<T, NoError>) -> Signal<T, NoError> { return { $0 } }
final class LocalSavedTagsService {
    private var generation: UInt64 = 0
    private var disposed = false
    private var subscriptions: [UUID: MetaDisposable] = [:]
    fileprivate let delivery = LocalSavedTagsDelivery()
    var delayed: [Subscriber<LocalSavedTagsPageEvent,NoError>] = []
    var activeReads = 0
    var maxActiveReads = 0
    func fixtureDrain() { delivery.sync {} }
    func fixtureEmit(_ index: Int, _ event: LocalSavedTagsPageEvent) { delayed[index].putNext(event) }
    func fixtureComplete(_ index: Int) { delayed[index].putCompletion() }
    func fixtureSend(_ index: Int, _ event: LocalSavedTagsPageEvent) { fixtureEmit(index, event); fixtureDrain() }
    func fixtureSignal() -> Signal<LocalSavedTagsPageEvent, NoError> { bind(page(tagId: "fixture", cursor: nil, direction: .earlier)) }
    func makePageProvider(tagId: String) -> LocalSavedTagsPageProvider { LocalSavedTagsPageProvider(service: self, tagId: tagId) }
    fileprivate func page(tagId: String, cursor: LocalSavedTagsCursor?, direction: LocalSavedTagsDirection) -> Signal<LocalSavedTagsPageEvent,NoError> {
        return Signal { subscriber in
            self.activeReads += 1; self.maxActiveReads = max(self.maxActiveReads, self.activeReads)
            self.delayed.append(subscriber)
            return ActionDisposable { self.activeReads -= 1 }
        }
    }
    /* EXACT_SERVICE_BIND */
    /* EXACT_SERVICE_DISPOSE */
}
/* EXACT_PAGE_PROVIDER */
