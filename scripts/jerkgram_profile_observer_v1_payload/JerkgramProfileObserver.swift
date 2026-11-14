import Foundation
import Postbox
import sqlcipher

// MARK: Jerkgram PROFILE_TIME_MACHINE_OBSERVER_V1
// An opt-in, event-driven, off-main observer. Presence never creates profile snapshots.
// Only the first opening of a user profile enrolls that peer for the current account.
// All SQLite access and serialization stays on this single utility queue.

private struct JerkgramProfileObserverKey: Hashable {
    let accountPeerId: Int64
    let peerId: Int64
}

private struct JerkgramProfileObserverFields: Codable, Equatable {
    var displayName: String
    var username: String?
    var usernames: String
    var about: String?
    var aboutObserved: Bool
    var avatarResourceId: String?
    var emojiStatus: String
    var premium: Bool
    var profileColor: String?
    var profileBackgroundEmojiId: Int64?

    init(user: TelegramUser) {
        self.displayName = user.nameOrPhone
        self.username = user.addressName
        self.usernames = user.usernames.map {
            "\($0.flags.rawValue):\($0.username)"
        }.joined(separator: "|")
        self.about = nil
        self.aboutObserved = false
        self.avatarResourceId = user.profileImageRepresentations.last?.resource.id.stringRepresentation
        self.emojiStatus = String(describing: user.emojiStatus)
        self.premium = user.isPremium
        self.profileColor = user.profileColor.map { String(describing: $0) }
        self.profileBackgroundEmojiId = user.profileBackgroundEmojiId
    }

    func mergingIdentity(_ other: JerkgramProfileObserverFields) -> Self {
        var result = other
        result.about = self.about
        result.aboutObserved = self.aboutObserved
        return result
    }

    func changedKeys(since old: Self?) -> [String] {
        guard let old else { return ["baseline"] }
        var result: [String] = []
        if old.displayName != self.displayName { result.append("displayName") }
        if old.username != self.username { result.append("username") }
        if old.usernames != self.usernames { result.append("usernames") }
        if (old.aboutObserved != self.aboutObserved)
            || (self.aboutObserved && old.about != self.about) { result.append("about") }
        if old.avatarResourceId != self.avatarResourceId { result.append("avatar") }
        if old.emojiStatus != self.emojiStatus { result.append("emojiStatus") }
        if old.premium != self.premium { result.append("premium") }
        if old.profileColor != self.profileColor { result.append("profileColor") }
        if old.profileBackgroundEmojiId != self.profileBackgroundEmojiId {
            result.append("profileBackgroundEmojiId")
        }
        return result
    }
}

private let jerkgramProfileSQLiteTransient = unsafeBitCast(
    -1, to: sqlite3_destructor_type.self
)

private final class JerkgramProfileObserver {
    static let shared = JerkgramProfileObserver()

    private let queue = DispatchQueue(
        label: "com.jerkgram.profile-time-machine.observer",
        qos: .utility
    )
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    private var connection: OpaquePointer?
    private var didAttemptOpen = false
    private var didLogError = false
    private var watched = Set<JerkgramProfileObserverKey>()
    // Only the most recently touched states are retained in RAM. Disk history
    // itself is not capped by an arbitrary event count.
    private var stateCache: [JerkgramProfileObserverKey: JerkgramProfileObserverFields] = [:]
    private let maximumCachedStates = 256

    private init() {}

    deinit {
        if let connection {
            sqlite3_close(connection)
        }
    }

    private func logStorageErrorOnce(_ operation: String) {
        guard !self.didLogError else { return }
        self.didLogError = true
        NSLog("[Jerkgram Profile Observer] storage operation failed: %@", operation)
    }

    private func runSQL(_ sql: String) -> Bool {
        guard let connection else { return false }
        return sqlite3_exec(connection, sql, nil, nil, nil) == SQLITE_OK
    }

    private func prepare(_ sql: String) -> OpaquePointer? {
        guard let connection else { return nil }
        var statement: OpaquePointer?
        guard sqlite3_prepare_v2(connection, sql, -1, &statement, nil) == SQLITE_OK else {
            self.logStorageErrorOnce("prepare")
            return nil
        }
        return statement
    }

    private func bind(_ value: Int64, at index: Int32, in statement: OpaquePointer?) {
        sqlite3_bind_int64(statement, index, value)
    }

    private func bind(_ value: String, at index: Int32, in statement: OpaquePointer?) {
        value.withCString { cString in
            sqlite3_bind_text(statement, index, cString, -1, jerkgramProfileSQLiteTransient)
        }
    }

    private func bind(_ value: Data, at index: Int32, in statement: OpaquePointer?) {
        value.withUnsafeBytes { bytes in
            sqlite3_bind_blob(
                statement,
                index,
                bytes.baseAddress,
                Int32(bytes.count),
                jerkgramProfileSQLiteTransient
            )
        }
    }

