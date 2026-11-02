// Additional assertions on actual final controller (all accepted Task1 scenarios above run too).
do {
    var p = BotBridgeHistoryProgress(owner: 7, peer: 1, testing: false, generation: "g1")
    p.terminal = .cancelled
    let h = Host(progress: p); h.start(); h.queue.drain()
    check(h.network.requests.isEmpty && h.manager.customStarts == 0, "restored terminal cannot restart import")
    check(h.sink.values.count == 1 && h.sink.values[0].phase == .restoredTerminal && h.sink.values[0].reason == .cancelled, "truthful restored terminal snapshot")
}
do {
    let h = Host(); h.seedToDifference(); h.reply(difference(100))
    let terminal = h.sink.values.first { $0.phase == .terminal }!
    check(terminal.original?.pts == 100 && terminal.candidate?.pts == 90 && terminal.retrieval?.pts == 100, "exact retrieval tuple export boundary")
    check(terminal.live == BotBridgeCursor(pts: 7, qts: 8, date: 9, seq: 10), "numeric observed live tuple from existing read only transaction")
    check(terminal.reservedRequests == 2 && terminal.committedPages == 1, "reserved attempts distinct from commits")
}
print("PASS final controller restored-terminal and observed live tuple")
