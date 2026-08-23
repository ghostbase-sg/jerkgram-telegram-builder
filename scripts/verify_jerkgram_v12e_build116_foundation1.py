#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()

SETTINGS = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramSettingsStore.swift"
ARCHIVE = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramArchive.swift"


def require(value, message):
    if not value:
        raise RuntimeError("[verify Build116 foundation] " + message)


def verify(settings, archive):
    require(settings.count("BUILD116_SETTINGS_FOUNDATION1") == 1, "Settings marker count != 1")
    require(archive.count("BUILD116_ARCHIVE_FOUNDATION1") == 1, "Archive marker count != 1")
    for token in (
        "JerkgramSettingsV1: Codable, Equatable",
        "JerkgramSendStyleV1: String, Codable, CaseIterable",
        "func load() throws -> JerkgramSettingsV1",
        "func save(_ value: JerkgramSettingsV1) throws",
        "unsupportedSchemaVersion",
        ".atomic",
    ):
        require(token in settings, "Settings invariant missing: " + token)
    for token in (
        "JerkgramArchiveManifestV1: Codable, Equatable",
        "JerkgramArchiveEventV1: Codable, Equatable",
        "JerkgramArchiveV1: Codable, Equatable",
        "maximumEventCount = 100_000",
        "values[event.identity] = event",
        "values.values.sorted",
        "JSONEncoder.OutputFormatting.sortedKeys",
    ):
        require(token in archive, "Archive invariant missing: " + token)
    for forbidden in (
        "authKey", "accessToken", "sessionToken", "mobileprovision", "signingCertificate",
    ):
        require(forbidden not in archive, "forbidden archive field: " + forbidden)


def main():
    require(SETTINGS.is_file(), "Settings foundation missing")
    require(ARCHIVE.is_file(), "Archive foundation missing")
    verify(SETTINGS.read_text(encoding="utf-8"), ARCHIVE.read_text(encoding="utf-8"))
    print("[verify Build116 foundation] GREEN: typed, versioned, bounded, deterministic")


if __name__ == "__main__":
    main()
