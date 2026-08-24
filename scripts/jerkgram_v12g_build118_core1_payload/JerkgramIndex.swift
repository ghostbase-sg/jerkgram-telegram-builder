import Foundation

// MARK: Jerkgram v1.2G BUILD118_REFERENCE_INDEX1
public struct JerkgramCanonicalLocator: Codable, Equatable {
    public let kind: JerkgramEventKind
    public let relativeFile: String
    public let eventId: JerkgramEventId

    public init(kind: JerkgramEventKind, relativeFile: String, eventId: JerkgramEventId) throws {
        guard !relativeFile.hasPrefix("/"), !relativeFile.split(separator: "/").contains("..") else {
            throw JerkgramCoreError.invalidRelativePath(relativeFile)
        }
        self.kind = kind
        self.relativeFile = relativeFile
        self.eventId = eventId
    }
}

public struct JerkgramTimeMachineIndexRecord: Codable, Equatable {
    public let accountPeerId: Int64
    public let chatPeerId: Int64
    public let eventId: JerkgramEventId
    public let sequence: Int64
    public let kind: JerkgramEventKind
    public let senderPeerId: Int64?
    public let observedAtMs: Int64
    public let locator: JerkgramCanonicalLocator
    public let searchKey: String

    public init(
        accountPeerId: Int64,
        chatPeerId: Int64,
        eventId: JerkgramEventId,
        sequence: Int64,
        kind: JerkgramEventKind,
        senderPeerId: Int64?,
        observedAtMs: Int64,
        locator: JerkgramCanonicalLocator,
        searchKey: String
    ) {
        self.accountPeerId = accountPeerId
        self.chatPeerId = chatPeerId
        self.eventId = eventId
        self.sequence = sequence
        self.kind = kind
        self.senderPeerId = senderPeerId
        self.observedAtMs = observedAtMs
        self.locator = locator
        self.searchKey = searchKey
    }
}
