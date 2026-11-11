import Foundation

func require(_ value: Bool, _ message: String) {
    if !value { fatalError(message) }
}
func rejects<T>(_ expected: LocalSavedTagsError, _ f: () throws -> T) {
    do { _ = try f(); fatalError("accepted \(expected)") }
    catch { require(error as? LocalSavedTagsError == expected, "wrong rejection \(error)") }
}
let root = URL(fileURLWithPath: CommandLine.arguments[1])
let peer = PeerId(namespace: ._internalFromInt32Value(0), id: ._internalFromInt64Value(123))
let foreign = PeerId(namespace: ._internalFromInt32Value(0), id: ._internalFromInt64Value(456))
func message(_ id: Int32, thread: Int64? = nil) -> LocalSavedTagMessage {
    LocalSavedTagMessage(id: MessageId(peerId: peer, namespace: 0, id: id), timestamp: id, threadId: thread)
}
func open(_ name: String) -> (SQLiteFixtureValueBox, LocalSavedTagsTable) {
    let box = SQLiteFixtureValueBox(path: root.appendingPathComponent(name).path)
    return (box, LocalSavedTagsTable(valueBox: box, table: LocalSavedTagsTable.tableSpec(0x4A470001), useCaches: false))
}
if CommandLine.arguments.count == 3 && CommandLine.arguments[2] == "--reopen-process" {
    let (reopenBox, reopenStore) = open("transaction.sqlite")
    let catalogue = try reopenStore.catalogue(selfPeerId: peer)
    require(catalogue.revision == 2 && catalogue.totalMembershipCount == 1, "fresh process did not recover committed counters")
    require(catalogue.tags.count == 1 && catalogue.tags[0].name == "Notify", "fresh process did not recover catalogue")
    require(try reopenStore.tags(selfPeerId: peer, messageId: message(1).id) == [catalogue.tags[0].id], "fresh process lost full Saved identity")
    let prefs = PreferencesTable(valueBox: reopenBox, table: PreferencesTable.tableSpec(35), useCaches: false)
    require(prefs.get(key: localSavedTagsRevisionKey())?.get(LocalSavedTagsRevision.self)?.revision == 2, "fresh process revision mismatch")
    print("PASS fresh-process SQLite reopen")
    exit(0)
}
let (box, store) = open("a.sqlite")
box.begin()
require(box.gets == 0 && box.ranges == 0, "constructor enumerated storage")
let first = try store.create(selfPeerId: peer, name: "  Cafe\u{301}  ")
let second = try store.create(selfPeerId: peer, name: "Work")
require(first.name == "Café", "canonical normalization")
rejects(.duplicateName) { try store.create(selfPeerId: peer, name: "Café") }
rejects(.invalidName) { try store.create(selfPeerId: peer, name: String(repeating: "x", count: 65)) }
rejects(.invalidName) { try store.create(selfPeerId: peer, name: "\u{0001}") }
rejects(.invalidName) { try store.create(selfPeerId: peer, name: "\u{200D}") }
require(try LocalSavedTagsCodec.name("👨‍👩‍👧‍👦") == "👨‍👩‍👧‍👦", "valid ZWJ emoji rejected")
rejects(.wrongAccount) { try store.catalogue(selfPeerId: foreign) }
rejects(.wrongAccount) { try store.set(selfPeerId: foreign, tagId: first.id, messages: [], assigned: true) }
rejects(.invalidTag) { try store.rename(selfPeerId: peer, tagId: "not-a-uuid", name: "Name") }
for id in [Int32(0), Int32(-1)] {
    rejects(.invalidMessage) { try store.set(selfPeerId: peer, tagId: first.id, messages: [message(id)], assigned: true) }
}
rejects(.invalidMessage) { try store.set(selfPeerId: peer, tagId: first.id, messages: [LocalSavedTagMessage(id: MessageId(peerId: peer, namespace: 1, id: 1), timestamp: 1, threadId: nil)], assigned: true) }
rejects(.invalidMessage) { try store.set(selfPeerId: peer, tagId: first.id, messages: [message(1), LocalSavedTagMessage(id: MessageId(peerId: foreign, namespace: 0, id: 2), timestamp: 2, threadId: nil)], assigned: true) }
require(try store.catalogue(selfPeerId: peer).totalMembershipCount == 0, "invalid batch partially committed")
_ = try store.set(selfPeerId: peer, tagId: first.id, messages: [message(1), message(1), message(2, thread: 99)], assigned: true)
let revision = try store.catalogue(selfPeerId: peer).revision
_ = try store.set(selfPeerId: peer, tagId: first.id, messages: [message(1)], assigned: true)
require(try store.catalogue(selfPeerId: peer).revision == revision, "idempotence rewrote revision")
_ = try store.set(selfPeerId: peer, tagId: second.id, messages: [message(1)], assigned: true)
_ = try store.set(selfPeerId: peer, tagId: first.id, messages: [message(1)], assigned: false)
require(try store.tags(selfPeerId: peer, messageId: message(1).id) == [second.id], "remove lost unrelated tag")
let writes = box.sets
_ = try store.rename(selfPeerId: peer, tagId: second.id, name: "Renamed")
require(box.sets - writes == 2, "rename rewrote memberships")
box.commit()
let (reopenedBox, reopened) = open("a.sqlite")
require(try reopened.tags(selfPeerId: peer, messageId: message(1).id) == [second.id], "actual reopen lost membership")
require(try reopened.catalogue(selfPeerId: peer).tags.first(where: { $0.id == second.id })?.name == "Renamed", "actual reopen lost rename")
let (_, isolated) = open("b.sqlite")
require(try isolated.catalogue(selfPeerId: peer).tags.isEmpty, "database/account isolation")
reopenedBox.begin()
_ = try reopened.removeMessages(selfPeerId: peer, ids: [message(1).id])
require(try reopened.tags(selfPeerId: peer, messageId: message(2).id) == [first.id], "Saved copy identity collapsed")
_ = try reopened.removeGlobalIds(selfPeerId: peer, ids: [2])
require(try reopened.catalogue(selfPeerId: peer).totalMembershipCount == 0, "uncached global ID removal")
rejects(.batchLimit) { try reopened.removeGlobalIds(selfPeerId: peer, ids: Array(repeating: 1, count: 1001)) }
rejects(.invalidMessage) { try reopened.removeGlobalIds(selfPeerId: peer, ids: [1, 0]) }
rejects(.invalidMessage) { try reopened.set(selfPeerId: peer, tagId: first.id, messages: [message(1), LocalSavedTagMessage(id: message(1).id, timestamp: 50, threadId: nil)], assigned: true) }
rejects(.invalidMessage) { try reopened.removeRange(selfPeerId: peer, scope: LocalSavedTagsDeletionScope(minId: 9, maxId: 1)) }
let many = try reopened.create(selfPeerId: peer, name: "Archive")
_ = try reopened.set(selfPeerId: peer, tagId: many.id, messages: (1...1000).map { message(Int32($0), thread: $0 % 2 == 0 ? 99 : nil) }, assigned: true)
_ = try reopened.set(selfPeerId: peer, tagId: many.id, messages: [message(1001)], assigned: true)
rejects(.batchLimit) { try reopened.set(selfPeerId: peer, tagId: many.id, messages: (1...1001).map { message(Int32($0)) }, assigned: true) }
var cursor: LocalSavedTagsCursor? = nil
var seen: [Int32] = []
let pagingRows = reopenedBox.rows, pagingRanges = reopenedBox.ranges
var maxPageRows = 0
repeat {
    let before = reopenedBox.rows
    let page = try reopened.page(selfPeerId: peer, tagId: many.id, cursor: cursor, direction: .earlier, limit: 45)
    require(page.messages.count <= 45 && reopenedBox.rows - before <= 47, "page fetched unbounded rows")
    maxPageRows = max(maxPageRows, reopenedBox.rows - before)
    seen += page.messages.map { $0.id.id }
    cursor = page.earlier
} while cursor != nil
require(seen == Array((1...1001).reversed()).map(Int32.init), "oldest of1001 not reachable")
print("MEASURE traversal1001 indexRows=\(reopenedBox.rows - pagingRows) rangeRequests=\(reopenedBox.ranges - pagingRanges) maxRowsPerPage=\(maxPageRows)")
let oldest = try reopened.page(selfPeerId: peer, tagId: many.id, cursor: nil, direction: .later, limit: 1)
require(oldest.messages.first?.id.id == 1, "ascending oldest")
rejects(.invalidPage) { try reopened.page(selfPeerId: peer, tagId: many.id, cursor: nil, direction: .earlier, limit: 46) }
rejects(.invalidPage) { try reopened.page(selfPeerId: peer, tagId: many.id, cursor: nil, direction: .later, limit: 0) }
var ascending: [Int32] = []; cursor = nil
repeat {
    let page = try reopened.page(selfPeerId: peer, tagId: many.id, cursor: cursor, direction: .later, limit: 45)
    ascending += page.messages.map { $0.id.id }; cursor = page.later
} while cursor != nil
require(ascending == Array(1...1001).map(Int32.init), "later traversal")
_ = try reopened.removeRange(selfPeerId: peer, scope: LocalSavedTagsDeletionScope(threadId: 99, minId: 100, maxId: 200))
require(try reopened.catalogue(selfPeerId: peer).totalMembershipCount == 950, "thread numeric range cleanup")
_ = try reopened.removeRange(selfPeerId: peer, scope: LocalSavedTagsDeletionScope(minTimestamp: 900, maxTimestamp: 1001))
require(try reopened.catalogue(selfPeerId: peer).totalMembershipCount == 848, "timestamp cleanup")
let deleteStart = Date(); let rowsBefore = reopenedBox.rows
_ = try reopened.delete(selfPeerId: peer, tagId: many.id)
require(try reopened.catalogue(selfPeerId: peer).totalMembershipCount == 0, "delete counters")
print("MEASURE delete848 seconds=\(Date().timeIntervalSince(deleteStart)) indexRows=\(reopenedBox.rows - rowsBefore)")
reopenedBox.commit()
// Real keyed Postbox adapter, not JSONEncoder.
let rev = LocalSavedTagsRevision(revision: 123)
require(PreferencesEntry(rev)?.get(LocalSavedTagsRevision.self)?.revision == 123, "revision Postbox codec")
for bytes in [Data(), Data([2]), Data(repeating: 255, count: 400)] {
    rejects(.corruptStore) { try LocalSavedTagsCodec.definition(bytes, id: first.id) }
}

