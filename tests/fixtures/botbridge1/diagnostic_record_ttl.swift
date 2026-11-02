func check(_ value: @autoclosure () -> Bool, _ reason: String) { precondition(value(), reason) }
let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
try! FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
let q = DispatchQueue(label: "record-ttl-fixture")
let session = UUID(), epoch = UUID()
let file = root.appendingPathComponent("events-active.jsonl")
func seed(_ sequence: UInt64) {
 let now = Date().timeIntervalSince1970
 let stale = BotBridgeDiagnosticRecord(session: session, epoch: epoch, sequence: sequence, wall: now - 86460, phase: .submitted)
 let fresh = BotBridgeDiagnosticRecord(session: session, epoch: epoch, sequence: sequence + 1, wall: now, phase: .result)
 var bytes = try! JSONEncoder().encode(stale); bytes.append(10)
 bytes.append(try! JSONEncoder().encode(fresh)); bytes.append(10)
 try! bytes.write(to: file, options: .atomic)
 let modified = (try! file.resourceValues(forKeys: [.contentModificationDateKey])).contentModificationDate!
 check(Date().timeIntervalSince(modified) < 30, "regression requires fresh file mtime despite stale record")
}
func diskRecords() -> [BotBridgeDiagnosticRecord] {
 let files = try! FileManager.default.contentsOfDirectory(at: root, includingPropertiesForKeys: []).filter { $0.pathExtension == "jsonl" }
 return files.flatMap { url in (try! Data(contentsOf: url)).split(separator: 10).map { try! JSONDecoder().decode(BotBridgeDiagnosticRecord.self, from: Data($0)) } }
}
seed(10)
let sink = BotBridgeDiagnosticSink(root: root, queue: q, listDirectory: { url in
 check(!Thread.isMainThread, "retention enumeration must stay off main")
 return try FileManager.default.contentsOfDirectory(at: url, includingPropertiesForKeys: [.contentModificationDateKey, .fileSizeKey])
})
q.sync {
 check(diskRecords().map { $0.sequence } == [11], "prepare physically removes old record with fresh mtime")
 // Refresh the same active file, as low steady traffic does; drain must inspect records again.
 seed(20)
}
let live = BotBridgeDiagnosticRecord(session: session, epoch: epoch, sequence: 30, wall: Date().timeIntervalSince1970, phase: .result)
sink.accept(live, reserved: false)
q.sync {
 check(diskRecords().map { $0.sequence } == [21,30], "drain physically prunes stale records while preserving recent records")
 seed(40)
}
let done = DispatchSemaphore(value: 0)
sink.export { result in
 guard case let .success(url) = result else { preconditionFailure("record TTL export") }
 let json = try! JSONSerialization.jsonObject(with: Data(contentsOf: url)) as! [String: Any]
 check((json["retentionExpiredRecords"] as! NSNumber).intValue == 3, "each successful physical removal counted once across access/drain/export")
 check(diskRecords().map { $0.sequence } == [41], "export physically prunes disk, beyond filtering the export")
 check((json["records"] as! [[String:Any]]).count == 1, "fresh record remains exportable")
 sink.release(url); done.signal()
}
check(done.wait(timeout: .now() + 5) == .success, "TTL completes without polling or main queue work")
q.sync {}; try? FileManager.default.removeItem(at: root)
print("PASS actual record TTL: prepare/drain/export physically remove stale records despite fresh active-file mtime")
