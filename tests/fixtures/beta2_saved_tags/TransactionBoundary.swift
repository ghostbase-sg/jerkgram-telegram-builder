import Foundation

// Exact production Transaction API is injected below. Only the containing
// queue/account/view lifecycle shell is replaced; actual PreferencesTable,
// PreferencesEntry codecs, table algorithms and SQLite I/O execute unchanged.
final class FixtureQueue { func isCurrent() -> Bool { true } }
final class FixturePostbox {
    let localSavedTagsTable: LocalSavedTagsTable
    let preferencesTable: PreferencesTable
    var currentPreferencesOperations: [PreferencesOperation] = []
    var operations: [PreferencesOperation] { currentPreferencesOperations }
    init(_ box: SQLiteFixtureValueBox) {
        localSavedTagsTable = LocalSavedTagsTable(valueBox: box, table: LocalSavedTagsTable.tableSpec(0x4A470001), useCaches: false)
        preferencesTable = PreferencesTable(valueBox: box, table: PreferencesTable.tableSpec(35), useCaches: false)
    }
    /* EXACT_PREFERENCES_SINK */
}
final class Transaction {
    private let queue = FixtureQueue()
    private let postbox: FixturePostbox?
    var disposed = false
    init(_ postbox: FixturePostbox) { self.postbox = postbox }
    /* EXACT_TRANSACTION_API */
}
