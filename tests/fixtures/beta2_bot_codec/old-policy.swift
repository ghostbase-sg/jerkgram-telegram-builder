// Foundation-only policy is also compiled verbatim by the focused native fixtures.
struct BotBridgeCursor: Codable, Equatable {
    let pts: Int32
    let qts: Int32
    let date: Int32
    let seq: Int32

    var isValid: Bool { return pts >= 0 && qts >= 0 && date >= 0 && seq >= 0 }

    func candidate(unread: Int32) -> BotBridgeCursor? {
        guard isValid, unread > 0, pts > 1 else { return nil }
        return BotBridgeCursor(pts: Int32(max(1, Int64(pts) - Int64(unread))), qts: qts, date: date, seq: seq)
    }

    func advances(_ previous: BotBridgeCursor) -> Bool {
        return isValid && self != previous && pts >= previous.pts && qts >= previous.qts && date >= previous.date && seq >= previous.seq
    }
}

enum BotBridgeHistoryReason: String, Codable {
    case completed, noCandidate, tooLong, limit, deadline, clockChanged, corrupt
    case nonadvancing, rpcError, timeout, cancelled, replaced, loggedOut, softReset, interruptedState
}

enum BotBridgeHistoryRequest: Equatable {
    case state
    case difference(BotBridgeCursor)
}

struct BotBridgeHistoryProgress: Codable, Equatable {
    static let maxDeleteIdsPerPage = 20000
    let schema: Int
    let owner: Int64
    let peer: Int64
    let testing: Bool
    let generation: String
    var started: Double?
    var deadline: Double?
    var lastWall: Double?
    var original: BotBridgeCursor?
    var candidate: BotBridgeCursor?
    var next: BotBridgeCursor?
    var reservedState = false
    var reservedPages = 0
    var committedPages = 0
    var examined = 0
    var inserted = 0
    var insertedPeers = 0
    var insertedUsers = 0
    var insertedChats = 0
    var deleteIdsObserved = 0
    var skipped = 0
    var unsupported = 0
    var deletions = 0
    var missingReferences = 0
    var terminal: BotBridgeHistoryReason?

    init(owner: Int64, peer: Int64, testing: Bool, generation: String) {
        self.schema = 1
        self.owner = owner
        self.peer = peer
        self.testing = testing
        self.generation = generation
    }

    var isValid: Bool {
        guard schema == 1, !generation.isEmpty, generation.utf8.count <= 64,
            reservedPages >= 0, reservedPages <= 32, committedPages >= 0, committedPages <= reservedPages,
            examined >= 0, examined <= 20000, inserted >= 0, inserted <= examined,
            insertedPeers >= 0, insertedPeers <= 320000, insertedUsers >= 0, insertedUsers <= 320000, insertedChats >= 0, insertedChats <= 320000, insertedUsers + insertedChats == insertedPeers,
            deleteIdsObserved >= 0, deleteIdsObserved <= 640001,
            skipped >= 0, skipped <= examined, unsupported >= 0, unsupported <= 800000,
            deletions >= 0, deletions <= 320000, missingReferences >= 0, missingReferences <= 3200000 else { return false }
        if let started = started {
            guard started.isFinite, let deadline = deadline, deadline.isFinite, deadline == started + 120,
                let lastWall = lastWall, lastWall.isFinite, lastWall >= started, reservedState else { return false }
        } else if deadline != nil || lastWall != nil || reservedState || original != nil || candidate != nil || next != nil || reservedPages != 0 || committedPages != 0 {
            return false
        }
        if let original = original {
            guard original.isValid, reservedState else { return false }
            if let candidate = candidate {
                guard candidate.isValid, candidate.pts >= 1, candidate.pts <= original.pts,
                    candidate.qts == original.qts, candidate.date == original.date, candidate.seq == original.seq,
                    let next = next, next.isValid, next.pts >= candidate.pts,
                    next.qts >= candidate.qts, next.date >= candidate.date, next.seq >= candidate.seq else { return false }
            } else if next != nil || terminal != .noCandidate { return false }
        } else if candidate != nil || next != nil || reservedPages != 0 || committedPages != 0 { return false }
        return true
    }

