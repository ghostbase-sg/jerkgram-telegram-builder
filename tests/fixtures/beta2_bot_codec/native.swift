import Foundation

func require(_ value: @autoclosure () -> Bool, _ message: String) {
    if !value() { fatalError(message) }
}

// Storage I/O only: bytes always pass through the actual PreferencesEntry codec.
// These minimal account objects allow the unchanged prepare/read/write helpers
// to run; this does not verify a Postbox database or account authorization.
struct PeerId: Equatable {
    let value: Int64
    func toInt64() -> Int64 { value }
}
final class AuthorizedAccountState {
    let peerId: PeerId
    let isTestingEnvironment: Bool
    init(peerId: PeerId, testing: Bool) { self.peerId = peerId; isTestingEnvironment = testing }
}
final class TelegramUser { let botInfo: Bool? = true }
let botBridgeHistoryKey: Int32 = 0x4A470002
final class Transaction {
    var bytes: Data?
    init(_ entry: PreferencesEntry? = nil) { bytes = entry?.data }
    func getState() -> Any? { AuthorizedAccountState(peerId: peer, testing: true) }
    func getPeer(_ id: PeerId) -> Any? { TelegramUser() }
    func getPreferencesEntry(key: Int32) -> PreferencesEntry? {
        return bytes.map { PreferencesEntry(data: $0) }
    }
    func updatePreferencesEntry(key: Int32, _ f: (PreferencesEntry?) -> PreferencesEntry?) {
        bytes = f(getPreferencesEntry(key: key))?.data
    }
}

/* REAL_STORAGE_BOUNDARY */

let owner: Int64 = 0x123456789abcdef
let peer = PeerId(value: 0x23456789abcdef0)
let generation = "retained-build178-authorization"
func initial() -> BotBridgeHistoryProgress {
    return BotBridgeHistoryProgress(owner: owner, peer: peer.value, testing: true, generation: generation)
}

@discardableResult func roundtrip(_ value: BotBridgeHistoryProgress) -> BotBridgeHistoryProgress {
    require(value.isValid, "test expected valid policy state")
    guard let entry = PreferencesEntry(value), let decoded = PreferencesEntry(data: entry.data).get(BotBridgeHistoryProgress.self) else {
        fatalError("actual PreferencesEntry roundtrip failed")
    }
    require(value == decoded, "actual Postbox roundtrip changed value")
    require(decoded.isValid, "roundtrip policy validity")
    return decoded
}

let counterKeys = ["reservedPages", "committedPages", "examined", "inserted", "insertedPeers", "insertedUsers", "insertedChats", "deleteIdsObserved", "skipped", "unsupported", "deletions", "missingReferences"]

// Same primitive field layout written by the optimized Build 178 encoder. The
// root hash is intentionally the actual production type's hash; no JSON facade.
func releaseWire(omit: String? = nil, changedKey: String? = nil, change: ((PostboxEncoder, String) -> Void)? = nil) -> PreferencesEntry {
    let encoder = PostboxEncoder()
    func field(_ key: String, _ write: () -> Void) {
        if key == omit { return }
        if key == changedKey, let change = change { change(encoder, key) } else { write() }
    }
    field("schema") { encoder.encodeInt32(1, forKey: "schema") }
    field("owner") { encoder.encodeInt64(owner, forKey: "owner") }
    field("peer") { encoder.encodeInt64(peer.value, forKey: "peer") }
    field("testing") { encoder.encodeBool(true, forKey: "testing") }
    field("generation") { encoder.encodeString(generation, forKey: "generation") }
    field("reservedState") { encoder.encodeBool(false, forKey: "reservedState") }
    for key in counterKeys { field(key) { encoder.encodeInt32(0, forKey: key) } }
    // Optional fields (including terminal) were absent in the initial release record.
    if let changedKey = changedKey, ["terminal", "started", "deadline", "lastWall", "original", "candidate", "next"].contains(changedKey), let change = change {
        change(encoder, changedKey)
    }
    let root = PostboxEncoder()
    root.encodeInnerObjectDataWithHeader(typeHash: postboxEncodableTypeHash(BotBridgeHistoryProgress.self), data: encoder.makeData(), valueType: .Object, forKey: "_")
    return PreferencesEntry(data: root.makeData())
}

