#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramArchiveFlowController.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_ARCHIVE_EXPORT_RUNTIME1"
IMPORT_MARKER = "// MARK: Jerkgram v1.2M BUILD124_ARCHIVE_IMPORT_BACKGROUND1"


def fail(message: str) -> None:
    raise SystemExit("[verify Build124 archive export runtime] ERROR: " + message)


def require(value: bool, message: str) -> None:
    if not value:
        fail(message)


def balanced_region(text: str, token: str) -> str:
    start = text.find(token)
    require(start >= 0, f"function missing: {token}")
    brace = text.find("{", start + len(token))
    require(brace >= 0, f"opening brace missing: {token}")
    depth = 0
    in_string = False
    escaped = False
    for i in range(brace, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    fail("unbalanced Swift function: " + token)
    return ""


def main() -> None:
    require(TARGET.is_file(), f"materialized archive flow missing: {TARGET}")
    source = TARGET.read_text(encoding="utf-8")
    require(source.count(MARKER) == 1, "export marker must exist exactly once")
    require(source.count(IMPORT_MARKER) == 1, "archive import runtime overlay was lost")

    export = balanced_region(source, "public func jerkgramPresentArchiveExport(")
    require("Queue.concurrentDefaultQueue().async" in export, "export worker queue missing")
    require("JerkgramCaptureRecorder.flushSynchronously()" in export, "capture drain missing")
    require("let events = try eventStore.events(accountPeerId: accountPeerId, chatPeerId: nil)" in export, "canonical event read is not throwing")
    require("(try? eventStore.events" not in export, "store failure can still become empty history")
    require(") ?? []" not in export, "empty-history fallback survived")
    require("SSZipArchive.createZipFile" in export, "ZIP export owner missing")
    require("jerkgramPresentArchiveExportError(" in export, "visible error path missing")

    worker = export.index("Queue.concurrentDefaultQueue().async")
    drain = export.index("JerkgramCaptureRecorder.flushSynchronously()")
    read = export.index("eventStore.events(")
    zip_work = export.index("SSZipArchive.createZipFile")
    require(worker < drain < read < zip_work, "export work ordering is not worker -> drain -> canonical read -> ZIP")

    helper = balanced_region(source, "private func jerkgramPresentArchiveExportError(")
    require("Queue.mainQueue().async" in helper, "error UI does not return to main queue")
    require("presentationData.strings.jerkgram.exportArchive" in helper, "localized export title missing")
    require("presentationData.strings.Common_OK" in helper, "localized OK action missing")

    print("[verify Build124 archive export runtime] SOURCE VERIFIED")
    print("[verify Build124 archive export runtime] buffered capture drains before canonical snapshot; store failures cannot export empty history")
    print("[verify Build124 archive export runtime] ZIP remains off-main and failures return visibly on main")


if __name__ == "__main__":
    main()