    mutating func checkTime(now: Double) -> Bool {
        guard terminal == nil else { return false }
        guard isValid, now.isFinite else { terminal = .corrupt; return false }
        if let lastWall = lastWall, now < lastWall { terminal = .clockChanged; return false }
        if let deadline = deadline, now >= deadline { terminal = .deadline; return false }
        if started != nil { lastWall = now }
        return true
    }

    // Called only inside the preference transaction, before subscribing to Network.
    // A reservation survives a crash; page commits are a different counter.
    mutating func reserve(now: Double) -> BotBridgeHistoryRequest? {
        guard checkTime(now: now) else { return nil }
        if original == nil {
            guard !reservedState else { terminal = .interruptedState; return nil }
            started = now
            deadline = now + 120
            lastWall = now
            reservedState = true
            return .state
        }
        guard let next = next else { terminal = .corrupt; return nil }
        guard reservedPages < 32 else { terminal = .limit; return nil }
        reservedPages += 1
        return .difference(next)
    }

    mutating func acceptState(_ cursor: BotBridgeCursor, unread: Int32, now: Double) -> Bool {
        guard checkTime(now: now), original == nil, reservedState, cursor.isValid, unread >= 0 else {
            if terminal == nil { terminal = .corrupt }
            return false
        }
        original = cursor
        candidate = cursor.candidate(unread: unread)
        next = candidate
        if candidate == nil { terminal = .noCandidate }
        return true
    }

    static func withinPageBounds(messages: Int, peers: Int, updates: Int, examined: Int) -> Bool {
        return messages >= 0 && messages <= 5000 && peers >= 0 && peers <= 10000 && updates >= 0 && updates <= 10000 && examined >= 0 && examined <= 20000 && messages <= 20000 - examined
    }

    mutating func commit(next cursor: BotBridgeCursor, final: Bool, examined pageExamined: Int, inserted pageInserted: Int, peers: Int, users: Int = 0, skipped pageSkipped: Int, unsupported pageUnsupported: Int, deletions pageDeletions: Int, missing: Int, now: Double) -> Bool {
        guard checkTime(now: now), let previous = next, committedPages < reservedPages else {
            if terminal == nil { terminal = .corrupt }
            return false
        }
        guard cursor.isValid, cursor.pts >= previous.pts, cursor.qts >= previous.qts, cursor.date >= previous.date, cursor.seq >= previous.seq,
            final || cursor.advances(previous) else { terminal = .nonadvancing; return false }
        guard Self.withinPageBounds(messages: pageExamined, peers: peers, updates: 0, examined: examined),
            pageInserted >= 0, pageInserted <= pageExamined, users >= 0, users <= peers, pageSkipped >= 0, pageSkipped <= pageExamined,
            pageUnsupported >= 0, pageUnsupported <= 25000, pageDeletions >= 0, pageDeletions <= 10000,
            missing >= 0, missing <= 100000 else { terminal = .limit; return false }
        next = cursor
        committedPages += 1
        examined += pageExamined
        inserted += pageInserted
        insertedPeers += peers
        insertedUsers += users
        insertedChats += peers - users
        skipped += pageSkipped
        unsupported += pageUnsupported
        deletions += pageDeletions
        missingReferences += missing
        if final { terminal = .completed }
        return true
    }
}

// Transactions use this token too: queue teardown cannot admit a stale page.
final class BotBridgeLifetime {
    private let lock = NSLock()
    private var active = true
    var isActive: Bool { lock.lock(); defer { lock.unlock() }; return active }
    func cancel() { lock.lock(); active = false; lock.unlock() }
}

final class BotBridgeOnceGate {
    private let lock = NSLock()
    private var open = true
    var isOpen: Bool { lock.lock(); defer { lock.unlock() }; return open }
    @discardableResult func finish() -> Bool {
        lock.lock(); defer { lock.unlock() }
        guard open else { return false }
        open = false
        return true
    }
}
