func require(_ x: @autoclosure () -> Bool, _ why: String) { precondition(x(), why) }
final class Namespace {}
let namespace = Namespace()
let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
let sink = BotBridgeDiagnosticSink(root: root)
var cancellations: [BotBridgeDiagnosticLifecycle] = []
let scope = BotBridgeDiagnosticScope(generation: UUID().uuidString, sink: sink, cancelHistory: { cancellations.append($0) })
let registration = BotBridgeScopeRegistration(); registration.install(scope)
require(BotBridgeDiagnosticRegistry.shared.register(namespace: namespace, record: 1, scope: scope), "single admission")
for _ in 0..<12 { scope.lifecycle(.stateManagementReset, terminal: false) }
require(cancellations.isEmpty && !scope.isFrozen, "routine reset observes without invalidation or freeze")
let routineEvents = scope.snapshotEvents()
require(routineEvents.count == 8 && routineEvents.allSatisfy { $0.lifecycle == .stateManagementReset }, "bounded routine events")
require(routineEvents.last?.evictedEvents == 4, "routine overflow is counted")
require(registration.begin(method: "updates.getState", context: nil) != nil, "registration remains attached")
require(BotBridgeDiagnosticRegistry.shared.target(namespace: namespace, record: 1) != nil, "owner remains registered")
scope.lifecycle(.softReset, terminal: false)
require(cancellations == [.softReset], "auth soft reset still hard cancels")
for kind in [BotBridgeDiagnosticLifecycle.authKeyUnknown, .localLogout, .remoteLogout, .serverLogout, .removed, .deinitialized] {
    let s = BotBridgeDiagnosticScope(generation: UUID().uuidString, sink: sink, cancelHistory: { cancellations.append($0) })
    s.lifecycle(kind)
    require(cancellations.last == kind && s.isFrozen, "hard lifecycle cancels and freezes")
    s.lifecycle(.stateManagementReset, terminal: false)
    require(s.isFrozen && cancellations.last == kind, "routine reset cannot reopen hard terminal")
}
print("PASS production diagnostics routine and hard lifecycle")
