func require(_ result: @autoclosure () -> Bool, _ message: String) { precondition(result(), message) }
func fresh() -> BotBridgeHistoryProgress { BotBridgeHistoryProgress(owner: 7, peer: 1, testing: false, generation: "fixture") }
var progress = fresh()
require(progress.reserve(now: 1000) == .state, "initial request")
let live = BotBridgeCursor(pts: 70000, qts: 4, date: 1800000000, seq: 9)
require(progress.acceptState(live, unread: 0, now: 1001), "read bot admission")
require(progress.candidate == BotBridgeCursor(pts: 0, qts: 0, date: 0, seq: 0), "full replay must not depend on unread")
for page in 1...32 {
    require(progress.reserve(now: Double(1001 + page)) != nil, "page reservation")
    require(progress.commit(next: BotBridgeCursor(pts: Int32(page), qts: 0, date: Int32(page), seq: 0), final: false, examined: 1000, inserted: 1000, peers: 0, skipped: 0, unsupported: 0, deletions: 0, missing: 0, now: Double(1001 + page)), "page beyond old 20k ceiling")
}
require(progress.examined == 32000 && progress.isValid, "32k preserved")
require(progress.reserve(now: 1034) == nil && progress.terminal == .limit, "bounded window")
let cursor = progress.next
require(progress.resumeHistoryWindow(now: 1035), "window continuation")
require(progress.historyWindow == 1 && progress.next == cursor && progress.isValid, "server cursor retained")
require(progress.reserve(now: 1036) == .difference(cursor!), "resume never rewinds to zero")
require(!progress.resumeHistoryWindow(now: 1037), "running window cannot renew")
progress.terminal = .limit
require(!progress.resumeHistoryWindow(now: 1038), "no progress cannot loop")
var old = fresh();old.historyPolicyVersion = 1
require(old.reserve(now: 1000) == .state && old.acceptState(live, unread: 0, now: 1001), "legacy record")
require(old.terminal == .noCandidate, "legacy policy retained for migration")
let upgraded = JerkgramBotReplayPolicy.upgrade(old, owner: 7, peer: 1, testing: false, now: 1002)
require(upgraded.historyPolicyVersion == 2 && upgraded.original == nil && upgraded.terminal == nil, "completed short replay upgrades once")
require(JerkgramBotReplayPolicy.upgrade(old, owner: 8, peer: 1, testing: false, now: 1002) == old, "foreign account")
old.terminal = .corrupt
require(JerkgramBotReplayPolicy.upgrade(old, owner: 7, peer: 1, testing: false, now: 1002) == old, "corrupt cannot renew")
for record in [fresh(), progress, upgraded] {
    guard let entry = PreferencesEntry(record), let decoded = PreferencesEntry(data: entry.data).get(BotBridgeHistoryProgress.self) else { fatalError("Postbox codec") }
    require(decoded == record && decoded.isValid, "actual keyed Postbox roundtrip")
}
print("PASS post180 real policy and Postbox codec: zero-unread, 32k, resume cursor, no-progress, migration, isolation")
