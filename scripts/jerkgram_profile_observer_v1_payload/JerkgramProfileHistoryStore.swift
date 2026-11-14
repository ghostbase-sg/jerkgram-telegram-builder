import Foundation
import sqlcipher

// A missing dictionary key means unknown. A present value with nil means
// observed and confirmed absent. Never reinterpret legacy nil as confirmed.
struct JerkgramProfileFieldValue: Codable, Equatable {
    let value: String?
}

struct JerkgramProfileObservation {
    let peerId: Int64
    let fields: [String: JerkgramProfileFieldValue]
    let observedAtMs: Int64
    let source: String
}

struct JerkgramProfileHistoryEvent {
    let sequence: Int64
    let observedAtMs: Int64
    let kind: String
    let source: String
    let payload: Data
    let changedFields: [String]
}

struct JerkgramProfileHistoryCounts {
    let snapshots: Int64
    let enrichments: Int64
    let presence: Int64
    let legacySources: Int64
}

private let jerkgramHistoryTransient = unsafeBitCast(-1, to: sqlite3_destructor_type.self)

// Caller owns a serial utility queue. This class never dispatches, retains an
// Account, changes SQLCipher global defaults, or deletes a failed database.
// No peer or history collection is cached in RAM: memory use is independent of
// the number of watched peers. All hot lookups use indexed primary keys.
final class JerkgramProfileHistoryStore {
    let databasePath: String
    private let directory: String
    private let accountPeerId: Int64
    private var keyData: Data
    private var db: OpaquePointer?
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    private(set) var status = "closed"
    private(set) var lastSQLiteCode: Int32 = SQLITE_OK

    init(accountPath: String, accountPeerId: Int64, keyData: Data) {
        self.directory = URL(fileURLWithPath: accountPath).appendingPathComponent("jerkgram-profile-history", isDirectory: true).path
        self.databasePath = URL(fileURLWithPath: self.directory).appendingPathComponent("history-v2.sqlite").path
        self.accountPeerId = accountPeerId
        self.keyData = keyData
        self.encoder.outputFormatting = [.sortedKeys]
    }

    deinit { self.close() }

    @discardableResult private func failure(_ operation: String, _ code: Int32? = nil) -> Bool {
        self.lastSQLiteCode = code ?? (self.db.map { sqlite3_errcode($0) } ?? SQLITE_ERROR)
        // Never log query text, profile content, paths or encryption material.
        self.status = operation
        return false
    }

    private func execute(_ sql: String) -> Bool {
        guard let db = self.db else { return false }
        let code = sqlite3_exec(db, sql, nil, nil, nil)
        return code == SQLITE_OK ? true : self.failure("sql-failed", code)
    }

    private func prepare(_ sql: String) -> OpaquePointer? {
        guard let db = self.db else { return nil }
        var statement: OpaquePointer?
        let code = sqlite3_prepare_v2(db, sql, -1, &statement, nil)
        guard code == SQLITE_OK else {
            if let statement { sqlite3_finalize(statement) }
            self.failure("prepare-failed", code)
            return nil
        }
        return statement
    }

    @discardableResult private func bind(_ value: Int64, _ index: Int32, _ statement: OpaquePointer) -> Bool {
        let code = sqlite3_bind_int64(statement, index, value)
        return code == SQLITE_OK ? true : self.failure("bind-failed", code)
    }

    @discardableResult private func bind(_ value: String, _ index: Int32, _ statement: OpaquePointer) -> Bool {
        // Explicit length preserves embedded NUL in historical text.
        let bytes = value.utf8CString
        guard bytes.count - 1 <= Int(Int32.max) else { return self.failure("value-too-large") }
        let code = bytes.withUnsafeBytes { raw in
            sqlite3_bind_text(statement, index, raw.baseAddress?.assumingMemoryBound(to: CChar.self), Int32(bytes.count - 1), jerkgramHistoryTransient)
        }
        return code == SQLITE_OK ? true : self.failure("bind-failed", code)
    }

    @discardableResult private func bind(_ value: Data, _ index: Int32, _ statement: OpaquePointer) -> Bool {
        guard value.count <= Int(Int32.max) else { return self.failure("value-too-large") }
        let code: Int32
        if value.isEmpty {
            code = sqlite3_bind_zeroblob(statement, index, 0)
        } else {
            code = value.withUnsafeBytes { sqlite3_bind_blob(statement, index, $0.baseAddress, Int32(value.count), jerkgramHistoryTransient) }
        }
        return code == SQLITE_OK ? true : self.failure("bind-failed", code)
    }

    private func text(_ statement: OpaquePointer, _ column: Int32) -> String {
        guard let bytes = sqlite3_column_text(statement, column) else { return "" }
        return String(decoding: UnsafeBufferPointer(start: bytes, count: Int(sqlite3_column_bytes(statement, column))), as: UTF8.self)
    }

    private func data(_ statement: OpaquePointer, _ column: Int32) -> Data {
        let length = Int(sqlite3_column_bytes(statement, column))
        guard length > 0, let pointer = sqlite3_column_blob(statement, column) else { return Data() }
        return Data(bytes: pointer, count: length)
    }

    private func finish(_ statement: OpaquePointer) -> Bool {
        let code = sqlite3_step(statement)
        return code == SQLITE_DONE ? true : self.failure("write-failed", code)
    }