    private func openIfNeeded() -> Bool {
        if self.didAttemptOpen { return self.connection != nil }
        self.didAttemptOpen = true

        guard let support = FileManager.default.urls(
            for: .applicationSupportDirectory, in: .userDomainMask
        ).first else { return false }

        let directory = support
            .appendingPathComponent("Jerkgram", isDirectory: true)
            .appendingPathComponent("ProfileTimeMachine", isDirectory: true)

        do {
            try FileManager.default.createDirectory(
                at: directory,
                withIntermediateDirectories: true,
                attributes: [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication]
            )
            var resourceValues = URLResourceValues()
            resourceValues.isExcludedFromBackup = true
            var mutableDirectory = directory
            try? mutableDirectory.setResourceValues(resourceValues)
        } catch {
            self.logStorageErrorOnce("directory")
            return false
        }

        let databaseURL = directory.appendingPathComponent("observer-v1.sqlite")
        var opened: OpaquePointer?
        let flags = SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_FULLMUTEX
        guard sqlite3_open_v2(databaseURL.path, &opened, flags, nil) == SQLITE_OK,
              let opened else {
            if let opened { sqlite3_close(opened) }
            self.logStorageErrorOnce("open")
            return false
        }
        self.connection = opened
        try? FileManager.default.setAttributes(
            [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication],
            ofItemAtPath: databaseURL.path
        )
        sqlite3_busy_timeout(opened, 2000)
        guard self.runSQL("PRAGMA journal_mode=WAL"),
              self.runSQL("PRAGMA synchronous=NORMAL"),
              self.runSQL("""
                  CREATE TABLE IF NOT EXISTS watched (
                      account_id INTEGER NOT NULL,
                      peer_id INTEGER NOT NULL,
                      started_at_ms INTEGER NOT NULL,
                      state BLOB NOT NULL,
                      PRIMARY KEY (account_id, peer_id)
                  )
                  """),
              self.runSQL("""
                  CREATE TABLE IF NOT EXISTS snapshots (
                      sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                      account_id INTEGER NOT NULL,
                      peer_id INTEGER NOT NULL,
                      observed_at_ms INTEGER NOT NULL,
                      changed_keys TEXT NOT NULL,
                      state BLOB NOT NULL
                  )
                  """),
              self.runSQL("""
                  CREATE INDEX IF NOT EXISTS snapshots_peer_time
                  ON snapshots (account_id, peer_id, observed_at_ms, sequence)
                  """) else {
            self.logStorageErrorOnce("schema")
            sqlite3_close(opened)
            self.connection = nil
            return false
        }

        guard let statement = self.prepare("SELECT account_id, peer_id FROM watched") else {
            self.connection = nil
            sqlite3_close(opened)
            return false
        }
        defer { sqlite3_finalize(statement) }
        while sqlite3_step(statement) == SQLITE_ROW {
            self.watched.insert(
                JerkgramProfileObserverKey(
                    accountPeerId: sqlite3_column_int64(statement, 0),
                    peerId: sqlite3_column_int64(statement, 1)
                )
            )
        }
        return true
    }

    private func state(for key: JerkgramProfileObserverKey) -> JerkgramProfileObserverFields? {
        if let value = self.stateCache[key] { return value }
        guard let statement = self.prepare(
            "SELECT state FROM watched WHERE account_id = ? AND peer_id = ?"
        ) else { return nil }
        defer { sqlite3_finalize(statement) }
        self.bind(key.accountPeerId, at: 1, in: statement)
        self.bind(key.peerId, at: 2, in: statement)
        guard sqlite3_step(statement) == SQLITE_ROW else { return nil }
        let length = Int(sqlite3_column_bytes(statement, 0))
        guard length > 0, let pointer = sqlite3_column_blob(statement, 0) else { return nil }
        let data = Data(bytes: pointer, count: length)
        guard let value = try? self.decoder.decode(JerkgramProfileObserverFields.self, from: data) else {
            self.logStorageErrorOnce("decode")
            return nil
        }
        self.putCached(value, for: key)
        return value
    }

    private func putCached(
        _ value: JerkgramProfileObserverFields,
        for key: JerkgramProfileObserverKey
    ) {
        if self.stateCache.count >= self.maximumCachedStates,
           self.stateCache[key] == nil {
            self.stateCache.removeAll(keepingCapacity: true)
        }
        self.stateCache[key] = value
    }

    private func persist(
        key: JerkgramProfileObserverKey,
        new: JerkgramProfileObserverFields,
        old: JerkgramProfileObserverFields?,
        observedAtMs: Int64
    ) {
        let keys = new.changedKeys(since: old)
        guard !keys.isEmpty,
              let encoded = try? self.encoder.encode(new),
              self.runSQL("BEGIN IMMEDIATE") else { return }

        var success = false
        if let snapshot = self.prepare("""
            INSERT INTO snapshots (account_id, peer_id, observed_at_ms, changed_keys, state)
            VALUES (?, ?, ?, ?, ?)
            """) {
            self.bind(key.accountPeerId, at: 1, in: snapshot)
            self.bind(key.peerId, at: 2, in: snapshot)
            self.bind(observedAtMs, at: 3, in: snapshot)
            self.bind(keys.joined(separator: ","), at: 4, in: snapshot)
            self.bind(encoded, at: 5, in: snapshot)
            success = sqlite3_step(snapshot) == SQLITE_DONE
            sqlite3_finalize(snapshot)
        }
        if success, let tracked = self.prepare("""
            INSERT INTO watched (account_id, peer_id, started_at_ms, state)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(account_id, peer_id) DO UPDATE SET state = excluded.state
            """) {
            self.bind(key.accountPeerId, at: 1, in: tracked)
            self.bind(key.peerId, at: 2, in: tracked)
            self.bind(observedAtMs, at: 3, in: tracked)
            self.bind(encoded, at: 4, in: tracked)
            success = sqlite3_step(tracked) == SQLITE_DONE
            sqlite3_finalize(tracked)
        } else {
            success = false
        }

        if success && self.runSQL("COMMIT") {
            self.watched.insert(key)
            self.putCached(new, for: key)
        } else {
            _ = self.runSQL("ROLLBACK")
            self.logStorageErrorOnce("persist")
        }
    }

