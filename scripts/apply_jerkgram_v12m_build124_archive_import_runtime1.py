#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramArchiveFlowController.swift"
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_ARCHIVE_IMPORT_BACKGROUND1"
REFRESH_MARKER = "// MARK: Jerkgram v1.2M BUILD124_ARCHIVE_IMPORT_REFRESH1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 archive import runtime] " + message)


def balanced_region(text: str, token: str) -> tuple[int, int]:
    start = text.find(token)
    require(start >= 0, f"function missing: {token}")
    brace = text.find("{", start + len(token))
    require(brace >= 0, f"opening brace missing: {token}")
    depth = 0
    in_string = False
    escaped = False
    i = brace
    while i < len(text):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1
    raise RuntimeError("[Build124 archive import runtime] unbalanced Swift function")


SETTINGS_REFRESH_HELPER = r'''// MARK: Jerkgram v1.2M BUILD124_ARCHIVE_IMPORT_REFRESH1
private let jerkgramSettingsDidImportNotification = Notification.Name("JerkgramSettingsDidImport")

func jerkgramNotifySettingsImported(accountPeerId: Int64) {
    NotificationCenter.default.post(
        name: jerkgramSettingsDidImportNotification,
        object: nil,
        userInfo: ["accountPeerId": NSNumber(value: accountPeerId)]
    )
}

private func jerkgramSettingsImportRefreshSignal(
    accountPeerId: Int64,
    reload: @escaping () -> Void
) -> Signal<Void, NoError> {
    return Signal { subscriber in
        // Seed combineLatest immediately. The observer itself is retained only
        // by the controller state signal and is removed with that subscription.
        subscriber.putNext(())
        let observer = NotificationCenter.default.addObserver(
            forName: jerkgramSettingsDidImportNotification,
            object: nil,
            queue: OperationQueue.main,
            using: { notification in
                guard let rawAccountPeerId = notification.userInfo?["accountPeerId"] as? NSNumber,
                      rawAccountPeerId.int64Value == accountPeerId else {
                    return
                }
                reload()
            }
        )
        return ActionDisposable {
            NotificationCenter.default.removeObserver(observer)
        }
    }
}

'''


def patch_settings_refresh_text(text: str) -> str:
    if REFRESH_MARKER in text:
        return text
    require(
        "BUILD123_ACCOUNT_SETTINGS_SCOPE1" in text or "BUILD123_ACCOUNT_SETTINGS_OWNER1" in text,
        "Build123 account-scoped settings owner missing",
    )

    # Do not anchor to the formatting of the public controller declaration.
    # The entries builder is a stable single owner reused by Build123 and the
    # later Build124 settings-redesign overlay.
    helper_anchor = "private func ghostBaseSettingsEntries("
    require(text.count(helper_anchor) == 1, f"settings entries owner anchor count: {text.count(helper_anchor)}")
    helper_start = text.index(helper_anchor)
    text = text[:helper_start] + SETTINGS_REFRESH_HELPER + text[helper_start:]

    state_anchor = "    let stateValue = Atomic(value: initialState)\n"
    require(text.count(state_anchor) == 1, f"settings Atomic anchor count: {text.count(state_anchor)}")
    refresh_setup = state_anchor + r'''    let jerkgramImportRefreshSignal = jerkgramSettingsImportRefreshSignal(
        accountPeerId: accountPeerId,
        reload: {
            let refreshed = GhostBaseSettingsState.load(accountPeerId: accountPeerId, mirrorLegacy: true)
            stateValue.modify { _ in refreshed }
            statePromise.set(refreshed)
        }
    )
    // Retain the import observer through the controller's existing state
    // subscription without changing the arity or closure shape of whatever
    // combineLatest the release chain already uses.
    let jerkgramImportRefreshStateSignal = combineLatest(
        __JERKGRAM_IMPORT_REFRESH_STATE_PROMISE__,
        jerkgramImportRefreshSignal
    )
    |> map { state, _ in state }
'''
    text = text.replace(state_anchor, refresh_setup, 1)

    setup_marker = "    |> map { state, _ in state }\n"
    setup_start = text.index("    let jerkgramImportRefreshStateSignal = combineLatest(")
    setup_end = text.index(setup_marker, setup_start) + len(setup_marker)
    controller_start, controller_end = balanced_region(text, "private func ghostBaseSettingsPageController(")
    controller_text = text[controller_start:controller_end]
    state_get = "statePromise.get()"
    require(controller_text.count(state_get) >= 1, "settings controller no longer consumes statePromise.get()")
    controller_text = controller_text.replace(state_get, "jerkgramImportRefreshStateSignal", 1)
    text = text[:controller_start] + controller_text + text[controller_end:]
    require(text.count("__JERKGRAM_IMPORT_REFRESH_STATE_PROMISE__") == 1, "settings refresh placeholder count")
    text = text.replace("__JERKGRAM_IMPORT_REFRESH_STATE_PROMISE__", state_get, 1)

    require(REFRESH_MARKER in text, "settings refresh marker missing after patch")
    require("ActionDisposable" in text, "settings refresh observer is not lifecycle-bound")
    require("jerkgramImportRefreshStateSignal" in text, "settings refresh state bridge missing")
    return text