    private func transaction(_ action: () -> Bool) -> Bool {
        guard self.execute("BEGIN IMMEDIATE") else { return false }
        if action(), self.execute("COMMIT") {
            self.status = "ready"
            self.lastSQLiteCode = SQLITE_OK
            return true
        }
        let failedStatus = self.status
        let failedCode = self.lastSQLiteCode
        _ = self.execute("ROLLBACK")
        self.status = failedStatus
        self.lastSQLiteCode = failedCode
        return false
    }

    func open() -> Bool {
        if self.db != nil { return true }
        guard self.keyData.count == 32 else { return self.failure("invalid-key-length") }
        do {
            try FileManager.default.createDirectory(atPath: self.directory, withIntermediateDirectories: true, attributes: nil)
            #if os(iOS)
            try FileManager.default.setAttributes([.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication], ofItemAtPath: self.directory)
            #endif
            var url = URL(fileURLWithPath: self.directory)
            var values = URLResourceValues()
            values.isExcludedFromBackup = true
            try url.setResourceValues(values)
        } catch { return self.failure("directory-unavailable") }
        var opened: OpaquePointer?
        let code = sqlite3_open_v2(self.databasePath, &opened, SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_FULLMUTEX, nil)
        guard code == SQLITE_OK, let opened else {
            if let opened { sqlite3_close(opened) }
            return self.failure("open-unavailable", code)
        }
        self.db = opened
        sqlite3_busy_timeout(opened, 100)
        // Raw device key, random per-file SQLCipher salt. Explicit per-connection
        // header setting is essential: Postbox changes the process-wide default.
        let hex = self.keyData.map { String(format: "%02x", $0) }.joined()
        guard self.execute("PRAGMA key=\"x'\(hex)'\""),
              self.execute("PRAGMA cipher_plaintext_header_size=0"),
              self.verifyCipher(), self.verifyReadable(),
              self.execute("PRAGMA foreign_keys=ON"),
              self.execute("PRAGMA temp_store=MEMORY"),
              self.execute("PRAGMA mmap_size=0"),
              self.execute("PRAGMA synchronous=FULL"),
              self.enableWAL(), self.createSchema(), self.protectFiles() else {
            let failedStatus = self.status
            let failedCode = self.lastSQLiteCode
            self.close()
            self.status = failedStatus
            self.lastSQLiteCode = failedCode
            return false
        }
        self.status = "ready"
        self.lastSQLiteCode = SQLITE_OK
        return true
    }

    private func verifyCipher() -> Bool {
        guard let statement = self.prepare("PRAGMA cipher_version") else { return false }
        defer { sqlite3_finalize(statement) }
        guard sqlite3_step(statement) == SQLITE_ROW, !self.text(statement, 0).isEmpty else {
            return self.failure("sqlcipher-unavailable")
        }
        return true
    }

    private func verifyReadable() -> Bool {
        guard let statement = self.prepare("SELECT count(*) FROM sqlite_master") else { return self.failure("key-or-database-unreadable") }
        defer { sqlite3_finalize(statement) }
        guard sqlite3_step(statement) == SQLITE_ROW else { return self.failure("key-or-database-unreadable") }
        return true
    }

    private func enableWAL() -> Bool {
        guard let statement = self.prepare("PRAGMA journal_mode=WAL") else { return false }
        defer { sqlite3_finalize(statement) }
        guard sqlite3_step(statement) == SQLITE_ROW, self.text(statement, 0).lowercased() == "wal" else { return self.failure("wal-unavailable") }
        return true
    }

    private func protectFiles() -> Bool {
        #if os(iOS)
        do {
            for suffix in ["", "-wal", "-shm"] {
                let path = self.databasePath + suffix
                if FileManager.default.fileExists(atPath: path) {
                    try FileManager.default.setAttributes([.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication], ofItemAtPath: path)
                }
            }
        } catch { return self.failure("file-protection-failed") }
        #endif
        return true
    }

