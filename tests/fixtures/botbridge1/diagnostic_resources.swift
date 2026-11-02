func check(_ value: @autoclosure () -> Bool, _ reason: String) { precondition(value(), reason) }
let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
try! FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
let stale = root.appendingPathComponent("BOTBRIDGE1-export-stale.json")
try! Data("PRIVATE_STALE_EXPORT".utf8).write(to: stale)
let queue = DispatchQueue(label: "bounded-fixture"); queue.suspend()
let sink = BotBridgeDiagnosticSink(root: root, queue: queue)
let now = Date().timeIntervalSince1970
let session = UUID(), epoch = UUID()
let flights = (0..<64).map { _ in BotBridgeDiagnosticFlight(request: UUID(), logical: UUID(), category: .media, flags: [.reply,.media,.post], attempt: 1, submittedAt: now) }
for n in 0..<400 {
 var event = BotBridgeDiagnosticRecord(session: session, epoch: epoch, sequence: UInt64(n), wall: now, phase: .snapshot)
 event.inFlight = flights
 sink.accept(event, reserved: false)
}
for n in 0..<20 {
 var event = BotBridgeDiagnosticRecord(session: session, epoch: epoch, sequence: UInt64(400+n), wall: now, phase: .snapshot)
 event.lifecycle = .serverLogout
 sink.accept(event, reserved: true)
}
let done = DispatchSemaphore(value: 0)
var exported: URL?
sink.export { result in
 guard case let .success(url) = result else { preconditionFailure("first export") }
 exported = url
 let bytes = try! Data(contentsOf: url)
 let report = try! JSONSerialization.jsonObject(with: bytes) as! [String: Any]
 check((report["sinkDropped"] as! NSNumber).intValue == 152, "248 ordinary +8 reserved pending bound")
 check((report["snapshotDropped"] as! NSNumber).intValue == 12, "reserved snapshot bound with explicit loss")
 check((report["rotationEvictedFiles"] as! NSNumber).intValue > 0, "rotation reports loss")
 check(bytes.count <= 2 * 1024 * 1024, "export including envelope bounded")
 check(!FileManager.default.fileExists(atPath: stale.path), "stale artifact cleanup off main")
 let files = try! FileManager.default.contentsOfDirectory(at: root, includingPropertiesForKeys: [.fileSizeKey]).filter { $0.pathExtension == "jsonl" }
 check(files.count <= 8, "at most eight retained files")
 let sizes = files.map { (try! $0.resourceValues(forKeys: [.fileSizeKey])).fileSize! }
 check(sizes.allSatisfy { $0 <= 256 * 1024 } && sizes.reduce(0,+) <= 2 * 1024 * 1024, "byte limits before append")
 let records = report["records"] as! [[String: Any]]
 check(records.contains { ($0["lifecycle"] as? String) == "serverLogout" }, "reserved lifecycle survives ordinary saturation")
 sink.export { result in if case .failure(.busy) = result {} else { preconditionFailure("only one export") }; done.signal() }
}
queue.resume()
check(done.wait(timeout: .now() + 15) == .success, "saturation/rotation export complete")
// Retention applies on next sink access; no permanent timer/polling is installed.
sink.release(exported!)
queue.sync {
 for url in try! FileManager.default.contentsOfDirectory(at: root, includingPropertiesForKeys: []) where url.pathExtension == "jsonl" {
  try! FileManager.default.setAttributes([.modificationDate: Date(timeIntervalSinceNow: -86401)], ofItemAtPath: url.path)
 }
}
let ttl = DispatchSemaphore(value: 0)
sink.export { result in
 guard case let .success(url) = result else { preconditionFailure("TTL export") }
 let report = try! JSONSerialization.jsonObject(with: Data(contentsOf: url)) as! [String: Any]
 check(report["status"] as? String == "no_captured_sessions", "truthful empty report after TTL")
 check((report["retentionExpiredFiles"] as! NSNumber).intValue > 0, "TTL losses visible")
 check(!FileManager.default.fileExists(atPath: exported!.path), "idempotent cleanup removes only export")
 sink.release(url); ttl.signal()
}
check(ttl.wait(timeout: .now() + 5) == .success, "TTL completion")
queue.sync {}
try? FileManager.default.removeItem(at: root)
print("PASS actual sink: saturation, reserved snapshots, rotation/bytes, single export, cleanup, TTL, no captured sessions")
