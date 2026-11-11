func check(_ condition: @autoclosure () -> Bool, _ message: String) { precondition(condition(), message) }
let id: Int64 = 879123456789
let storedKey = JerkgramDefaultFolderSettings.scopedKey(accountPeerId: id)
let absentKey = JerkgramDefaultFolderSettings.scopedKey(accountPeerId: id + 1)
let falseKey = JerkgramDefaultFolderSettings.scopedKey(accountPeerId: id + 2)
let defaults = UserDefaults.standard
let previous = defaults.object(forKey: storedKey)
let absentPrevious = defaults.object(forKey: absentKey)
let falsePrevious = defaults.object(forKey: falseKey)
defer {
    if let previous { defaults.set(previous, forKey: storedKey) } else { defaults.removeObject(forKey: storedKey) }
    if let absentPrevious { defaults.set(absentPrevious, forKey: absentKey) } else { defaults.removeObject(forKey: absentKey) }
    if let falsePrevious { defaults.set(falsePrevious, forKey: falseKey) } else { defaults.removeObject(forKey: falseKey) }
}
defaults.set(true, forKey: storedKey)
defaults.removeObject(forKey: absentKey)
defaults.set(false, forKey: falseKey)
let account = Account(id)
let transaction = account.postbox.storage
private let saved = JerkgramDefaultFolderOrder(ids: [3, 0, 2])
transaction.entries[PreferencesKeys.jerkgramDefaultFolderOrder] = PreferencesEntry(saved)
let savedBytes = try! JSONEncoder().encode(saved) // Fixture retention probe, not Postbox wire proof.
let native: [Int32] = [0, 2, 3, 4]
check(!JerkgramDefaultFolderSettings.snapshot(accountPeerId: id).enabled, "persisted true must be inert")
check(!JerkgramDefaultFolderSettings.enabled(accountPeerId: id + 1), "missing bool must remain false")
check(!JerkgramDefaultFolderSettings.enabled(accountPeerId: id + 2), "stored false must remain false")
check(defaults.object(forKey: absentKey) == nil, "reading defaults must not create a preference")
JerkgramDefaultFolderSettings.update(accountPeerId: id, enabled: true)
check(!JerkgramDefaultFolderSettings.enabled(accountPeerId: id), "cache updates must not reactivate")
JerkgramDefaultFolderSettings.update(accountPeerId: id, enabled: false)
JerkgramDefaultFolderSettings.update(accountPeerId: id, enabled: true)
check(!JerkgramDefaultFolderSettings.enabled(accountPeerId: id), "account reactivation must remain disabled")
check(defaults.bool(forKey: storedKey), "stored true must be retained")
check(JerkgramFolderOrder.effective(native: native, saved: saved.ids, allowed: [2, 3], active: true) == native, "stale active flag must use native order")
check(!JerkgramFolderOrder.proposalIsCurrent(enabled: true, premium: false, generation: 8, proposedGeneration: 8), "stale enabled policy must reject proposals")
check(JerkgramFolderOrder.startupReady(enabled: true, premium: nil, localRead: true), "local experiment must not wait for premium")
check(!JerkgramFolderOrder.startupReady(enabled: false, premium: nil, localRead: false), "native data readiness remains required")
for premium in [nil, false, true] as [Bool?] {
    transaction.peer = premium.map { Peer(isPremium: $0) }
    let snapshot = _internal_updatedJerkgramChatListFilters(account: account).value
    check(snapshot.filters.map { $0.id } == native, "native order must survive premium state changes")
    check(snapshot.nativeFilters.map { $0.id } == native, "native projection must remain unchanged")
    check(snapshot.isPremium == premium, "native entitlement must remain unchanged")
    check(snapshot.limits.maxFoldersCount == 2 && snapshot.allowedIds == [2, 3], "native free limits must remain unchanged")
    check(!snapshot.policyEnabled && !snapshot.localActive && !snapshot.defaultMissing && snapshot.proposal == nil, "snapshot must disable every local bypass")
    check(snapshot.startupReady, "native snapshot must become ready")
    check(snapshot.normalizedOrder([3, 0, 2]) == native, "normalization must fall back to native")
}
account.viewTracker.hiddenChatListFilterIds = Signal(value: [3])
let hiddenSnapshot = _internal_updatedJerkgramChatListFilters(account: account).value
check(hiddenSnapshot.filters.map { $0.id } == [0, 2, 4], "native hidden-folder projection must survive")
check(hiddenSnapshot.allowedIds == [2, 4], "allowed native IDs must use the existing hidden-folder limit")
account.viewTracker.hiddenChatListFilterIds = Signal(value: [])
transaction.peer = Peer(isPremium: false)
let generation = JerkgramDefaultFolderSettings.generation(accountPeerId: id)
for staleGeneration in [generation, generation &- 1] {
    let proposal = JerkgramChatListFilterProposal(token: JerkgramFolderProposalToken(lifetime: account.postbox, generation: staleGeneration), nativeIds: native, allowedIds: [2, 3])
    let result = _internal_updateJerkgramChatListFilterOrder(account: account, ids: [3, 0, 2], proposal: proposal).value
    check(result.map { $0.id } == native, "stale Done handlers must complete with native filters")
}
check(transaction.writes == 0 && transaction.nativeWrites == 0, "disabled proposals must write neither order domain")
let readsBeforePrune = transaction.reads
jerkgramPruneDefaultFolderOrder(transaction: transaction, old: transaction.filters, new: [.allChats, .folder(2)])
check(transaction.reads == readsBeforePrune && transaction.writes == 0, "disabled prune must not even read saved local order")
private let retained = transaction.entries[PreferencesKeys.jerkgramDefaultFolderOrder]!.get(JerkgramDefaultFolderOrder.self)!
check(try! JSONEncoder().encode(retained) == savedBytes, "saved local preference must remain unchanged")
check(defaults.bool(forKey: storedKey), "no fixture operation may clear persisted true")
check(defaults.object(forKey: falseKey) as? Bool == false, "stored false must not be removed")
print("beta2 recovery production policy/snapshot/transaction/prune fixtures passed")