    private func createSchema() -> Bool {
        return self.transaction {
            guard self.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"),
                  self.execute("CREATE TABLE IF NOT EXISTS watched (peer_id INTEGER PRIMARY KEY, started_at_ms INTEGER NOT NULL, state BLOB NOT NULL)"),
                  self.execute("CREATE TABLE IF NOT EXISTS events (sequence INTEGER PRIMARY KEY AUTOINCREMENT, peer_id INTEGER NOT NULL, observed_at_ms INTEGER NOT NULL, kind TEXT NOT NULL, source TEXT NOT NULL, payload BLOB NOT NULL, changed_fields BLOB NOT NULL, legacy_source_id INTEGER, legacy_ordinal INTEGER, legacy_identity TEXT UNIQUE, UNIQUE(legacy_source_id,legacy_ordinal))"),
                  self.execute("CREATE INDEX IF NOT EXISTS events_peer_sequence ON events(peer_id,sequence DESC)"),
                  self.execute("CREATE INDEX IF NOT EXISTS events_peer_kind_sequence ON events(peer_id,kind,sequence DESC)"),
                  self.execute("CREATE TABLE IF NOT EXISTS presence_events (sequence INTEGER PRIMARY KEY AUTOINCREMENT, peer_id INTEGER NOT NULL, observed_at_ms INTEGER NOT NULL, status TEXT NOT NULL, hidden INTEGER NOT NULL, until_value INTEGER, last_activity INTEGER NOT NULL, source TEXT NOT NULL, payload BLOB, legacy_source_id INTEGER, legacy_ordinal INTEGER, legacy_identity TEXT UNIQUE, UNIQUE(legacy_source_id,legacy_ordinal))"),
                  self.execute("CREATE INDEX IF NOT EXISTS presence_peer_sequence ON presence_events(peer_id,sequence DESC)"),
                  self.execute("CREATE TABLE IF NOT EXISTS presence_current (peer_id INTEGER PRIMARY KEY, status TEXT NOT NULL, hidden INTEGER NOT NULL)"),
                  self.execute("CREATE TABLE IF NOT EXISTS legacy_sources (id INTEGER PRIMARY KEY, peer_id INTEGER NOT NULL, source_key TEXT NOT NULL, fingerprint TEXT NOT NULL, payload BLOB NOT NULL, provenance TEXT NOT NULL)"),
                  self.execute("CREATE INDEX IF NOT EXISTS legacy_lookup ON legacy_sources(source_key,fingerprint)"),
                  self.execute("CREATE INDEX IF NOT EXISTS legacy_peer ON legacy_sources(peer_id,id)"),
                  self.execute("CREATE TABLE IF NOT EXISTS gaps (sequence INTEGER PRIMARY KEY AUTOINCREMENT, observed_at_ms INTEGER NOT NULL, dropped_count INTEGER NOT NULL, reason TEXT NOT NULL)"),
                  self.execute("INSERT OR IGNORE INTO metadata(key,value) VALUES('schema_version','2')") else { return false }
            guard let version = self.prepare("SELECT value FROM metadata WHERE key='schema_version'") else { return false }
            let versionCode = sqlite3_step(version)
            let supported = versionCode == SQLITE_ROW && self.text(version, 0) == "2"
            sqlite3_finalize(version)
            guard supported else { return self.failure("unsupported-schema") }
            guard let statement = self.prepare("SELECT value FROM metadata WHERE key='account_peer_id'") else { return false }
            let result = sqlite3_step(statement)
            let existing = result == SQLITE_ROW ? self.text(statement, 0) : nil
            sqlite3_finalize(statement)
            if let existing { return existing == String(self.accountPeerId) ? true : self.failure("account-mismatch") }
            guard result == SQLITE_DONE, let insert = self.prepare("INSERT INTO metadata(key,value) VALUES('account_peer_id',?)") else { return false }
            defer { sqlite3_finalize(insert) }
            return self.bind(String(self.accountPeerId), 1, insert) && self.finish(insert)
        }
    }

    func close() {
        if let db = self.db {
            // SQLite close preserves committed WAL on checkpoint failure. Never
            // remove WAL/SHM manually, including after wrong-key opens.
            sqlite3_close_v2(db)
            self.db = nil
        }
        self.status = "closed"
    }

    func isWatched(peerId: Int64) -> Bool {
        guard self.open(), let statement = self.prepare("SELECT 1 FROM watched WHERE peer_id=?") else { return false }
        defer { sqlite3_finalize(statement) }
        guard self.bind(peerId, 1, statement) else { return false }
        let code = sqlite3_step(statement)
        if code != SQLITE_ROW && code != SQLITE_DONE { self.failure("read-failed", code) }
        return code == SQLITE_ROW
    }

    func enumerateWatched(_ visit: (Int64) -> Void) {
        guard self.open(), let statement = self.prepare("SELECT peer_id FROM watched ORDER BY peer_id") else { return }
        defer { sqlite3_finalize(statement) }
        var code = sqlite3_step(statement)
        while code == SQLITE_ROW {
            visit(sqlite3_column_int64(statement, 0))
            code = sqlite3_step(statement)
        }
        if code != SQLITE_DONE { self.failure("read-failed", code) }
    }

    @discardableResult func observe(_ observation: JerkgramProfileObservation, enroll: Bool) -> Bool {
        guard self.open() else { return false }
        guard let statement = self.prepare("SELECT state FROM watched WHERE peer_id=?") else { return false }
        guard self.bind(observation.peerId, 1, statement) else { sqlite3_finalize(statement); return false }
        let code = sqlite3_step(statement)
        let oldData = code == SQLITE_ROW ? self.data(statement, 0) : nil
        sqlite3_finalize(statement)
        guard code == SQLITE_ROW || code == SQLITE_DONE else { return self.failure("read-failed", code) }
        if oldData == nil && !enroll { return true }
        let old: [String: JerkgramProfileFieldValue]
        if let oldData {
            guard let decoded = try? self.decoder.decode([String: JerkgramProfileFieldValue].self, from: oldData) else { return self.failure("state-unreadable") }
            old = decoded
        } else { old = [:] }
        var next = old
        var changed: [String] = []
        var enriched: [String] = []
        for (field, value) in observation.fields {
            if let previous = old[field] {
                if previous != value { changed.append(field) }
            } else { enriched.append(field) }
            next[field] = value
        }
        if oldData != nil && changed.isEmpty && enriched.isEmpty { return true }
        guard !next.isEmpty, let payload = try? self.encoder.encode(next) else { return self.failure("empty-or-unencodable-observation") }
        let kind = old.isEmpty || !changed.isEmpty ? "snapshot" : "enrichment"
        let keys = old.isEmpty ? ["baseline"] : (kind == "enrichment" ? enriched.sorted() : changed.sorted())
        return self.transaction {
            guard self.insertEvent(peerId: observation.peerId, observedAtMs: observation.observedAtMs, kind: kind, source: observation.source, payload: payload, changedFields: keys),
                  let update = self.prepare("INSERT INTO watched(peer_id,started_at_ms,state) VALUES(?,?,?) ON CONFLICT(peer_id) DO UPDATE SET state=excluded.state") else { return false }
            defer { sqlite3_finalize(update) }
            return self.bind(observation.peerId, 1, update) && self.bind(observation.observedAtMs, 2, update) && self.bind(payload, 3, update) && self.finish(update) && self.protectFiles()
        }
    }

