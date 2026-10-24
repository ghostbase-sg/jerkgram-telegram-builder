"""Run real Stars state-update and UI count expressions on macOS."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
from run_jg13_deleted_reply import block

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('JG13_SOURCE',ROOT/'work/swiftgram-src'))
core=(SOURCE/'submodules/TelegramCore/Sources/TelegramEngine/Payments/Stars.swift').read_text()
screen=(SOURCE/'submodules/TelegramUI/Components/Stars/StarsTransactionsScreen/Sources/StarsTransactionsScreen.swift').read_text()
core_helper=block(core,'private func ghostBaseLocalStarsVisualBalance()')
ui_helper=block(screen,'private func ghostBaseLocalStarsAmountForDisplay()')
update=block(core,'private func updateState(_ state: StarsContext.State)')
count=re.search(r'count: (\(component\.starsContext\.ton \? nil[^\n]+),\n',screen).group(1)

facade='''
import Foundation
struct StarsAmount: Equatable {
    let value: Int64
    let nanos: Int32
    static let zero = StarsAmount(value: 0, nanos: 0)
}
enum StarsContext {
    struct State {
        var balance: StarsAmount
        let transactionMarker: String
    }
}
enum StateSignal { case single(StarsContext.State) }
final class StatePromise {
    var value: StarsContext.State?
    func set(_ signal: StateSignal) {
        switch signal { case let .single(value): self.value=value }
    }
}
final class StateFixture {
    let ton: Bool
    var _state: StarsContext.State?
    let _statePromise = StatePromise()
    init(ton: Bool) { self.ton=ton }
    ACTUAL_UPDATE
    func receive(_ state: StarsContext.State) { self.updateState(state) }
}
struct ContextDescriptor { let ton: Bool }
struct ComponentDescriptor { let starsContext: ContextDescriptor }
struct UIFixture {
    let starsState: StarsContext.State?
    func count(component: ComponentDescriptor) -> StarsAmount { return ACTUAL_COUNT }
}
'''.replace('ACTUAL_UPDATE',update).replace('ACTUAL_COUNT',count)

fixture='''
let defaults=UserDefaults.standard
let enabledKey="jerkgram.Stars.LocalBalance.Enabled"
let amountKey="jerkgram.Stars.LocalBalance.Amount"
let oldEnabled=defaults.object(forKey:enabledKey), oldAmount=defaults.object(forKey:amountKey)
defer {
    if let oldEnabled { defaults.set(oldEnabled,forKey:enabledKey) } else { defaults.removeObject(forKey:enabledKey) }
    if let oldAmount { defaults.set(oldAmount,forKey:amountKey) } else { defaults.removeObject(forKey:amountKey) }
}
let values:[(String,StarsAmount?)]=[
    ("123.456",StarsAmount(value:123,nanos:456_000_000)),
    ("0",.zero),
    ("9 876,5",StarsAmount(value:9876,nanos:500_000_000)),
    ("invalid",nil)
]
var cases=0
for enabled in [false,true] {
    defaults.set(enabled,forKey:enabledKey)
    for ton in [false,true] {
        for (raw,parsed) in values {
            defaults.set(raw,forKey:amountKey)
            let context=StateFixture(ton:ton)
            for server in [StarsAmount(value:17,nanos:80),StarsAmount(value:23,nanos:123_456_789)] {
                let incoming=StarsContext.State(balance:server,transactionMarker:"real-server-history")
                context.receive(incoming)
                let expected=(!ton && enabled ? parsed : nil) ?? server
                precondition(context._state?.balance==expected)
                precondition(context._statePromise.value?.balance==expected)
                precondition(context._state?.transactionMarker==incoming.transactionMarker)
                // UI guard must also work independently with an unmodified server state.
                let component=ComponentDescriptor(starsContext:ContextDescriptor(ton:ton))
                precondition(UIFixture(starsState:incoming).count(component:component)==expected)
                precondition(UIFixture(starsState:context._state).count(component:component)==expected)
                let emptyExpected=(!ton && enabled ? parsed : nil) ?? .zero
                precondition(UIFixture(starsState:nil).count(component:component)==emptyExpected)
                cases += 1
            }
        }
    }
}
print("PASS: actual Stars updateState + UI count",cases,"cases; TON/Gram real balance, Stars override on/off, decimals/zero/invalid, missing state, repeat updates, history retained")
'''
with tempfile.TemporaryDirectory() as directory:
    path=Path(directory)/'main.swift'
    path.write_text(facade+'\n'+core_helper+'\n'+ui_helper+'\n'+fixture)
    subprocess.run(['xcrun','swift',str(path)],check=True)