REPLACEMENT = r'''// MARK: Jerkgram v1.2M BUILD124_ARCHIVE_IMPORT_BACKGROUND1
private func jerkgramProjectImportedSettingsToActiveDefaults(_ snapshot: JerkgramSettingsSnapshot) {
    let defaults = UserDefaults.standard
    for (key, value) in snapshot.toggles {
        defaults.set(value, forKey: key)
    }
    for (key, value) in snapshot.stringValues {
        defaults.set(value, forKey: key)
    }
    for (key, value) in snapshot.integerValues {
        defaults.set(value, forKey: key)
    }

    // Archive v2 originally used Jerkgram-prefixed portable names while a few
    // low-level runtime owners still consume their legacy GhostBase projection.
    // Project both spellings for the three synchronous side-effect settings.
    let legacyRuntimeKeys: [String: String] = [
        "jerkgram.GhostMode.ScheduledSend": "GhostBase.GhostMode.ScheduledSend",
        "jerkgram.ProtectedContent.Enabled": "GhostBase.ProtectedContent.Enabled",
        "jerkgram.ProtectedContent.OneTimeSave": "GhostBase.ProtectedContent.OneTimeSave",
    ]
    for (portableKey, legacyKey) in legacyRuntimeKeys {
        if let value = snapshot.toggles[portableKey] {
            defaults.set(value, forKey: legacyKey)
            if legacyKey == "GhostBase.GhostMode.ScheduledSend" {
                (UserDefaults(suiteName: "group.4a348a9b186b700c.1") ?? defaults).set(value, forKey: legacyKey)
            }
        }
    }
}

private func jerkgramPresentArchiveImportError(
    context: AccountContext,
    controller: ViewController,
    presentationData: PresentationData,
    text: String
) {
    Queue.mainQueue().async {
        let alert = textAlertController(
            context: context,
            title: presentationData.strings.jerkgram.importArchive,
            text: text,
            actions: [
                TextAlertAction(
                    type: .defaultAction,
                    title: presentationData.strings.Common_OK,
                    action: {}
                )
            ]
        )
        controller.present(alert, in: .window(.root), with: nil)
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

            // ZIP enumeration/unzip, payload reads and JSON validation are all
            // potentially unbounded file I/O. Never execute them in the file
            // picker/UI callback.
            Queue.concurrentDefaultQueue().async {
                defer {
                    if didAccess {
                        sourceURL.stopAccessingSecurityScopedResource()
                    }
                }
                let workURL = FileManager.default.temporaryDirectory
                    .appendingPathComponent("jerkgram-import-\(UUID().uuidString)", isDirectory: true)
                defer { try? FileManager.default.removeItem(at: workURL) }

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
                        payloads[descriptor.relativePath] = try Data(
                            contentsOf: workURL.appendingPathComponent(descriptor.relativePath)
                        )
                    }
                    try JerkgramArchiveV2.validateExtractedPayloads(
                        manifest: JerkgramArchiveManifestV2(
                            createdAtMs: manifest.createdAtMs,
                            accounts: [account]
                        ),
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

                    Queue.mainQueue().async {
                        let strings = presentationData.strings.jerkgram
                        let alert = textAlertController(
                            context: context,
                            title: strings.importArchive,
                            text: strings.importSettingsConfirmation(accountPeerId),
                            actions: [
                                TextAlertAction(
                                    type: .genericAction,
                                    title: presentationData.strings.Common_Cancel,
                                    action: {}
                                ),
                                TextAlertAction(
                                    type: .defaultAction,
                                    title: strings.importSettings,
                                    action: {
                                        // ArchiveTransaction loads/merges and may atomically
                                        // rewrite the complete canonical account store. Keep
                                        // that transaction and its rollback away from UI.
                                        Queue.concurrentDefaultQueue().async {
                                            do {
                                                let eventStore = JerkgramJSONLEventStore(
                                                    rootURL: jerkgramCoreRootURL()
                                                )
                                                let settingsStore = JerkgramUserDefaultsSnapshotStore()
                                                try JerkgramArchiveTransaction.apply(
                                                    selectedAccountPeerIds: [accountPeerId],
                                                    availableAccountPeerIds: [context.account.peerId.toInt64()],
                                                    incomingEvents: [accountPeerId: events],
                                                    incomingSettings: [accountPeerId: settings],
                                                    confirmSettingsChanges: true,
                                                    eventStore: eventStore,
                                                    settingsStore: settingsStore
                                                )
                                                try JerkgramRetentionRuntime.save(retention)
                                                jerkgramProjectImportedSettingsToActiveDefaults(settings)
                                                Queue.mainQueue().async {
                                                    jerkgramNotifySettingsImported(accountPeerId: accountPeerId)
                                                }
                                            } catch {
                                                jerkgramPresentArchiveImportError(
                                                    context: context,
                                                    controller: controller,
                                                    presentationData: presentationData,
                                                    text: String(describing: error)
                                                )
                                            }
                                        }
                                    }
                                ),
                            ]
                        )
                        controller.present(alert, in: .window(.root), with: nil)
                    }
                } catch {
                    jerkgramPresentArchiveImportError(
                        context: context,
                        controller: controller,
                        presentationData: presentationData,
                        text: String(describing: error)
                    )
                }
            }
        }
    )
    controller.present(picker, in: .window(.root), with: nil)
}'''


