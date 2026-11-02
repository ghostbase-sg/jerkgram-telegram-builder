// Executes the real Foundation recorder, registry, observer and sink above.
func check(_ value: @autoclosure () -> Bool, _ reason: String) { precondition(value(), reason) }
final class Namespace {}
let tmp = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
let sink = BotBridgeDiagnosticSink(root: tmp)
var now = Date().timeIntervalSince1970
let scope = BotBridgeDiagnosticScope(generation: UUID().uuidString, sink: sink, clock: { now }, cancelHistory: { _ in })
let registration = BotBridgeScopeRegistration(); registration.install(scope)
let context = BotBridgeOperationContext(flags: [.reply, .post])
let a = registration.begin(method: "messages.sendMedia", context: context)!
a.acknowledge(); a.finish(.result); a.cancel()
let b = registration.begin(method: "messages.sendMedia", context: context)!
b.cancel(); b.finish(.result)
let events = scope.snapshotEvents()
check(events.filter { $0.phase == .cancelled }.count == 1, "result disposal is not cancellation")
check(events.filter { $0.phase == .submitted }.map { $0.attempt } == [1, 2], "subscription attempts")
check(events[0].flags.contains(.reply) && events[0].flags.contains(.media) && events[0].flags.contains(.post), "additive flags")
check(BotBridgeDiagnosticCategory.classify("messages.readHistory") == .readAck, "read ack distinct")
check(BotBridgeDiagnosticCategory.classify("updates.getDifference") == .stateRead, "update reads alone do not prove bridge ownership")
check(BotBridgeDiagnosticCategory.classify("private.sentinal") == .unknown, "unknown name never exported")
for _ in 0..<400 { registration.begin(method: "messages.sendMessage", context: nil)?.finish(.result) }
check(scope.snapshotEvents().count <= 256, "bounded ring")
var held: [BotBridgeRequestObservation] = []
for _ in 0..<80 { if let item = registration.begin(method: "messages.sendMessage", context: nil) { held.append(item) } }
check(scope.activeCount <= 64, "bounded active")
now += 1801; scope.lifecycle(.softReset, terminal: false)
check(scope.activeCount == 0, "TTL expires correlations")
check(registration.begin(method: "messages.sendMessage", context: nil) != nil, "soft reset keeps recorder")
let namespaceA = Namespace(), namespaceB = Namespace()
let scopeB = BotBridgeDiagnosticScope(generation: UUID().uuidString, sink: sink, cancelHistory: { _ in })
check(BotBridgeDiagnosticRegistry.shared.register(namespace: namespaceA, record: 7, scope: scope), "registry A")
check(BotBridgeDiagnosticRegistry.shared.register(namespace: namespaceB, record: 7, scope: scopeB), "registry B")
BotBridgeDiagnosticRegistry.shared.notify(namespace: namespaceA, record: 7, kind: .localLogout)
check(scope.isFrozen && !scopeB.isFrozen, "namespace isolation")
registration.install(scopeB)
weak var weakScope: BotBridgeDiagnosticScope?
do { let s = BotBridgeDiagnosticScope(generation: UUID().uuidString, sink: sink, cancelHistory: { _ in }); weakScope = s; registration.install(s) }
check(weakScope == nil, "registration owns no scope")
var retainedObservation: BotBridgeRequestObservation?
do {
 let temporary = BotBridgeDiagnosticScope(generation: UUID().uuidString, sink: sink, cancelHistory: { _ in })
 weakScope = temporary
 retainedObservation = temporary.begin(category: .text, context: nil)
}
check(weakScope == nil, "observer owns no scope")
retainedObservation?.finish(.result) // old epoch cannot resolve a replacement scope
let parallelA = BotBridgeDiagnosticScope(generation: UUID().uuidString, sink: sink, cancelHistory: { _ in })
let parallelB = BotBridgeDiagnosticScope(generation: UUID().uuidString, sink: sink, cancelHistory: { _ in })
DispatchQueue.concurrentPerform(iterations: 200) { index in
 let target = index % 2 == 0 ? parallelA : parallelB
 target.begin(category: .reaction, context: nil)?.finish(.result)
}
check(parallelA.snapshotEvents().allSatisfy { $0.session == parallelA.session }, "parallel account A isolation")
check(parallelB.snapshotEvents().allSatisfy { $0.session == parallelB.session }, "parallel account B isolation")
let semaphore = DispatchSemaphore(value: 0)
sink.export { result in
 if case let .success(url) = result {
  let bytes = try! Data(contentsOf: url)
  let text = String(data: bytes, encoding: .utf8)!
  check(!text.contains("private.sentinal"), "method privacy sentinel")
  check(bytes.count <= 2 * 1024 * 1024, "bounded export including envelope")
  check(text.contains("internalRetriesUnobserved"), "truthful coverage")
  sink.release(url)
 } else { preconditionFailure("export failed") }
 semaphore.signal()
}
check(semaphore.wait(timeout: .now() + 5) == .success, "async export completion")
try? FileManager.default.removeItem(at: tmp)
print("PASS actual recorder, observer, TTL, bounds, weak registry, export")
