import Foundation

// Fixed-memory membership admission plus bounded FIFO. No Telegram/SQLite/JSON
// dependencies: this exact production core is executable in the native fixture.
final class JerkgramProfileObserverAdmission<Event> {
    private let lock = NSLock()
    private var words = [UInt64](repeating: 0, count: 8192) // 64KiB/account
    private var anyWatched = false
    private var loading = true
    private var active = false
    private var generation: UInt64 = 0
    private var ring: [Event?]
    private var head = 0
    private var count = 0
    private var draining = false
    private var dropped = 0

    init(capacity: Int = 4096) {
        precondition(capacity > 0)
        self.ring = [Event?](repeating: nil, count: capacity)
    }

    @discardableResult func start() -> UInt64 {
        self.lock.lock(); defer { self.lock.unlock() }
        self.generation &+= 1
        self.active = true
        self.loading = true
        return self.generation
    }

    @discardableResult func stop() -> Int {
        self.lock.lock(); defer { self.lock.unlock() }
        let cancelled = self.count + self.dropped
        self.dropped = 0
        self.active = false
        self.generation &+= 1
        self.ring = [Event?](repeating: nil, count: self.ring.count)
        self.head = 0; self.count = 0; self.draining = false
        self.words = [UInt64](repeating: 0, count: 8192)
        self.anyWatched = false
        return cancelled
    }

    func isCurrent(_ generation: UInt64) -> Bool {
        self.lock.lock(); defer { self.lock.unlock() }
        return self.active && self.generation == generation
    }

    private func hashes(_ peerId: Int64) -> (UInt64, UInt64) {
        var x = UInt64(bitPattern: peerId) &+ 0x9e3779b97f4a7c15
        x = (x ^ (x >> 30)) &* 0xbf58476d1ce4e5b9
        x = (x ^ (x >> 27)) &* 0x94d049bb133111eb
        x ^= x >> 31
        return (x, (x >> 32) | 1)
    }

    private func addLocked(_ peerId: Int64) {
        let (first, step) = self.hashes(peerId)
        for offset in UInt64(0)..<UInt64(3) {
            let bit = Int((first &+ offset &* step) & 524287)
            self.words[bit >> 6] |= UInt64(1) << UInt64(bit & 63)
        }
        self.anyWatched = true
    }

    private func containsLocked(_ peerId: Int64) -> Bool {
        guard self.anyWatched else { return false }
        let (first, step) = self.hashes(peerId)
        for offset in UInt64(0)..<UInt64(3) {
            let bit = Int((first &+ offset &* step) & 524287)
            if self.words[bit >> 6] & (UInt64(1) << UInt64(bit & 63)) == 0 { return false }
        }
        return true
    }

    func addWatched(_ peerId: Int64) {
        self.lock.lock(); defer { self.lock.unlock() }
        self.addLocked(peerId)
    }

    func loaded(generation: UInt64) {
        self.lock.lock(); defer { self.lock.unlock() }
        if self.generation == generation { self.loading = false }
    }

    // Invalidation may arrive before disk membership has loaded. Keep only the
    // bounded invalidation ID; scheduler waits for ready + exact SQLite lookup.
    func mightWatch(_ peerId: Int64, includeLoading: Bool = false) -> Bool {
        self.lock.lock(); defer { self.lock.unlock() }
        return self.active && ((includeLoading && self.loading) || self.containsLocked(peerId))
    }

    var hasCandidates: Bool {
        self.lock.lock(); defer { self.lock.unlock() }
        return self.active && (self.loading || self.anyWatched)
    }

    // True means the caller must schedule ONE drain. make() is evaluated only
    // for admitted events and never for irrelevant traffic or a full mailbox.
    func enqueue(peerId: Int64, enroll: Bool, generation: UInt64? = nil, make: () -> Event) -> Bool {
        self.lock.lock(); defer { self.lock.unlock() }
        guard self.active, generation == nil || generation == self.generation,
              enroll || self.loading || self.containsLocked(peerId) else { return false }
        guard self.count < self.ring.count else {
            if self.dropped < Int.max { self.dropped += 1 }
            return false
        }
        if enroll { self.addLocked(peerId) }
        self.ring[(self.head + self.count) % self.ring.count] = make()
        self.count += 1
        if self.draining { return false }
        self.draining = true
        return true
    }

    func take(generation: UInt64) -> Event? {
        self.lock.lock(); defer { self.lock.unlock() }
        guard self.active, self.generation == generation else { return nil }
        guard self.count != 0 else { self.draining = false; return nil }
        let result = self.ring[self.head]
        self.ring[self.head] = nil
        self.head = (self.head + 1) % self.ring.count
        self.count -= 1
        return result
    }

    func takeDropped(generation: UInt64) -> Int {
        self.lock.lock(); defer { self.lock.unlock() }
        guard self.active, self.generation == generation else { return 0 }
        let result = self.dropped
        self.dropped = 0
        return result
    }
}
