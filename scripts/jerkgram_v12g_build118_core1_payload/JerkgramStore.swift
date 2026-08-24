import Foundation

// MARK: Jerkgram v1.2G BUILD118_EVENT_STORE1
public protocol JerkgramEventStore {
    func append(_ event: JerkgramCanonicalEvent) throws
    func events(accountPeerId: Int64, chatPeerId: Int64?) throws -> [JerkgramCanonicalEvent]
    func replaceAtomically(accountPeerId: Int64, events: [JerkgramCanonicalEvent]) throws
}

public final class JerkgramJSONLEventStore: JerkgramEventStore {
    private let rootURL: URL
    private let lock = NSLock()
    private let decoder = JSONDecoder()

    public init(rootURL: URL) {
        self.rootURL = rootURL
    }

    public func append(_ event: JerkgramCanonicalEvent) throws {
        self.lock.lock()
        defer { self.lock.unlock() }
        var current = try self.loadAccount(event.accountPeerId)
        if let existing = current.first(where: { $0.eventId == event.eventId }) {
            if existing == event {
                throw JerkgramCoreError.duplicateEvent(event.eventId)
            } else {
                throw JerkgramCoreError.conflictingEvent(event.eventId)
            }
        }
        current.append(event)
        try self.writeAccount(event.accountPeerId, events: current)
    }

    public func events(accountPeerId: Int64, chatPeerId: Int64?) throws -> [JerkgramCanonicalEvent] {
        self.lock.lock()
        defer { self.lock.unlock() }
        return try self.loadAccount(accountPeerId)
            .filter { chatPeerId == nil || $0.chatPeerId == chatPeerId }
            .sorted { lhs, rhs in
                if lhs.sequence != rhs.sequence { return lhs.sequence < rhs.sequence }
                return lhs.eventId < rhs.eventId
            }
    }

    public func replaceAtomically(accountPeerId: Int64, events: [JerkgramCanonicalEvent]) throws {
        self.lock.lock()
        defer { self.lock.unlock() }
        precondition(events.allSatisfy { $0.accountPeerId == accountPeerId })
        var identities = Set<JerkgramEventId>()
        for event in events {
            guard identities.insert(event.eventId).inserted else {
                throw JerkgramCoreError.duplicateEvent(event.eventId)
            }
        }
        try self.writeAccount(accountPeerId, events: events)
    }

    private func accountURL(_ accountPeerId: Int64) -> URL {
        return self.rootURL.appendingPathComponent("accounts", isDirectory: true)
            .appendingPathComponent(String(accountPeerId), isDirectory: true)
            .appendingPathComponent("events.jsonl", isDirectory: false)
    }

    private func loadAccount(_ accountPeerId: Int64) throws -> [JerkgramCanonicalEvent] {
        let url = self.accountURL(accountPeerId)
        guard FileManager.default.fileExists(atPath: url.path) else { return [] }
        let data = try Data(contentsOf: url)
        return try data.split(separator: 0x0a).map { line in
            let event = try self.decoder.decode(JerkgramCanonicalEvent.self, from: Data(line))
            guard event.schemaVersion == 1 else {
                throw JerkgramCoreError.unsupportedSchemaVersion(event.schemaVersion)
            }
            return event
        }
    }

    private func writeAccount(_ accountPeerId: Int64, events: [JerkgramCanonicalEvent]) throws {
        let url = self.accountURL(accountPeerId)
        try FileManager.default.createDirectory(
            at: url.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        var data = Data()
        for event in events.sorted(by: { lhs, rhs in
            if lhs.sequence != rhs.sequence { return lhs.sequence < rhs.sequence }
            return lhs.eventId < rhs.eventId
        }) {
            data.append(try encoder.encode(event))
            data.append(0x0a)
        }
        try data.write(to: url, options: .atomic)
    }
}

// Transaction boundaries call this lightweight serial recorder. The event id
// is generated once before enqueueing; equal text never participates in identity.
public enum JerkgramCaptureRecorder {
    private static let queue = DispatchQueue(label: "jerkgram.capture.recorder", qos: .utility)
    private static var sequenceCounter: Int64 = 0

    public static func record(
        accountPeerId: Int64,
        chatPeerId: Int64,
        kind: JerkgramEventKind,
        senderPeerId: Int64?,
        messageNamespace: Int32?,
        messageId: Int32?,
        observedAtMs: Int64,
        payload: JerkgramEventPayload
    ) {
        let eventId = JerkgramEventId.random()
        self.queue.async {
            self.sequenceCounter += 1
            let sequence = max(observedAtMs * 1_000, observedAtMs * 1_000 + self.sequenceCounter)
            let event = JerkgramCanonicalEvent(
                accountPeerId: accountPeerId,
                chatPeerId: chatPeerId,
                eventId: eventId,
                sequence: sequence,
                kind: kind,
                senderPeerId: senderPeerId,
                messageNamespace: messageNamespace,
                messageId: messageId,
                observedAtMs: observedAtMs,
                payload: payload
            )
            let rootURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
                .appendingPathComponent("Jerkgram", isDirectory: true)
            try? JerkgramJSONLEventStore(rootURL: rootURL).append(event)
        }
    }
}
