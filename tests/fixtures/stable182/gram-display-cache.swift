// Execute actual Wallet View refresh/display methods with a counted settings reader.
struct GramFixturePeerId { let value: Int64; func toInt64() -> Int64 { value } }
struct GramFixtureAccount { let peerId: GramFixturePeerId }
struct GramFixtureContext { let account: GramFixtureAccount }
struct GramFixtureComponent { let context: GramFixtureContext }
struct GramFixtureBalance { let currentValue: Int64 }
struct GramFixtureWalletState { let balance: GramFixtureBalance }
final class GramFixtureComponentState {
    enum Transition { case immediate }
    var updates = 0
    func updated(transition: Transition) { updates += 1 }
}
enum CountingGramBalance {
    static var values: [Int64: Int64] = [101: 8_000_000_000, 202: 9_000_000_000]
    static var reads = 0
    static func visualBalance(accountPeerId: Int64) -> Int64? {
        reads += 1
        return values[accountPeerId]
    }
}
final class GramDisplayHarness {
    var component: GramFixtureComponent?
    var componentState: GramFixtureComponentState? = GramFixtureComponentState()
    var localGramVisualBalance: Int64?
    var walletState: GramFixtureWalletState? = GramFixtureWalletState(balance: GramFixtureBalance(currentValue: 17_000_000_000))
    // ACTUAL_WALLET_METHODS
}
let view = GramDisplayHarness()
func component(_ account: Int64) -> GramFixtureComponent {
    GramFixtureComponent(context: GramFixtureContext(account: GramFixtureAccount(peerId: GramFixturePeerId(value: account))))
}
view.component = component(101)
view.refreshLocalGramBalance()
let initialReads = CountingGramBalance.reads
for _ in 0..<1_000 { check(view.displayBalance == 8_000_000_000, "cached display") }
check(CountingGramBalance.reads == initialReads, "layout never loads settings or parses amount")
view.refreshLocalGramBalance(notification: Notification(name: JerkgramLocalGramBalance.changed, userInfo: ["accountPeerId": NSNumber(value: 202)]))
check(CountingGramBalance.reads == initialReads, "other account notification does not read")
CountingGramBalance.values[101] = nil
view.refreshLocalGramBalance(notification: Notification(name: JerkgramLocalGramBalance.changed, userInfo: ["accountPeerId": NSNumber(value: 101)]))
check(view.displayBalance == 17_000_000_000, "off notification restores real balance")
CountingGramBalance.values[101] = 0
view.refreshLocalGramBalance(notification: Notification(name: Notification.Name("JerkgramSettingsDidImport"), userInfo: ["accountPeerId": NSNumber(value: 101)]))
check(view.displayBalance == 0, "archive import refresh includes explicit zero")
view.component = component(202)
view.refreshLocalGramBalance()
check(view.displayBalance == 9_000_000_000, "component identity refresh replaces previous account snapshot")
view.component = nil
view.refreshLocalGramBalance()
check(view.localGramVisualBalance == nil, "cleared component clears cached override")
print("actual Wallet View cached display and account/import invalidation matrix passed")
