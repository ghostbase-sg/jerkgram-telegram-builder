import Foundation
import Postbox
import SwiftSignalKit
internal import TelegramApi

// MARK: Jerkgram PROFILE_TIME_MACHINE_OBSERVER_V1
// Foundation only: no UI/polling/notification/premium changes. Actual received
// values are observed, never inferred server-change times or continuous presence.
public enum JerkgramProfileObserverStorageStatus: Equatable {
    case unregistered
    case opening
    case ready
    case failed(operation: String, sqliteCode: Int32)
    case stopped
}

struct JerkgramProfileObserverPublicName {
    let firstName: String
    let lastName: String
}

private struct JerkgramProfileObserverEvent {
    let user: TelegramUser?
    let peerId: Int64
    let publicName: JerkgramProfileObserverPublicName?
    let about: String?
    let aboutObserved: Bool
    let presence: TelegramUserPresence?
    let enroll: Bool
    let observedAtMs: Int64
    let source: String
}

private final class JerkgramProfileObserverCancellation {
    private let lock = NSLock()
    private var cancelled = false
    func cancel() { self.lock.lock(); self.cancelled = true; self.lock.unlock() }
    var isCancelled: Bool {
        self.lock.lock(); defer { self.lock.unlock() }
        return self.cancelled
    }
}

private final class JerkgramProfileObserverSession {
    weak var account: Account?
    let accountPeerId: Int64
    let queue = DispatchQueue(label: "com.jerkgram.profile-observer.store", qos: .utility)
    let admission = JerkgramProfileObserverAdmission<JerkgramProfileObserverEvent>()
    let ready = ValuePromise<Bool>(false, ignoreRepeated: true)
    let newWatches = ValuePipe<PeerId>()
    let storageStatus = ValuePromise<JerkgramProfileObserverStorageStatus>(.opening, ignoreRepeated: true)
    private let path: String
    private let key: Data
    private let lifecycle = NSLock()
    private var running = false
    private var generation: UInt64 = 0
    // Confined to queue. No global/shared Postbox connection or SQLCipher PRAGMA.
    private var store: JerkgramProfileHistoryStore?
    private var pendingGap = 0
    private var didLogGapFailure = false

    init(account: Account, key: Data) {
        self.account = account
        self.accountPeerId = account.peerId.toInt64()
        self.path = account.basePath
        self.key = key
    }

    func start() {
        self.lifecycle.lock()
        guard !self.running else { self.lifecycle.unlock(); return }
        self.running = true
        let generation = self.admission.start()
        self.generation = generation
        self.queue.async { [weak self] in
            guard let self, self.admission.isCurrent(generation) else { return }
            self.storageStatus.set(.opening)
            let store = JerkgramProfileHistoryStore(accountPath: self.path, accountPeerId: self.accountPeerId, keyData: self.key)
            guard store.open() else {
                self.initializationFailed(store: store, generation: generation)
                return
            }
            self.store = store
            // Preserve original stores/writers. Loading stays true until all
            // migrated watch IDs are restored; ready gates BIO requests.
            let migrated = store.migrateLegacy(defaults: .standard)
            var observerMigrated = true
            if let support = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first {
                let legacy = support.appendingPathComponent("Jerkgram/ProfileTimeMachine/observer-v1.sqlite").path
                if FileManager.default.fileExists(atPath: legacy) { observerMigrated = store.migrateLegacyObserver(databasePath: legacy) }
            }
            store.enumerateWatched { peerId in self.admission.addWatched(peerId) }
            guard migrated && observerMigrated && store.status == "ready" else {
                self.initializationFailed(store: store, generation: generation)
                return
            }
            guard self.admission.isCurrent(generation) else { store.close(); self.store = nil; return }
            self.admission.loaded(generation: generation)
            self.flushGap(store: store)
            if self.pendingGap == 0 {
                self.storageStatus.set(.ready)
                self.ready.set(true)
            }
        }
        self.lifecycle.unlock()
    }

    private func initializationFailed(store: JerkgramProfileHistoryStore, generation: UInt64) {
        let operation = store.status
        let code = store.lastSQLiteCode
        self.lifecycle.lock()
        if self.generation == generation {
            self.running = false
            self.addGap(self.admission.stop())
        }
        self.lifecycle.unlock()
        store.close()
        self.store = nil
        self.ready.set(false)
        self.storageStatus.set(.failed(operation: operation, sqliteCode: code))
        // No IDs, profile contents, paths or encryption material in diagnostics.
        NSLog("[Jerkgram Profile Observer] storage initialization failed: %@ (%d)", operation, code)
    }

