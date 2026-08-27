from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts/apply_jerkgram_v12m_build124_archive_export_runtime1.py"


def load_patch_module():
    spec = importlib.util.spec_from_file_location("build124_archive_export_runtime", PATCH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Build124 archive export patch")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FIXTURE = r'''import Foundation

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
            let settings = jerkgramSettingsSnapshot(accountPeerId: accountPeerId)
            let retention = JerkgramRetentionRuntime.configuration(accountPeerId: accountPeerId)
            let eventStore = JerkgramJSONLEventStore(rootURL: jerkgramCoreRootURL())
            let events = (try? eventStore.events(accountPeerId: accountPeerId, chatPeerId: nil)) ?? []
            _ = settings
            _ = retention
            _ = events
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
                    dismissed: {},
                    completion: { _ in }
                )
                controller.present(picker, in: .window(.root), with: nil)
            }
        } catch {
            try? FileManager.default.removeItem(at: workURL)
            try? FileManager.default.removeItem(at: outputURL)
        }
    }
}

public func jerkgramPresentArchiveImport(context: AccountContext, controller: ViewController) {
    // import sentinel must remain untouched by the export overlay
}
'''


class Build124ArchiveExportRuntimeTests(unittest.TestCase):
    def test_patch_requires_production_module(self) -> None:
        self.assertTrue(PATCH.is_file())

    def test_export_flushes_capture_before_reading_canonical_events(self) -> None:
        module = load_patch_module()
        updated = module.patch_text(FIXTURE)
        body = updated[updated.index("public func jerkgramPresentArchiveExport("):updated.index("public func jerkgramPresentArchiveImport(")]
        self.assertIn("JerkgramCaptureRecorder.flushSynchronously()", body)
        self.assertLess(body.index("JerkgramCaptureRecorder.flushSynchronously()"), body.index("eventStore.events("))

    def test_export_never_turns_store_failure_into_empty_history(self) -> None:
        module = load_patch_module()
        updated = module.patch_text(FIXTURE)
        body = updated[updated.index("public func jerkgramPresentArchiveExport("):updated.index("public func jerkgramPresentArchiveImport(")]
        self.assertIn("let events = try eventStore.events(accountPeerId: accountPeerId, chatPeerId: nil)", body)
        self.assertNotIn("(try? eventStore.events", body)
        self.assertNotIn(") ?? []", body)

    def test_export_work_stays_off_main_and_failure_returns_to_main_ui(self) -> None:
        module = load_patch_module()
        updated = module.patch_text(FIXTURE)
        export_start = updated.index("public func jerkgramPresentArchiveExport(")
        export_end = updated.index("public func jerkgramPresentArchiveImport(")
        body = updated[export_start:export_end]
        worker = body.index("Queue.concurrentDefaultQueue().async")
        flush = body.index("JerkgramCaptureRecorder.flushSynchronously()")
        zip_work = body.index("SSZipArchive.createZipFile")
        self.assertLess(worker, flush)
        self.assertLess(worker, zip_work)
        self.assertIn("jerkgramPresentArchiveExportError(", body)
        helper = updated[updated.index("private func jerkgramPresentArchiveExportError("):export_start]
        self.assertIn("Queue.mainQueue().async", helper)
        self.assertIn("presentationData.strings.jerkgram.exportArchive", helper)

    def test_patch_is_idempotent_and_does_not_rewrite_import(self) -> None:
        module = load_patch_module()
        once = module.patch_text(FIXTURE)
        twice = module.patch_text(once)
        self.assertEqual(once, twice)
        import_before = FIXTURE[FIXTURE.index("public func jerkgramPresentArchiveImport("):]
        import_after = once[once.index("public func jerkgramPresentArchiveImport("):]
        self.assertEqual(import_before, import_after)
        self.assertEqual(once.count(module.MARKER), 1)


if __name__ == "__main__":
    unittest.main()