    private func insertEvent(peerId: Int64, observedAtMs: Int64, kind: String, source: String, payload: Data, changedFields: [String], legacySource: Int64? = nil, ordinal: Int64? = nil, legacyIdentity: String? = nil) -> Bool {
        guard let changed = try? self.encoder.encode(changedFields), let statement = self.prepare("INSERT INTO events(peer_id,observed_at_ms,kind,source,payload,changed_fields,legacy_source_id,legacy_ordinal,legacy_identity) VALUES(?,?,?,?,?,?,?,?,?)") else { return false }
        defer { sqlite3_finalize(statement) }
        guard self.bind(peerId, 1, statement), self.bind(observedAtMs, 2, statement), self.bind(kind, 3, statement), self.bind(source, 4, statement), self.bind(payload, 5, statement), self.bind(changed, 6, statement) else { return false }
        if let legacySource { guard self.bind(legacySource, 7, statement) else { return false } }
        if let ordinal { guard self.bind(ordinal, 8, statement) else { return false } }
        if let legacyIdentity { guard self.bind(legacyIdentity, 9, statement) else { return false } }
        return self.finish(statement)
    }

    func page(peerId: Int64, beforeSequence: Int64?, limit: Int, kind: String? = nil) -> [JerkgramProfileHistoryEvent] {
        guard self.open() else { return [] }
        var sql = "SELECT sequence,observed_at_ms,kind,source,payload,changed_fields FROM events WHERE peer_id=?"
        if beforeSequence != nil { sql += " AND sequence<?" }
        if kind != nil { sql += " AND kind=?" }
        sql += " ORDER BY sequence DESC LIMIT ?"
        guard let statement = self.prepare(sql) else { return [] }
        defer { sqlite3_finalize(statement) }
        var index: Int32 = 1
        guard self.bind(peerId, index, statement) else { return [] }; index += 1
        if let beforeSequence { guard self.bind(beforeSequence, index, statement) else { return [] }; index += 1 }
        if let kind { guard self.bind(kind, index, statement) else { return [] }; index += 1 }
        guard self.bind(Int64(max(1, min(limit, 256))), index, statement) else { return [] }
        var result: [JerkgramProfileHistoryEvent] = []
        var code = sqlite3_step(statement)
        while code == SQLITE_ROW {
            guard let keys = try? self.decoder.decode([String].self, from: self.data(statement, 5)) else { self.failure("event-unreadable"); return [] }
            result.append(JerkgramProfileHistoryEvent(sequence: sqlite3_column_int64(statement, 0), observedAtMs: sqlite3_column_int64(statement, 1), kind: self.text(statement, 2), source: self.text(statement, 3), payload: self.data(statement, 4), changedFields: keys))
            code = sqlite3_step(statement)
        }
        guard code == SQLITE_DONE else { self.failure("read-failed", code); return [] }
        return result
    }

    func counts(peerId: Int64) -> JerkgramProfileHistoryCounts? {
        guard self.open(), let statement = self.prepare("SELECT (SELECT count(*) FROM events WHERE peer_id=? AND kind='snapshot'),(SELECT count(*) FROM events WHERE peer_id=? AND kind='enrichment'),(SELECT count(*) FROM presence_events WHERE peer_id=?),(SELECT count(*) FROM legacy_sources WHERE peer_id=?)") else { return nil }
        defer { sqlite3_finalize(statement) }
        for index in 1...4 { guard self.bind(peerId, Int32(index), statement) else { return nil } }
        guard sqlite3_step(statement) == SQLITE_ROW else { self.failure("read-failed"); return nil }
        return JerkgramProfileHistoryCounts(snapshots: sqlite3_column_int64(statement, 0), enrichments: sqlite3_column_int64(statement, 1), presence: sqlite3_column_int64(statement, 2), legacySources: sqlite3_column_int64(statement, 3))
    }