    func stop() {
        self.lifecycle.lock()
        self.running = false
        let cancelled = self.admission.stop()
        // Serialize close before another start can enqueue a fresh open.
        self.queue.async {
            self.ready.set(false)
            self.storageStatus.set(.stopped)
            self.addGap(cancelled)
            if let store = self.store { self.flushGap(store: store) }
            self.store?.close()
            self.store = nil
        }
        self.lifecycle.unlock()
    }

    func token() -> UInt64 {
        self.lifecycle.lock(); defer { self.lifecycle.unlock() }
        return self.generation
    }

    func submit(user: TelegramUser?, peerId: PeerId, publicName: JerkgramProfileObserverPublicName? = nil, about: String? = nil,
                aboutObserved: Bool = false, presence: TelegramUserPresence? = nil,
                enroll: Bool = false, generation expectedGeneration: UInt64? = nil, source: String) {
        guard peerId.toInt64() != self.accountPeerId,
              peerId.namespace == Namespaces.Peer.CloudUser else { return }
        let generation = expectedGeneration ?? self.token()
        let schedule = self.admission.enqueue(peerId: peerId.toInt64(), enroll: enroll, generation: generation) {
            JerkgramProfileObserverEvent(user: user, peerId: peerId.toInt64(), publicName: publicName, about: about,
                aboutObserved: aboutObserved, presence: presence, enroll: enroll,
                observedAtMs: Int64(Date().timeIntervalSince1970 * 1000), source: source)
        }
        if schedule { self.queue.async { [weak self] in self?.drain(generation: generation) } }
    }

    private func drain(generation: UInt64) {
        guard self.admission.isCurrent(generation), let store else { return }
        // One bounded FIFO; serialize at most64 observations per utility task.
        // take() clears the scheduled flag only on the empty transition.
        for _ in 0..<64 {
            guard let event = self.admission.take(generation: generation) else {
                self.persistGap(generation: generation, store: store)
                return
            }
            guard self.admission.isCurrent(generation) else { return }
            let wasWatched = store.isWatched(peerId: event.peerId)
            guard wasWatched || event.enroll else { continue } // Bloom false positive
            if let presence = event.presence {
                self.persistPresence(presence, event: event, store: store)
                continue
            }
            guard let user = event.user else { continue }
            var fields = self.fields(user)
            if let publicName = event.publicName {
                fields["publicFirstName"] = JerkgramProfileFieldValue(value: publicName.firstName.isEmpty ? nil : publicName.firstName)
                fields["publicLastName"] = JerkgramProfileFieldValue(value: publicName.lastName.isEmpty ? nil : publicName.lastName)
            }
            if event.aboutObserved { fields["about"] = JerkgramProfileFieldValue(value: event.about) }
            let success = store.observe(JerkgramProfileObservation(peerId: event.peerId, fields: fields,
                observedAtMs: event.observedAtMs, source: event.source), enroll: event.enroll)
            if !success { self.addGap(1) }
            if event.enroll {
                _ = store.migrateLegacy(defaults: .standard, peerId: event.peerId)
                if success && !wasWatched, self.admission.isCurrent(generation) {
                    self.newWatches.putNext(user.id)
                }
            }
        }
        self.persistGap(generation: generation, store: store)
        self.queue.async { [weak self] in self?.drain(generation: generation) }
    }

    private func persistGap(generation: UInt64, store: JerkgramProfileHistoryStore) {
        self.addGap(self.admission.takeDropped(generation: generation))
        self.flushGap(store: store)
    }

    private func addGap(_ count: Int) {
        self.pendingGap = self.pendingGap > Int.max - count ? Int.max : self.pendingGap + count
    }

    private func flushGap(store: JerkgramProfileHistoryStore) {
        guard self.pendingGap > 0 else { return }
        if store.recordGap(droppedCount: self.pendingGap, observedAtMs: Int64(Date().timeIntervalSince1970 * 1000)) {
            self.pendingGap = 0
            self.didLogGapFailure = false
            if self.admission.isCurrent(self.token()) {
                self.storageStatus.set(.ready)
                self.ready.set(true)
            }
        } else if !self.didLogGapFailure {
            self.storageStatus.set(.failed(operation: "capture-gap-pending", sqliteCode: store.lastSQLiteCode))
            self.didLogGapFailure = true
            NSLog("[Jerkgram Profile Observer] history capture gap pending; storage unavailable")
        }
    }

    private func canonical<T: Encodable>(_ value: T) -> String? {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        return (try? encoder.encode(value)).flatMap { String(data: $0, encoding: .utf8) }
    }

