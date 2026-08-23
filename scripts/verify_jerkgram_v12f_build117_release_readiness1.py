#!/usr/bin/env python3

from pathlib import Path
import os


SOURCE_ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
BUILDER_ROOT = Path(__file__).resolve().parents[1]
SETTINGS = SOURCE_ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramSettingsStore.swift"
ARCHIVE = SOURCE_ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramArchive.swift"
ACTIVE_WORKFLOWS = (
    BUILDER_ROOT / ".github/workflows/build.yml",
    BUILDER_ROOT / ".github/workflows/build-official.yml",
)


def require(value, message):
    if not value:
        raise RuntimeError("[Build117 release readiness] " + message)


def main():
    settings = SETTINGS.read_text(encoding="utf-8")
    archive = ARCHIVE.read_text(encoding="utf-8")
    require("BUILD116_SETTINGS_FOUNDATION1" in settings, "typed Settings foundation missing")
    require("public var schemaVersion: Int = 1" in settings, "Settings schemaVersion is not v1")
    require("BUILD116_ARCHIVE_FOUNDATION1" in archive, "typed Archive foundation missing")
    require("public var schemaVersion: Int = 1" in archive, "Archive schemaVersion is not v1")
    require("maximumEventCount = 100_000" in archive, "bounded Archive codec missing")

    for path in ACTIVE_WORKFLOWS:
        workflow = path.read_text(encoding="utf-8")
        require("Jerkgram-build117" in workflow, f"{path.name}: Build117 artifact missing")
        require(workflow.count("uses: actions/upload-artifact@v4") == 1, f"{path.name}: exactly one success artifact required")
        require("if: always()" not in workflow, f"{path.name}: duplicate always-upload remains")
        # Release packaging must never copy an unrelated Whitegram dylib payload.
        require("Whitegram" not in workflow, f"{path.name}: foreign payload reference")
    print("[Build117 release readiness] GREEN: foundations retained; exactly one success artifact; no foreign payload")


if __name__ == "__main__":
    main()
