// Appended to the existing actual SQLite production-store fixture.
// Exact Core helpers execute with a transaction/message shell; no live account,
// API server or UIKit is simulated as native app evidence.
let (coreBox, _) = open("core.sqlite")
let corePostbox = FixturePostbox(coreBox)
let coreTransaction = Transaction(corePostbox)
coreTransaction.fixtureState = AuthorizedAccountState(peerId: peer)
coreBox.begin()
let coreTag = try coreTransaction.createLocalSavedTag(selfPeerId: peer, name: "Core").get()
let unrelated = try coreTransaction.createLocalSavedTag(selfPeerId: peer, name: "Independent").get()
let coreEntries = (1...1000).map { message(Int32($0), thread: $0 % 2 == 0 ? 99 : nil) }
_ = try coreTransaction.setLocalSavedTag(selfPeerId: peer, tagId: coreTag.id, messages: coreEntries, assigned: true).get()
_ = try coreTransaction.setLocalSavedTag(selfPeerId: peer, tagId: unrelated.id, messages: [message(1)], assigned: true).get()
let summary = try _internal_localSavedTagsSelectionSummary(transaction: coreTransaction, selfPeerId: peer, messageIds: [message(1).id, message(1).id, message(2).id]).get()
require(summary.selectedCount == 2 && summary.assignedCounts[coreTag.id] == 2 && summary.assignedCounts[unrelated.id] == 1, "mixed selection summary")
require(coreTransaction.fixtureMessageReads == 0, "summary read history")
rejects(.batchLimit) { try _internal_localSavedTagsSelectionSummary(transaction: coreTransaction, selfPeerId: peer, messageIds: Array(repeating: message(1).id, count: 1001)).get() }
rejects(.invalidMessage) { try _internal_localSavedTagsSelectionSummary(transaction: coreTransaction, selfPeerId: peer, messageIds: [MessageId(peerId: foreign, namespace: 0, id: 1)]).get() }
rejects(.unavailable) { try _internal_setLocalSavedTag(transaction: coreTransaction, selfPeerId: peer, tagId: coreTag.id, messageIds: [message(1).id], assigned: true).get() }
let membershipBefore = try coreTransaction.localSavedTagsCatalogue(selfPeerId: peer).get().totalMembershipCount
require(membershipBefore == 1001, "content miss purged membership")
_ = try _internal_removeLocalSavedTag(transaction: coreTransaction, selfPeerId: peer, tagId: coreTag.id, entries: [LocalSavedTagMessage(id: message(1).id, timestamp: -500, threadId: 42)]).get()
require(try coreTransaction.localSavedTagsForMessage(selfPeerId: peer, messageId: message(1).id).get() == [unrelated.id], "unavailable removal lost independent relation")
_internal_removeLocalSavedTagsMessages(transaction: coreTransaction, ids: [MessageId(peerId: foreign, namespace: 0, id: 1), MessageId(peerId: peer, namespace: 1, id: 1), message(0).id])
require(try coreTransaction.localSavedTagsForMessage(selfPeerId: peer, messageId: message(1).id).get() == [unrelated.id], "mixed deletion touched Saved copy")
_internal_removeLocalSavedTagsGlobalIds(transaction: coreTransaction, ids: [1,2,0,-1])
require(try coreTransaction.localSavedTagsForMessage(selfPeerId: peer, messageId: message(1).id).get().isEmpty, "uncached raw global IDs ignored")
_internal_removeLocalSavedTagsRange(transaction: coreTransaction, peerId: foreign, namespaces: .just(Set([0])), scope: LocalSavedTagsDeletionScope())
_internal_removeLocalSavedTagsRange(transaction: coreTransaction, peerId: peer, namespaces: .just(Set([1])), scope: LocalSavedTagsDeletionScope())
require(try coreTransaction.localSavedTagsCatalogue(selfPeerId: peer).get().totalMembershipCount == 998, "nonself/namespace range changed store")
_internal_removeLocalSavedTagsRange(transaction: coreTransaction, peerId: peer, namespaces: .just(Set([0])), scope: LocalSavedTagsDeletionScope(threadId: 99, minId: 4, maxId: 10))
require(try coreTransaction.localSavedTagsCatalogue(selfPeerId: peer).get().totalMembershipCount == 994, "inclusive thread range")
coreTransaction.fixtureState = nil
_internal_removeLocalSavedTagsGlobalIds(transaction: coreTransaction, ids: [3])
require(try coreTransaction.localSavedTagsCatalogue(selfPeerId: peer).get().totalMembershipCount == 994, "missing authorized state guessed self")
coreTransaction.fixtureState = AuthorizedAccountState(peerId: peer)
_internal_removeLocalSavedTagsMessages(transaction: coreTransaction, ids: (1...1200).map { message(Int32($0)).id })
require(try coreTransaction.localSavedTagsCatalogue(selfPeerId: peer).get().totalMembershipCount == 0, "same-transaction deletion chunking")
require(try coreTransaction.localSavedTagsCatalogue(selfPeerId: peer).get().tags.count == 2, "full clear erased definitions")
// Successful admission resolves actual current Saved metadata, and rejects a
// missing last ID before writing any of the valid leading selection.
coreTransaction.fixtureMessages[message(1201).id] = Message(id: message(1201).id, timestamp: 9999, threadId: 42)
rejects(.unavailable) { try _internal_setLocalSavedTag(transaction: coreTransaction, selfPeerId: peer, tagId: coreTag.id, messageIds: [message(1201).id, message(1202).id], assigned: true).get() }
require(try coreTransaction.localSavedTagsCatalogue(selfPeerId: peer).get().totalMembershipCount == 0, "partial metadata resolution committed leading IDs")
_ = try _internal_setLocalSavedTag(transaction: coreTransaction, selfPeerId: peer, tagId: coreTag.id, messageIds: [message(1201).id], assigned: true).get()
let actualMetadata = try coreTransaction.localSavedTagsPage(selfPeerId: peer, tagId: coreTag.id, cursor: nil, direction: .earlier).get().messages[0]
require(actualMetadata.id == message(1201).id && actualMetadata.timestamp == 9999 && actualMetadata.threadId == 42, "assignment fabricated metadata")
_internal_removeLocalSavedTagsRange(transaction: coreTransaction, peerId: peer, namespaces: .just(Set([0])), scope: LocalSavedTagsDeletionScope())
require(try coreTransaction.localSavedTagsCatalogue(selfPeerId: peer).get().totalMembershipCount == 0, "nil-thread full clear missed indexed row")
coreBox.commit()
print("PASS exact Core operations and semantic helpers with SQLite")

