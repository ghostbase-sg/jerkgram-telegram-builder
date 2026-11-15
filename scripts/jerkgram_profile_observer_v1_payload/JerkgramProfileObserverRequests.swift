import Foundation
import Postbox
import SwiftSignalKit
internal import TelegramApi
import MtProtoKit

// BEGIN NATIVE REQUEST POLICY
// Pure policy: its clock is injected; no timer, API, storage or UI dependencies.
struct JerkgramProfileRequestPolicy {
    enum Outcome {
        case success
        case permanent
        case transient
        case floodWait(Double)
    }
    struct Work {
        let peerId: Int64
        let token: UInt64
        var attempts: Int
        var dirty: Bool
    }
    private struct Pending {
        let peerId: Int64
        let attempts: Int
        let notBefore: Double
    }
    var ready = false
    private(set) var foreground = false
    private(set) var dropped = 0
    private(set) var inFlight: Work?
    private var pending: [Pending] = []
    private var pendingIds = Set<Int64>()
    private var lastTimes: [Int64: Double] = [:]
    private var lastGlobal: Double?
    private var cooldown: Double = 0
    private var nextToken: UInt64 = 0
    var count: Int { self.pending.count }
    var cachedTimesCount: Int { self.lastTimes.count }

    mutating func enqueue(_ peerId: Int64) {
        if self.inFlight?.peerId == peerId {
            self.inFlight?.dirty = true
            return
        }
        self.append(peerId, attempts: 0, notBefore: 0)
    }

    private mutating func append(_ peerId: Int64, attempts: Int, notBefore: Double) {
        guard !self.pendingIds.contains(peerId) else { return }
        guard self.pending.count < 4096 else {
            self.dropped += 1
            return
        }
        self.pending.append(Pending(peerId: peerId, attempts: attempts, notBefore: notBefore))
        self.pendingIds.insert(peerId)
    }

    mutating func setForeground(_ value: Bool) {
        self.foreground = value
        if !value, let work = self.inFlight {
            self.inFlight = nil
            self.nextToken &+= 1
            self.append(work.peerId, attempts: work.attempts, notBefore: 0)
        }
    }

    func wait(now: Double) -> Double? {
        guard self.ready, self.foreground, self.inFlight == nil,
              let first = self.pending.first else { return nil }
        let due = max(
            max(self.cooldown, first.notBefore),
            max(self.lastGlobal.map { $0 + 1 } ?? 0,
                self.lastTimes[first.peerId].map { $0 + 5 } ?? 0)
        )
        return max(0, due - now)
    }

    mutating func take(now: Double) -> Work? {
        guard self.wait(now: now) == 0 else { return nil }
        let first = self.pending.removeFirst()
        self.pendingIds.remove(first.peerId)
        self.nextToken &+= 1
        let work = Work(peerId: first.peerId, token: self.nextToken, attempts: first.attempts, dirty: false)
        self.inFlight = work
        if self.lastTimes.count >= 512, self.lastTimes[first.peerId] == nil,
           let oldest = self.lastTimes.min(by: { $0.value < $1.value })?.key {
            self.lastTimes.removeValue(forKey: oldest)
        }
        self.lastTimes[first.peerId] = now
        self.lastGlobal = now
        return work
    }

    mutating func finish(token: UInt64, outcome: Outcome, now: Double) {
        guard let work = self.inFlight, work.token == token else { return }
        self.inFlight = nil
        var retryAt: Double?
        switch outcome {
        case .success, .permanent:
            break
        case .transient:
            if work.attempts < 2 { retryAt = now + Double(2 << work.attempts) }
        case let .floodWait(seconds):
            self.cooldown = max(self.cooldown, now + max(1, seconds))
            if work.attempts < 2 { retryAt = self.cooldown }
        }
        if work.dirty {
            self.append(work.peerId, attempts: 0, notBefore: retryAt ?? 0)
        } else if let retryAt {
            self.append(work.peerId, attempts: work.attempts + 1, notBefore: retryAt)
        }
    }

    static func floodWait(_ error: String) -> Double? {
        for prefix in ["FLOOD_WAIT_", "FLOOD_PREMIUM_WAIT_"] where error.hasPrefix(prefix) {
            let suffix = error.dropFirst(prefix.count)
            if let seconds = Int32(suffix), seconds >= 0 {
                return Double(seconds)
            }
        }
        return nil
    }
}
// Mutable only under the ingress Atomic lock until swap transfers exclusive
// ownership to the draining queue. Reference storage avoids cloning a growing
// Set for every incoming update batch.
final class JerkgramProfileRequestIngress<Id: Hashable> {
    private(set) var peers = Set<Id>()
    private(set) var scheduled = false
    private(set) var overflow = false