    private func apply(
        key: JerkgramProfileObserverKey,
        identity: JerkgramProfileObserverFields?,
        about: String?,
        aboutObserved: Bool,
        enroll: Bool,
        observedAtMs: Int64
    ) {
        guard self.openIfNeeded() else { return }
        guard enroll || self.watched.contains(key) else { return }
        let previous = self.watched.contains(key) ? self.state(for: key) : nil
        // Fail closed if a watched row exists but its last state is unreadable.
        if self.watched.contains(key) && previous == nil { return }
        guard var next = previous ?? identity else { return }
        if let identity {
            next = next.mergingIdentity(identity)
        }
        if aboutObserved {
            next.about = about
            next.aboutObserved = true
        }
        if next == previous { return }
        self.persist(key: key, new: next, old: previous, observedAtMs: observedAtMs)
    }

    func begin(accountPeerId: PeerId, user: TelegramUser, cachedData: CachedPeerData?) {
        guard accountPeerId != user.id else { return }
        let key = JerkgramProfileObserverKey(
            accountPeerId: accountPeerId.toInt64(),
            peerId: user.id.toInt64()
        )
        let identity = JerkgramProfileObserverFields(user: user)
        let knownAbout = cachedData as? CachedUserData
        let now = Int64(Date().timeIntervalSince1970 * 1000)
        self.queue.async {
            self.apply(
                key: key,
                identity: identity,
                about: knownAbout?.about,
                aboutObserved: knownAbout != nil,
                enroll: true,
                observedAtMs: now
            )
        }
    }

    func updatedPeers(
        accountPeerId: PeerId,
        peers: [Peer],
        excludingPeerId: PeerId?
    ) {
        guard !peers.isEmpty else { return }
        let accountId = accountPeerId.toInt64()
        let excluded = excludingPeerId?.toInt64()
        let now = Int64(Date().timeIntervalSince1970 * 1000)
        self.queue.async {
            guard self.openIfNeeded(), !self.watched.isEmpty else { return }
            for peer in peers {
                guard let user = peer as? TelegramUser else { continue }
                let peerId = user.id.toInt64()
                if peerId == excluded { continue }
                let key = JerkgramProfileObserverKey(accountPeerId: accountId, peerId: peerId)
                guard self.watched.contains(key) else { continue }
                self.apply(
                    key: key,
                    identity: JerkgramProfileObserverFields(user: user),
                    about: nil,
                    aboutObserved: false,
                    enroll: false,
                    observedAtMs: now
                )
            }
        }
    }

    func fullUser(accountPeerId: PeerId, user: TelegramUser, about: String?) {
        let key = JerkgramProfileObserverKey(
            accountPeerId: accountPeerId.toInt64(),
            peerId: user.id.toInt64()
        )
        let identity = JerkgramProfileObserverFields(user: user)
        let now = Int64(Date().timeIntervalSince1970 * 1000)
        self.queue.async {
            self.apply(
                key: key,
                identity: identity,
                about: about,
                aboutObserved: true,
                enroll: false,
                observedAtMs: now
            )
        }
    }
}

// Called only after opening a profile. Subsequent observations are automatic
// while this process receives Telegram updates, regardless of the visible chat.
public func jerkgramProfileObserverBegin(
    accountPeerId: PeerId,
    peer: EnginePeer,
    cachedData: CachedPeerData?
) {
    guard case let .user(user) = peer else { return }
    JerkgramProfileObserver.shared.begin(
        accountPeerId: accountPeerId,
        user: user,
        cachedData: cachedData
    )
}

// TelegramCore update path: only identity/decor changes, never presence.
func jerkgramProfileObserverUpdatedPeers(
    accountPeerId: PeerId,
    peers: [Peer],
    excludingPeerId: PeerId? = nil
) {
    JerkgramProfileObserver.shared.updatedPeers(
        accountPeerId: accountPeerId,
        peers: peers,
        excludingPeerId: excludingPeerId
    )
}

// Full-user refresh combines BIO and identity into one observation.
func jerkgramProfileObserverFullUser(
    accountPeerId: PeerId,
    user: TelegramUser,
    about: String?
) {
    JerkgramProfileObserver.shared.fullUser(
        accountPeerId: accountPeerId,
        user: user,
        about: about
    )
}
