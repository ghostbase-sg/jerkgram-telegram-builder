#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
ARCHIVE = ROOT / "submodules/JerkgramCore/Sources/JerkgramArchiveV2.swift"
TRANSACTION = ROOT / "submodules/JerkgramCore/Sources/JerkgramArchiveTransaction.swift"


def require(value, message):
    if not value:
        raise RuntimeError("[verify Build118 Archive v2] " + message)


def main():
    require(ARCHIVE.is_file() and TRANSACTION.is_file(), "sources missing")
    archive = ARCHIVE.read_text(encoding="utf-8")
    transaction = TRANSACTION.read_text(encoding="utf-8")
    for token in ("schemaVersion = 2", "accountPeerId", "settingsSnapshot", "sha256", "maximumUncompressedBytes", "unsafePath", "checksumMismatch", "public init(\n        component:", "public init(\n        accountPeerId:"):
        require(token in archive, "archive invariant missing: " + token)
    for forbidden in ("authKey", "sessionToken", "provisioning", "embedded.mobileprovision"):
        require(forbidden not in archive, "forbidden archive payload: " + forbidden)
    for token in ("confirmSettingsChanges", "availableAccountPeerIds", "eventId", "rollback", "replaceAtomically"):
        require(token.lower() in transaction.lower(), "transaction invariant missing: " + token)
    require("payload.text" not in transaction, "text-based identity detected")
    print("[verify Build118 Archive v2] GREEN: exact accounts/IDs, SHA-256, traversal checks, settings confirmation, rollback")


if __name__ == "__main__":
    main()
