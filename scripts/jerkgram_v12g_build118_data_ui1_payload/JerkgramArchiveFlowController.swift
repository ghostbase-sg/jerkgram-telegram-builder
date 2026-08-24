import Foundation
import Display
import SwiftSignalKit
import TelegramCore
import TelegramPresentationData
import PresentationDataUtils
import AccountContext
import AlertUI
import LegacyMediaPickerUI
import JerkgramCore
import ZipArchive

// MARK: Jerkgram v1.2G BUILD118_ARCHIVE_FLOW1
private let jerkgramPortableBooleanKeys: [String] = [
    "jerkgram.Profile.Enabled", "jerkgram.Profile.ShowIds", "jerkgram.Profile.ShowDCs",
    "jerkgram.Profile.ShowRegistration", "jerkgram.Glass.Enabled",
    "jerkgram.ProfileBlur.Avatar", "jerkgram.ProfileBlur.Animated",
    "jerkgram.ProfileBlur.Tint", "jerkgram.ProfileBlur.Reduced",
    "jerkgram.GhostMode.ReadMessages", "jerkgram.GhostMode.TypingActions",
    "jerkgram.GhostMode.HideRecording", "jerkgram.GhostMode.HideUploading",
    "jerkgram.GhostMode.HideStickerActivity", "jerkgram.GhostMode.HideGameActivity",
    "jerkgram.GhostMode.HideEmojiActivity", "jerkgram.GhostMode.Presence",
    "jerkgram.GhostMode.ScheduledSend", "jerkgram.Messages.SaveDeleted",
    "jerkgram.Messages.ShowDeleted", "jerkgram.Messages.SaveEditHistory",
    "jerkgram.Messages.ShowEditHistory", "jerkgram.Messages.DeletedPortableReplies",
    "jerkgram.Messages.PreserveDeletedMedia", "jerkgram.Appearance.ShowRamUnderClock",
    "jerkgram.Appearance.MessageSeconds", "jerkgram.Appearance.HideOwnPhone",
    "jerkgram.ProtectedContent.Enabled", "jerkgram.ProtectedContent.GalleryShare",
    "jerkgram.ProtectedContent.GallerySave", "jerkgram.ProtectedContent.GalleryCopy",
    "jerkgram.ProtectedContent.ChatSave", "jerkgram.ProtectedContent.ChatCopy",
    "jerkgram.ProtectedContent.ChatForward", "jerkgram.ProtectedContent.AllowScreenshots",
    "jerkgram.ProtectedContent.AllowScreenRecording",
    "jerkgram.ProtectedContent.OneTimeScreenshots",
    "jerkgram.ProtectedContent.OneTimeScreenRecording",
    "jerkgram.ProtectedContent.OneTimeSave", "jerkgram.Stories.Save",
    "jerkgram.Stars.LocalBalance.Enabled",
]

private let jerkgramPortableStringKeys = [
    "jerkgram.Messages.SendTextStyle",
    "jerkgram.Stars.LocalBalance.Amount",
    "jerkgram.Stars.LocalBalance.BaseAmount",
]

private let jerkgramPortableIntegerKeys = [
    "jerkgram.Messages.DeletedMediaCacheLimit",
    "jerkgram.Messages.DeletedMediaRetentionDays",
]

private func jerkgramCoreRootURL() -> URL {
    return FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        .appendingPathComponent("Jerkgram", isDirectory: true)
}

private func jerkgramSettingsSnapshot(accountPeerId: Int64) -> JerkgramSettingsSnapshot {
    var toggles: [String: Bool] = [:]
    var strings: [String: String] = [:]
    var integers: [String: Int64] = [:]
    for key in jerkgramPortableBooleanKeys {
        let scoped = "jerkgram.account.\(accountPeerId).setting.\(key)"
        if let value = UserDefaults.standard.object(forKey: scoped) as? Bool {
            toggles[key] = value
        } else if let value = UserDefaults.standard.object(forKey: key) as? Bool {
            toggles[key] = value
        }
    }
    for key in jerkgramPortableStringKeys {
        let scoped = "jerkgram.account.\(accountPeerId).setting.\(key)"
        if let value = UserDefaults.standard.string(forKey: scoped) {
            strings[key] = value
        } else if let value = UserDefaults.standard.string(forKey: key) {
            strings[key] = value
        }
    }
    for key in jerkgramPortableIntegerKeys {
        let scoped = "jerkgram.account.\(accountPeerId).setting.\(key)"
        if let value = UserDefaults.standard.object(forKey: scoped) as? NSNumber {
            integers[key] = value.int64Value
        } else if let value = UserDefaults.standard.object(forKey: key) as? NSNumber {
            integers[key] = value.int64Value
        }
    }
    return JerkgramSettingsSnapshot(
        accountPeerId: accountPeerId,
        toggles: toggles,
        integerValues: integers,
        stringValues: strings
    )
}