    @discardableResult func observePresence(peerId: Int64, status: String, isHidden: Bool, until: Int32?, lastActivity: Int32, observedAtMs: Int64) -> Bool {
        guard self.open(), let previous = self.prepare("SELECT status,hidden FROM presence_current WHERE peer_id=?") else { return false }
        guard self.bind(peerId, 1, previous) else { sqlite3_finalize(previous); return false }
        let code = sqlite3_step(previous)
        let same = code == SQLITE_ROW && self.text(previous, 0) == status && (sqlite3_column_int(previous, 1) != 0) == isHidden
        sqlite3_finalize(previous)
        guard code == SQLITE_ROW || code == SQLITE_DONE else { return self.failure("read-failed", code) }
        if same { return true }
        return self.transaction {
            guard let statement = self.prepare("INSERT INTO presence_events(peer_id,observed_at_ms,status,hidden,until_value,last_activity,source) VALUES(?,?,?,?,?,?,'observed')") else { return false }
            defer { sqlite3_finalize(statement) }
            guard self.bind(peerId, 1, statement), self.bind(observedAtMs, 2, statement), self.bind(status, 3, statement), self.bind(isHidden ? 1 : 0, 4, statement), self.bind(Int64(lastActivity), 6, statement) else { return false }
            if let until { guard self.bind(Int64(until), 5, statement) else { return false } }
            guard self.finish(statement), let update = self.prepare("INSERT INTO presence_current(peer_id,status,hidden) VALUES(?,?,?) ON CONFLICT(peer_id) DO UPDATE SET status=excluded.status,hidden=excluded.hidden") else { return false }
            defer { sqlite3_finalize(update) }
            return self.bind(peerId, 1, update) && self.bind(status, 2, update) && self.bind(isHidden ? 1 : 0, 3, update) && self.finish(update) && self.protectFiles()
        }
    }

    // The source archive is authoritative for legacy data. Normalized entries
    // retain provenance; they never enroll a peer or overwrite current truth.
    @discardableResult func migrateLegacy(defaults: UserDefaults, peerId: Int64? = nil) -> Bool {
        guard self.open() else { return false }
        let sources: [String: Any]
        if let peerId {
            // Profile openings inspect a fixed set of source keys. They never
            // snapshot/copy unrelated settings or another peer's large archive.
            var targeted: [String: Any] = [:]
            let scoped = String(self.accountPeerId) + "." + String(peerId)
            let families = ["ProfileHistory.V11G.", "ProfileIntel3.PersonalChannel.", "PresenceHistory1.", "GiftHistory1.", "PresenceGlobal1.KnownUser."]
            for prefix in ["GhostBase.", "jerkgram.", "Jerkgram."] {
                for family in families {
                    let key = prefix + family + scoped
                    if let value = defaults.object(forKey: key) { targeted[key] = value }
                }
                for suffix in ["Snapshot", "History", "Started", "SessionStart", "Updated"] {
                    let key = prefix + "ProfileIntel2." + scoped + "." + suffix
                    if let value = defaults.object(forKey: key) { targeted[key] = value }
                }
            }
            sources = targeted
        } else {
            sources = defaults.dictionaryRepresentation()
        }
        for key in sources.keys.sorted() {
            guard let owner = self.legacyOwner(key), peerId == nil || owner.peerId == peerId, let value = sources[key] else { continue }
            guard let payload = try? PropertyListSerialization.data(fromPropertyList: ["value": value], format: .binary, options: 0) else { return self.failure("legacy-value-unencodable") }
            let fingerprint = self.fingerprint(payload)
            guard let lookup = self.prepare("SELECT payload FROM legacy_sources WHERE source_key=? AND fingerprint=?") else { return false }
            guard self.bind(key, 1, lookup), self.bind(fingerprint, 2, lookup) else { sqlite3_finalize(lookup); return false }
            var found = false
            var code = sqlite3_step(lookup)
            while code == SQLITE_ROW {
                if self.data(lookup, 0) == payload { found = true; break }
                code = sqlite3_step(lookup)
            }
            sqlite3_finalize(lookup)
            guard code == SQLITE_ROW || code == SQLITE_DONE else { return self.failure("migration-read-failed", code) }
            if found { continue }
            let normalized = self.legacyEntries(value, family: owner.family)
            let provenance: String
            if normalized != nil {
                provenance = "legacy-unverified-observation"
            } else if self.legacyHasUnknownObservationTime(value, family: owner.family) {
                provenance = "legacy-observation-time-unknown"
            } else {
                provenance = "legacy-unparsed-preserved"
            }
            guard self.transaction({
                guard let insert = self.prepare("INSERT INTO legacy_sources(peer_id,source_key,fingerprint,payload,provenance) VALUES(?,?,?,?,?)") else { return false }
                let bound = self.bind(owner.peerId, 1, insert) && self.bind(key, 2, insert) && self.bind(fingerprint, 3, insert) && self.bind(payload, 4, insert) && self.bind(provenance, 5, insert) && self.finish(insert)
                sqlite3_finalize(insert)
                guard bound, let db = self.db else { return false }
                let sourceId = sqlite3_last_insert_rowid(db)
                var occurrences: [Data: Int] = [:]
                for (ordinal, entry) in (normalized ?? []).enumerated() {
                    guard let encoded = try? JSONSerialization.data(withJSONObject: entry, options: [.sortedKeys]) else { return self.failure("legacy-entry-unencodable") }
                    let occurrence = occurrences[encoded, default: 0]
                    occurrences[encoded] = occurrence + 1
                    let identityBase = key + ":" + self.fingerprint(encoded) + ":" + String(occurrence)
                    guard let identity = self.resolveLegacyIdentity(identityBase, payload: encoded, presence: owner.family == "presence") else { return false }
                    if identity.exists { continue }
                    guard let seconds = self.legacyObservedSeconds(entry) else { return self.failure("legacy-observation-time-unknown") }
                    let timestamp = seconds.multipliedReportingOverflow(by: 1000)
                    guard !timestamp.overflow else { return self.failure("legacy-timestamp-overflow") }
                    if owner.family == "presence" {
                        guard self.insertLegacyPresence(entry, peerId: owner.peerId, observedAtMs: timestamp.partialValue, sourceId: sourceId, ordinal: Int64(ordinal), payload: encoded, identity: identity.value) else { return false }
                    } else {
                        guard self.insertEvent(peerId: owner.peerId, observedAtMs: timestamp.partialValue, kind: "legacy_" + owner.family, source: provenance + ":" + key, payload: encoded, changedFields: [], legacySource: sourceId, ordinal: Int64(ordinal), legacyIdentity: identity.value) else { return false }
                    }
                }
                return self.protectFiles()
            }) else { return false }
        }
        return true
    }


