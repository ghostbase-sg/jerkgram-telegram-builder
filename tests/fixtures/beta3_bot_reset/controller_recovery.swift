// Exact production controller/storage reject callbacks and terminal writes from
// the predecessor after preparation persisted a recovered generation.
do {
    let h = Host()
    h.transaction.state = AuthorizedAccountState(peerId: account, isTestingEnvironment: false,
        state: .init(pts: 51, qts: 3, date: 17, seq: 2))
    check(botBridgeObservedLive(transaction: h.transaction) == BotBridgeCursor(pts: 51, qts: 3, date: 17, seq: 2),
        "observed live cursor uses the account state")
}
do {
    let h = Host(); h.start(); h.queue.drain()
    var old = h.progress; old.terminal = .softReset
    h.transaction.progress = PreferencesEntry(old)
    let fresh = jerkgramPrepareBotBridgeHistory(transaction: h.transaction, owner: 7, accountPeerId: account, lifetime: BotBridgeLifetime())!
    check(fresh.softResetRecoveryVersion == 1 && fresh.generation != old.generation, "migrate retained initial shape")
    h.reply(state(), at: 0)
    check(h.progress == fresh && h.transaction.messages.isEmpty, "old state and terminal writes cannot modify recovered generation")
    h.controller!.cancel(reason: .softReset); h.queue.drain()
    check(h.progress == fresh, "late predecessor cancellation cannot mark recovery terminal")
}
do {
    var old = BotBridgeHistoryProgress(owner: 7, peer: 1, testing: false, generation: "retained")
    _ = old.reserve(now: 1000); old.terminal = .softReset
    let h = Host(progress: old); h.start(); h.queue.drain()
    check(h.progress.softResetRecoveryVersion == 1 && h.network.requests.count == 1, "recovery dispatches state once")
    h.controller!.cancel(reason: .softReset); h.queue.drain(); h.finished(.softReset)
    let generation = h.progress.generation
    h.crash(); h.restart()
    check(h.progress.generation == generation && h.network.requests.count == 1, "recovery auth failure is sticky across relaunch")
}
print("PASS recovered generation rejects predecessor callbacks and terminal writes")