private func jerkgramWritePayload<T: Encodable>(
    _ value: T,
    component: JerkgramArchiveComponent,
    relativePath: String,
    rootURL: URL,
    recordCount: Int
) throws -> JerkgramArchivePayloadDescriptor {
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.sortedKeys]
    let data = try encoder.encode(value)
    let url = rootURL.appendingPathComponent(relativePath)
    try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
    try data.write(to: url, options: .atomic)
    return JerkgramArchivePayloadDescriptor(
        component: component,
        relativePath: relativePath,
        recordCount: recordCount,
        uncompressedBytes: Int64(data.count),
        sha256: JerkgramSHA256.hex(data)
    )
}

public func jerkgramPresentArchiveExport(
    context: AccountContext,
    controller: ViewController
) {
    let accountPeerId = context.account.peerId.toInt64()
    Queue.concurrentDefaultQueue().async {
        let workURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("jerkgram-export-\(UUID().uuidString)", isDirectory: true)
        let outputURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("Jerkgram-\(accountPeerId)-Build118.jerkgram")
        do {
            try FileManager.default.createDirectory(at: workURL, withIntermediateDirectories: true)
            let base = "accounts/\(accountPeerId)"
            let settings = jerkgramSettingsSnapshot(accountPeerId: accountPeerId)
            let retention = JerkgramRetentionRuntime.configuration(accountPeerId: accountPeerId)
            let eventStore = JerkgramJSONLEventStore(rootURL: jerkgramCoreRootURL())
            let events = (try? eventStore.events(accountPeerId: accountPeerId, chatPeerId: nil)) ?? []
            let descriptors = try [
                jerkgramWritePayload(settings, component: .settingsSnapshot, relativePath: "\(base)/settings.json", rootURL: workURL, recordCount: settings.toggles.count + settings.stringValues.count),
                jerkgramWritePayload(retention, component: .retentionPolicies, relativePath: "\(base)/retention.json", rootURL: workURL, recordCount: retention.chatOverrides.count + 1),
                jerkgramWritePayload(events, component: .canonicalEvents, relativePath: "\(base)/events.json", rootURL: workURL, recordCount: events.count),
            ]
            let manifest = JerkgramArchiveManifestV2(
                createdAtMs: Int64(Date().timeIntervalSince1970 * 1000.0),
                accounts: [JerkgramArchiveAccountManifest(accountPeerId: accountPeerId, payloads: descriptors)]
            )
            let encoder = JSONEncoder()
            encoder.outputFormatting = [.sortedKeys]
            try encoder.encode(manifest).write(to: workURL.appendingPathComponent("manifest.json"), options: .atomic)
            try? FileManager.default.removeItem(at: outputURL)
            guard SSZipArchive.createZipFile(atPath: outputURL.path, withContentsOfDirectory: workURL.path) else {
                throw CocoaError(.fileWriteUnknown)
            }
            Queue.mainQueue().async {
                let presentationData = context.sharedContext.currentPresentationData.with { $0 }
                let picker = legacyICloudFilePicker(
                    theme: presentationData.theme,
                    mode: .export,
                    url: outputURL,
                    documentTypes: [],
                    dismissed: {
                        try? FileManager.default.removeItem(at: workURL)
                        try? FileManager.default.removeItem(at: outputURL)
                    },
                    completion: { _ in
                        try? FileManager.default.removeItem(at: workURL)
                        try? FileManager.default.removeItem(at: outputURL)
                    }
                )
                controller.present(picker, in: .window(.root), with: nil)
            }
        } catch {
            try? FileManager.default.removeItem(at: workURL)
            try? FileManager.default.removeItem(at: outputURL)
        }
    }
}

private final class JerkgramUserDefaultsSnapshotStore: JerkgramSettingsSnapshotStore {
    func snapshot(accountPeerId: Int64) throws -> JerkgramSettingsSnapshot {
        return jerkgramSettingsSnapshot(accountPeerId: accountPeerId)
    }

    func replace(_ snapshot: JerkgramSettingsSnapshot) throws {
        for (key, value) in snapshot.toggles {
            UserDefaults.standard.set(value, forKey: "jerkgram.account.\(snapshot.accountPeerId).setting.\(key)")
        }
        for (key, value) in snapshot.stringValues {
            UserDefaults.standard.set(value, forKey: "jerkgram.account.\(snapshot.accountPeerId).setting.\(key)")
        }
        for (key, value) in snapshot.integerValues {
            UserDefaults.standard.set(value, forKey: "jerkgram.account.\(snapshot.accountPeerId).setting.\(key)")
        }
    }
}

