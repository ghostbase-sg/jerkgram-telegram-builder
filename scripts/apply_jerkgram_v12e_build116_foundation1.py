#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()


def require(value, message):
    if not value:
        raise RuntimeError("[Build116 foundation] " + message)


def settings_source():
    return '''import Foundation

// MARK: Jerkgram v1.2E BUILD116_SETTINGS_FOUNDATION1
public enum JerkgramSendStyleV1: String, Codable, CaseIterable {
    case normal
    case bold
    case italic
    case monospace
    case strikethrough
    case underline
    case spoiler
}

public struct JerkgramSettingsV1: Codable, Equatable {
    public var schemaVersion: Int = 1
    public var sendStyle: JerkgramSendStyleV1
    public var saveDeletedMessages: Bool
    public var saveEditHistory: Bool
    public var portableDeletedReplies: Bool
    public var preserveDeletedMedia: Bool

    public init(
        sendStyle: JerkgramSendStyleV1 = .normal,
        saveDeletedMessages: Bool = false,
        saveEditHistory: Bool = false,
        portableDeletedReplies: Bool = false,
        preserveDeletedMedia: Bool = false
    ) {
        self.sendStyle = sendStyle
        self.saveDeletedMessages = saveDeletedMessages
        self.saveEditHistory = saveEditHistory
        self.portableDeletedReplies = portableDeletedReplies
        self.preserveDeletedMedia = preserveDeletedMedia
    }
}

public enum JerkgramSettingsStoreError: Error, Equatable {
    case unsupportedSchemaVersion(Int)
}

public final class JerkgramSettingsStore {
    private let fileURL: URL
    private let decoder = JSONDecoder()

    public init(fileURL: URL) {
        self.fileURL = fileURL
    }

    public func load() throws -> JerkgramSettingsV1 {
        guard FileManager.default.fileExists(atPath: self.fileURL.path) else {
            return JerkgramSettingsV1()
        }
        let value = try self.decoder.decode(
            JerkgramSettingsV1.self,
            from: Data(contentsOf: self.fileURL)
        )
        guard value.schemaVersion == 1 else {
            throw JerkgramSettingsStoreError.unsupportedSchemaVersion(value.schemaVersion)
        }
        return value
    }

    public func save(_ value: JerkgramSettingsV1) throws {
        guard value.schemaVersion == 1 else {
            throw JerkgramSettingsStoreError.unsupportedSchemaVersion(value.schemaVersion)
        }
        try FileManager.default.createDirectory(
            at: self.fileURL.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )
        let encoder = JSONEncoder()
        encoder.outputFormatting = JSONEncoder.OutputFormatting.sortedKeys
        try encoder.encode(value).write(to: self.fileURL, options: .atomic)
    }
}
'''


