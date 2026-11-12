import Foundation
// Identity adapters only; production HistoryFilter is inserted verbatim by
// the harness. Full TelegramUI typechecking remains the app-build gate.
public struct MemoryBuffer: Equatable {
    public let bytes: [UInt8]
    public init(_ bytes: [UInt8]) { self.bytes = bytes }
}
/* EXACT_HISTORY_FILTER */
func require(_ value: Bool, _ message: String) {
    if !value { fatalError(message) }
}
let cloud = HistoryFilter(customTag: MemoryBuffer([1, 2, 3]), isActive: true)
let local = HistoryFilter(localSavedTagId: "same-account-local-id")
require(local.customTag == nil, "local tag leaked cloud bytes")
require(cloud.localSavedTagId == nil, "cloud buffer leaked local identity")
require(cloud.customTag == MemoryBuffer([1, 2, 3]), "cloud adapter changed bytes")
require(local != cloud, "local and cloud domains compared equal")
require(local == HistoryFilter(localSavedTagId: "same-account-local-id"), "local identity unstable")
require(local != HistoryFilter(localSavedTagId: "different-id"), "local switch lost identity")
var paused = local
paused.isActive = false
require(paused != local && paused.localSavedTagId == local.localSavedTagId, "activation lost domain")
print("PASS actual HistoryFilter local/cloud identity")
/* EXACT_RENDER_GATE */
let renderTheme = NSObject()
let renderStrings = NSObject()
func renderKey(_ revision: Int64 = 1, _ selected: String? = nil, _ width: CGFloat = 390) -> JerkgramLocalSavedTagsRenderKey {
    return JerkgramLocalSavedTagsRenderKey(revision: revision, selectedId: selected,
        theme: ObjectIdentifier(renderTheme), strings: ObjectIdentifier(renderStrings),
        width: width, leftInset: 0, rightInset: 0, available: true)
}
var renderGate = JerkgramLocalSavedTagsRenderGate()
require(renderGate.update(renderKey()), "first native strip render suppressed")
var redundantBuilds = 0
for _ in 0..<1000 { if renderGate.update(renderKey()) { redundantBuilds += 1 } }
require(redundantBuilds == 0, "unchanged native panel inputs rebuilt local buttons")
require(renderGate.update(renderKey(2)), "catalogue revision did not rebuild chips")
require(renderGate.update(renderKey(2, "selected")), "selection did not rebuild chips")
require(renderGate.update(renderKey(2, "selected", 430)), "width did not relayout chips")
renderGate.invalidate()
require(renderGate.update(renderKey(2, "selected", 430)), "return from cloud domain failed to rebuild local chips")
print("PASS exact native strip render gate skips 1000 unchanged panel updates")
typealias NativeTagsFixtureHistoryFilter = HistoryFilter
enum ChatPresentationInterfaceState { typealias HistoryFilter = NativeTagsFixtureHistoryFilter }
/* EXACT_TRANSITION_HELPERS */
let filterA = HistoryFilter(localSavedTagId: "A")
let filterB = HistoryFilter(localSavedTagId: "B")
require(jerkgramClearingLocalSavedTagsFilter(filterB, expectedId: "A", generation: 2, expectedGeneration: 1) == filterB, "late A account/catalogue callback cleared B")
require(jerkgramClearingLocalSavedTagsFilter(cloud, expectedId: "A", generation: 3, expectedGeneration: 1) == cloud, "late local callback cleared cloud filter")
require(jerkgramClearingLocalSavedTagsFilter(filterA, expectedId: "A", generation: 3, expectedGeneration: 1) == filterA, "A to B to A accepted stale first-A clear")
require(jerkgramClearingLocalSavedTagsFilter(filterA, expectedId: "A", generation: 1, expectedGeneration: 1) == nil, "current account/catalogue clear rejected")
var historyIsLocal = true
var historyLocation = 999
let originalAnchor = 10
let requestedJump = 500
var deferredPresentationUpdates: [() -> Void] = []
func clearHistorySynchronously() {
    // The node's nil-to-nil guard makes late presentation clear idempotent.
    guard historyIsLocal else { return }
    historyIsLocal = false
    historyLocation = originalAnchor
}
jerkgramResolveLocalSavedTagsNavigation(clearHistory: {
    clearHistorySynchronously()
}, replayLocation: {
    require(!historyIsLocal, "offwindow jump replayed before local history was cleared")
    historyLocation = requestedJump
}, notifyFilterCleared: {
    deferredPresentationUpdates.append { clearHistorySynchronously() }
})
require(historyLocation == requestedJump && !historyIsLocal, "offwindow jump lost before asynchronous presentation update")
for update in deferredPresentationUpdates { update() }
require(historyLocation == requestedJump, "asynchronous filter clear restored old anchor over jump")
print("PASS exact native filter clear generation and offwindow asynchronous presentation transition")