    func insert(_ peerId: Id) -> Bool {
        if self.peers.count < 4096 {
            self.peers.insert(peerId)
        } else if !self.peers.contains(peerId) {
            self.overflow = true
        }
        guard !self.scheduled else { return false }
        self.scheduled = true
        return true
    }
}
// END NATIVE REQUEST POLICY

private final class JerkgramProfileObserverRequests {
    private weak var account: Account?
    private let accountPeerId: PeerId
    private let queue = Queue(name: "Jerkgram.ProfileObserverRequests", qos: .utility)
    private let subscriptions = DisposableSet()
    private let request = MetaDisposable()
    private let ingress = Atomic<JerkgramProfileRequestIngress<PeerId>>(value: JerkgramProfileRequestIngress())
    private var wakeup: SwiftSignalKit.Timer?
    private var policy = JerkgramProfileRequestPolicy()
    private let cancelled = Atomic<Bool>(value: false)
    private var disposed = false
    private var isDisposed: Bool { self.disposed || self.cancelled.with { $0 } }
    private var overflowReported = false

    init(account: Account, inForeground: Signal<Bool, NoError>) {
        self.account = account
        self.accountPeerId = account.peerId
        self.subscriptions.add((jerkgramProfileObserverReady(account: account)
        |> deliverOn(self.queue)).start(next: { [weak self] ready in
            guard let self, !self.isDisposed else { return }
            self.policy.ready = ready
            self.pump()
        }))
        self.subscriptions.add((inForeground |> distinctUntilChanged
        |> deliverOn(self.queue)).start(next: { [weak self] foreground in
            guard let self, !self.isDisposed else { return }
            self.policy.setForeground(foreground)
            if !foreground {
                self.request.set(nil)
                self.wakeup?.invalidate()
                self.wakeup = nil
            }
            self.pump()
        }))
        self.subscriptions.add(account.stateManager.jerkgramProfileObserverInvalidatedPeerIds.start(next: { [weak self] peerIds in
            guard let self, !self.cancelled.with({ $0 }), let account = self.account else { return }
            var schedule = false
            _ = self.ingress.modify { current in
                for peerId in peerIds where peerId.namespace == Namespaces.Peer.CloudUser && peerId != account.peerId {
                    // The registry admits potential watchers while loading.
                    guard jerkgramProfileObserverMightWatch(account: account, peerId: peerId) else { continue }
                    if current.insert(peerId) { schedule = true }
                }
                return current
            }
            if schedule {
                self.queue.async { [weak self] in self?.drainInvalidations() }
            }
        }))
        self.subscriptions.add((jerkgramProfileObserverNewWatches(account: account)
        |> deliverOn(self.queue)).start(next: { [weak self] peerId in
            guard let self, !self.isDisposed else { return }
            self.enqueue(peerId)
            self.pump()
        }))
    }

    private func drainInvalidations() {
        let batch = self.ingress.swap(JerkgramProfileRequestIngress())
        guard !self.isDisposed else { return }
        for peerId in batch.peers { self.enqueue(peerId) }
        if batch.overflow { self.reportOverflow() }
        self.pump()
    }

    private func reportOverflow() {
        guard !self.overflowReported else { return }
        self.overflowReported = true
        NSLog("[Jerkgram Profile Observer] BIO invalidation queue reached its bounded capacity; some invalidations were not sampled")
    }

    private var now: Double {
        Double(DispatchTime.now().uptimeNanoseconds) / 1_000_000_000
    }

    private func enqueue(_ peerId: PeerId) {
        self.policy.enqueue(peerId.toInt64())
        if self.policy.dropped > 0 { self.reportOverflow() }
    }

    private func isCurrent(_ work: JerkgramProfileRequestPolicy.Work) -> Bool {
        !self.isDisposed && self.policy.foreground && self.policy.inFlight?.token == work.token
            && self.account?.peerId == self.accountPeerId
    }

    private func finish(_ work: JerkgramProfileRequestPolicy.Work, _ outcome: JerkgramProfileRequestPolicy.Outcome) {
        guard self.isCurrent(work) else { return }
        self.policy.finish(token: work.token, outcome: outcome, now: self.now)
        self.request.set(nil)
        self.pump()
    }

    private func pump() {
        guard !self.isDisposed, self.account != nil else { return }
        if self.policy.dropped > 0 { self.reportOverflow() }
        self.wakeup?.invalidate()
        self.wakeup = nil
        guard let wait = self.policy.wait(now: self.now) else { return }
        if wait > 0 {
            let timer = SwiftSignalKit.Timer(timeout: wait, repeat: false, completion: { [weak self] in
                self?.pump()
            }, queue: self.queue)
            self.wakeup = timer
            timer.start()
            return
        }
        guard let work = self.policy.take(now: self.now), let account = self.account else { return }
        let peerId = PeerId(work.peerId)
        self.request.set((jerkgramProfileObserverCheckWatched(account: account, peerId: peerId)
        |> take(1) |> deliverOn(self.queue)).start(next: { [weak self] watched in
            guard let self, self.isCurrent(work), let account = self.account else { return }
            guard watched else {
                self.finish(work, .permanent)
                return
            }
            self.loadInputUser(account: account, peerId: peerId, work: work)
        }))
    }