def archive_source():
    return '''import Foundation

// MARK: Jerkgram v1.2E BUILD116_ARCHIVE_FOUNDATION1
public enum JerkgramArchiveEventKindV1: String, Codable, CaseIterable {
    case profileSnapshot
    case presence
    case gift
    case edit
    case delete
    case deletedReply
}

public struct JerkgramArchiveManifestV1: Codable, Equatable {
    public var schemaVersion: Int = 1
    public let createdTimestamp: Int64
    public let sourceBuild: Int

    public init(createdTimestamp: Int64, sourceBuild: Int) {
        self.createdTimestamp = createdTimestamp
        self.sourceBuild = sourceBuild
    }
}

public struct JerkgramArchiveEventIdentityV1: Hashable, Comparable {
    public let accountPeerId: Int64
    public let peerId: Int64
    public let messageId: Int32
    public let eventTimestamp: Int64
    public let kind: JerkgramArchiveEventKindV1

    public static func < (lhs: Self, rhs: Self) -> Bool {
        if lhs.eventTimestamp != rhs.eventTimestamp { return lhs.eventTimestamp < rhs.eventTimestamp }
        if lhs.accountPeerId != rhs.accountPeerId { return lhs.accountPeerId < rhs.accountPeerId }
        if lhs.peerId != rhs.peerId { return lhs.peerId < rhs.peerId }
        if lhs.messageId != rhs.messageId { return lhs.messageId < rhs.messageId }
        return lhs.kind.rawValue < rhs.kind.rawValue
    }
}

public struct JerkgramArchiveEventV1: Codable, Equatable {
    public let accountPeerId: Int64
    public let peerId: Int64
    public let messageId: Int32
    public let eventTimestamp: Int64
    public let kind: JerkgramArchiveEventKindV1
    public let payload: [String: String]

    public var identity: JerkgramArchiveEventIdentityV1 {
        return JerkgramArchiveEventIdentityV1(
            accountPeerId: self.accountPeerId,
            peerId: self.peerId,
            messageId: self.messageId,
            eventTimestamp: self.eventTimestamp,
            kind: self.kind
        )
    }
}

public struct JerkgramArchiveV1: Codable, Equatable {
    public var schemaVersion: Int = 1
    public var manifest: JerkgramArchiveManifestV1
    public var events: [JerkgramArchiveEventV1]

    public init(manifest: JerkgramArchiveManifestV1, events: [JerkgramArchiveEventV1]) {
        self.manifest = manifest
        self.events = events
    }
}

public enum JerkgramArchiveError: Error, Equatable {
    case unsupportedSchemaVersion(Int)
    case eventLimitExceeded(Int)
}

public enum JerkgramArchiveCodec {
    public static let maximumEventCount = 100_000

    public static func encode(_ archive: JerkgramArchiveV1) throws -> Data {
        try self.validate(archive)
        let encoder = JSONEncoder()
        encoder.outputFormatting = JSONEncoder.OutputFormatting.sortedKeys
        return try encoder.encode(archive)
    }

    public static func decode(_ data: Data) throws -> JerkgramArchiveV1 {
        let archive = try JSONDecoder().decode(JerkgramArchiveV1.self, from: data)
        try self.validate(archive)
        return archive
    }

    public static func merged(
        current: JerkgramArchiveV1,
        imported: JerkgramArchiveV1
    ) throws -> JerkgramArchiveV1 {
        try self.validate(current)
        try self.validate(imported)
        var values: [JerkgramArchiveEventIdentityV1: JerkgramArchiveEventV1] = [:]
        for event in current.events { values[event.identity] = event }
        for event in imported.events { values[event.identity] = event }
        let events = values.values.sorted { $0.identity < $1.identity }
        guard events.count <= self.maximumEventCount else {
            throw JerkgramArchiveError.eventLimitExceeded(events.count)
        }
        return JerkgramArchiveV1(manifest: imported.manifest, events: events)
    }

    private static func validate(_ archive: JerkgramArchiveV1) throws {
        guard archive.schemaVersion == 1, archive.manifest.schemaVersion == 1 else {
            throw JerkgramArchiveError.unsupportedSchemaVersion(archive.schemaVersion)
        }
        guard archive.events.count <= self.maximumEventCount else {
            throw JerkgramArchiveError.eventLimitExceeded(archive.events.count)
        }
    }
}
'''


def event_identity(event):
    return (
        int(event["accountPeerId"]),
        int(event["peerId"]),
        int(event["messageId"]),
        int(event["eventTimestamp"]),
        str(event["kind"]),
    )


def merge_events(current, imported):
    values = {event_identity(event): event for event in current}
    for event in imported:
        values[event_identity(event)] = event
    return sorted(
        values.values(),
        key=lambda event: (
            int(event["eventTimestamp"]),
            int(event["accountPeerId"]),
            int(event["peerId"]),
            int(event["messageId"]),
            str(event["kind"]),
        ),
    )


def materialized_files():
    return {
        "submodules/SettingsUI/Sources/Jerkgram/JerkgramSettingsStore.swift": settings_source(),
        "submodules/SettingsUI/Sources/Jerkgram/JerkgramArchive.swift": archive_source(),
    }


def main():
    for relative, contents in materialized_files().items():
        path = ROOT / relative
        if path.exists():
            require(
                path.read_text(encoding="utf-8") == contents,
                "foundation owner exists with different content: " + relative,
            )
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
    print("[Build116 foundation] typed SettingsV1 and ArchiveV1 materialized")


if __name__ == "__main__":
    main()
