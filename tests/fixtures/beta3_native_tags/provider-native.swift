// Additional exact production table + provider cases, appended to the accepted
// Core assembly. Signal transport is a deterministic boundary, not live UI.
let (nativeTagsBox, _) = open("beta3-native-tags.sqlite")
let nativeTagsPostbox = FixturePostbox(nativeTagsBox)
let nativeTagsTransaction = Transaction(nativeTagsPostbox)
nativeTagsTransaction.fixtureState = AuthorizedAccountState(peerId: peer)
nativeTagsBox.begin()
let nativeTagsTag = try nativeTagsTransaction.createLocalSavedTag(selfPeerId: peer, name: "Native strip fixture").get()
let nativeTagsEntries = (1...925).map { message(Int32($0), thread: $0 % 3 == 0 ? 55 : nil) }
_ = try nativeTagsTransaction.setLocalSavedTag(selfPeerId: peer, tagId: nativeTagsTag.id, messages: nativeTagsEntries, assigned: true).get()
let nativeTagsService = LocalSavedTagsService()
let nativeTagsProvider = nativeTagsService.makePageProvider(tagId: nativeTagsTag.id)
var nativeTagsOutput: LocalSavedTagsContentPage?
var nativeTagsDeliveries = 0
func nativeTagsLoad(_ cursor: LocalSavedTagsCursor?, _ direction: LocalSavedTagsDirection) throws -> LocalSavedTagsContentPage {
    nativeTagsOutput = nil
    let subscription = nativeTagsProvider.request(cursor: cursor, direction: direction).start(next: { event in
        if case let .result(content) = event { nativeTagsOutput = content; nativeTagsDeliveries += 1 }
    })
    let page = try nativeTagsTransaction.localSavedTagsPage(selfPeerId: peer, tagId: nativeTagsTag.id, cursor: cursor, direction: direction).get()
    require(page.messages.count <= 45, "native strip page exceeded 45 indexed IDs")
    // Every row deliberately uncached: only exact indexed IDs are represented.
    let rows = page.messages.map { LocalSavedTagsContentRow(entry: $0, message: nil) }
    nativeTagsService.fixtureSend(nativeTagsService.delayed.count - 1, .result(LocalSavedTagsContentPage(page: page, rows: rows, windows: [], earlier: page.earlier, later: page.later)))
    subscription.dispose()
    guard let output = nativeTagsOutput else { fatalError("provider lost page") }
    let retained = output.windows.flatMap { $0 }
    require(output.windows.count <= 3 && retained.count <= 135, "native bubble window grew beyond 135")
    require(Set(retained.map { $0.entry.id }).count == retained.count, "native bubble window duplicated IDs")
    require(retained.allSatisfy { $0.message == nil }, "uncached fixture synthesized messages")
    return output
}
var nativeTagsContent = try nativeTagsLoad(nil, .earlier)
var nativeTagsSeen = Set(nativeTagsContent.windows.flatMap { $0 }.map { $0.entry.id })
var nativeTagsPages = 1
while let cursor = nativeTagsContent.earlier {
    nativeTagsContent = try nativeTagsLoad(cursor, .earlier)
    nativeTagsSeen.formUnion(nativeTagsContent.windows.flatMap { $0 }.map { $0.entry.id })
    nativeTagsPages += 1
    require(nativeTagsPages <= 22, "earlier cursor loop")
}
require(nativeTagsSeen.count == 925, "offviewport native traversal stopped at 135/500 or skipped members")
require(nativeTagsPages == 21, "indexed page count changed")
var nativeTagsReverse = Set(nativeTagsContent.windows.flatMap { $0 }.map { $0.entry.id })
var nativeTagsReversePages = 0
while let cursor = nativeTagsContent.later {
    nativeTagsContent = try nativeTagsLoad(cursor, .later)
    nativeTagsReverse.formUnion(nativeTagsContent.windows.flatMap { $0 }.map { $0.entry.id })
    nativeTagsReversePages += 1
    require(nativeTagsReversePages <= 22, "later cursor loop")
}
require(nativeTagsReverse.count == 925, "reverse after eviction skipped indexed memberships")
require(try nativeTagsTransaction.localSavedTagsCatalogue(selfPeerId: peer).get().totalMembershipCount == 925, "uncached browsing erased memberships")
let nativeTagsEmpty = try nativeTagsTransaction.createLocalSavedTag(selfPeerId: peer, name: "Native empty").get()
let nativeTagsEmptyPage = try nativeTagsTransaction.localSavedTagsPage(selfPeerId: peer, tagId: nativeTagsEmpty.id, cursor: nil, direction: .earlier).get()
require(nativeTagsEmptyPage.messages.isEmpty && nativeTagsEmptyPage.earlier == nil && nativeTagsEmptyPage.later == nil, "empty local tag exposed fabricated paging")
let nativeTagsBeforeReset = nativeTagsDeliveries
nativeTagsProvider.reset()
nativeTagsService.fixtureSend(nativeTagsService.delayed.count - 1, .result(nativeTagsContent))
require(nativeTagsDeliveries == nativeTagsBeforeReset, "cancelled native filter published old page")
let nativeTagsPending = nativeTagsProvider.request().start(next: { _ in nativeTagsDeliveries += 1 })
nativeTagsService.dispose()
nativeTagsService.fixtureSend(nativeTagsService.delayed.count - 1, .result(nativeTagsContent))
require(nativeTagsDeliveries == nativeTagsBeforeReset, "switched account published old native filter")
nativeTagsPending.dispose(); nativeTagsProvider.dispose()
nativeTagsBox.commit()
print("PASS beta3 native tags 925 memberships both directions / eviction / nil rows / empty / generation / account")
