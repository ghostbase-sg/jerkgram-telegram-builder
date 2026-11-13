let before=Before(), after=After()
let records=(0..<50_000).map { JerkgramTimeMachineIndexRecord(rawSequence:Int64($0/2),rawChat:7,eventId:JerkgramEventId(value:$0)) }
func compare(_ bucket:[JerkgramTimeMachineIndexRecord],_ lower:Int64?,_ upper:Int64?) {
 let expected=before.filteredRecords(bucket,chatPeerId:7,afterSequence:lower,throughSequence:upper)
 let actual=after.filteredRecords(bucket,chatPeerId:7,afterSequence:lower,throughSequence:upper)
 precondition(actual==expected,"range semantic mismatch")
}
for lower:Int64? in [nil,Int64.min,-1,0,1,24_990,24_999,25_000,Int64.max] {
 for upper:Int64? in [nil,Int64.min,-1,0,1,24_990,24_999,25_000,Int64.max] {compare(records,lower,upper)}
}
compare([],nil,nil)
let shuffled=Array(records.reversed())
let buckets=after.groupedRecordsByChat(shuffled)
precondition(buckets[7]==records)
let left=Array(records.prefix(20_000)),right=Array(records.suffix(30_000))
precondition(after.mergeAscending(left,right)==records)
let alternatingLeft=records.enumerated().filter{$0.offset%2==0}.map{$0.element}
let alternatingRight=records.enumerated().filter{$0.offset%2==1}.map{$0.element}
precondition(after.mergeAscending(alternatingLeft,alternatingRight)==records)
reads=0
let old=before.filteredRecords(records,chatPeerId:7,afterSequence:24_990,throughSequence:24_999)
let oldReads=reads
reads=0
let new=after.filteredRecords(records,chatPeerId:7,afterSequence:24_990,throughSequence:24_999)
let newReads=reads
precondition(old==new && old.count==18)
precondition(oldReads>=50_000 && newReads<=32)
print("cached range 50k records,18 returned: property reads \(oldReads) -> \(newReads); outputs equal; no FPS claim")
