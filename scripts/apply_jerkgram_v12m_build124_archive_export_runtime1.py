#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramArchiveFlowController.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_ARCHIVE_EXPORT_RUNTIME1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 archive export runtime] " + message)


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
    raise RuntimeError("[Build124 archive export runtime] unbalanced Swift function")


REPLACEMENT = r'''// MARK: Jerkgram v1.2M BUILD124_ARCHIVE_EXPORT_RUNTIME1
private func jerkgramPresentArchiveExportError(
    context: AccountContext,
    controller: ViewController,
    text: String
) {
    Queue.mainQueue().async {
        let presentationData = context.sharedContext.currentPresentationData.with { $0 }
        let alert = textAlertController(
            context: context,
            title: presentationData.strings.jerkgram.exportArchive,
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

public func jerkgramPresentArchiveExport(
    context: AccountContext,
    controller: ViewController
) {
    let accountPeerId = context.account.peerId.toInt64()

    // Full event snapshotting, JSON encoding and ZIP creation are intentionally
    // kept off the UI thread. Flush the recorder on this worker first so the
    // archive does not race the 250 ms capture buffer and silently miss the
    // newest deleted/edited events.
    Queue.concurrentDefaultQueue().async {
        let workURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("jerkgram-export-\(UUID().uuidString)", isDirectory: true)
        let outputURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("Jerkgram-\(accountPeerId)-Build124.jerkgram")
        do {
            JerkgramCaptureRecorder.flushSynchronously()
            try FileManager.default.createDirectory(at: workURL, withIntermediateDirectories: true)
            let base = "accounts/\(accountPeerId)"
            let settings = jerkgramSettingsSnapshot(accountPeerId: accountPeerId)
            let retention = JerkgramRetentionRuntime.configuration(accountPeerId: accountPeerId)
            let eventStore = JerkgramJSONLEventStore(rootURL: jerkgramCoreRootURL())

            // Never convert a canonical-store failure into an apparently valid
            // empty archive. If reading history fails, surface that failure and
            // leave the user's canonical store untouched.
            let events = try eventStore.events(accountPeerId: accountPeerId, chatPeerId: nil)
            let descriptors = try [
                jerkgramWritePayload(
                    settings,
                    component: .settingsSnapshot,
                    relativePath: "\(base)/settings.json",
                    rootURL: workURL,
                    recordCount: settings.toggles.count + settings.stringValues.count
                ),
                jerkgramWritePayload(
                    retention,
                    component: .retentionPolicies,
                    relativePath: "\(base)/retention.json",
                    rootURL: workURL,
                    recordCount: retention.chatOverrides.count + 1
                ),
                jerkgramWritePayload(
                    events,
                    component: .canonicalEvents,
                    relativePath: "\(base)/events.json",
                    rootURL: workURL,
                    recordCount: events.count
                ),
            ]
            let manifest = JerkgramArchiveManifestV2(
                createdAtMs: Int64(Date().timeIntervalSince1970 * 1000.0),
                accounts: [
                    JerkgramArchiveAccountManifest(
                        accountPeerId: accountPeerId,
                        payloads: descriptors
                    )
                ]
            )
            let encoder = JSONEncoder()
            encoder.outputFormatting = [.sortedKeys]
            try encoder.encode(manifest).write(
                to: workURL.appendingPathComponent("manifest.json"),
                options: .atomic
            )
            try? FileManager.default.removeItem(at: outputURL)
            guard SSZipArchive.createZipFile(
                atPath: outputURL.path,
                withContentsOfDirectory: workURL.path
            ) else {
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
            jerkgramPresentArchiveExportError(
                context: context,
                controller: controller,
                text: String(describing: error)
            )
        }
    }
}'''


def patch_text(text: str) -> str:
    if MARKER in text:
        return text
    token = "public func jerkgramPresentArchiveExport("
    start, end = balanced_region(text, token)
    original = text[start:end]
    require("Queue.concurrentDefaultQueue().async" in original, "Build118 background export owner missing")
    require("SSZipArchive.createZipFile" in original, "Build118 ZIP export owner missing")
    require("eventStore.events(accountPeerId: accountPeerId, chatPeerId: nil)" in original, "Build118 canonical export read missing")
    updated = text[:start] + REPLACEMENT + text[end:]
    require(MARKER in updated, "export runtime marker missing")
    export_start = updated.index("public func jerkgramPresentArchiveExport(")
    import_start = updated.find("public func jerkgramPresentArchiveImport(", export_start)
    export_body = updated[export_start:import_start if import_start >= 0 else len(updated)]
    require("JerkgramCaptureRecorder.flushSynchronously()" in export_body, "capture drain missing")
    require("let events = try eventStore.events(accountPeerId: accountPeerId, chatPeerId: nil)" in export_body, "throwing canonical event read missing")
    require("(try? eventStore.events" not in export_body, "silent empty-history fallback survived")
    require("jerkgramPresentArchiveExportError(" in export_body, "visible export error path missing")
    require(export_body.index("Queue.concurrentDefaultQueue().async") < export_body.index("SSZipArchive.createZipFile"), "ZIP work escaped background queue")
    return updated


def main() -> None:
    require(TARGET.is_file(), f"materialized archive flow missing: {TARGET}")
    original = TARGET.read_text(encoding="utf-8")
    updated = patch_text(original)
    TARGET.write_text(updated, encoding="utf-8")
    print("[Build124 archive export runtime] GREEN")
    print("[Build124 archive export runtime] buffered capture is drained before snapshot; canonical read failures cannot become empty archives")
    print("[Build124 archive export runtime] export failures are visible; JSON/ZIP work remains off the UI thread")


if __name__ == "__main__":
    main()