func readAndPersist(_ transaction: Transaction) -> BotBridgeHistoryProgress {
    guard let value = jerkgramPrepareBotBridgeHistory(transaction: transaction, owner: owner, accountPeerId: peer, lifetime: BotBridgeLifetime()) else {
        fatalError("production prepare unexpectedly refused fixture account")
    }
    let read = transaction.getPreferencesEntry(key: botBridgeHistoryKey)?.get(BotBridgeHistoryProgress.self)
    require(read == value, "production read/write boundary changed valid value")
    return value
}

func rejectsAndStoresCorrupt(_ entry: PreferencesEntry) {
    let transaction = Transaction(entry)
    let fallback = readAndPersist(transaction)
    require(fallback.terminal == .corrupt && fallback.isValid, "invalid record must fail closed")
    for _ in 0..<5 {
        let relaunched = Transaction(PreferencesEntry(data: transaction.bytes!))
        require(readAndPersist(relaunched) == fallback, "corrupt fallback not relaunch stable")
    }
}

roundtrip(initial())
var progress = initial()
require(progress.reserve(now: 1000) == .state, "state reservation")
progress = roundtrip(progress)
require(progress.acceptState(BotBridgeCursor(pts: 200, qts: 8, date: 30, seq: 4), unread: 50, now: 1001), "accept state")
progress = roundtrip(progress)
require(progress.reserve(now: 1002) == .difference(progress.next!), "page reservation")
progress = roundtrip(progress)
require(progress.commit(next: BotBridgeCursor(pts: 180, qts: 9, date: 31, seq: 5), final: false, examined: 9, inserted: 7, peers: 5, users: 3, skipped: 2, unsupported: 1, deletions: 4, missing: 6, now: 1003), "page commit")
progress.deleteIdsObserved = 11
progress = roundtrip(progress)
let reasons: [BotBridgeHistoryReason] = [.completed, .noCandidate, .tooLong, .limit, .deadline, .clockChanged, .corrupt, .nonadvancing, .rpcError, .timeout, .cancelled, .replaced, .loggedOut, .softReset, .interruptedState]
for reason in reasons {
    var terminal = progress
    terminal.terminal = reason
    terminal = roundtrip(terminal)
    require(terminal.reserve(now: 1004) == nil, "terminal must stop scheduling")
    var freshTerminal = initial()
    freshTerminal.terminal = reason
    roundtrip(freshTerminal)
}
var noCandidate = initial()
require(noCandidate.reserve(now: 2000) == .state, "no candidate reserve")
require(noCandidate.acceptState(BotBridgeCursor(pts: 1, qts: 0, date: 0, seq: 0), unread: 0, now: 2001), "no candidate accept")
require(roundtrip(noCandidate).terminal == .noCandidate, "no candidate roundtrip")

let legacy = releaseWire()
require(legacy.get(BotBridgeHistoryProgress.self) == initial(), "legacy release wire identity")
if CommandLine.arguments.count == 2 {
    let actualOldBytes = try Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1]))
    let oldEntry = PreferencesEntry(data: actualOldBytes)
    require(oldEntry.get(BotBridgeHistoryProgress.self) == initial(), "actual old optimized release record identity")
    let oldTransaction = Transaction(oldEntry)
    require(readAndPersist(oldTransaction) == initial(), "actual old generation was replaced during prepare")
}
let retained = Transaction(legacy)
for _ in 0..<6 {
    let value = readAndPersist(retained)
    require(value.generation == generation && value.owner == owner && value.peer == peer.value, "legacy authorization identity changed")
}