coreBox.begin()
// Actual provider and service-generation methods with deterministic delayed
// signals. Transport/Signal are shells; the Dispatch delivery domain, windows
// and cancellation bodies are the actual production code.
_ = try coreTransaction.setLocalSavedTag(selfPeerId: peer, tagId: coreTag.id, messages: coreEntries, assigned: true).get()
var coreCursor: LocalSavedTagsCursor? = nil
var contentPages: [LocalSavedTagsContentPage] = []
for _ in 0..<4 {
    let page = try coreTransaction.localSavedTagsPage(selfPeerId: peer, tagId: coreTag.id, cursor: coreCursor, direction: .earlier).get()
    let rows = page.messages.map { LocalSavedTagsContentRow(entry: $0, message: nil) }
    contentPages.append(LocalSavedTagsContentPage(page: page, rows: rows, windows: [], earlier: page.earlier, later: page.later))
    coreCursor = page.earlier
}
let delayedService = LocalSavedTagsService()
let provider = delayedService.makePageProvider(tagId: coreTag.id)
var delivered: [LocalSavedTagsPageEvent] = []
let obsolete = provider.request().start(next: { delivered.append($0) })
let current = provider.request().start(next: { delivered.append($0) })
require(delayedService.activeReads == 1 && delayedService.maxActiveReads == 1, "more than one active load or hidden prefetch")
delayedService.fixtureSend(0, .result(contentPages[0]))
require(delivered.isEmpty, "stale request published")
delayedService.fixtureSend(1, .result(contentPages[0]))
for index in 1..<4 {
    let request = provider.request(cursor: contentPages[index-1].page.earlier).start(next: { delivered.append($0) })
    delayedService.fixtureSend(index+1, .result(contentPages[index]))
    // Keep returned subscription alive through explicit result delivery.
    withExtendedLifetime(request) {}
}
guard case let .result(lastContent) = delivered.last! else { fatalError("missing content page") }
require(lastContent.windows.count == 3 && lastContent.windows.flatMap({ $0 }).count == 135, "window bound exceeded")
require(lastContent.rows.count == 45 && lastContent.rows.allSatisfy({ $0.message == nil }), "unavailable rows dropped")
require(lastContent.page.earlier != nil, "unavailable rows lost pagination")
let reverse = provider.request(cursor: lastContent.later, direction: .later).start(next: { delivered.append($0) })
let reversePage = try _internal_localSavedTagsPage(transaction: coreTransaction, selfPeerId: peer, tagId: coreTag.id, cursor: lastContent.later, direction: .later).get().0
let reverseRows = reversePage.messages.map { LocalSavedTagsContentRow(entry: $0, message: nil) }
delayedService.fixtureSend(delayedService.delayed.count - 1, .result(LocalSavedTagsContentPage(page: reversePage, rows: reverseRows, windows: [], earlier: reversePage.earlier, later: reversePage.later)))
guard case let .result(reversedContent) = delivered.last! else { fatalError("missing reversed page") }
require(reversedContent.windows.flatMap({ $0 }).count == 135, "reversal lost bounded adjacent windows")
require(reversedContent.later == nil && reversedContent.earlier == contentPages[2].page.earlier, "retained window cursors don't track outer edges after reversal")
require(reversedContent.earlier != reversedContent.page.earlier, "latest requested page incorrectly used as outer boundary")
reverse.dispose()
provider.reset()
let priorCount = delivered.count
delayedService.fixtureSend(delayedService.delayed.count - 1, .result(contentPages[0]))
require(delivered.count == priorCount, "reset allowed stale result")
let reentrantService = LocalSavedTagsService()
let reentrantProvider = reentrantService.makePageProvider(tagId: coreTag.id)
var replacement: Disposable?
let reentrant = reentrantProvider.request().start(next: { event in
    reentrantProvider.reset()
    replacement = reentrantProvider.request().start(next: { _ in reentrantProvider.dispose() })
})
reentrantService.fixtureSend(0, .failure(.invalidPage))
reentrantService.fixtureSend(1, .result(contentPages[0]))
let beforeDisposed = reentrantService.activeReads
require(beforeDisposed == 0, "reentrant disposal retained request")
reentrantService.fixtureSend(1, .result(contentPages[0]))
let accountService = LocalSavedTagsService()
let accountProvider = accountService.makePageProvider(tagId: coreTag.id)
var accountResult = 0
let accountRequest = accountProvider.request().start(next: { _ in accountResult += 1 })
accountService.dispose()
accountService.fixtureSend(0, .result(contentPages[0]))
require(accountResult == 0 && accountService.activeReads == 0, "account disposal published delayed result")
obsolete.dispose(); current.dispose(); reentrant.dispose(); replacement?.dispose(); accountRequest.dispose()
provider.dispose(); accountProvider.dispose()
print("PASS exact Core provider cancellation/reentrancy/window bounds with Signal boundary")

