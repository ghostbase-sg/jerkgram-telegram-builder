import Foundation
import sqlcipher

func check(_ condition: @autoclosure () -> Bool, _ message: String) {
    if !condition() { fatalError(message) }
}
let root = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("profile-store-tests-\(UUID().uuidString)")
try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
defer { try? FileManager.default.removeItem(at: root) }
let key = Data((0..<32).map { UInt8($0) })
let store = JerkgramProfileHistoryStore(accountPath: root.path, accountPeerId: 11, keyData: key)
check(store.open(), "encrypted store opens")
func observation(_ fields: [String: JerkgramProfileFieldValue], _ at: Int64 = 1000) -> JerkgramProfileObservation {
    return JerkgramProfileObservation(peerId: 22, fields: fields, observedAtMs: at, source: "native-test")
}
check(store.observe(observation(["name": .init(value: "personal-secret-marker")]), enroll: true), "baseline")
check(store.observe(observation(["name": .init(value: "personal-secret-marker")]), enroll: true), "repeated baseline")
check(store.observe(observation(["bio": .init(value: nil)], 2000), enroll: false), "confirmed absent enrichment")
check(store.observe(observation(["bio": .init(value: "hello"), "name": .init(value: "new")], 3000), enroll: false), "atomic two field change")
check(store.counts(peerId: 22)?.snapshots == 2, "only baseline and actual change")
check(store.counts(peerId: 22)?.enrichments == 1, "first known bio retains its own timestamp")
let events = store.page(peerId: 22, beforeSequence: nil, limit: 1)
check(events.count == 1 && events[0].observedAtMs == 3000, "first keyset page")
check(store.page(peerId: 22, beforeSequence: events[0].sequence, limit: 10).count == 2, "remaining keyset page")
check(store.observePresence(peerId: 22, status: "recently", isHidden: false, until: nil, lastActivity: 1, observedAtMs: 4000), "presence first")
check(store.observePresence(peerId: 22, status: "recently", isHidden: false, until: 99, lastActivity: 10, observedAtMs: 5000), "presence duplicate")
check(store.counts(peerId: 22)?.presence == 1, "presence ignores timestamps")
final class ProfileObserverTrackingDefaults: UserDefaults {
    var fullDomainReads = 0
    override func dictionaryRepresentation() -> [String: Any] {
        self.fullDomainReads += 1
        return super.dictionaryRepresentation()
    }
}
let suite = "profile-store-test-\(UUID().uuidString)"
let defaults = UserDefaults(suiteName: suite)!
defer { defaults.removePersistentDomain(forName: suite) }
let legacyKey = "GhostBase.ProfileHistory.V11G.11.22"
let legacy = Data("{\"current\":{\"observedAt\":10,\"displayName\":\"old\"},\"events\":[{\"observedAt\":10,\"displayName\":\"old\"}]}".utf8)
defaults.set(legacy, forKey: legacyKey)
defaults.set(Data([0xff, 0xfe]), forKey: "jerkgram.GiftHistory1.11.22")
defaults.set("unparsed legacy text", forKey: "GhostBase.ProfileIntel2.11.22.History")
defaults.set(legacy, forKey: "GhostBase.ProfileHistory.V11G.111.22")
let trackedSuite = "profile-store-peer-test-\(UUID().uuidString)"
let trackedDefaults = ProfileObserverTrackingDefaults(suiteName: trackedSuite)!
defer { trackedDefaults.removePersistentDomain(forName: trackedSuite) }
var expectedPeerValues: [String: Data] = [:]
for prefix in ["GhostBase.", "jerkgram.", "Jerkgram."] {
    let suffixes = ["ProfileHistory.V11G.11.99", "ProfileIntel3.PersonalChannel.11.99", "PresenceHistory1.11.99", "GiftHistory1.11.99", "PresenceGlobal1.KnownUser.11.99"] + ["Snapshot", "History", "Started", "SessionStart", "Updated"].map { "ProfileIntel2.11.99." + $0 }
    for suffix in suffixes {
        let key = prefix + suffix
        let original = Data(("retained-original:" + key).utf8)
        expectedPeerValues[key] = original
        trackedDefaults.set(original, forKey: key)
    }
}
trackedDefaults.set(Data(repeating: 7, count: 1024 * 1024), forKey: "unrelated.large.preference")
trackedDefaults.set(Data([9]), forKey: "jerkgram.GiftHistory1.11.100")
trackedDefaults.fullDomainReads = 0
check(store.migrateLegacy(defaults: trackedDefaults, peerId: 99), "targeted peer migration")
check(trackedDefaults.fullDomainReads == 0, "peer opening never copies the full settings domain")
let peerArchives = store.legacyPage(peerId: 99, limit: 256)
check(peerArchives.count == expectedPeerValues.count, "all exact source families and prefixes included")
for entry in peerArchives {
    let plist = try PropertyListSerialization.propertyList(from: entry.payload, options: [], format: nil) as! [String: Any]
    check(plist["value"] as? Data == expectedPeerValues[entry.sourceKey], "targeted migration preserves original bytes")
}
check(store.counts(peerId: 100)?.legacySources == 0, "targeted migration excludes other peers")
let undatedGift = Data("[{\"giftDate\":1700000000,\"title\":\"undated observed gift\"}]".utf8)
let undatedKnownUser = Data("{\"peerId\":97,\"firstSeen\":1700000000,\"lastSeen\":1700000001}".utf8)
trackedDefaults.set(undatedGift, forKey: "jerkgram.GiftHistory1.11.97")
trackedDefaults.set(undatedKnownUser, forKey: "jerkgram.PresenceGlobal1.KnownUser.11.97")
check(store.migrateLegacy(defaults: trackedDefaults, peerId: 97), "undated valid JSON archive")
let undatedArchives = store.legacyPage(peerId: 97)
check(undatedArchives.count == 2, "undated JSON sources preserved")
check(undatedArchives.allSatisfy { $0.provenance == "legacy-observation-time-unknown" }, "missing observation time remains unknown")
check(store.page(peerId: 97, beforeSequence: nil, limit: 256).isEmpty, "no invented epoch-zero event from undated sources")
for entry in undatedArchives {
    let plist = try PropertyListSerialization.propertyList(from: entry.payload, options: [], format: nil) as! [String: Any]
    let expected = entry.sourceKey.contains("GiftHistory1") ? undatedGift : undatedKnownUser
    check(plist["value"] as? Data == expected, "undated source bytes retained")
}
check(store.migrateLegacy(defaults: defaults), "legacy raw and parsed migration")
let migrated = store.counts(peerId: 22)!
check(migrated.legacySources == 3, "account isolation and all matching source families")
check(store.migrateLegacy(defaults: defaults), "idempotent migration")
check(store.counts(peerId: 22)?.legacySources == migrated.legacySources, "no source duplicate")
check(defaults.data(forKey: legacyKey) == legacy, "source retained")
check(store.observe(observation(["bio": .init(value: "hello"), "name": .init(value: "new")], 6000), enroll: false), "migration cannot replace current truth")
check(store.counts(peerId: 22)?.snapshots == 2, "legacy does not change live state")
store.close()
let bytes = try Data(contentsOf: URL(fileURLWithPath: store.databasePath))
check(!bytes.starts(with: Data("SQLite format 3".utf8)), "header encrypted")
check(bytes.range(of: Data("personal-secret-marker".utf8)) == nil, "no plaintext personal data")
let wrong = JerkgramProfileHistoryStore(accountPath: root.path, accountPeerId: 11, keyData: Data(repeating: 9, count: 32))
check(!wrong.open(), "wrong key fails closed")
wrong.close()
check(store.open(), "reopen after wrong key preserves history")
check(store.counts(peerId: 22)?.snapshots == 2, "reopen durable")
// Force an actual SQLite transaction failure after archiving a source but
// before its normalized event is committed. The marker/archive must roll back.
var inspection: OpaquePointer?
check(sqlite3_open(store.databasePath, &inspection) == SQLITE_OK, "open inspection connection")
let keyHex = key.map { String(format: "%02x", $0) }.joined()
check(sqlite3_exec(inspection, "PRAGMA key=\"x'\(keyHex)'\"", nil, nil, nil) == SQLITE_OK, "inspection key")
check(sqlite3_exec(inspection, "PRAGMA cipher_plaintext_header_size=0", nil, nil, nil) == SQLITE_OK, "inspection header")
check(sqlite3_exec(inspection, "CREATE TRIGGER fail_migration BEFORE INSERT ON events WHEN NEW.kind='legacy_personal_channel' BEGIN SELECT RAISE(ABORT,'fixture'); END", nil, nil, nil) == SQLITE_OK, "install failure trigger")
let channelKey = "jerkgram.ProfileIntel3.PersonalChannel.11.22"
defaults.set(Data("{\"current\":{\"observedAt\":20},\"events\":[{\"observedAt\":20}]}".utf8), forKey: channelKey)
check(!store.migrateLegacy(defaults: defaults), "triggered migration must fail")
check(store.counts(peerId: 22)?.legacySources == migrated.legacySources, "failed source and marker rolled back")
check(sqlite3_exec(inspection, "DROP TRIGGER fail_migration", nil, nil, nil) == SQLITE_OK, "remove failure trigger")
sqlite3_close(inspection)
check(store.migrateLegacy(defaults: defaults), "retry succeeds after transaction rollback")
check(store.counts(peerId: 22)?.legacySources == migrated.legacySources + 1, "exactly one retried source")
let archive = store.legacyPage(peerId: 22)
check(archive.contains { $0.provenance == "legacy-unparsed-preserved" }, "unparseable source remains accessible")
let presenceKey = "jerkgram.PresenceHistory1.11.22"
defaults.set(Data("[{\"observedAt\":2,\"status\":\"был недавно\",\"lastActivity\":3,\"isHidden\":false},{\"observedAt\":3,\"status\":\"был недавно\",\"lastActivity\":4,\"isHidden\":false}]".utf8), forKey: presenceKey)
check(store.migrateLegacy(defaults: defaults), "legacy presence migration")
check(store.counts(peerId: 22)?.presence == 3, "all old presence preserved including repetitions")
check(store.page(peerId: 22, beforeSequence: nil, limit: 256).allSatisfy { $0.kind != "legacy_presence" }, "presence never enters profile events")
check(store.recordGap(droppedCount: 7, observedAtMs: 7000), "overflow gap is durable")
// A changing legacy source must preserve revisions without duplicating old
// normalized events, even when migration is resumed while old writers exist.
let updatedLegacy = Data("{\"current\":{\"observedAt\":11,\"displayName\":\"new old\"},\"events\":[{\"observedAt\":10,\"displayName\":\"old\"},{\"observedAt\":11,\"displayName\":\"new old\"}]}".utf8)
defaults.set(updatedLegacy, forKey: legacyKey)
check(store.migrateLegacy(defaults: defaults), "changed source migration")
check(store.page(peerId: 22, beforeSequence: nil, limit: 256, kind: "legacy_profile").count == 2, "source revisions do not duplicate old events")
let oldPath = root.appendingPathComponent("observer-v1.sqlite").path
var old: OpaquePointer?
check(sqlite3_open(oldPath, &old) == SQLITE_OK, "open legacy plaintext fixture")
let oldStateHex = Data("{\"displayName\":\"old observer\",\"aboutObserved\":true}".utf8).map { String(format: "%02x", $0) }.joined()
check(sqlite3_exec(old, "CREATE TABLE snapshots(sequence INTEGER PRIMARY KEY,account_id INTEGER,peer_id INTEGER,observed_at_ms INTEGER,state BLOB,changed_keys TEXT); CREATE TABLE watched(account_id INTEGER,peer_id INTEGER,started_at_ms INTEGER,state BLOB)", nil, nil, nil) == SQLITE_OK, "old schema")
check(sqlite3_exec(old, "INSERT INTO snapshots VALUES(1,11,22,500,X'\(oldStateHex)','baseline'); INSERT INTO snapshots VALUES(2,12,33,600,X'\(oldStateHex)','baseline'); INSERT INTO watched VALUES(11,22,500,X'\(oldStateHex)'); INSERT INTO watched VALUES(11,44,500,X'\(oldStateHex)')", nil, nil, nil) == SQLITE_OK, "old account rows")
sqlite3_close(old)
let oldCount = store.counts(peerId: 22)!.legacySources
check(store.migrateLegacyObserver(databasePath: oldPath), "plaintext observer import")
check(store.counts(peerId: 22)?.legacySources == oldCount + 2, "only this account old snapshot and watched row")
check(store.counts(peerId: 33)?.legacySources == 0, "other legacy account not imported")
for _ in 0..<20 {
    check(store.migrateLegacyObserver(databasePath: oldPath), "plaintext observer repeated import")
    check(store.counts(peerId: 22)?.legacySources == oldCount + 2, "plaintext observer idempotent regardless of plist dictionary ordering")
}
check(sqlite3_open(oldPath, &old) == SQLITE_OK, "reopen legacy fixture for a real revision")
let revisedStateHex = Data("{\"displayName\":\"changed observer\",\"aboutObserved\":true}".utf8).map { String(format: "%02x", $0) }.joined()
check(sqlite3_exec(old, "UPDATE snapshots SET state=X'\(revisedStateHex)' WHERE account_id=11 AND sequence=1", nil, nil, nil) == SQLITE_OK, "legacy source genuinely changes")
sqlite3_close(old)
check(store.migrateLegacyObserver(databasePath: oldPath), "changed legacy row remains a new revision")
check(store.counts(peerId: 22)?.legacySources == oldCount + 3, "content changes are preserved instead of deduplicated")
check(store.migrateLegacyObserver(databasePath: oldPath), "revised row repeated import")
check(store.counts(peerId: 22)?.legacySources == oldCount + 3, "revised row is also idempotent")
check(FileManager.default.fileExists(atPath: oldPath), "plaintext original retained")
check(store.counts(peerId: 22)?.snapshots == 2, "old observer cannot overwrite known current truth")
check(store.isWatched(peerId: 44), "old opt-in watch membership restored")
check(store.counts(peerId: 44)?.snapshots == 0, "legacy watch import invents no baseline")
check(store.observe(JerkgramProfileObservation(peerId: 44, fields: ["firstName": .init(value: "observed now")], observedAtMs: 9000, source: "newly-observed"), enroll: false), "restored watch receives new observations")
check(store.counts(peerId: 44)?.snapshots == 1, "first actual value supplies baseline")
check(store.page(peerId: 44, beforeSequence: nil, limit: 1)[0].observedAtMs == 9000, "baseline time never backfilled")
let mismatched = JerkgramProfileHistoryStore(accountPath: root.path, accountPeerId: 999, keyData: key)
check(!mismatched.open(), "same directory cannot serve another account")
mismatched.close()
// Histories have no event cap; pagination stays bounded.
for number in 0..<1100 {
    check(store.observe(observation(["bio": .init(value: String(number))], 8000 + Int64(number)), enroll: false), "long history append")
}
check(store.counts(peerId: 22)?.snapshots == 1102, "history exceeds former caps losslessly")
check(store.page(peerId: 22, beforeSequence: nil, limit: Int.max).count == 256, "read memory bounded by page size")
let isolated = JerkgramProfileHistoryStore(accountPath: root.appendingPathComponent("other-account").path, accountPeerId: 12, keyData: key)
check(isolated.open() && !isolated.isWatched(peerId: 22), "account directory isolated")
isolated.close()
print("Profile observer native SQLCipher storage tests passed")
