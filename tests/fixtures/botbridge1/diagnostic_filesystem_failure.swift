func check(_ value: @autoclosure () -> Bool, _ reason: String) { precondition(value(), reason) }
final class DirectoryGate { var count=0; var failAll=true; var failAt:Int? }
let root=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
try! FileManager.default.createDirectory(at:root,withIntermediateDirectories:true)
// Creation remains possible while enumeration is denied, the exact R3 failure.
for n in 0..<9 {try! Data().write(to:root.appendingPathComponent("events-existing-\(n).jsonl"))}
let q=DispatchQueue(label:"failure-boundary");let gate=DirectoryGate()
let sink=BotBridgeDiagnosticSink(root:root,queue:q,listDirectory:{ url in
 gate.count += 1
 if gate.failAll || gate.failAt == gate.count {throw CocoaError(.fileReadNoPermission)}
 return try FileManager.default.contentsOfDirectory(at:url,includingPropertiesForKeys:[.contentModificationDateKey,.fileSizeKey])
})
let record=BotBridgeDiagnosticRecord(session:UUID(),epoch:UUID(),sequence:1,wall:Date().timeIntervalSince1970,phase:.submitted)
for _ in 0..<3 {sink.accept(record,reserved:false);q.sync {}}
func expectStorage() {
 let done=DispatchSemaphore(value:0)
 sink.export {result in if case .failure(.storage)=result {} else {preconditionFailure("enumeration failure must not export false no_captured_sessions")};done.signal()}
 check(done.wait(timeout:.now()+5) == .success,"failure export returns asynchronously")
}
expectStorage()
let existing=try! FileManager.default.contentsOfDirectory(at:root,includingPropertiesForKeys:[])
check(existing.filter{$0.pathExtension=="jsonl"}.count==9,"unknown retention prevents all new appends")
check(existing.filter{$0.pathExtension=="json"}.isEmpty,"failure creates no misleading JSON artifact")
q.sync {gate.failAll=false;gate.failAt=nil}
// With no pending events: export performs retention listing, stale-export listing,
// then retained-record listing. Every one must fail closed, even after earlier success.
for call in [1,2,3] {q.sync {gate.count=0;gate.failAt=call};expectStorage()}
q.sync {gate.count=0;gate.failAt=nil}
let done=DispatchSemaphore(value:0)
sink.export {result in
 guard case let .success(url)=result else {preconditionFailure("recovery export")}
 let json=try! JSONSerialization.jsonObject(with:Data(contentsOf:url)) as! [String:Any]
 check((json["storageFailures"] as! NSNumber).intValue>=7,"enumeration/storage losses explicitly counted")
 check(json["storageLossCountUnknown"] as? Bool == true,"failed persistence remains explicit after recovery")
 sink.release(url);done.signal()
}
check(done.wait(timeout:.now()+5) == .success,"recovered export")
q.sync {};try? FileManager.default.removeItem(at:root)
print("PASS actual sink policy: all directory listing failures stop appends/export and report storage loss")