let staleCursor = contentPages[0].page.earlier!
_ = try coreTransaction.renameLocalSavedTag(selfPeerId: peer, tagId: coreTag.id, name: "Changed").get()
let beforeStaleReads = coreTransaction.fixtureMessageReads
rejects(.invalidPage) { try _internal_localSavedTagsPage(transaction: coreTransaction, selfPeerId: peer, tagId: coreTag.id, cursor: staleCursor, direction: .earlier).get() }
require(coreTransaction.fixtureMessageReads == beforeStaleReads, "stale cursor read content before rejection")
let emptyTag = try coreTransaction.createLocalSavedTag(selfPeerId: peer, name: "Empty").get()
let emptyPage = try _internal_localSavedTagsPage(transaction: coreTransaction, selfPeerId: peer, tagId: emptyTag.id, cursor: nil, direction: .earlier).get()
require(emptyPage.0.messages.isEmpty && emptyPage.1.isEmpty && coreTransaction.fixtureMessageReads == beforeStaleReads, "empty page attempted content read")
coreBox.commit()
print("PASS stale cursor rejected before content reads; empty page bounded")

// Force the exact check-to-delivery boundary via the fixture Subscriber seam.
// A worker invalidates while delivery is paused before the external callback.
// Invalidation must wait, then future next/completion sends must be suppressed.
// Release the callback before joining the invalidating worker: callbacks must
// never synchronously wait for teardown on another thread.
final class FixtureDeliveryRace {
    let entered = DispatchSemaphore(value: 0)
    let release = DispatchSemaphore(value: 0)
    let invalidationStarted = DispatchSemaphore(value: 0)
    let invalidationFinished = DispatchSemaphore(value: 0)
    private let lock = NSLock()
    private var invalidated = false
    private(set) var delivered = 0
    private(set) var stale = 0
    func pause() { entered.signal(); require(release.wait(timeout: .now() + 5) == .success, "delivery seam timeout") }
    func record() { lock.lock(); delivered += 1; if invalidated { stale += 1 }; lock.unlock() }
    func finishInvalidation() { lock.lock(); invalidated = true; lock.unlock(); invalidationFinished.signal() }
}
func verifyDeliveryFence(_ name: String, signal: Signal<LocalSavedTagsPageEvent, NoError>, completion: Bool, emit: @escaping () -> Void, invalidate: @escaping () -> Void, drain: () -> Void) {
    let race = FixtureDeliveryRace()
    let subscription = signal.start(next: { _ in if !completion { race.record() } }, completed: { if completion { race.record() } }, beforeNext: completion ? nil : { race.pause() }, beforeCompleted: completion ? { race.pause() } : nil)
    DispatchQueue.global().async { emit() }
    require(race.entered.wait(timeout: .now() + 5) == .success, "\(name): no delivery seam")
    DispatchQueue.global().async { race.invalidationStarted.signal(); invalidate(); race.finishInvalidation() }
    require(race.invalidationStarted.wait(timeout: .now() + 5) == .success, "\(name): invalidation not attempted")
    require(race.invalidationFinished.wait(timeout: .now() + 0.2) == .timedOut, "\(name): invalidation returned before in-flight callback")
    race.release.signal()
    require(race.invalidationFinished.wait(timeout: .now() + 5) == .success, "\(name): invalidation fence did not complete")
    drain()
    require(race.delivered == 1 && race.stale == 0, "\(name): stale callback after invalidation return")
    emit(); drain()
    require(race.delivered == 1 && race.stale == 0, "\(name): new callback after invalidation return")
    subscription.dispose()
}
for completion in [false, true] {
    let serviceFence = LocalSavedTagsService()
    verifyDeliveryFence("service dispose \(completion)", signal: serviceFence.fixtureSignal(), completion: completion, emit: {
        if completion { serviceFence.fixtureComplete(0) } else { serviceFence.fixtureEmit(0, .progress) }
    }, invalidate: { serviceFence.dispose() }, drain: { serviceFence.fixtureDrain() })
    for dispose in [false, true] {
        let pageService = LocalSavedTagsService()
        let pageProvider = pageService.makePageProvider(tagId: coreTag.id)
        verifyDeliveryFence("provider reset/dispose \(dispose) \(completion)", signal: pageProvider.request(), completion: completion, emit: {
            if completion { pageService.fixtureComplete(0) } else { pageService.fixtureEmit(0, .result(contentPages[0])) }
        }, invalidate: { if dispose { pageProvider.dispose() } else { pageProvider.reset() } }, drain: { pageService.fixtureDrain() })
        pageProvider.dispose(); pageService.dispose()
    }
}
print("PASS concurrent next/completion delivery fences for service disposal and provider reset/disposal")

