// Actual shared presentation stream; transport/signal boundaries only are facades.
func combineLatest<A,B,E:Error>(_ a:Signal<A,E>,_ b:Signal<B,E>)->Signal<(A,B),E> {
    Signal { sub in
        var aa:A?,bb:B?
        let da=a.start(next:{ value in aa=value; if let a=aa,let b=bb { sub.putNext((a,b)) } })
        let db=b.start(next:{ value in bb=value; if let a=aa,let b=bb { sub.putNext((a,b)) } })
        return ActionDisposable {da.dispose();db.dispose()}
    }
}
func map<A,B,E:Error>(_ transform:@escaping(A)->B)->(Signal<A,E>)->Signal<B,E> {
    { source in Signal { sub in source.start(next:{sub.putNext(transform($0))}) } }
}
// ACTUAL_GRAM_SIGNAL
let accountA:Int64=19_000_001,accountB:Int64=19_000_002
for account in [accountA,accountB] {
    UserDefaults.standard.removeObject(forKey:JerkgramLocalGramBalance.scopedKey(accountPeerId:account,key:JerkgramLocalGramBalance.enabledKey))
    UserDefaults.standard.removeObject(forKey:JerkgramLocalGramBalance.scopedKey(accountPeerId:account,key:JerkgramLocalGramBalance.amountKey))
}
defer {
    for account in [accountA,accountB] {
        UserDefaults.standard.removeObject(forKey:JerkgramLocalGramBalance.scopedKey(accountPeerId:account,key:JerkgramLocalGramBalance.enabledKey))
        UserDefaults.standard.removeObject(forKey:JerkgramLocalGramBalance.scopedKey(accountPeerId:account,key:JerkgramLocalGramBalance.amountKey))
    }
}
let nativeA=ValuePromise<Int64>(7,ignoreRepeated:true),nativeB=ValuePromise<Int64>(200,ignoreRepeated:true)
var a:[Int64]=[],b:[Int64]=[]
let da=JerkgramLocalGramBalance.displayedBalance(accountPeerId:accountA,native:nativeA.get()).start(next:{a.append($0)})
let db=JerkgramLocalGramBalance.displayedBalance(accountPeerId:accountB,native:nativeB.get()).start(next:{b.append($0)})
precondition(a==[7] && b==[200])
JerkgramLocalGramBalance.commit(accountPeerId:accountA,enabled:true,amount:"8.000000001")
precondition(a.last==8_000_000_001 && b==[200])
let prior=a.count
nativeA.set(11)
precondition(a.count==prior && nativeA.value==11,"native engine value remains real")
JerkgramLocalGramBalance.commit(accountPeerId:accountA,enabled:true,amount:"0")
precondition(a.last==0)
JerkgramLocalGramBalance.commit(accountPeerId:accountA,enabled:false,amount:"0")
precondition(a.last==11)
JerkgramLocalGramBalance.commit(accountPeerId:accountB,enabled:true,amount:"9")
precondition(b.last==9_000_000_000 && a.last==11)
UserDefaults.standard.set(true,forKey:JerkgramLocalGramBalance.scopedKey(accountPeerId:accountA,key:JerkgramLocalGramBalance.enabledKey))
UserDefaults.standard.set("12",forKey:JerkgramLocalGramBalance.scopedKey(accountPeerId:accountA,key:JerkgramLocalGramBalance.amountKey))
NotificationCenter.default.post(name:Notification.Name("JerkgramSettingsDidImport"),object:nil,userInfo:["accountPeerId":NSNumber(value:accountA)])
precondition(a.last==12_000_000_000)
da.dispose();db.dispose()
let finalCount=a.count
JerkgramLocalGramBalance.commit(accountPeerId:accountA,enabled:true,amount:"13")
nativeA.set(15)
precondition(a.count==finalCount && nativeA.listeners.isEmpty && nativeB.listeners.isEmpty,"owner disposal stops observers and source subscriptions")
print("PASS actual GRAM presentation stream: real native state retained, zero/off/import, A/B isolation, distinct values and disposal")