// Exact Transaction wrappers exercise existing PreferencesTable operations and
// actual supported Postbox codec. Queue/view delivery remains a shell boundary.
let (transactionBox, _) = open("transaction.sqlite")
let postbox = FixturePostbox(transactionBox)
let exactTransaction = Transaction(postbox)
transactionBox.begin()
let transactional = try exactTransaction.createLocalSavedTag(selfPeerId: peer, name: "Notify").get()
require(postbox.operations.count == 1, "new table write did not invalidate PreferencesView")
_ = try exactTransaction.setLocalSavedTag(selfPeerId: peer, tagId: transactional.id, messages: [message(1)], assigned: true).get()
require(postbox.operations.count == 2, "assignment did not notify")
_ = try exactTransaction.setLocalSavedTag(selfPeerId: peer, tagId: transactional.id, messages: [message(1)], assigned: true).get()
require(postbox.operations.count == 2, "idempotent assignment notified")
rejects(.invalidName) { try exactTransaction.renameLocalSavedTag(selfPeerId: peer, tagId: transactional.id, name: "").get() }
require(postbox.operations.count == 2, "rejected mutation notified")
postbox.preferencesTable.beforeCommit(); transactionBox.commit()
let (reopenTransactionBox, _) = open("transaction.sqlite")
let reopenPreferences = PreferencesTable(valueBox: reopenTransactionBox, table: PreferencesTable.tableSpec(35), useCaches: false)
require(reopenPreferences.get(key: localSavedTagsRevisionKey())?.get(LocalSavedTagsRevision.self)?.revision == 2, "revision not durably committed with table")
require(try FixturePostbox(reopenTransactionBox).localSavedTagsTable.catalogue(selfPeerId: peer).revision == 2, "scalar/table revisions diverged")

