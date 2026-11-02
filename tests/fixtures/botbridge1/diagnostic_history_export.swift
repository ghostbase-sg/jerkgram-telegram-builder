func check(_ value:@autoclosure()->Bool,_ reason:String){precondition(value(),reason)}
let root=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
let sink=BotBridgeDiagnosticSink(root:root)
let scope=BotBridgeDiagnosticScope(generation:UUID().uuidString,sink:sink,cancelHistory:{_ in})
let phases:[BotBridgeHistoryEvent.Phase]=[.started,.terminal,.restoredTerminal]
let reasons:[BotBridgeHistoryReason?]=[nil,.completed,.limit]
for index in 0..<3 {
 let n=Int32(index*100)
 let e=BotBridgeHistoryEvent(phase:phases[index],original:BotBridgeCursor(pts:11+n,qts:12+n,date:13+n,seq:14+n),candidate:BotBridgeCursor(pts:21+n,qts:22+n,date:23+n,seq:24+n),retrieval:BotBridgeCursor(pts:31+n,qts:32+n,date:33+n,seq:34+n),live:BotBridgeCursor(pts:41+n,qts:42+n,date:43+n,seq:44+n),reservedRequests:17+index,committedPages:9+index,examinedMessages:311+index,insertedMessages:101+index,insertedPeers:53+index,insertedUsers:23+index,insertedChats:30+index,deleteIdsObserved:29+index,skipped:79+index,unsupported:127+index,historicalDeletionObserved:5+index,missingReferences:87+index,reason:reasons[index])
 let adapted=botBridgeDiagnosticHistory(e) // The exact production mapping, no fixture mapping.
 scope.history(adapted.history,phase:adapted.phase)
}
let done=DispatchSemaphore(value:0)
sink.export {result in
 guard case let .success(url)=result else {preconditionFailure("history export")}
 let data=try! Data(contentsOf:url)
 let report=try! JSONSerialization.jsonObject(with:data) as! [String:Any]
 let records=(report["records"] as! [[String:Any]]).sorted {($0["sequence"] as! NSNumber).intValue < ($1["sequence"] as! NSNumber).intValue}
 check(records.count==3,"three real serialized history records")
 let wantedPhases=["historyStart","historyEnd","restoredTerminal"]
 let fields:[String:Int]=["reservedAttempts":17,"committedPages":9,"examinedMessages":311,"insertedMessages":101,"insertedPeers":53,"insertedUsers":23,"insertedChats":30,"deleteIdsObserved":29,"skipped":79,"unsupported":127,"historicalDeletionObserved":5,"missingReferences":87]
 let baseKeys=Set(fields.keys).union(["original","candidate","lastRetrieval","observedLive","deletionCoverageLimited","liveStateNeverReplaced","modernProcessingResumed"])
 for index in 0..<3 {
  let record=records[index];check(record["phase"] as? String == wantedPhases[index],"serialized phase")
  let history=record["history"] as! [String:Any]
  check(Set(history.keys)==(index==0 ? baseKeys : baseKeys.union(["reason"])),"exact export history fields, no progress/private identifiers")
  for (key,value) in fields {check((history[key] as! NSNumber).intValue==value+index,"distinct exact \(key) mapping")}
  let tupleBases=["original":11,"candidate":21,"lastRetrieval":31,"observedLive":41]
  for (key,base) in tupleBases {
   let tuple=history[key] as! [String:Any]
   check(Set(tuple.keys)==["pts","qts","date","seq"],"numeric tuple schema")
   for (offset,part) in ["pts","qts","date","seq"].enumerated(){check((tuple[part] as! NSNumber).intValue==base+index*100+offset,"distinct numeric tuple \(key).\(part)")}
  }
  check(history["liveStateNeverReplaced"] as? Bool == true && history["deletionCoverageLimited"] as? Bool == true,"explicit handoff/coverage bounds")
  check(history["modernProcessingResumed"] as? Bool == (index==2),"restored-terminal is resumed status")
 }
 check((records[1]["history"] as! [String:Any])["reason"] as? String == "completed","finite end reason")
 check((records[2]["history"] as! [String:Any])["reason"] as? String == "limit","finite restored reason")
 let text=String(data:data,encoding:.utf8)!
 for forbidden in ["PRIVATE_BOT_TOKEN","PRIVATE_MESSAGE_QUOTE","parameters","\"owner\"","\"peer\"","\"progress\"","authKey","errorDescription"] {check(!text.contains(forbidden),"history export privacy sentinel")}
 sink.release(url);done.signal()
}
check(done.wait(timeout:.now()+5) == .success,"history adapter async export completion")
print("PASS actual history adapter -> recorder -> serialized export: start/end/restored exact fields/tuples/counters/privacy")