    private func fields(_ user: TelegramUser) -> [String: JerkgramProfileFieldValue] {
        var fields: [String: JerkgramProfileFieldValue] = [:]
        func put(_ key: String, _ value: String?) { fields[key] = JerkgramProfileFieldValue(value: value) }
        put("firstName", user.firstName)
        put("lastName", user.lastName)
        put("username", user.username)
        // Length-delimited canonical JSON; no delimiter collisions/reflection.
        put("usernames", self.canonical(user.usernames.map { ["flags": String($0.flags.rawValue), "username": $0.username] }))
        put("avatar", self.canonical(user.photo.map { [
            "resourceId": $0.resource.id.stringRepresentation,
            "width": String($0.dimensions.width), "height": String($0.dimensions.height),
            "hasVideo": String($0.hasVideo), "isPersonal": String($0.isPersonal)
        ] }))
        put("emojiStatus", user.emojiStatus.flatMap { self.canonical($0) })
        put("premium", user.isPremium ? "true" : "false")
        switch user.nameColor {
        case let .preset(color)?: put("nameColor", "preset:\(color.rawValue)")
        case let .collectible(color)?: put("nameColor", self.canonical(color))
        case nil: put("nameColor", nil)
        }
        put("backgroundEmojiId", user.backgroundEmojiId.map { String($0) })
        put("profileColor", user.profileColor.map { String($0.rawValue) })
        put("profileBackgroundEmojiId", user.profileBackgroundEmojiId.map { String($0) })
        put("verificationIconFileId", user.verificationIconFileId.map { String($0) })
        return fields
    }

    private func persistPresence(_ presence: TelegramUserPresence, event: JerkgramProfileObserverEvent,
                                 store: JerkgramProfileHistoryStore) {
        // Semantic precision only: never derive offline from absence of updates.
        let status: String
        let hidden: Bool
        let until: Int32?
        switch presence.status {
        case .none: status = "none"; hidden = false; until = nil
        case let .present(value):
            status = Int64(value) > event.observedAtMs / 1000 ? "online" : "lastSeen"
            hidden = false; until = value
        case let .recently(value): status = "recently"; hidden = value; until = nil
        case let .lastWeek(value): status = "lastWeek"; hidden = value; until = nil
        case let .lastMonth(value): status = "lastMonth"; hidden = value; until = nil
        }
        if !store.observePresence(peerId: event.peerId, status: status, isHidden: hidden,
                until: until, lastActivity: presence.lastActivity, observedAtMs: event.observedAtMs) {
            self.addGap(1)
        }
    }

    func checkWatched(peerId: PeerId) -> Signal<Bool, NoError> {
        return Signal { [weak self] subscriber in
            guard let self else { subscriber.putNext(false); subscriber.putCompletion(); return EmptyDisposable }
            let cancellation = JerkgramProfileObserverCancellation()
            let generation = self.token()
            self.queue.async { [weak self] in
                guard !cancellation.isCancelled else { return }
                guard let self, self.admission.isCurrent(generation) else {
                    subscriber.putNext(false); subscriber.putCompletion(); return
                }
                subscriber.putNext(self.store?.isWatched(peerId: peerId.toInt64()) ?? false)
                subscriber.putCompletion()
            }
            return ActionDisposable { cancellation.cancel() }
        }
    }
}

private final class JerkgramProfileObserverRegistry {
    static let shared = JerkgramProfileObserverRegistry()
    private let lock = NSLock()
    private var sessions: [Int64: JerkgramProfileObserverSession] = [:]

    func register(account: Account, key: Data) {
        guard !account.supplementary, key.count == 32 else { return }
        self.lock.lock()
        let dead = self.sessions.filter { $0.value.account == nil }.map { $0.key }
        let stale = dead.compactMap { self.sessions.removeValue(forKey: $0) }
        let old = self.sessions[account.peerId.toInt64()]
        let session: JerkgramProfileObserverSession
        if let old, old.account === account { session = old } else {
            session = JerkgramProfileObserverSession(account: account, key: key)
            self.sessions[account.peerId.toInt64()] = session
        }
        self.lock.unlock()
        for session in stale { session.stop() }
        if old !== session { old?.stop() }
        session.start()
    }

    func session(accountPeerId: PeerId) -> JerkgramProfileObserverSession? {
        self.lock.lock(); defer { self.lock.unlock() }
        guard let session = self.sessions[accountPeerId.toInt64()], session.account != nil else { return nil }
        return session
    }
    func session(account: Account) -> JerkgramProfileObserverSession? {
        guard let session = self.session(accountPeerId: account.peerId), session.account === account else { return nil }
        return session
    }
}

