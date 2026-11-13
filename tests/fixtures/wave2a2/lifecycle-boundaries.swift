// Scheduling/subscription boundaries only. Real controller lifecycle, feed
// construction and gate declarations are inserted verbatim from each owner.
import Foundation
enum NoError: Error {}
protocol Disposable { func dispose() }
final class ActionDisposable: Disposable {
    var body: (() -> Void)?
    init(_ body: @escaping () -> Void = {}) { self.body = body }
    func dispose() { let f = body; body = nil; f?() }
}
final class MetaDisposable: Disposable {
    var item: Disposable?; var disposed = false
    func set(_ item: Disposable?) { if disposed { item?.dispose(); return }; self.item?.dispose(); self.item = item }
    func dispose() { disposed = true; item?.dispose(); item = nil }
}
final class Subscriber<T> {
    var active = true
    let next: (T) -> Void; let completed: () -> Void
    init(_ next: @escaping (T) -> Void, _ completed: @escaping () -> Void) { self.next = next; self.completed = completed }
    func putNext(_ v: T) { if active { next(v) } }
    func putCompletion() { if active { active = false; completed() } }
}
final class Signal<T, E: Error> {
    let generator: (Subscriber<T>) -> Disposable
    init(_ generator: @escaping (Subscriber<T>) -> Disposable) { self.generator = generator }
    func start(next: @escaping (T) -> Void, completed: @escaping () -> Void = {}) -> Disposable {
        let sub = Subscriber(next, completed); let work = generator(sub)
        return ActionDisposable { sub.active = false; work.dispose() }
    }
    static func single(_ v: T) -> Signal<T, E> { Signal { s in s.putNext(v); s.putCompletion(); return ActionDisposable() } }
    static func never() -> Signal<T, E> { Signal { _ in ActionDisposable() } }
}
infix operator |> : AdditionPrecedence
func |> <A, B>(lhs: A, rhs: (A) -> B) -> B { rhs(lhs) }
func then<T, E: Error>(_ second: Signal<T, E>) -> (Signal<T, E>) -> Signal<T, E> {
    { first in Signal { sub in
        let a = MetaDisposable(), b = MetaDisposable()
        a.set(first.start(next: sub.putNext, completed: { b.set(second.start(next: sub.putNext, completed: sub.putCompletion)) }))
        return ActionDisposable { a.dispose(); b.dispose() }
    } }
}
func mapToSignal<A, B, E: Error>(_ f: @escaping (A) -> Signal<B, E>) -> (Signal<A, E>) -> Signal<B, E> {
    { outer in Signal { sub in
        let inner = MetaDisposable()
        let work = outer.start(next: { v in inner.set(f(v).start(next: sub.putNext)) })
        return ActionDisposable { work.dispose(); inner.dispose() }
    } }
}
func distinctUntilChanged<T: Equatable, E: Error>(_ source: Signal<T, E>) -> Signal<T, E> {
    Signal { sub in var previous: T?; return source.start(next: { value in if previous != value { previous = value; sub.putNext(value) } }) }
}
final class ValuePromise<T: Equatable> {
    var value: T; var id = 0; var listeners: [Int: (T) -> Void] = [:]
    init(_ value: T, ignoreRepeated: Bool) { self.value = value }
    func set(_ next: T) { if value == next { return }; value = next; for f in Array(listeners.values) { f(next) } }
    func get() -> Signal<T, NoError> {
        Signal { [self] sub in id += 1; let token = id; listeners[token] = sub.putNext; sub.putNext(value); return ActionDisposable { [weak self] in self?.listeners.removeValue(forKey: token) } }
    }
}
class ItemListController {
    var feeds: [Disposable] = []
    func viewWillAppear(_ animated: Bool) {}
    func viewDidAppear(_ animated: Bool) {}
    func viewWillDisappear(_ animated: Bool) {}
    deinit { for feed in feeds { feed.dispose() } }
}
final class JerkgramPerformanceDiagnostics {
    static let shared = JerkgramPerformanceDiagnostics()
    func setVisibleRoute(_ route: String, owner: AnyObject) {}
    func clearVisibleRoute(owner: AnyObject) {}
}
struct EnginePeer: Equatable { let id: Int }
enum Page { case about, media }
final class Tracker {
    var starts = 0, disposals = 0, activeHistory = 0, activePoll = 0, maxActive = 0, deliveries = 0
    var callbacks: [(JerkgramAboutChannelState) -> Void] = []
    func feed() -> Signal<JerkgramAboutChannelState, NoError> {
        Signal { [self] sub in
            starts += 1; activeHistory += 1; activePoll += 1; maxActive = max(maxActive, activeHistory)
            sub.putNext(.available(peer: EnginePeer(id: 1), preview: "cached/latest")); callbacks.append(sub.putNext)
            return ActionDisposable { [weak self] in guard let self else { return }; self.disposals += 1; self.activeHistory -= 1; self.activePoll -= 1 }
        }
    }
    func deliver() { for f in callbacks { f(.available(peer: EnginePeer(id: 1), preview: "new")) } }
}
final class AccountContext { let tracker = Tracker() }
private func jerkgramAboutChannelState(context: AccountContext, enabled: Bool, username: String) -> Signal<JerkgramAboutChannelState, NoError> { enabled ? context.tracker.feed() : .single(.unavailable) }
func check(_ flag: @autoclosure () -> Bool, _ reason: String) { precondition(flag(), reason) }