    @discardableResult func recordGap(droppedCount: Int, observedAtMs: Int64) -> Bool {
        guard droppedCount > 0, self.open() else { return false }
        return self.transaction {
            guard let statement = self.prepare("INSERT INTO gaps(observed_at_ms,dropped_count,reason) VALUES(?,?,'ingress-or-storage-unavailable')") else { return false }
            defer { sqlite3_finalize(statement) }
            return self.bind(observedAtMs, 1, statement) && self.bind(Int64(droppedCount), 2, statement) && self.finish(statement) && self.protectFiles()
        }
    }

    // Identity persists across changing UserDefaults source versions. An
    // occurrence ordinal preserves intentionally repeated identical old events.
    // Fingerprint collisions are resolved using exact event bytes.
    private func resolveLegacyIdentity(_ base: String, payload: Data, presence: Bool) -> (value: String, exists: Bool)? {
        let table = presence ? "presence_events" : "events"
        var collision = 0
        while true {
            let value = collision == 0 ? base : base + ":collision:" + String(collision)
            guard let statement = self.prepare("SELECT payload FROM " + table + " WHERE legacy_identity=?") else { return nil }
            guard self.bind(value, 1, statement) else { sqlite3_finalize(statement); return nil }
            let code = sqlite3_step(statement)
            let matches = code == SQLITE_ROW && self.data(statement, 0) == payload
            sqlite3_finalize(statement)
            if code == SQLITE_DONE { return (value, false) }
            if matches { return (value, true) }
            guard code == SQLITE_ROW else { self.failure("migration-read-failed", code); return nil }
            collision += 1
        }
    }

    private func insertLegacyPresence(_ entry: [String: Any], peerId: Int64, observedAtMs: Int64, sourceId: Int64, ordinal: Int64, payload: Data, identity: String) -> Bool {
        guard let status = entry["status"] as? String else { return self.failure("legacy-presence-status-unreadable") }
        guard let statement = self.prepare("INSERT INTO presence_events(peer_id,observed_at_ms,status,hidden,until_value,last_activity,source,payload,legacy_source_id,legacy_ordinal,legacy_identity) VALUES(?,?,?,?,?,?,'legacy-unverified',?,?,?,?)") else { return false }
        defer { sqlite3_finalize(statement) }
        let hidden = (entry["isHidden"] as? Bool) ?? false
        let lastActivity = (entry["lastActivity"] as? NSNumber)?.int64Value ?? 0
        guard self.bind(peerId, 1, statement), self.bind(observedAtMs, 2, statement), self.bind(status, 3, statement), self.bind(hidden ? 1 : 0, 4, statement), self.bind(lastActivity, 6, statement), self.bind(payload, 7, statement), self.bind(sourceId, 8, statement), self.bind(ordinal, 9, statement), self.bind(identity, 10, statement) else { return false }
        if let until = (entry["until"] as? NSNumber)?.int64Value { guard self.bind(until, 5, statement) else { return false } }
        return self.finish(statement)
    }

    // Bounded access to original, losslessly archived UserDefaults values.
    // Payload decodes as a property list dictionary containing the "value" key.
    func legacyPage(peerId: Int64, beforeId: Int64? = nil, limit: Int = 64) -> [(id: Int64, sourceKey: String, payload: Data, provenance: String)] {
        guard self.open(), let statement = self.prepare("SELECT id,source_key,payload,provenance FROM legacy_sources WHERE peer_id=? AND id<? ORDER BY id DESC LIMIT ?") else { return [] }
        defer { sqlite3_finalize(statement) }
        guard self.bind(peerId, 1, statement), self.bind(beforeId ?? Int64.max, 2, statement), self.bind(Int64(max(1, min(limit, 256))), 3, statement) else { return [] }
        var result: [(id: Int64, sourceKey: String, payload: Data, provenance: String)] = []
        var code = sqlite3_step(statement)
        while code == SQLITE_ROW {
            result.append((sqlite3_column_int64(statement, 0), self.text(statement, 1), self.data(statement, 2), self.text(statement, 3)))
            code = sqlite3_step(statement)
        }
        guard code == SQLITE_DONE else { self.failure("read-failed", code); return [] }
        return result
    }

