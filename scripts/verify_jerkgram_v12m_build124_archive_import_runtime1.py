#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramArchiveFlowController.swift"
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_ARCHIVE_IMPORT_BACKGROUND1"
REFRESH_MARKER = "// MARK: Jerkgram v1.2M BUILD124_ARCHIVE_IMPORT_REFRESH1"


def fail(message: str) -> None:
    raise SystemExit("[verify Build124 archive import runtime] ERROR: " + message)


def require(value: bool, message: str) -> None:
    if not value:
        fail(message)


def main() -> None:
    require(TARGET.is_file(), f"archive flow owner missing: {TARGET}")
    require(SETTINGS.is_file(), f"settings owner missing: {SETTINGS}")
    text = TARGET.read_text(encoding="utf-8")
    settings_text = SETTINGS.read_text(encoding="utf-8")
    require(text.count(MARKER) == 1, "archive import runtime marker must exist exactly once")
    require(settings_text.count(REFRESH_MARKER) == 1, "settings import refresh marker must exist exactly once")

    import_start = text.index("public func jerkgramPresentArchiveImport(")
    import_text = text[import_start:]
    completion_start = import_text.index("completion: { urls in")
    background_start = import_text.index("Queue.concurrentDefaultQueue().async", completion_start)
    zip_start = import_text.index("SSZipArchive.getEntriesForFile", completion_start)
    data_start = import_text.index("Data(contentsOf:", completion_start)
    require(background_start < zip_start, "ZIP listing still runs before background queue")
    require(background_start < data_start, "archive payload reads still run before background queue")

    action_start = import_text.index("title: strings.importSettings")
    transaction_start = import_text.index("JerkgramArchiveTransaction.apply", action_start)
    action_background = import_text.index("Queue.concurrentDefaultQueue().async", action_start)
    require(action_background < transaction_start, "ArchiveTransaction.apply still runs on alert action/UI thread")
    require("try? JerkgramArchiveTransaction.apply" not in import_text, "archive transaction errors are still swallowed")

    projection = "jerkgramProjectImportedSettingsToActiveDefaults(settings)"
    notify = "jerkgramNotifySettingsImported(accountPeerId: accountPeerId)"
    require(projection in import_text, "successful import does not refresh active runtime settings")
    require(notify in import_text, "successful import does not notify open Settings controllers")
    projection_pos = import_text.index(projection, transaction_start)
    notify_pos = import_text.index(notify, projection_pos)
    require(transaction_start < projection_pos < notify_pos, "import refresh order must be transaction -> projection -> UI reload notification")
    require("Queue.mainQueue().async" in import_text[projection_pos:notify_pos], "settings refresh notification is not marshalled to main queue")

    require('"jerkgram.GhostMode.ScheduledSend": "GhostBase.GhostMode.ScheduledSend"' in text, "Scheduled Send portable/legacy projection missing")
    require('"jerkgram.ProtectedContent.Enabled": "GhostBase.ProtectedContent.Enabled"' in text, "protected-content portable/legacy projection missing")
    require('"jerkgram.ProtectedContent.OneTimeSave": "GhostBase.ProtectedContent.OneTimeSave"' in text, "one-time portable/legacy projection missing")
    require('UserDefaults(suiteName: "group.4a348a9b186b700c.1")' in text, "Scheduled Send shared-suite projection missing after import")

    require("JerkgramSettingsDidImport" in settings_text, "account-scoped settings refresh notification owner missing")
    require("rawAccountPeerId.int64Value == accountPeerId" in settings_text, "settings refresh is not filtered to the current account")
    require("ActionDisposable" in settings_text, "settings import observer is not tied to signal lifetime")
    require("GhostBaseSettingsState.load(accountPeerId: accountPeerId, mirrorLegacy: true)" in settings_text, "settings refresh does not reload persisted account state")
    require("stateValue.modify { _ in refreshed }" in settings_text, "settings Atomic state is not refreshed after import")
    require("statePromise.set(refreshed)" in settings_text, "settings UI promise is not refreshed after import")
    require("let stateSignal = combineLatest" in settings_text, "existing Build123 settings state pipeline was not preserved")
    require("combineLatest(stateSignal, jerkgramImportRefreshSignal)" in settings_text, "settings refresh signal is not retained by controller state pipeline")
    require("|> map { value, _ in value }" in settings_text, "settings refresh wrapper does not preserve the completed Build123 state value")

    require("Queue.mainQueue().async" in import_text, "import confirmation/error UI is not marshalled to main queue")
    require("controller.present(alert, in: .window(.root), with: nil)" in import_text, "import UI presentation missing")

    print("[verify Build124 archive import runtime] SOURCE VERIFIED")
    print("[verify Build124 archive import runtime] ZIP/decode/validation and transaction commit stay off UI thread")
    print("[verify Build124 archive import runtime] imported settings refresh active runtime and the open account-scoped Settings controller")


if __name__ == "__main__":
    main()
