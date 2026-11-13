func check(_ value: @autoclosure () -> Bool, _ message: String) {
    precondition(value(), message)
}
let suite = "stable182-gram-fixture-\(UUID().uuidString)"
let defaults = UserDefaults(suiteName: suite)!
defer { defaults.removePersistentDomain(forName: suite) }
let a: Int64 = 101, b: Int64 = 202
let marker = "jerkgram.Settings.ActiveProjectionAccount.V176"
defaults.set(a, forKey: marker)
for invalid in ["", "-1", "nan", "1.2.3", "1.", ".", "9223372036.854775808", "9223372037", "99999999999999999999"] {
    check(jerkgramSavedGramAmount(invalid) == nil, "reject invalid/range \(invalid)")
}
for (input, canonical, nanos) in [("0", "0", Int64(0)), (".5", "0.5", 500_000_000), ("1 234,1234567899", "1234.123456789", 1_234_123_456_789), ("9223372036.854775807", "9223372036.854775807", Int64.max)] {
    check(jerkgramSavedGramAmount(input) == canonical, "canonical decimal")
    check(JerkgramLocalGramBalance.nanotokens(canonical) == nanos, "exact native integer")
}
check(!jerkgramIsValidGramDraft("-1"), "control rejects negative")
check(!jerkgramIsValidGramDraft("1.2.3"), "control rejects multiple separators")
check(jerkgramIsValidGramDraft("1 234,5"), "control accepts localized decimal")
var state = JerkgramGramDraftState(enabled: false, amount: "0")
var writes = 0
var pending: [() -> Void] = []
let autosave = JerkgramGramAutosave(initial: state, commit: { value in
    writes += 1
    JerkgramLocalGramBalance.commit(accountPeerId: a, enabled: value.enabled, amount: value.amount, defaults: defaults)
}, schedule: { action in pending.append(action); return {} })
func update(_ transform: (inout JerkgramGramDraftState) -> Void) {
    transform(&state)
    autosave.update(state)
}
// ACTUAL_CONTROL_ARGUMENTS
arguments.setEnabled(true)
let immediateToggle = EXPECT_IMMEDIATE_TOGGLE
check(writes == (immediateToggle ? 1 : 0), "toggle persistence follows selected source contract")
if immediateToggle {
    check(JerkgramLocalGramBalance.visualBalance(accountPeerId: a, defaults: defaults) == 0, "enable immediately publishes explicit zero")
}
let writesAfterToggle = writes
for amount in ["1", "12", "123.456789123"] { arguments.setAmount(amount) }
check(writes == writesAfterToggle, "typing remains deferred")
pending.forEach { $0() }
check(writes == writesAfterToggle + 1, "rapid amount updates coalesce, canceled stale callbacks ignored")
check(JerkgramLocalGramBalance.visualBalance(accountPeerId: a, defaults: defaults) == 123_456_789_123, "display saved valid amount")
arguments.setAmount("invalid")
autosave.flush()
check(writes == writesAfterToggle + 1, "invalid input keeps last valid stored amount")
arguments.setEnabled(false)
if immediateToggle {
    check(JerkgramLocalGramBalance.visualBalance(accountPeerId: a, defaults: defaults) == nil, "disable immediately restores real presentation")
}
autosave.flush()
check(JerkgramLocalGramBalance.visualBalance(accountPeerId: a, defaults: defaults) == nil, "disable restores real presentation")
check(JerkgramLocalGramBalance.amount(accountPeerId: a, defaults: defaults) == "123.456789123", "disable retains choice")
arguments.setAmount("0")
arguments.setEnabled(true)
autosave.flush()
check(JerkgramLocalGramBalance.visualBalance(accountPeerId: a, defaults: defaults) == 0, "explicit zero override")
arguments.applyPreset(100)
autosave.flush()
check(JerkgramLocalGramBalance.amount(accountPeerId: a, defaults: defaults) == "100", "actual preset control persists")
// Switching accounts while A closes must not alter B's projection.
defaults.set(b, forKey: marker)
JerkgramLocalGramBalance.commit(accountPeerId: b, enabled: true, amount: "7.5", defaults: defaults)
arguments.setAmount("200")
autosave.flush()
check(defaults.string(forKey: JerkgramLocalGramBalance.amountKey) == "7.5", "stale A cannot replace B alias")
check(JerkgramLocalGramBalance.visualBalance(accountPeerId: b, defaults: defaults) == 7_500_000_000, "B remains independent")
check(JerkgramLocalGramBalance.visualBalance(accountPeerId: 303, defaults: defaults) == nil, "new account ignores global aliases")
var closing: JerkgramGramAutosave? = JerkgramGramAutosave(
    initial: JerkgramGramDraftState(enabled: false, amount: "0"),
    commit: { JerkgramLocalGramBalance.commit(accountPeerId: 404, enabled: $0.enabled, amount: $0.amount, defaults: defaults) },
    schedule: { _ in return {} })
closing?.update(JerkgramGramDraftState(enabled: true, amount: "9"))
closing = nil
check(JerkgramLocalGramBalance.visualBalance(accountPeerId: 404, defaults: defaults) == 9_000_000_000, "deinit flush retains final edit")
let relaunched = UserDefaults(suiteName: suite)!
check(JerkgramLocalGramBalance.amount(accountPeerId: a, defaults: relaunched) == "200", "relaunch reads scoped saved A")
check(JerkgramLocalGramBalance.amount(accountPeerId: b, defaults: relaunched) == "7.5", "relaunch reads scoped saved B")
print("stable182 GRAM native control/autosave/state matrix passed")