    func presencePage(peerId: Int64, beforeSequence: Int64? = nil, limit: Int = 64) -> [(sequence: Int64, observedAtMs: Int64, status: String, isHidden: Bool, source: String)] {
        guard self.open(), let statement = self.prepare("SELECT sequence,observed_at_ms,status,hidden,source FROM presence_events WHERE peer_id=? AND sequence<? ORDER BY sequence DESC LIMIT ?") else { return [] }
        defer { sqlite3_finalize(statement) }
        guard self.bind(peerId, 1, statement), self.bind(beforeSequence ?? Int64.max, 2, statement), self.bind(Int64(max(1, min(limit, 256))), 3, statement) else { return [] }
        var result: [(sequence: Int64, observedAtMs: Int64, status: String, isHidden: Bool, source: String)] = []
        var code = sqlite3_step(statement)
        while code == SQLITE_ROW {
            result.append((sqlite3_column_int64(statement, 0), sqlite3_column_int64(statement, 1), self.text(statement, 2), sqlite3_column_int(statement, 3) != 0, self.text(statement, 4)))
            code = sqlite3_step(statement)
        }
        guard code == SQLITE_DONE else { self.failure("read-failed", code); return [] }
        return result
    }

    // Import the experimental v1 global plaintext store without changing or
    // deleting it. Only this account's rows are read. Its BIO semantics were
    // unreliable, so these rows never become known current profile fields.
    @discardableResult func migrateLegacyObserver(databasePath sourcePath: String) -> Bool {
        guard FileManager.default.fileExists(atPath: sourcePath) else { return true }
        guard sourcePath != self.databasePath, self.open() else { return false }
        var source: OpaquePointer?
        let opened = sqlite3_open_v2(sourcePath, &source, SQLITE_OPEN_READONLY | SQLITE_OPEN_FULLMUTEX, nil)
        guard opened == SQLITE_OK, let source else {
            if let source { sqlite3_close(source) }
            return self.failure("legacy-observer-unavailable", opened)
        }
        defer { sqlite3_close(source) }
        sqlite3_busy_timeout(source, 100)
        let queries = [
            ("snapshots", "SELECT sequence,peer_id,observed_at_ms,state,changed_keys FROM snapshots WHERE account_id=? ORDER BY sequence"),
            ("watched", "SELECT peer_id,peer_id,started_at_ms,state,'' FROM watched WHERE account_id=? ORDER BY peer_id")
        ]
        for (table, query) in queries {
            var prepared: OpaquePointer?
            let result = sqlite3_prepare_v2(source, query, -1, &prepared, nil)
            guard result == SQLITE_OK, let statement = prepared else {
                if let prepared { sqlite3_finalize(prepared) }
                return self.failure("legacy-observer-schema-unreadable", result)
            }
            guard self.bind(self.accountPeerId, 1, statement) else { sqlite3_finalize(statement); return false }
            var code = sqlite3_step(statement)
            while code == SQLITE_ROW {
                let ordinal = sqlite3_column_int64(statement, 0)
                let peer = sqlite3_column_int64(statement, 1)
                let timestamp = sqlite3_column_int64(statement, 2)
                let originalState = self.data(statement, 3)
                let record: [String: Any] = ["table": table, "sequence": ordinal, "peer_id": peer, "account_id": self.accountPeerId, "observed_at_ms": timestamp, "state": originalState, "changed_keys": self.text(statement, 4)]
                guard let payload = try? PropertyListSerialization.data(fromPropertyList: record, format: .binary, options: 0),
                      self.archiveObserverRow(key: "observer-v1:" + sourcePath + ":" + table + ":" + String(ordinal), peerId: peer, timestamp: timestamp, payload: payload, state: originalState, kind: "legacy_observer_" + table, enrollUnknown: table == "watched") else {
                    sqlite3_finalize(statement)
                    return false
                }
                code = sqlite3_step(statement)
            }
            sqlite3_finalize(statement)
            guard code == SQLITE_DONE else { return self.failure("legacy-observer-read-failed", code) }
        }
        return true
    }

    private func archiveObserverRow(key: String, peerId: Int64, timestamp: Int64, payload: Data, state: Data, kind: String, enrollUnknown: Bool) -> Bool {
        let fingerprint = self.fingerprint(payload)
        guard let lookup = self.prepare("SELECT payload FROM legacy_sources WHERE source_key=? AND fingerprint=?") else { return false }
        guard self.bind(key, 1, lookup), self.bind(fingerprint, 2, lookup) else { sqlite3_finalize(lookup); return false }
        var code = sqlite3_step(lookup)
        while code == SQLITE_ROW {
            if self.data(lookup, 0) == payload {
                sqlite3_finalize(lookup)
                return !enrollUnknown || self.transaction { self.restoreUnknownWatched(peerId: peerId, startedAtMs: timestamp) }
            }
            code = sqlite3_step(lookup)
        }
        sqlite3_finalize(lookup)
        guard code == SQLITE_DONE else { return self.failure("migration-read-failed", code) }
        return self.transaction {
            guard let insert = self.prepare("INSERT INTO legacy_sources(peer_id,source_key,fingerprint,payload,provenance) VALUES(?,?,?,?,'legacy-observer-v1-unverified')") else { return false }
            let success = self.bind(peerId, 1, insert) && self.bind(key, 2, insert) && self.bind(fingerprint, 3, insert) && self.bind(payload, 4, insert) && self.finish(insert)
            sqlite3_finalize(insert)
            guard success, let db = self.db else { return false }
            guard self.insertEvent(peerId: peerId, observedAtMs: timestamp, kind: kind, source: "legacy-observer-v1-unverified", payload: state, changedFields: [], legacySource: sqlite3_last_insert_rowid(db), ordinal: 0) else { return false }
            if enrollUnknown && !self.restoreUnknownWatched(peerId: peerId, startedAtMs: timestamp) { return false }
            return self.protectFiles()
        }
    }

