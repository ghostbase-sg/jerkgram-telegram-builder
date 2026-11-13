func check(_ value:Bool) { precondition(value) }
let root=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
let reloadedRoot=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
defer {try? FileManager.default.removeItem(at:root);try? FileManager.default.removeItem(at:reloadedRoot)}
func event(_ id:Int,_ sequence:Int64,_ chat:Int64=7,_ account:Int64=1)->JerkgramCanonicalEvent {
 JerkgramCanonicalEvent(accountPeerId:account,chatPeerId:chat,eventId:JerkgramEventId(rawValue:String(format:"e%04d",id)),sequence:sequence,kind:.editedMessage,senderPeerId:9,messageNamespace:0,messageId:Int32(id),observedAtMs:1,payload:JerkgramEventPayload(text:"value\(id)"))
}
let store=JerkgramJSONLEventStore(rootURL:root)
let initial=(0..<80).reversed().map {event($0,Int64($0/2),$0%5==0 ? 8:7)}
try store.appendBatch(initial)
try store.appendBatch([event(101,5),event(102,39),event(103,Int64.max),event(104,Int64.min)])
try store.append(event(105,2,7,2))
let canonical=root.appendingPathComponent("accounts/1/events.jsonl")
let bytes=try Data(contentsOf:canonical)
let all=try store.events(accountPeerId:1,chatPeerId:7)
for lower:Int64? in [nil,Int64.min,-1,0,5,39,Int64.max] {
 for upper:Int64? in [nil,Int64.min,-1,0,5,39,Int64.max] {
  let expected=all.filter {e in (lower == nil || e.sequence > lower!) && (upper == nil || e.sequence <= upper!)}.map(\.eventId)
  let indexed=try store.indexRecords(accountPeerId:1,chatPeerId:7,afterSequence:lower,throughSequence:upper).map(\.eventId)
  let ready=try store.readyIndexRecords(accountPeerId:1,chatPeerId:7,afterSequence:lower,throughSequence:upper).map(\.eventId)
  precondition(indexed==expected && ready==expected)
 }
}
check(try store.indexRecords(accountPeerId:1,chatPeerId:999).isEmpty)
check(try store.indexRecords(accountPeerId:2,chatPeerId:7).map(\.eventId)==[JerkgramEventId(rawValue:"e0105")])
check(try Data(contentsOf:canonical)==bytes)
try FileManager.default.copyItem(at:root,to:reloadedRoot)
let reopened=JerkgramJSONLEventStore(rootURL:reloadedRoot)
check(try reopened.readyIndexRecords(accountPeerId:1,chatPeerId:7).map(\.eventId)==all.map(\.eventId))
// Existing canonical external-change invalidation and partial-tail behavior retained.
let handle=try FileHandle(forWritingTo:reloadedRoot.appendingPathComponent("accounts/1/events.jsonl"))
try handle.seekToEnd();try handle.write(contentsOf:Data("{partial".utf8));try handle.close()
check(try reopened.indexRecords(accountPeerId:1,chatPeerId:7).map(\.eventId)==all.map(\.eventId))
print("actual JSONL store: ordering/ties/out-of-order append/account isolation/reload/partial-tail/read-only query PASS")
