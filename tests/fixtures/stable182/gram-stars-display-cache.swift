// Actual StarsTransactions current-account GRAM display methods.
struct StarsAmount: Equatable { let value: Int64; let nanos: Int32; static let zero = StarsAmount(value: 0, nanos: 0) }
func ghostBaseLocalStarsAmountForDisplay() -> StarsAmount? { nil }
final class GramStarsSource { let ton: Bool; init(_ ton: Bool) { self.ton = ton } }
final class GramStarsContext {
    let account: GramFixtureAccount
    let tonContext: GramStarsSource?
    init(_ id: Int64, _ source: GramStarsSource?) { account = GramFixtureAccount(peerId: GramFixturePeerId(value: id)); tonContext = source }
}
struct GramStarsComponent { let context: GramStarsContext; let starsContext: GramStarsSource }
struct GramStarsState { let balance: StarsAmount }
final class GramStarsUpdates { var count=0; func updated() { count += 1 } }
final class GramStarsHarness {
    var component: GramStarsComponent?
    var localGramVisualBalance: Int64?
    var starsState: GramStarsState? = GramStarsState(balance: StarsAmount(value: 17, nanos: 0))
    var state: GramStarsUpdates? = GramStarsUpdates()
    var isUpdating=false
    // ACTUAL_STARS_METHODS
}
let starsView=GramStarsHarness(), ownSource=GramStarsSource(true), foreignSource=GramStarsSource(true)
let ownContext=GramStarsContext(101,ownSource)
CountingGramBalance.values[101]=8_000_000_001
starsView.component=GramStarsComponent(context:ownContext,starsContext:ownSource)
starsView.refreshLocalGramBalance()
let starsReads=CountingGramBalance.reads
for _ in 0..<1000 { check(starsView.displayBalance.value==8_000_000_001,"native GRAM labels share cache") }
check(CountingGramBalance.reads==starsReads,"GRAM display has no per-layout settings reads")
starsView.refreshLocalGramBalance(notification: Notification(name:JerkgramLocalGramBalance.changed,userInfo:["accountPeerId":NSNumber(value:202)]))
check(CountingGramBalance.reads==starsReads,"foreign account ignored")
starsView.component=GramStarsComponent(context:ownContext,starsContext:foreignSource)
starsView.refreshLocalGramBalance()
check(starsView.displayBalance.value==17,"unrelated revenue/source retains native balance")
starsView.component=GramStarsComponent(context:ownContext,starsContext:ownSource)
CountingGramBalance.values[101]=nil
starsView.refreshLocalGramBalance(notification: Notification(name:JerkgramLocalGramBalance.changed,userInfo:["accountPeerId":NSNumber(value:101)]))
check(starsView.displayBalance.value==17,"disabled restores native balance")
print("actual native GRAM balance labels/cache/source isolation matrix passed")
