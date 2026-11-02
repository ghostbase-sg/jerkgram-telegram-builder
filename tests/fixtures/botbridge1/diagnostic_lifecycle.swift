// The exact production logout Signal is inserted, backed by an unavoidable
// in-memory AccountManager transaction facade. No lifecycle/registry policy is faked.
protocol Disposable { func dispose() }
final class ActionDisposable: Disposable { let action: () -> Void; init(_ action: @escaping () -> Void) { self.action = action }; func dispose() { action() } }
public enum NoError: Error {}
final class Subscriber<T,E:Error> { let next:(T)->Void; let error:(E)->Void; let completed:()->Void; init(_ next:@escaping(T)->Void,_ error:@escaping(E)->Void,_ completed:@escaping()->Void) {self.next=next;self.error=error;self.completed=completed}; func putNext(_ value:T){next(value)};func putError(_ e:E){error(e)};func putCompletion(){completed()} }
public final class Signal<T,E:Error> { let generator:(Subscriber<T,E>)->Disposable; init(_ generator:@escaping(Subscriber<T,E>)->Disposable){self.generator=generator};func start(next:@escaping(T)->Void={_ in},error:@escaping(E)->Void={_ in},completed:@escaping()->Void={}) -> Disposable {generator(Subscriber(next,error,completed))} }
public struct AccountRecordId: Hashable { let int64:Int64 }
struct LoggedOutAccountAttribute {}
public struct TelegramAccountManagerTypes {enum Attribute {case loggedOut(LoggedOutAccountAttribute)}}
struct AccountRecord {let id:AccountRecordId;let attributes:[TelegramAccountManagerTypes.Attribute];let temporarySessionId:Int64?}
final class AccountTransaction { var records:[AccountRecordId:AccountRecord]=[:];func updateRecord(_ id:AccountRecordId,_ update:(AccountRecord?)->AccountRecord?){records[id]=update(records[id])} }
public final class AccountManager<T> {let value=AccountTransaction();var beforeTransaction:()->Void={};func transaction<R>(_ f:@escaping(AccountTransaction)->R)->Signal<R,NoError>{Signal{ s in self.beforeTransaction();s.putNext(f(self.value));s.putCompletion();return ActionDisposable{} }} }
final class Logger {static let shared=Logger();func log(_ category:String,_ text:String){}}
/* REAL_LOGOUT */
func check(_ value:@autoclosure()->Bool,_ reason:String){precondition(value(),reason)}
let root=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
let sink=BotBridgeDiagnosticSink(root:root)
let manager=AccountManager<TelegramAccountManagerTypes>(), other=AccountManager<TelegramAccountManagerTypes>()
let record=AccountRecordId(int64:17)
manager.value.records[record]=AccountRecord(id:record,attributes:[],temporarySessionId:nil)
var cancellations=0
let scope=BotBridgeDiagnosticScope(generation:UUID().uuidString,sink:sink,cancelHistory:{_ in cancellations += 1})
check(BotBridgeDiagnosticRegistry.shared.register(namespace:manager,record:17,scope:scope),"register")
manager.beforeTransaction={check(scope.isFrozen && cancellations==1,"cancellation and snapshot precede transaction execution")}
let signal=logoutFromAccount(id:record,accountManager:manager,alreadyLoggedOutRemotely:false)
check(cancellations==0 && scope.snapshotEvents().isEmpty && manager.value.records[record]!.attributes.isEmpty,"constructing logout has no lifecycle effect")
let _=signal.start()
check(cancellations==1 && scope.isFrozen && manager.value.records[record]!.attributes.count==1,"subscribed logout cancels before transaction")
let otherScope=BotBridgeDiagnosticScope(generation:UUID().uuidString,sink:sink,cancelHistory:{_ in})
check(BotBridgeDiagnosticRegistry.shared.register(namespace:other,record:17,scope:otherScope),"second namespace")
BotBridgeDiagnosticRegistry.shared.reconcile(namespace:manager,records:[])
check(!otherScope.isFrozen,"record removal isolated to namespace")
let oldEpoch=otherScope.epoch
BotBridgeDiagnosticRegistry.shared.unregister(namespace:other,record:17,epoch:oldEpoch)
let replacement=BotBridgeDiagnosticScope(generation:UUID().uuidString,sink:sink,cancelHistory:{_ in})
check(BotBridgeDiagnosticRegistry.shared.register(namespace:other,record:17,scope:replacement),"replacement")
BotBridgeDiagnosticRegistry.shared.unregister(namespace:other,record:17,epoch:oldEpoch)
BotBridgeDiagnosticRegistry.shared.notify(namespace:other,record:17,kind:.remoteLogout)
check(replacement.isFrozen,"old epoch cannot unregister replacement")
// Capacity fails closed while all cancellation targets remain alive.
final class Space {}
let registry=BotBridgeDiagnosticRegistry();let space=Space()
var scopes:[BotBridgeDiagnosticScope]=[]
for n in 0..<32 {let s=BotBridgeDiagnosticScope(generation:UUID().uuidString,sink:sink,cancelHistory:{_ in});scopes.append(s);check(registry.register(namespace:space,record:Int64(n),scope:s),"32 target admission")}
let extra=BotBridgeDiagnosticScope(generation:UUID().uuidString,sink:sink,cancelHistory:{_ in})
check(!registry.register(namespace:space,record:99,scope:extra),"capacity fails closed")
registry.notify(namespace:space,record:0,kind:.removed);check(scopes[0].isFrozen,"no live cancellation target evicted")
let owner=BotBridgeDiagnosticOwner();let registration=BotBridgeScopeRegistration()
check(!owner.admit(namespace:space,record:100,generation:"PRIVATE_BAD_GENERATION",registration:registration,cancelHistory:{_ in}),"generation admission validates UUID")
print("PASS actual logout/registry: cold subscription, namespaces, epoch replacement, capacity, generation")
// R1: immutable generation/epoch tokens cannot target a newly admitted account.
do {
 let r=BotBridgeDiagnosticRegistry();let ns=Space()
 let original=BotBridgeDiagnosticScope(generation:UUID().uuidString,sink:sink,cancelHistory:{_ in})
 check(r.register(namespace:ns,record:701,scope:original,directoryName:"account-deferred"),"original token admission")
 let oldTarget=r.target(namespace:ns,record:701)!
 original.lifecycle(.cleanupStart)
 r.unregister(namespace:ns,record:701,epoch:original.epoch)
 let next=BotBridgeDiagnosticScope(generation:UUID().uuidString,sink:sink,cancelHistory:{_ in})
 check(r.register(namespace:ns,record:701,scope:next,directoryName:"account-deferred"),"new generation admission")
 r.notify(target:oldTarget,kind:.cleanupResult)
 check(!next.isFrozen && next.snapshotEvents().isEmpty,"late cleanup completion cannot freeze replacement generation")
 let nextTarget=r.target(namespace:ns,record:701)!
 r.unregister(namespace:ns,record:701,epoch:next.epoch)
 let sameGeneration=BotBridgeDiagnosticScope(generation:next.generation,sink:sink,cancelHistory:{_ in})
 check(r.register(namespace:ns,record:701,scope:sameGeneration,directoryName:"account-deferred"),"same generation new epoch")
 r.notify(target:nextTarget,kind:.cleanupResult)
 check(!sameGeneration.isFrozen,"late cleanup also rejects a replacement epoch within the same generation")
}
// R2: execute the actual production path predicate/hook. A retained path is not
// scheduled for deletion merely because cleanup has started.
do {
 let ns=Space();let s=BotBridgeDiagnosticScope(generation:UUID().uuidString,sink:sink,cancelHistory:{_ in})
 check(BotBridgeDiagnosticRegistry.shared.register(namespace:ns,record:702,scope:s,directoryName:"account-retained"),"directory target")
 let targets=BotBridgeDiagnosticRegistry.shared.targets(namespace:ns)
 BotBridgeDiagnosticRegistry.shared.notify(target:targets[0],kind:.cleanupStart)
 check(!botBridgeScheduleAccountDirectoryDeletion(directoryName:"account-retained",validPaths:["account-retained"],targets:targets),"retained path not scheduled")
 check(!s.snapshotEvents().contains{$0.lifecycle == .deletionScheduled},"cleanup start cannot claim deletion")
 check(botBridgeScheduleAccountDirectoryDeletion(directoryName:"account-retained",validPaths:[],targets:targets),"excluded path schedules deletion")
 check(s.snapshotEvents().filter{$0.lifecycle == .deletionScheduled}.count==1,"one event at actual excluded directory boundary")
 BotBridgeDiagnosticRegistry.shared.unregister(namespace:ns,record:702,epoch:s.epoch)
 let replacement=BotBridgeDiagnosticScope(generation:UUID().uuidString,sink:sink,cancelHistory:{_ in})
 check(BotBridgeDiagnosticRegistry.shared.register(namespace:ns,record:702,scope:replacement,directoryName:"account-retained"),"directory replacement")
 check(botBridgeScheduleAccountDirectoryDeletion(directoryName:"account-retained",validPaths:[],targets:targets),"old queued native deletion remains scheduled")
 check(!replacement.isFrozen && replacement.snapshotEvents().isEmpty,"queued directory observation cannot freeze replacement")
}
print("PASS review fixes: stale generation/epoch cleanup and truthful directory scheduling")

do {
 let r=BotBridgeDiagnosticRegistry();var token:BotBridgeDiagnosticTarget?;weak var weakNamespace:Space?
 let s=BotBridgeDiagnosticScope(generation:UUID().uuidString,sink:sink,cancelHistory:{_ in})
 do {let ns=Space();weakNamespace=ns;check(r.register(namespace:ns,record:703,scope:s),"weak namespace registration");token=r.target(namespace:ns,record:703)}
 check(weakNamespace==nil && token?.namespace==nil,"deferred target retains neither namespace nor Account")
 r.notify(target:token,kind:.cleanupResult)
 check(!s.isFrozen,"dead namespace token cannot issue lifecycle callback")
}
