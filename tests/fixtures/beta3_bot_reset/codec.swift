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
    var authorized = true
    var bot = true
    func getState() -> Any? { authorized ? AuthorizedAccountState(peerId: peer, testing: true) : nil }
    func getPeer(_ id: PeerId) -> Any? { bot ? TelegramUser() : nil }
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

func retained() -> BotBridgeHistoryProgress {
    var p = initial()
    require(p.reserve(now: 1000) == .state, "old initial reservation")
    p.terminal = .softReset
    return p
}
// Build179 record with the real keyed Postbox primitives and no recovery field.
func oldWire(version: Int32? = nil) -> PreferencesEntry {
    let e = PostboxEncoder()
    e.encodeInt32(1, forKey: "schema")
    e.encodeInt64(owner, forKey: "owner"); e.encodeInt64(peer.value, forKey: "peer")
    e.encodeBool(true, forKey: "testing"); e.encodeString(generation, forKey: "generation")
    e.encodeDouble(1000, forKey: "started"); e.encodeDouble(1120, forKey: "deadline"); e.encodeDouble(1000, forKey: "lastWall")
    e.encodeBool(true, forKey: "reservedState"); e.encodeString("softReset", forKey: "terminal")
    e.encodeInt32(0, forKey: "reservedPages")
    for key in ["committedPages", "examined", "inserted", "insertedPeers", "insertedUsers", "insertedChats", "deleteIdsObserved", "skipped", "unsupported", "deletions", "missingReferences"] { e.encodeInt32(0, forKey: key) }
    if let version = version { e.encodeInt32(version, forKey: "softResetRecoveryVersion") }
    let root = PostboxEncoder()
    root.encodeInnerObjectDataWithHeader(typeHash: postboxEncodableTypeHash(BotBridgeHistoryProgress.self), data: e.makeData(), valueType: .Object, forKey: "_")
    return PreferencesEntry(data: root.makeData())
}
func prepare(_ t: Transaction, owner id: Int64 = owner, lifetime: BotBridgeLifetime = BotBridgeLifetime()) -> BotBridgeHistoryProgress? {
    jerkgramPrepareBotBridgeHistory(transaction: t, owner: id, accountPeerId: peer, lifetime: lifetime)
}
let old = oldWire()
require(old.get(BotBridgeHistoryProgress.self) == retained(), "absent keyed Int32 defaults to zero")
let t = Transaction(old)
var recovered = prepare(t)!
require(recovered.generation != generation && recovered.softResetRecoveryVersion == 1, "one fresh generation")
require(recovered.terminal == nil && !recovered.reservedState && recovered.started == nil, "fresh bounded budget")
require(t.getPreferencesEntry(key: botBridgeHistoryKey)!.get(BotBridgeHistoryProgress.self) == recovered, "marker persisted before return")
require(prepare(t) == recovered, "relaunch cannot grant again")
require(recovered.reserve(now: 9000) == .state && recovered.deadline == 9120, "one fresh 120 second window")
require(recovered.acceptState(BotBridgeCursor(pts: 100, qts: 1, date: 1, seq: 1), unread: 50, now: 9001), "accept state")
for n in 0..<32 {
    require(recovered.reserve(now: 9002 + Double(n)) != nil, "bounded recovery difference")
    require(recovered.commit(next: BotBridgeCursor(pts: 51 + Int32(n), qts: 1, date: 1, seq: 1), final: false, examined: 0, inserted: 0, peers: 0, skipped: 0, unsupported: 0, deletions: 0, missing: 0, now: 9002 + Double(n)), "bounded recovery commit")
}
require(recovered.reserve(now: 9040) == nil && recovered.terminal == .limit, "old 1 plus new 33 = maximum 34 requests")
for reason in [BotBridgeHistoryReason.softReset, .timeout, .completed, .deadline, .corrupt] {
    var p = retained(); p.softResetRecoveryVersion = 1; p.terminal = reason
    let tx = Transaction(PreferencesEntry(p))
    for _ in 0..<5 { require(prepare(tx) == p, "consumed marker persists through terminal and relaunch") }
}
var cases: [BotBridgeHistoryProgress] = []
for reason in [BotBridgeHistoryReason.completed, .timeout, .cancelled, .loggedOut, .interruptedState, .rpcError, .noCandidate] { var p = retained(); p.terminal = reason; cases.append(p) }
var p = initial(); p.terminal = .softReset; cases.append(p)
p = retained(); p.terminal = nil; cases.append(p)
p = retained(); p.unsupported = 1; cases.append(p)
p = retained(); p.deleteIdsObserved = 1; cases.append(p)
p = retained(); p.deletions = 1; cases.append(p)
p = retained(); p.missingReferences = 1; cases.append(p)
p = retained(); p.original = BotBridgeCursor(pts: 100, qts: 1, date: 1, seq: 1); p.candidate = BotBridgeCursor(pts: 50, qts: 1, date: 1, seq: 1); p.next = p.candidate; p.reservedPages = 1; p.committedPages = 1; cases.append(p)
for value in cases { require(value.isValid, "negative fixture must be valid"); require(prepare(Transaction(PreferencesEntry(value))) == value, "other retained shapes unchanged") }
require(botBridgeRecoverInitialSoftReset(retained(), owner: owner + 1, accountPeerId: peer.value, testing: true) == retained(), "foreign owner denied")
require(botBridgeRecoverInitialSoftReset(retained(), owner: owner, accountPeerId: peer.value + 1, testing: true) == retained(), "foreign peer denied")
require(botBridgeRecoverInitialSoftReset(retained(), owner: owner, accountPeerId: peer.value, testing: false) == retained(), "foreign environment denied")
for version in [Int32(-1), Int32(2), Int32.max] {
    let tx = Transaction(oldWire(version: version))
    require(tx.getPreferencesEntry(key: botBridgeHistoryKey)!.get(BotBridgeHistoryProgress.self) == nil, "unknown version fails decode")
    let corrupt = prepare(tx)!
    require(corrupt.terminal == .corrupt, "unknown version must never recover")
    require(prepare(tx) == corrupt, "unknown version stays fail closed")
}
p = retained(); p.softResetRecoveryVersion = 1; p.insertedUsers = -1
require(p.validatedForStorage.softResetRecoveryVersion == 1 && p.validatedForStorage.terminal == .corrupt, "invalid fallback preserves consumed grant")
let unauthorized = Transaction(old); unauthorized.authorized = false
require(prepare(unauthorized) == nil && unauthorized.bytes == old.data, "authorization checked before migration")
let human = Transaction(old); human.bot = false
require(prepare(human) == nil && human.bytes == old.data, "ordinary user checked before migration")
let dead = BotBridgeLifetime(); dead.cancel()
let stopped = Transaction(old)
require(prepare(stopped, lifetime: dead) == nil && stopped.bytes == old.data, "cancellation before prepare cannot migrate")
let foreign = prepare(Transaction(old), owner: owner + 1)!
require(foreign.terminal == .corrupt, "foreign record fails closed")
roundtrip(recovered)
print("PASS Beta3 actual Postbox reset recovery")