    private func restoreUnknownWatched(peerId: Int64, startedAtMs: Int64) -> Bool {
        guard let statement = self.prepare("INSERT OR IGNORE INTO watched(peer_id,started_at_ms,state) VALUES(?,?,?)") else { return false }
        defer { sqlite3_finalize(statement) }
        // Preserve the opt-in, but no untrusted legacy values. This placeholder
        // creates no event; its first actual observation supplies a new baseline.
        return self.bind(peerId, 1, statement) && self.bind(startedAtMs, 2, statement) && self.bind(Data("{}".utf8), 3, statement) && self.finish(statement)
    }

    private func legacyOwner(_ key: String) -> (family: String, peerId: Int64)? {
        let prefixes = ["GhostBase.", "jerkgram.", "Jerkgram."]
        guard let prefix = prefixes.first(where: { key.hasPrefix($0) }) else { return nil }
        let rest = String(key.dropFirst(prefix.count))
        let families: [(String, String)] = [("ProfileHistory.V11G.", "profile"), ("ProfileIntel3.PersonalChannel.", "personal_channel"), ("ProfileIntel2.", "profile_intel"), ("PresenceHistory1.", "presence"), ("GiftHistory1.", "gift"), ("PresenceGlobal1.KnownUser.", "known_user")]
        for (familyPrefix, family) in families where rest.hasPrefix(familyPrefix) {
            let components = rest.dropFirst(familyPrefix.count).split(separator: ".", omittingEmptySubsequences: false)
            guard components.count >= 2, Int64(components[0]) == self.accountPeerId, let peer = Int64(components[1]) else { return nil }
            return (family, peer)
        }
        let idsPrefix = "PresenceGlobal1.KnownUserIds."
        if rest.hasPrefix(idsPrefix), Int64(rest.dropFirst(idsPrefix.count)) == self.accountPeerId { return ("known_user_ids", 0) }
        return nil
    }

    private func legacyEntries(_ value: Any, family: String) -> [[String: Any]]? {
        guard let bytes = value as? Data, let object = try? JSONSerialization.jsonObject(with: bytes) else { return nil }
        if family == "profile" || family == "personal_channel" {
            guard let history = object as? [String: Any], var events = history["events"] as? [[String: Any]], let current = history["current"] as? [String: Any] else { return nil }
            // Keep current if missing from events, while preserving every stored
            // event, including repetitions and uncertain BIO values.
            let currentBytes = try? JSONSerialization.data(withJSONObject: current, options: [.sortedKeys])
            let lastBytes = events.last.flatMap { try? JSONSerialization.data(withJSONObject: $0, options: [.sortedKeys]) }
            if currentBytes != lastBytes { events.append(current) }
            return self.validLegacyTimestamps(events) ? events : nil
        }
        if let entries = object as? [[String: Any]] {
            if family == "presence" && entries.contains(where: { $0["status"] as? String == nil }) { return nil }
            return self.validLegacyTimestamps(entries) ? entries : nil
        }
        if let entry = object as? [String: Any] { return self.validLegacyTimestamps([entry]) ? [entry] : nil }
        return nil
    }

    private func legacyObservedSeconds(_ entry: [String: Any]) -> Int64? {
        // Gift issuance date and known-user firstSeen are distinct semantics.
        // Only an explicitly stored observation timestamp can date an event.
        return (entry["observedAt"] as? NSNumber)?.int64Value ?? (entry["firstObservedAt"] as? NSNumber)?.int64Value
    }

    private func validLegacyTimestamps(_ entries: [[String: Any]]) -> Bool {
        return entries.allSatisfy { entry in
            guard let seconds = self.legacyObservedSeconds(entry) else { return false }
            return !seconds.multipliedReportingOverflow(by: 1000).overflow
        }
    }

    private func legacyHasUnknownObservationTime(_ value: Any, family: String) -> Bool {
        guard let bytes = value as? Data, let object = try? JSONSerialization.jsonObject(with: bytes) else { return false }
        let entries: [[String: Any]]
        if family == "profile" || family == "personal_channel" {
            guard let history = object as? [String: Any], let events = history["events"] as? [[String: Any]], let current = history["current"] as? [String: Any] else { return false }
            entries = events + [current]
        } else if let array = object as? [[String: Any]] {
            entries = array
        } else if let entry = object as? [String: Any] {
            entries = [entry]
        } else { return false }
        return entries.contains { self.legacyObservedSeconds($0) == nil }
    }

    private func fingerprint(_ bytes: Data) -> String {
        // FNV is only a lookup accelerator. Exact source bytes are compared
        // after lookup, so a collision cannot discard historical data.
        var hash: UInt64 = 14_695_981_039_346_656_037
        for byte in bytes { hash = (hash ^ UInt64(byte)) &* 1_099_511_628_211 }
        return "fnv1a64:" + String(hash, radix: 16)
    }
}
