
private func runAutosaveCases() {
    for (input, expected) in [("", nil), (".", nil), ("12.", nil), ("12,5", "12.5"), (".5", "0.5"), ("00012", "12"), ("9 001", "9001"), ("-1", nil), ("١", nil), ("9223372036854775808", nil), ("1.1234567891", "1.123456789"), ("1.2.3", nil)] as [(String, String?)] {
        precondition(jerkgramSavedStarsAmount(input) == expected, input)
    }
    precondition(jerkgramStarsPreset(String(Int64.max), delta: 100) == String(Int64.max))
    precondition(jerkgramStarsPreset("0", delta: -100) == "0")
    let initial = JerkgramStarsDraftState(enabled: false, amount: "0")
    var commits: [JerkgramStarsDraftState] = []
    var callbacks: [() -> Void] = []
    var cancellations = 0
    var editor: JerkgramStarsAutosave? = JerkgramStarsAutosave(initial: initial, commit: { commits.append($0) }, schedule: { action in
        callbacks.append(action)
        return { cancellations += 1 }
    })
    for amount in ["1", "12", "123", "123.", ".", "", "invalid"] {
        editor!.update(JerkgramStarsDraftState(enabled: true, amount: amount))
    }
    precondition(commits.isEmpty, "input must not write synchronously")
    // Even if a cancelled callback executes, its generation cannot write.
    for callback in callbacks { callback() }
    precondition(commits == [JerkgramStarsDraftState(enabled: true, amount: "123")])
    precondition(cancellations == 3)
    editor!.flush()
    precondition(commits.count == 1)
    editor!.update(JerkgramStarsDraftState(enabled: true, amount: "7.5"))
    editor!.flush() // navigation departure before delay
    precondition(commits.last!.amount == "7.5" && commits.count == 2)
    for callback in callbacks { callback() }
    precondition(commits.count == 2)
    editor!.update(JerkgramStarsDraftState(enabled: false, amount: ""))
    editor = nil // release also flushes latest valid draft/toggle
    precondition(commits.last! == JerkgramStarsDraftState(enabled: false, amount: "7.5"))
    precondition(commits.count == 3)
    var otherAccount: [JerkgramStarsDraftState] = []
    let other = JerkgramStarsAutosave(initial: initial, commit: { otherAccount.append($0) }, schedule: { _ in return {} })
    other.update(JerkgramStarsDraftState(enabled: true, amount: "55"))
    other.flush()
    precondition(otherAccount.last!.amount == "55" && commits.last!.amount == "7.5")
    print("actual autosave: valid/invalid/partial/overflow/coalescing/stale/departure/release/account isolation PASS")
}
runAutosaveCases()
