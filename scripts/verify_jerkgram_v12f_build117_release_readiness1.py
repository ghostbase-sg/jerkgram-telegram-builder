#!/usr/bin/env python3

from pathlib import Path
import os
import re


SOURCE_ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
BUILDER_ROOT = Path(__file__).resolve().parents[1]
SETTINGS = SOURCE_ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramSettingsStore.swift"
ARCHIVE = SOURCE_ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramArchive.swift"
PROFILE_REPORT = SOURCE_ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileReportPaneNode.swift"
ACTIVE_WORKFLOWS = (
    BUILDER_ROOT / ".github/workflows/build.yml",
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
    profile_report = PROFILE_REPORT.read_text(encoding="utf-8")
    require("localizedProfileReport(rawText)" in profile_report, "profile logging localization gate missing")

    for path in ACTIVE_WORKFLOWS:
        workflow = path.read_text(encoding="utf-8")
        # Build117 predates the canary naming convention. Successor workflows
        # may publish either a normal release-line artifact (Jerkgram-buildN)
        # or an explicitly non-public canary (Jerkgram-BuildN-canary). Both
        # still have to represent Build118 or newer; this gate never accepts a
        # generic/unversioned artifact name.
        artifact_builds = [int(value) for value in re.findall(r"Jerkgram-build(\d+)", workflow)]
        artifact_builds += [int(value) for value in re.findall(r"Jerkgram-Build(\d+)-canary", workflow)]
        require(
            artifact_builds and max(artifact_builds) >= 118,
            f"{path.name}: Build118-or-newer Jerkgram artifact missing",
        )
        success_ipa_uploads = re.findall(
            r"(?ms)^\s*- name: Upload Jerkgram .*?\n\s*if: success\(\)\n\s*uses: actions/upload-artifact@v4",
            workflow,
        )
        require(len(success_ipa_uploads) == 1, f"{path.name}: exactly one successful Jerkgram IPA upload required")
        require("name: Upload materialized Build124 diagnostic owners" not in workflow or "if: failure()" in workflow, f"{path.name}: diagnostic artifact must remain failure-only")
        require("if: always()" not in workflow, f"{path.name}: duplicate always-upload remains")
        # Release packaging must never copy an unrelated Whitegram dylib payload.
        require("Whitegram" not in workflow, f"{path.name}: foreign payload reference")
    print("[Build117 release readiness] GREEN: foundations retained; Build118+ successor artifact; exactly one success artifact; no foreign payload")


if __name__ == "__main__":
    main()