// Missing required fields; wrong primitive width; unknown enum; negative,
// Int32.max/out-of-policy, and Int64 values beyond Int32 are all decoded safely.
for key in ["schema", "owner", "peer", "testing", "generation", "reservedState"] + counterKeys {
    rejectsAndStoresCorrupt(releaseWire(omit: key))
}
rejectsAndStoresCorrupt(releaseWire(changedKey: "schema") { $0.encodeInt32(2, forKey: $1) })
rejectsAndStoresCorrupt(releaseWire(changedKey: "schema") { $0.encodeInt32(-1, forKey: $1) })
rejectsAndStoresCorrupt(releaseWire(changedKey: "schema") { $0.encodeInt64(Int64.max, forKey: $1) })
rejectsAndStoresCorrupt(releaseWire(changedKey: "terminal") { $0.encodeString("future-unknown", forKey: $1) })
rejectsAndStoresCorrupt(releaseWire(changedKey: "terminal") { $0.encodeInt32(1, forKey: $1) })
rejectsAndStoresCorrupt(releaseWire(changedKey: "owner") { $0.encodeInt64(owner + 1, forKey: $1) })
rejectsAndStoresCorrupt(releaseWire(changedKey: "peer") { $0.encodeInt64(peer.value + 1, forKey: $1) })
rejectsAndStoresCorrupt(releaseWire(changedKey: "testing") { $0.encodeBool(false, forKey: $1) })
rejectsAndStoresCorrupt(releaseWire(changedKey: "generation") { $0.encodeString("", forKey: $1) })
rejectsAndStoresCorrupt(releaseWire(changedKey: "generation") { $0.encodeString(String(repeating: "x", count: 65), forKey: $1) })
rejectsAndStoresCorrupt(releaseWire(changedKey: "started") { $0.encodeDouble(.nan, forKey: $1) })
rejectsAndStoresCorrupt(releaseWire(changedKey: "deadline") { $0.encodeDouble(.infinity, forKey: $1) })
rejectsAndStoresCorrupt(releaseWire(changedKey: "original") { $0.encodeString("wrong-container", forKey: $1) })
rejectsAndStoresCorrupt(releaseWire(changedKey: "original") { $0.encode(BotBridgeCursor(pts: -1, qts: 0, date: 0, seq: 0), forKey: $1) })
for key in counterKeys {
    rejectsAndStoresCorrupt(releaseWire(changedKey: key) { $0.encodeInt32(-1, forKey: $1) })
    rejectsAndStoresCorrupt(releaseWire(changedKey: key) { $0.encodeInt32(Int32.max, forKey: $1) })
    rejectsAndStoresCorrupt(releaseWire(changedKey: key) { $0.encodeInt64(Int64(Int32.max) + 1, forKey: $1) })
}
rejectsAndStoresCorrupt(PreferencesEntry(data: Data()))

// Invalid in-memory states must be repaired BEFORE Postbox's try! encoding.
for invalidCounter in [-1, Int(Int32.max) + 1, Int.max] {
    var invalid = initial()
    invalid.insertedUsers = invalidCounter
    do {
        _ = try AdaptedPostboxEncoder().encode(invalid)
        fatalError("invalid direct encode unexpectedly succeeded")
    } catch { /* Thrown validation error, outside Postbox's try! boundary. */ }
    let transaction = Transaction()
    botBridgeWriteProgress(invalid, transaction: transaction)
    let safe = transaction.getPreferencesEntry(key: botBridgeHistoryKey)!.get(BotBridgeHistoryProgress.self)!
    require(safe.isValid && safe.terminal == .corrupt && safe.generation == generation, "invalid write fallback")
}
var invalidTime = initial()
invalidTime.started = .infinity
roundtrip(invalidTime.validatedForStorage)

// Relaunch after initial, state reservation, page progress, then terminal.
let lifecycle = Transaction(legacy)
var live = readAndPersist(lifecycle)
require(live.reserve(now: 3000) == .state, "relaunch reserve")
botBridgeWriteProgress(live, transaction: lifecycle)
live = readAndPersist(lifecycle)
require(live.acceptState(BotBridgeCursor(pts: 30, qts: 1, date: 3, seq: 1), unread: 10, now: 3001), "relaunch state")
botBridgeWriteProgress(live, transaction: lifecycle)
live = readAndPersist(lifecycle)
require(live.reserve(now: 3002) != nil, "relaunch page")
botBridgeWriteProgress(live, transaction: lifecycle)
live = readAndPersist(lifecycle)
live.terminal = .timeout
botBridgeWriteProgress(live, transaction: lifecycle)
for _ in 0..<6 {
    live = readAndPersist(lifecycle)
    require(live.terminal == .timeout && live.reserve(now: 3003) == nil, "terminal relaunch scheduled work")
}
print("PASS actual pinned PreferencesEntry/Postbox codec")