// Queue old next AND completion while inside an external callback, then
// invalidate inline. Both sends are pending in the real delivery queue before
// invalidation returns; neither may escape afterwards. This also exercises
// completion callback reentrancy independently of the next callback cases.
func verifyQueuedReentrantFence(_ name: String, signal: Signal<LocalSavedTagsPageEvent, NoError>, completion: Bool, emitNext: @escaping () -> Void, emitCompletion: @escaping () -> Void, invalidate: @escaping () -> Void, drain: () -> Void) {
    let returned = DispatchSemaphore(value: 0)
    var callbacks = 0
    var invalidated = false
    var stale = 0
    func callback() {
        callbacks += 1
        if invalidated { stale += 1; return }
        emitNext()
        emitCompletion()
        invalidate()
        invalidated = true
        returned.signal()
    }
    let subscription = signal.start(next: { _ in callback() }, completed: { callback() })
    if completion { emitCompletion() } else { emitNext() }
    require(returned.wait(timeout: .now() + 5) == .success, "\(name): callback invalidation deadlocked")
    // The callback signals only after both old sends are queued and the inline
    // fence has returned, so this barrier is ordered behind both pending sends.
    drain()
    require(callbacks == 1 && stale == 0, "\(name): queued callback survived reentrant invalidation")
    subscription.dispose()
}
for completion in [false, true] {
    let serviceFence = LocalSavedTagsService()
    verifyQueuedReentrantFence("service queued/reentrant \(completion)", signal: serviceFence.fixtureSignal(), completion: completion,
        emitNext: { serviceFence.fixtureEmit(0, .progress) }, emitCompletion: { serviceFence.fixtureComplete(0) },
        invalidate: { serviceFence.dispose() }, drain: { serviceFence.fixtureDrain() })
    for dispose in [false, true] {
        let pageService = LocalSavedTagsService()
        let pageProvider = pageService.makePageProvider(tagId: coreTag.id)
        verifyQueuedReentrantFence("provider queued/reentrant \(dispose) \(completion)", signal: pageProvider.request(), completion: completion,
            emitNext: { pageService.fixtureEmit(0, .result(contentPages[0])) }, emitCompletion: { pageService.fixtureComplete(0) },
            invalidate: { if dispose { pageProvider.dispose() } else { pageProvider.reset() } }, drain: { pageService.fixtureDrain() })
        pageProvider.dispose(); pageService.dispose()
    }
}
print("PASS queued next/completion rejected after reentrant service disposal and provider reset/disposal")