let (limitsBox, limits) = open("limits.sqlite")
limitsBox.begin()
var definitions: [LocalSavedTag] = []
for i in 1...256 { definitions.append(try limits.create(selfPeerId: peer, name: "Tag \(i)")) }
rejects(.tagLimit) { try limits.create(selfPeerId: peer, name: "Overflow") }
require(try limits.catalogue(selfPeerId: peer).tags.count == 256, "tag rejection evicted definitions")
for tag in definitions.prefix(16) { _ = try limits.set(selfPeerId: peer, tagId: tag.id, messages: [message(1)], assigned: true) }
rejects(.messageTagLimit) { try limits.set(selfPeerId: peer, tagId: definitions[16].id, messages: [message(2), message(1)], assigned: true) }
require(try limits.tags(selfPeerId: peer, messageId: message(2).id).isEmpty, "per-message quota partially assigned batch")
_ = try limits.updateMetadata(selfPeerId: peer, messages: [LocalSavedTagMessage(id: message(1).id, timestamp: -20, threadId: 543)])
let moved = try limits.page(selfPeerId: peer, tagId: definitions[0].id, cursor: nil, direction: .earlier, limit: 45)
require(moved.messages.first?.timestamp == -20 && moved.messages.first?.threadId == 543, "metadata index not moved")
_ = try limits.removeRange(selfPeerId: peer, scope: LocalSavedTagsDeletionScope(threadId: 543, minTimestamp: -20, maxTimestamp: -20))
require(try limits.catalogue(selfPeerId: peer).totalMembershipCount == 0, "negative inclusive thread timestamp deletion")
require(try limits.catalogue(selfPeerId: peer).tags.count == 256, "history clear deleted definitions")
// Tag deletion preserves a second relation; full history clear preserves tags.
_ = try limits.set(selfPeerId: peer, tagId: definitions[0].id, messages: [message(3)], assigned: true)
_ = try limits.set(selfPeerId: peer, tagId: definitions[1].id, messages: [message(3), message(4)], assigned: true)
_ = try limits.delete(selfPeerId: peer, tagId: definitions[0].id)
require(try limits.tags(selfPeerId: peer, messageId: message(3).id) == [definitions[1].id], "tag delete removed unrelated relation")
_ = try limits.removeRange(selfPeerId: peer, scope: LocalSavedTagsDeletionScope())
require(try limits.catalogue(selfPeerId: peer).totalMembershipCount == 0, "full clear left memberships")
require(try limits.catalogue(selfPeerId: peer).tags.count == 255, "full clear changed catalogue")
let clearRevision = try limits.catalogue(selfPeerId: peer).revision
_ = try limits.removeRange(selfPeerId: peer, scope: LocalSavedTagsDeletionScope())
require(try limits.catalogue(selfPeerId: peer).revision == clearRevision, "empty clear changed revision")
limitsBox.commit()

