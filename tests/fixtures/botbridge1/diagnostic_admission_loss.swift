func check(_ value: @autoclosure () -> Bool, _ reason: String) { precondition(value(), reason) }
final class Namespace {}
let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
let q = DispatchQueue(label: "admission-loss-fixture")
var listings = 0
let sink = BotBridgeDiagnosticSink(root: root, queue: q, listDirectory: { url in
 listings += 1
 return try FileManager.default.contentsOfDirectory(at: url, includingPropertiesForKeys: [.contentModificationDateKey,.fileSizeKey])
})
q.sync {}
let namespace = Namespace(), registry = BotBridgeDiagnosticRegistry.shared
let before = registry.admissionLoss
var scopes: [BotBridgeDiagnosticScope] = []
for index in 0..<32 {
 let scope = BotBridgeDiagnosticScope(generation: UUID().uuidString, sink: sink, cancelHistory: { _ in })
 check(registry.register(namespace: namespace, record: Int64(index), scope: scope), "32 live targets admitted")
 scopes.append(scope)
}
let admitted = registry.targets(namespace: namespace).map { $0.epoch }
var listingsBefore = 0
q.sync { listingsBefore = listings }
let rejected = BotBridgeDiagnosticScope(generation: UUID().uuidString, sink: sink, cancelHistory: { _ in })
check(!registry.register(namespace: namespace, record: 0, scope: rejected), "duplicate live target denied")
check(!registry.register(namespace: namespace, record: 32, scope: rejected), "33rd live target denied")
check(registry.targets(namespace: namespace).map { $0.epoch } == admitted, "no live scope eviction or replacement")
let invalid = BotBridgeDiagnosticScope(generation: "invalid", sink: sink, cancelHistory: { _ in })
check(!registry.register(namespace: namespace, record: 33, scope: invalid), "invalid generation denied separately")
let losses = registry.admissionLoss
check(losses.capacity == before.capacity + 1, "capacity denial counted independently")
check(losses.duplicateTarget == before.duplicateTarget + 1, "duplicate denial counted independently")
check(losses.invalidGeneration == before.invalidGeneration + 1, "invalid generation counted independently")
q.sync { check(listings == listingsBefore, "denial only changes RAM counter; schedules no sink I/O") }
let done = DispatchSemaphore(value: 0)
sink.export { result in
 guard case let .success(url) = result else { preconditionFailure("denial export") }
 let bytes = try! Data(contentsOf: url)
 let json = try! JSONSerialization.jsonObject(with: bytes) as! [String:Any]
 let exportedLosses = json["admissionDenied"] as! [String: Any]
 check((exportedLosses["capacity"] as! NSNumber).uint64Value == before.capacity + 1, "capacity denial exported without event records")
 check((exportedLosses["duplicateTarget"] as! NSNumber).uint64Value == before.duplicateTarget + 1, "duplicate target denial exported separately")
 check((exportedLosses["invalidGeneration"] as! NSNumber).uint64Value == before.invalidGeneration + 1, "invalid generation denial exported separately")
 check((json["records"] as! [Any]).isEmpty, "denial does not synthesize an account recorder")
 check(json["status"] as? String == "no_captured_sessions", "empty sessions remain truthful alongside explicit admission loss")
 let text = String(data: bytes, encoding: .utf8)!
 for scope in scopes { check(!text.contains(scope.generation), "aggregate loss exports no rejected/admitted account generation") }
 check(!text.contains(rejected.generation), "rejected generation remains RAM only")
 sink.release(url); done.signal()
}
check(done.wait(timeout: .now() + 5) == .success, "export does not recurse/deadlock with registry")
for (index, scope) in scopes.enumerated() { registry.unregister(namespace: namespace, record: Int64(index), epoch: scope.epoch) }
q.sync {}; try? FileManager.default.removeItem(at: root)
print("PASS actual registry: duplicate/capacity loss counted and exported, no live eviction, no denied-event I/O")