func jerkgramProfileObserverRegister(account: Account, encryptionParameters: ValueBoxEncryptionParameters) {
    JerkgramProfileObserverRegistry.shared.register(account: account, key: encryptionParameters.key.data)
}
public func jerkgramProfileObserverStop(account: Account) {
    JerkgramProfileObserverRegistry.shared.session(account: account)?.stop()
}
func jerkgramProfileObserverReady(account: Account) -> Signal<Bool, NoError> {
    guard let session = JerkgramProfileObserverRegistry.shared.session(account: account) else { return .single(false) }
    session.start()
    return session.ready.get()
}
func jerkgramProfileObserverNewWatches(account: Account) -> Signal<PeerId, NoError> {
    return JerkgramProfileObserverRegistry.shared.session(account: account)?.newWatches.signal() ?? .complete()
}
func jerkgramProfileObserverMightWatch(accountPeerId: PeerId, peerId: PeerId) -> Bool {
    return JerkgramProfileObserverRegistry.shared.session(accountPeerId: accountPeerId)?.admission.mightWatch(peerId.toInt64(), includeLoading: true) ?? false
}
func jerkgramProfileObserverMightWatch(account: Account, peerId: PeerId) -> Bool {
    return JerkgramProfileObserverRegistry.shared.session(account: account)?.admission.mightWatch(peerId.toInt64(), includeLoading: true) ?? false
}
func jerkgramProfileObserverCheckWatched(account: Account, peerId: PeerId) -> Signal<Bool, NoError> {
    return JerkgramProfileObserverRegistry.shared.session(account: account)?.checkWatched(peerId: peerId) ?? .single(false)
}

public func jerkgramProfileObserverBegin(account: Account, peerId: PeerId) {
    guard peerId != account.peerId, peerId.namespace == Namespaces.Peer.CloudUser,
          let session = JerkgramProfileObserverRegistry.shared.session(account: account) else { return }
    session.start()
    let generation = session.token()
    // Use the current Postbox owner, not a potentially stale UI EnginePeer.
    _ = account.postbox.transaction { transaction -> TelegramUser? in
        return transaction.getPeer(peerId) as? TelegramUser
    }.start(next: { [weak session] user in
        guard let session, let user else { return }
        session.submit(user: user, peerId: peerId, enroll: true, generation: generation, source: "profile_open")
    })
}
func jerkgramProfileObserverUpdatedPeers(transaction: Transaction, accountPeerId: PeerId, peers: AccumulatedPeers, excludingPeerId: PeerId? = nil) {
    guard let session = JerkgramProfileObserverRegistry.shared.session(accountPeerId: accountPeerId),
          session.admission.hasCandidates else { return }
    // Empty API placeholders are not observed deletions. Min users are partial;
    // wait for a real identity update/full response rather than invent fields.
    // No new array/captured batch, task, projection, Date or I/O for unrelated IDs.
    for (peerId, apiUser) in peers.users {
        guard peerId != excludingPeerId,
              session.admission.mightWatch(peerId.toInt64(), includeLoading: true) else { continue }
        switch apiUser {
        case let .user(data):
            guard data.flags & (1 << 20) == 0 else { continue }
        case .userEmpty: continue
        }
        // Observe the effective native merge, after updatePeersCustom, rather
        // than a parsed intermediate that can differ for contact/min identities.
        guard let user = transaction.getPeer(peerId) as? TelegramUser else { continue }
        session.submit(user: user, peerId: peerId, source: "merged_peer")
    }
}
func jerkgramProfileObserverUpdatedUser(accountPeerId: PeerId, user: TelegramUser, publicName: JerkgramProfileObserverPublicName? = nil) {
    JerkgramProfileObserverRegistry.shared.session(accountPeerId: accountPeerId)?.submit(user: user, peerId: user.id, publicName: publicName, source: "peer_update")
}
func jerkgramProfileObserverFullUser(accountPeerId: PeerId, user: TelegramUser, about: String?) {
    JerkgramProfileObserverRegistry.shared.session(accountPeerId: accountPeerId)?.submit(user: user, peerId: user.id, about: about, aboutObserved: true, source: "full_user")
}
func jerkgramProfileObserverPresence(accountPeerId: PeerId, peerId: PeerId, presence: TelegramUserPresence) {
    JerkgramProfileObserverRegistry.shared.session(accountPeerId: accountPeerId)?.submit(user: nil, peerId: peerId, presence: presence, source: "presence_update")
}

public func jerkgramProfileObserverStorageStatus(account: Account) -> Signal<JerkgramProfileObserverStorageStatus, NoError> {
    return JerkgramProfileObserverRegistry.shared.session(account: account)?.storageStatus.get() ?? .single(.unregistered)
}