//100k accepted edges are retained until explicit user deletion. This is real
// production admission/index work, not fabricated metadata or a smaller quota.
let (quotaBox, quota) = open("quota.sqlite")
quotaBox.begin()
let quotaTag = try quota.create(selfPeerId: peer, name: "Durable")
let fillStart = Date()
for block in 0..<100 {
    let lower = block * 1000 + 1, upper = min((block + 1) * 1000, 99999)
    _ = try quota.set(selfPeerId: peer, tagId: quotaTag.id, messages: (lower...upper).map { message(Int32($0)) }, assigned: true)
}
let quotaRevision = try quota.catalogue(selfPeerId: peer).revision
rejects(.membershipLimit) { try quota.set(selfPeerId: peer, tagId: quotaTag.id, messages: [message(100000),message(100001)], assigned: true) }
require(try quota.tags(selfPeerId: peer, messageId: message(100000).id).isEmpty, "membership quota partially wrote")
require(try quota.catalogue(selfPeerId: peer).revision == quotaRevision, "quota rejection changed revision")
require(try quota.tags(selfPeerId: peer, messageId: message(1).id) == [quotaTag.id], "quota evicted oldest")
_ = try quota.set(selfPeerId: peer, tagId: quotaTag.id, messages: [message(100000)], assigned: true)
quotaBox.commit()
print("MEASURE seed100000 seconds=\(Date().timeIntervalSince(fillStart)) sets=\(quotaBox.sets)")
let pageRowsBefore = quotaBox.rows
let oldestPage = try quota.page(selfPeerId: peer, tagId: quotaTag.id, cursor: nil, direction: .later, limit: 45)
require(oldestPage.messages.first?.id.id == 1 && quotaBox.rows - pageRowsBefore <= 47, "quota-sized page not indexed/bounded")
require(quotaBox.rangePlan().contains("SEARCH") && quotaBox.rangePlan().contains("PRIMARY KEY"), "SQLite page query became a table scan")
print("MEASURE oldest45of100000 indexRows=\(quotaBox.rows - pageRowsBefore) queryPlan=\(quotaBox.rangePlan())")
quotaBox.begin()
// Removal must remain available at the edge quota, and a replacement then
// restores exactly100000 for the streaming deletion measurement.
_ = try quota.set(selfPeerId: peer, tagId: quotaTag.id, messages: [message(100000)], assigned: false)
_ = try quota.set(selfPeerId: peer, tagId: quotaTag.id, messages: [message(100000)], assigned: true)
let heavyStart = Date(), heavyRows = quotaBox.rows, heavyRemoves = quotaBox.removes
_ = try quota.delete(selfPeerId: peer, tagId: quotaTag.id)
quotaBox.commit()
require(try quota.catalogue(selfPeerId: peer).totalMembershipCount == 0, "large delete did not drain indexes")
require(quotaBox.largestRange <= 257, "unbounded range allocation") //257 only bounded catalogue corruption probe
print("MEASURE delete100000 seconds=\(Date().timeIntervalSince(heavyStart)) indexRows=\(quotaBox.rows - heavyRows) removes=\(quotaBox.removes - heavyRemoves) largestRangeRequest=\(quotaBox.largestRange)")