def patch_text(text: str) -> str:
    if MARKER in text:
        if "jerkgramNotifySettingsImported(accountPeerId: accountPeerId)" in text:
            return text
        old = "                                                jerkgramProjectImportedSettingsToActiveDefaults(settings)\n"
        require(text.count(old) == 1, "existing Build124 import projection anchor missing during refresh upgrade")
        return text.replace(
            old,
            old
            + "                                                Queue.mainQueue().async {\n"
            + "                                                    jerkgramNotifySettingsImported(accountPeerId: accountPeerId)\n"
            + "                                                }\n",
            1,
        )
    token = "public func jerkgramPresentArchiveImport("
    start, end = balanced_region(text, token)
    updated = text[:start] + REPLACEMENT + text[end:]
    require(MARKER in updated, "background import marker missing")
    require(
        updated.index("Queue.concurrentDefaultQueue().async", updated.index("completion: { urls in"))
        < updated.index("SSZipArchive.getEntriesForFile", updated.index("completion: { urls in")),
        "ZIP I/O still precedes background queue",
    )
    require("try? JerkgramArchiveTransaction.apply" not in updated, "archive transaction errors are still swallowed")
    return updated


def main() -> None:
    require(TARGET.is_file(), f"materialized archive flow missing: {TARGET}")
    require(SETTINGS.is_file(), f"materialized settings owner missing: {SETTINGS}")

    archive_original = TARGET.read_text(encoding="utf-8")
    archive_updated = patch_text(archive_original)
    TARGET.write_text(archive_updated, encoding="utf-8")

    settings_original = SETTINGS.read_text(encoding="utf-8")
    settings_updated = patch_settings_refresh_text(settings_original)
    SETTINGS.write_text(settings_updated, encoding="utf-8")

    print("[Build124 archive import runtime] GREEN")
    print("[Build124 archive import runtime] ZIP/decode and ArchiveTransaction.apply run off the UI thread")
    print("[Build124 archive import runtime] imported critical runtime settings project immediately to active defaults")
    print("[Build124 archive import runtime] open account-scoped Settings controllers reload after successful import")


if __name__ == "__main__":
    main()
