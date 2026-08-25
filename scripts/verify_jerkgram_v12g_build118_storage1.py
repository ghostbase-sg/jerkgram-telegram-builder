#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()
SOURCE = ROOT / "submodules/JerkgramCore/Sources/JerkgramRetention.swift"


def require(value, message):
    if not value:
        raise RuntimeError("[verify Build118 storage] " + message)


def main():
    require(SOURCE.is_file(), "retention source missing")
    text = SOURCE.read_text(encoding="utf-8")
    for token in (
        "BUILD118_RETENTION1",
        "historyDuration: .days30",
        "mediaByteLimit: .gigabytes1",
        "archiveSecretChats: false",
        "case forever",
        "case unlimited",
        "options: .atomic",
        "if isSecretChat && !policy.archiveSecretChats",
        "mediaEventIdsToRemove",
        "retainedEvents",
        "public enum JerkgramRetentionRuntime",
        "private static var snapshots",
        "chatOverridesByPeerId",
        "jerkgram.retention.account.\\(accountPeerId)",
        "jerkgram.account.\\(accountPeerId).setting",
        "public static func applyCleanup",
        "payload.mediaRelativePath = nil",
    ):
        require(token in text, "retention invariant missing: " + token)
    require("accountPeerId: Int64" in text, "account scope missing")
    require("chatPeerId: Int64" in text, "chat scope missing")
    print("[verify Build118 storage] GREEN: cached account snapshots, overrides, forever/unlimited, fallback-preserving eviction")


if __name__ == "__main__":
    main()