    private func loadInputUser(account: Account, peerId: PeerId, work: JerkgramProfileRequestPolicy.Work) {
        self.request.set((account.postbox.transaction { transaction -> Api.InputUser? in
            guard let user = transaction.getPeer(peerId) as? TelegramUser else { return nil }
            return apiInputUser(user, sourceMessageId: nil, transaction: transaction)
        } |> deliverOn(self.queue)).start(next: { [weak self] inputUser in
            guard let self, self.isCurrent(work), let account = self.account else { return }
            guard let inputUser else {
                self.finish(work, .permanent)
                return
            }
            self.fetch(account: account, inputUser: inputUser, peerId: peerId, work: work)
        }))
    }

    private func fetch(account: Account, inputUser: Api.InputUser, peerId: PeerId, work: JerkgramProfileRequestPolicy.Work) {
        self.request.set((account.network.request(Api.functions.users.getFullUser(id: inputUser), automaticFloodWait: false)
        |> timeout(30, queue: self.queue, alternate: .fail(MTRpcError(errorCode: -1, errorDescription: "PROFILE_OBSERVER_TIMEOUT")))
        |> deliverOn(self.queue)).start(next: { [weak self] result in
            guard let self, self.isCurrent(work), let account = self.account else { return }
            switch result {
            case let .userFull(data):
                switch data.fullUser {
                case let .userFull(full):
                    self.merge(account: account, users: data.users, about: full.about, peerId: peerId, work: work)
                }
            }
        }, error: { [weak self] error in
            guard let self, self.isCurrent(work) else { return }
            if let seconds = JerkgramProfileRequestPolicy.floodWait(error.errorDescription) {
                self.finish(work, .floodWait(seconds))
            } else if error.errorCode >= 500 || error.errorCode < 0 {
                self.finish(work, .transient)
            } else {
                self.finish(work, .permanent)
            }
        }))
    }

    private func merge(account: Account, users: [Api.User], about: String?, peerId: PeerId, work: JerkgramProfileRequestPolicy.Work) {
        // Read/merge identity using Telegram's existing parser. BIO goes only to
        // the observer; this path never modifies notification settings.
        let accountPeerId = self.accountPeerId
        let cancelled = self.cancelled
        self.request.set((account.postbox.transaction { transaction -> TelegramUser? in
            guard !cancelled.with({ $0 }),
                  let apiUser = users.first(where: { $0.peerId == peerId }),
                  let user = TelegramUser.merge(transaction.getPeer(peerId) as? TelegramUser, rhs: apiUser) else { return nil }
            updatePeersCustom(transaction: transaction, peers: [user], update: { _, updated in updated })
            return transaction.getPeer(peerId) as? TelegramUser
        } |> deliverOn(self.queue)).start(next: { [weak self] user in
            guard let self, self.isCurrent(work) else { return }
            if let user {
                jerkgramProfileObserverFullUser(accountPeerId: accountPeerId, user: user, about: about)
            }
            self.finish(work, .success)
        }))
    }

    func dispose() {
        // Cancel subscriptions immediately; serialize policy teardown with all
        // callbacks. The returned Disposable owns this manager until teardown.
        if self.cancelled.swap(true) { return }
        self.subscriptions.dispose()
        self.request.dispose()
        _ = self.ingress.swap(JerkgramProfileRequestIngress())
        if let account = self.account {
            jerkgramProfileObserverStop(account: account)
        }
        self.queue.async {
            self.disposed = true
            self.policy.setForeground(false)
            self.wakeup?.invalidate()
            self.wakeup = nil
        }
    }
}

public func jerkgramProfileObserverManage(account: Account, inForeground: Signal<Bool, NoError>) -> Disposable {
    let manager = JerkgramProfileObserverRequests(account: account, inForeground: inForeground)
    return ActionDisposable {
        manager.dispose()
    }
}

// Final-state event unions preserve the same bound as individual update batches.
func jerkgramProfileObserverUnionInvalidations(_ lhs: Set<PeerId>, _ rhs: Set<PeerId>) -> Set<PeerId> {
    if lhs.isEmpty { return rhs }
    if rhs.isEmpty { return lhs }
    var result = lhs
    var overflow = false
    for peerId in rhs where !result.contains(peerId) {
        guard result.count < 4096 else { overflow = true; break }
        result.insert(peerId)
    }
    if overflow {
        NSLog("[Jerkgram Profile Observer] merged BIO invalidation capacity reached")
    }
    return result
}
