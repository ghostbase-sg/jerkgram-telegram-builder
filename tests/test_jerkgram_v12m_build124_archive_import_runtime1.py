from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts/apply_jerkgram_v12m_build124_archive_import_runtime1.py"

FIXTURE = '''import Foundation

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
                .appendingPathComponent("jerkgram-import-\\(UUID().uuidString)", isDirectory: true)
            do {
                try FileManager.default.createDirectory(at: workURL, withIntermediateDirectories: true)
                guard let entries = SSZipArchive.getEntriesForFile(atPath: sourceURL.path),
                      entries.count <= JerkgramArchiveV2.maximumPayloadCount + 1 else {
                    throw CocoaError(.fileReadCorruptFile)
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
                let base = "accounts/\\(accountPeerId)"
                let settings = try decoder.decode(JerkgramSettingsSnapshot.self, from: payloads["\\(base)/settings.json"]!)
                let retention = try decoder.decode(JerkgramRetentionConfiguration.self, from: payloads["\\(base)/retention.json"]!)
                let events = try decoder.decode([JerkgramCanonicalEvent].self, from: payloads["\\(base)/events.json"]!)
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
                let alert = textAlertController(context: context, title: presentationData.strings.jerkgram.importArchive, text: String(describing: error), actions: [])
                controller.present(alert, in: .window(.root), with: nil)
            }
            try? FileManager.default.removeItem(at: workURL)
        }
    )
    controller.present(picker, in: .window(.root), with: nil)
}
'''


class Build124ArchiveImportRuntimeTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_archive_import_runtime", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_zip_and_payload_io_move_off_ui_callback(self):
        module = self.load_patch()
        updated = module.patch_text(FIXTURE)
        self.assertIn("BUILD124_ARCHIVE_IMPORT_BACKGROUND1", updated)
        completion = updated[updated.index("completion: { urls in"):]
        self.assertLess(completion.index("Queue.concurrentDefaultQueue().async"), completion.index("SSZipArchive.getEntriesForFile"))
        self.assertLess(completion.index("Queue.concurrentDefaultQueue().async"), completion.index("Data(contentsOf:"))

    def test_transaction_commit_moves_off_alert_action_thread(self):
        module = self.load_patch()
        updated = module.patch_text(FIXTURE)
        action = updated[updated.index("title: strings.importSettings"):]
        self.assertLess(action.index("Queue.concurrentDefaultQueue().async"), action.index("JerkgramArchiveTransaction.apply"))
        self.assertNotIn("try? JerkgramArchiveTransaction.apply", action)

    def test_import_projects_current_account_settings_after_success(self):
        module = self.load_patch()
        updated = module.patch_text(FIXTURE)
        self.assertIn("jerkgramProjectImportedSettingsToActiveDefaults(settings)", updated)
        self.assertIn('UserDefaults(suiteName: "group.4a348a9b186b700c.1")', updated)

    def test_ui_presentation_returns_to_main_queue(self):
        module = self.load_patch()
        updated = module.patch_text(FIXTURE)
        self.assertIn("Queue.mainQueue().async", updated)
        self.assertIn("controller.present(alert, in: .window(.root), with: nil)", updated)

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_text(FIXTURE)
        self.assertEqual(once, module.patch_text(once))


if __name__ == "__main__":
    unittest.main()