let malformed = LocalSavedTag(id: first.id, name: "Valid", order: 1, count: 1)
let validBytes = LocalSavedTagsCodec.definition(malformed)
require(try LocalSavedTagsCodec.definition(validBytes, id: first.id) == malformed, "binary definition roundtrip")
for length in 0..<validBytes.count { rejects(.corruptStore) { try LocalSavedTagsCodec.definition(validBytes.prefix(length), id: first.id) } }
struct InvalidRevisionWire: Encodable {
    enum CodingKeys: String, CodingKey { case schema, revision }
    let schema: Int32, revision: Int64
    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(schema, forKey: .schema); try c.encode(revision, forKey: .revision)
    }
}
require(PreferencesEntry(InvalidRevisionWire(schema: 2, revision: 1))?.get(LocalSavedTagsRevision.self) == nil, "unknown revision schema admitted")
require(PreferencesEntry(InvalidRevisionWire(schema: 1, revision: -1))?.get(LocalSavedTagsRevision.self) == nil, "negative revision admitted")
let messageBytes = LocalSavedTagsCodec.message(message(42, thread: 99), count: 2)
require(try LocalSavedTagsCodec.message(messageBytes, owner: peer).0 == message(42, thread: 99), "full Saved identity codec")
rejects(.corruptStore) { try LocalSavedTagsCodec.message(messageBytes, owner: foreign) }
for length in 0..<messageBytes.count { rejects(.corruptStore) { try LocalSavedTagsCodec.message(messageBytes.prefix(length), owner: peer) } }
rejects(.invalidName) { try limits.create(selfPeerId: peer, name: String(repeating: "👨‍👩‍👧‍👦", count: 64)) }
// Actual database corruption: preflight must reject before changing any row.
func fixtureKey(_ bytes: Data) -> ValueBoxKey {
    let key = ValueBoxKey(length: bytes.count); key.setData(0, value: bytes); return key
}
let (corruptBox, corrupt) = open("corrupt.sqlite")
corruptBox.begin()
let corruptTag = try corrupt.create(selfPeerId: peer, name: "Checked")
_ = try corrupt.set(selfPeerId: peer, tagId: corruptTag.id, messages: [message(1), message(2)], assigned: true)
let corruptTable = LocalSavedTagsTable.tableSpec(0x4A470001)
let reverseBytes = Data([3]) + (try LocalSavedTagsCodec.uuid(corruptTag.id)) + LocalSavedTagsCodec.i32(Int32(2) ^ Int32.min) + LocalSavedTagsCodec.i32(0) + LocalSavedTagsCodec.i32(2)
let reverseKey = fixtureKey(reverseBytes)
let originalReverse = corruptBox.get(corruptTable, key: reverseKey)!.makeData()
corruptBox.set(corruptTable, key: reverseKey, value: ReadBuffer(data: Data([99])))
let corruptSets = corruptBox.sets, corruptRemoves = corruptBox.removes
rejects(.corruptStore) { try corrupt.removeMessages(selfPeerId: peer, ids: [message(1).id, message(2).id]) }
rejects(.corruptStore) { try corrupt.delete(selfPeerId: peer, tagId: corruptTag.id) }
rejects(.corruptStore) { try corrupt.removeRange(selfPeerId: peer, scope: LocalSavedTagsDeletionScope()) }
require(corruptBox.sets == corruptSets && corruptBox.removes == corruptRemoves, "corruption rejection partially wrote")
require(try corrupt.tags(selfPeerId: peer, messageId: message(1).id) == [corruptTag.id], "corruption preflight deleted good row")
corruptBox.set(corruptTable, key: reverseKey, value: ReadBuffer(data: originalReverse))
let phantomKey = fixtureKey(Data([5]) + LocalSavedTagsCodec.i32(Int32(0) ^ Int32.min) + LocalSavedTagsCodec.i32(0) + LocalSavedTagsCodec.i32(1))
corruptBox.set(corruptTable, key: phantomKey, value: ReadBuffer(data: LocalSavedTagsCodec.i32(1)))
let duplicateSets = corruptBox.sets, duplicateRemoves = corruptBox.removes
rejects(.corruptStore) { try corrupt.removeRange(selfPeerId: peer, scope: LocalSavedTagsDeletionScope(minTimestamp: -1, maxTimestamp: 1)) }
require(corruptBox.sets == duplicateSets && corruptBox.removes == duplicateRemoves, "wrong secondary key partially erased range")
require(try corrupt.catalogue(selfPeerId: peer).totalMembershipCount == 2, "wrong secondary key changed counters")
corruptBox.remove(corruptTable, key: phantomKey, secure: false)
corruptBox.set(corruptTable, key: fixtureKey(Data([0])), value: ReadBuffer(data: Data(repeating: 255, count: 400)))
rejects(.corruptStore) { try corrupt.catalogue(selfPeerId: peer) }
corruptBox.commit()
let (orderBox, orderStore) = open("order.sqlite")
orderBox.begin()
let orderBytes = LocalSavedTagsCodec.i32(1) + LocalSavedTagsCodec.i64(peer.toInt64()) + LocalSavedTagsCodec.i32(0) + LocalSavedTagsCodec.i64(1) + LocalSavedTagsCodec.i32(Int32.max - 1)
orderBox.set(corruptTable, key: fixtureKey(Data([0])), value: ReadBuffer(data: orderBytes))
_ = try orderStore.create(selfPeerId: peer, name: "Before rollover")
_ = try orderStore.create(selfPeerId: peer, name: "After rollover")
require(try orderStore.catalogue(selfPeerId: peer).tags.map { $0.order } == [0, 1], "creation order did not compact safely")
orderBox.commit()
let (exhaustedBox, _) = open("exhausted.sqlite")
exhaustedBox.begin()
let exhaustedPostbox = FixturePostbox(exhaustedBox)
let exhaustedTransaction = Transaction(exhaustedPostbox)
let exhaustedBytes = LocalSavedTagsCodec.i32(1) + LocalSavedTagsCodec.i64(peer.toInt64()) + LocalSavedTagsCodec.i32(0) + LocalSavedTagsCodec.i64(Int64.max - 1) + LocalSavedTagsCodec.i32(0)
exhaustedBox.set(corruptTable, key: fixtureKey(Data([0])), value: ReadBuffer(data: exhaustedBytes))
let exhaustedSets = exhaustedBox.sets
rejects(.corruptStore) { try exhaustedTransaction.createLocalSavedTag(selfPeerId: peer, name: "Exhausted").get() }
require(exhaustedBox.sets == exhaustedSets && exhaustedPostbox.operations.isEmpty, "exhausted revision partially committed")
require(try exhaustedPostbox.localSavedTagsTable.catalogue(selfPeerId: peer).tags.isEmpty, "exhausted revision added a tag")
exhaustedBox.commit()
print("PASS actual production Saved Tags table with SQLite storage; full Postbox lifecycle remains separate")

