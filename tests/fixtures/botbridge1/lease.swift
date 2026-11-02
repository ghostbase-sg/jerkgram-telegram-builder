import Foundation
protocol Disposable { func dispose() }
final class CountingDisposable: Disposable { var calls = 0; func dispose() { calls += 1 } }
final class MetaDisposable: Disposable {
    private var value: Disposable?; private var disposed = false
    func set(_ next: Disposable?) { if disposed { next?.dispose() } else { value?.dispose(); value = next } }
    func dispose() { guard !disposed else { return }; disposed = true; value?.dispose(); value = nil }
}
enum SwiftSignalKit { final class Timer { var invalidations = 0; func invalidate() { invalidations += 1 } } }
/* REAL_POLICY */
/* REAL_LEASE */
var completions = 0
var lease: BotBridgePageLease? = BotBridgePageLease(completion: { completions += 1 })
let network = CountingDisposable(); let timer = SwiftSignalKit.Timer()
lease!.work.set(network); lease!.timer = timer
lease!.finish() // timeout or cancellation; same production path as result completion
lease!.finish() // late callback, signal disposal, or repeated cancellation
precondition(completions == 1 && network.calls == 1 && timer.invalidations == 1 && !lease!.gate.isOpen)
let lateNetwork = CountingDisposable()
lease!.work.set(lateNetwork)
precondition(lateNetwork.calls == 1) // installing after cancellation cannot leak work
lease = nil
precondition(completions == 1 && network.calls == 1)
print("PASS real page lease: owned request disposal and completion once, late installation rejected")