public func jerkgramPresentArchiveImport(
    context: AccountContext,
    controller: ViewController
) {
    let presentationData = context.sharedContext.currentPresentationData.with { $0 }
    let picker = legacyICloudFilePicker(
        theme: presentationData.theme,
        mode: .import,
        documentTypes: ["public.zip-archive", "public.data"],
        completion: { urls in
            guard let sourceURL = urls.first else { return }
            let didAccess = sourceURL.startAccessingSecurityScopedResource()
            defer { if didAccess { sourceURL.stopAccessingSecurityScopedResource() } }
            let workURL = FileManager.default.temporaryDirectory
                .appendingPathComponent("jerkgram-import-\(UUID().uuidString)", isDirectory: true)
            do {
                try FileManager.default.createDirectory(at: workURL, withIntermediateDirectories: true)
                guard let entries = SSZipArchive.getEntriesForFile(atPath: sourceURL.path),
                      entries.count <= JerkgramArchiveV2.maximumPayloadCount + 1 else {
                    throw CocoaError(.fileReadCorruptFile)
                }
                for entry in entries {
                    let normalizedPath = entry.path.hasSuffix("/")
                        ? String(entry.path.dropLast())
                        : entry.path
                    if !normalizedPath.isEmpty {
                        try JerkgramArchiveV2.validateRelativePath(normalizedPath)
                    }
                }
                guard SSZipArchive.unzipFile(atPath: sourceURL.path, toDestination: workURL.path) else {
                    throw CocoaError(.fileReadCorruptFile)
                }
                let decoder = JSONDecoder()
                let manifest = try decoder.decode(
                    JerkgramArchiveManifestV2.self,
                    from: Data(contentsOf: workURL.appendingPathComponent("manifest.json"))
                )
                let accountPeerId = context.account.peerId.toInt64()
                guard let account = manifest.accounts.first(where: { $0.accountPeerId == accountPeerId }) else {
                    throw JerkgramArchiveValidationError.unavailableAccount(accountPeerId)
                }
                var payloads: [String: Data] = [:]
                for descriptor in account.payloads {
                    payloads[descriptor.relativePath] = try Data(contentsOf: workURL.appendingPathComponent(descriptor.relativePath))
                }
                try JerkgramArchiveV2.validateExtractedPayloads(
                    manifest: JerkgramArchiveManifestV2(createdAtMs: manifest.createdAtMs, accounts: [account]),
                    payloads: payloads
                )
                let base = "accounts/\(accountPeerId)"
                guard let settingsData = payloads["\(base)/settings.json"],
                      let retentionData = payloads["\(base)/retention.json"],
                      let eventsData = payloads["\(base)/events.json"] else {
                    throw JerkgramArchiveValidationError.missingPayload(base)
                }
                let settings = try decoder.decode(JerkgramSettingsSnapshot.self, from: settingsData)
                let retention = try decoder.decode(JerkgramRetentionConfiguration.self, from: retentionData)
                let events = try decoder.decode([JerkgramCanonicalEvent].self, from: eventsData)
                let strings = presentationData.strings.jerkgram
                let alert = textAlertController(
                    context: context,
                    title: strings.importArchive,
                    text: strings.importSettingsConfirmation(accountPeerId),
                    actions: [
                        TextAlertAction(type: .genericAction, title: presentationData.strings.Common_Cancel, action: {}),
                        TextAlertAction(type: .defaultAction, title: strings.importSettings, action: {
                            let eventStore = JerkgramJSONLEventStore(rootURL: jerkgramCoreRootURL())
                            let settingsStore = JerkgramUserDefaultsSnapshotStore()
                            try? JerkgramArchiveTransaction.apply(
                                selectedAccountPeerIds: [accountPeerId],
                                availableAccountPeerIds: [context.account.peerId.toInt64()],
                                incomingEvents: [accountPeerId: events],
                                incomingSettings: [accountPeerId: settings],
                                confirmSettingsChanges: true,
                                eventStore: eventStore,
                                settingsStore: settingsStore
                            )
                            try? JerkgramRetentionRuntime.save(retention)
                        }),
                    ]
                )
                controller.present(alert, in: .window(.root), with: nil)
            } catch {
                let alert = textAlertController(
                    context: context,
                    title: presentationData.strings.jerkgram.importArchive,
                    text: String(describing: error),
                    actions: [TextAlertAction(type: .defaultAction, title: presentationData.strings.Common_OK, action: {})]
                )
                controller.present(alert, in: .window(.root), with: nil)
            }
            try? FileManager.default.removeItem(at: workURL)
        }
    )
    controller.present(picker, in: .window(.root), with: nil)
}
