import Foundation
import SQLite3

// Boundary adapter only. This executes real durable SQLite transactions using
// production ValueBox's exclusive range and binary-byte key semantics. It is
// not production SqliteValueBox/sqlcipher, queue lifecycle, WAL or encryption.
final class SQLiteFixtureValueBox: ValueBox {
    private var db: OpaquePointer?
    private var opened = Set<Int32>()
    var gets = 0, ranges = 0, rows = 0, sets = 0, removes = 0, largestRange = 0
    init(path: String) {
        precondition(sqlite3_open(path, &db) == SQLITE_OK)
        execute("PRAGMA journal_mode=WAL")
    }
    deinit { sqlite3_close(db) }
    private func execute(_ sql: String) { precondition(sqlite3_exec(db, sql, nil, nil, nil) == SQLITE_OK, String(cString: sqlite3_errmsg(db))) }
    private func ensure(_ table: ValueBoxTable) {
        precondition(table.keyType == .binary)
        if opened.insert(table.id).inserted { execute("CREATE TABLE IF NOT EXISTS t\(table.id) (key BLOB PRIMARY KEY, value BLOB NOT NULL) WITHOUT ROWID") }
    }
    private func prepare(_ sql: String) -> OpaquePointer {
        var statement: OpaquePointer?
        precondition(sqlite3_prepare_v2(db, sql, -1, &statement, nil) == SQLITE_OK, String(cString: sqlite3_errmsg(db)))
        return statement!
    }
    private func bind(_ statement: OpaquePointer, _ index: Int32, _ key: ValueBoxKey) {
        precondition(sqlite3_bind_blob(statement, index, key.memory, Int32(key.length), unsafeBitCast(-1, to: sqlite3_destructor_type.self)) == SQLITE_OK)
    }
    private func data(_ statement: OpaquePointer, _ column: Int32) -> Data {
        let length = Int(sqlite3_column_bytes(statement, column))
        return length == 0 ? Data() : Data(bytes: sqlite3_column_blob(statement, column)!, count: length)
    }
    func rangePlan() -> String {
        let s = prepare("EXPLAIN QUERY PLAN SELECT key,value FROM t1246167041 WHERE key > ? AND key < ? ORDER BY key ASC LIMIT 45")
        defer { sqlite3_finalize(s) }
        precondition(sqlite3_step(s) == SQLITE_ROW)
        return String(cString: sqlite3_column_text(s, 3))
    }
    func begin() { execute("BEGIN IMMEDIATE") }
    func commit() { execute("COMMIT") }
    func checkpoint() { execute("PRAGMA wal_checkpoint(FULL)") }
    func beginStats() {}
    func endStats() {}
    func get(_ table: ValueBoxTable, key: ValueBoxKey) -> ReadBuffer? {
        gets += 1; ensure(table)
        let s = prepare("SELECT value FROM t\(table.id) WHERE key = ?")
        defer { sqlite3_finalize(s) }; bind(s, 1, key)
        let result = sqlite3_step(s)
        if result == SQLITE_DONE { return nil }
        precondition(result == SQLITE_ROW)
        return ReadBuffer(data: data(s, 0))
    }
    func exists(_ table: ValueBoxTable, key: ValueBoxKey) -> Bool { get(table, key: key) != nil }
    func set(_ table: ValueBoxTable, key: ValueBoxKey, value: MemoryBuffer) {
        sets += 1; ensure(table)
        let s = prepare("INSERT OR REPLACE INTO t\(table.id) (key,value) VALUES (?,?)")
        defer { sqlite3_finalize(s) }; bind(s, 1, key)
        precondition(sqlite3_bind_blob(s, 2, value.memory, Int32(value.length), unsafeBitCast(-1, to: sqlite3_destructor_type.self)) == SQLITE_OK)
        precondition(sqlite3_step(s) == SQLITE_DONE)
    }
    func remove(_ table: ValueBoxTable, key: ValueBoxKey, secure: Bool) {
        removes += 1; ensure(table)
        let s = prepare("DELETE FROM t\(table.id) WHERE key = ?")
        defer { sqlite3_finalize(s) }; bind(s, 1, key); precondition(sqlite3_step(s) == SQLITE_DONE)
    }
    func range(_ table: ValueBoxTable, start: ValueBoxKey, end: ValueBoxKey, values: (ValueBoxKey, ReadBuffer) -> Bool, limit: Int) {
        ranges += 1; largestRange = max(largestRange, limit); ensure(table); precondition(limit > 0)
        let ascending = start < end
        let s = prepare("SELECT key,value FROM t\(table.id) WHERE key > ? AND key < ? ORDER BY key \(ascending ? "ASC" : "DESC") LIMIT ?")
        defer { sqlite3_finalize(s) }
        bind(s, 1, ascending ? start : end); bind(s, 2, ascending ? end : start)
        precondition(sqlite3_bind_int64(s, 3, Int64(limit)) == SQLITE_OK)
        while true {
            let result = sqlite3_step(s)
            if result == SQLITE_DONE { break }
            precondition(result == SQLITE_ROW); rows += 1
            let bytes = data(s, 0), key = ValueBoxKey(length: Int(sqlite3_column_bytes(s, 0)))
            key.setData(0, value: bytes)
            if !values(key, ReadBuffer(data: data(s, 1))) { break }
        }
    }
    func range(_ table: ValueBoxTable, start: ValueBoxKey, end: ValueBoxKey, keys: (ValueBoxKey) -> Bool, limit: Int) {
        range(table, start: start, end: end, values: { k, _ in keys(k) }, limit: limit)
    }
    // The production store never invokes these protocol operations. Trap rather
    // than silently fake their semantics or hide a new all-table scan.
    func filteredRange(_ table: ValueBoxTable, start: ValueBoxKey, end: ValueBoxKey, values: (ValueBoxKey, ReadBuffer) -> ValueBoxFilterResult, limit: Int) { fatalError("unsupported filteredRange") }
    func filteredRange(_ table: ValueBoxTable, start: ValueBoxKey, end: ValueBoxKey, keys: (ValueBoxKey) -> ValueBoxFilterResult, limit: Int) { fatalError("unsupported filteredRange") }
    func scan(_ table: ValueBoxTable, values: (ValueBoxKey, ReadBuffer) -> Bool) { fatalError("all-table scan forbidden") }
    func scan(_ table: ValueBoxTable, keys: (ValueBoxKey) -> Bool) { fatalError("all-table scan forbidden") }
    func scanInt64(_ table: ValueBoxTable, values: (Int64, ReadBuffer) -> Bool) { fatalError("unsupported scan") }
    func scanInt64(_ table: ValueBoxTable, keys: (Int64) -> Bool) { fatalError("unsupported scan") }
    func read(_ table: ValueBoxTable, key: ValueBoxKey, _ process: (Int, (UnsafeMutableRawPointer, Int, Int) -> Void) -> Void) { fatalError("unsupported read") }
    func readWrite(_ table: ValueBoxTable, key: ValueBoxKey, _ process: (Int, (UnsafeMutableRawPointer, Int, Int) -> Void, (UnsafeRawPointer, Int, Int) -> Void) -> Void) { fatalError("unsupported readWrite") }
    func copy(fromTable: ValueBoxTable, fromKey: ValueBoxKey, toTable: ValueBoxTable, toKey: ValueBoxKey) { fatalError("unsupported copy") }
    func removeRange(_ table: ValueBoxTable, start: ValueBoxKey, end: ValueBoxKey) { fatalError("unsupported removeRange") }
    func fullTextSet(_ table: ValueBoxFullTextTable, collectionId: String, itemId: String, contents: String, tags: String) { fatalError("unsupported fulltext") }
    func fullTextMatch(_ table: ValueBoxFullTextTable, collectionId: String?, query: String, tags: String?, values: (String, String) -> Bool) { fatalError("unsupported fulltext") }
    func fullTextRemove(_ table: ValueBoxFullTextTable, itemId: String, secure: Bool) { fatalError("unsupported fulltext") }
    func removeAllFromTable(_ table: ValueBoxTable) { fatalError("unsupported removeAll") }
    func removeTable(_ table: ValueBoxTable) { fatalError("unsupported removeTable") }
    func renameTable(_ table: ValueBoxTable, to toTable: ValueBoxTable) { fatalError("unsupported rename") }
    func drop() { fatalError("unsupported drop") }
    func count(_ table: ValueBoxTable, start: ValueBoxKey, end: ValueBoxKey) -> Int { fatalError("unsupported count") }
    func count(_ table: ValueBoxTable) -> Int { fatalError("unsupported count") }
    func exportEncrypted(to exportBasePath: String, encryptionParameters: ValueBoxEncryptionParameters) { fatalError("unsupported encryption") }
}
