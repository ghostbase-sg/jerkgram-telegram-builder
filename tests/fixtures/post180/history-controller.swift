do {
    let h = Host();h.seedToDifference()
    h.reply(difference(101, slice: true, messages: [apiMessage(1)]))
    h.clock.offset += 121
    h.reply(difference(102, slice: true, messages: [apiMessage(2)]))
    check(h.progress.terminal == .deadline && h.transaction.messages.count == 1, "commit-time deadline preserves earlier advancing page")
    h.queue.advance(1)
    check(h.progress.historyWindow == 1 && h.network.requests.last?.cursor?.pts == 101, "commit-time deadline continues from last committed cursor")
    h.reply(difference(102, messages: [apiMessage(2)]));h.finished(.completed)
    check(h.transaction.messages.count == 2, "continued deadline imports previously uncommitted page")
}
do {
    let h = Host();h.seedToDifference()
    h.manager.modern();h.queue.drain()
    check(h.manager.modernRuns == 1 && h.manager.customStarts == 0, "live operation must finish while history RPC remains pending")
    h.queue.advance(10);h.finished(.timeout)
}
do {
    let h = Host();h.start();h.queue.drain();h.reply(state(100, unread: 0))
    check(h.network.requests.last?.cursor == BotBridgeCursor(pts: 0, qts: 0, date: 0, seq: 0), "zero unread retrieves history")
    for page in 0..<41 {
        let messages = (1...600).map { apiMessage(Int32(page * 600 + $0)) }
        h.manager.modern()
        h.reply(difference(Int32(101 + page), slice: page != 40, messages: messages))
        if page == 31 {
            check(h.progress.terminal == .limit && !h.manager.running, "yield after 32 requests")
            h.queue.advance(1)
            check(h.progress.historyWindow == 1, "continuation resumes")
            check(h.network.requests.last?.cursor?.pts == 132, "continuation uses server cursor")
        }
    }
    h.finished(.completed)
    check(h.transaction.messages.count == 24600, "all 24,600 returned historical messages inserted")
    check(h.manager.modernRuns == 41, "live operations run between history pages")
    check(h.transaction.state.peerId == account, "authorization not replaced")
}
do {
    let h = Host(bot: false);h.start();h.queue.drain()
    check(h.network.requests.isEmpty, "non-bot never starts history replay")
}
do {
    let h = Host();h.seedToDifference()
    h.controller?.cancel(reason: .loggedOut);h.queue.drain()
    h.reply(difference(101, messages: [apiMessage(1)]))
    h.queue.advance(120)
    check(h.transaction.messages.isEmpty && h.network.requests.count == 2, "logout rejects late page and continuation")
}
print("PASS actual post180 controller: 24,600 messages, two windows, live yield, nonbot, logout")
