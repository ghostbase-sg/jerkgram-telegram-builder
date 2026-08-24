#!/usr/bin/env python3

from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import shutil


REPO = Path(__file__).resolve().parents[1]
PAYLOAD = REPO / "scripts/jerkgram_v12g_build118_archive1_payload"
ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
DEST = ROOT / "submodules/JerkgramCore/Sources"


def require(value, message):
    if not value:
        raise RuntimeError("[Build118 Archive v2] " + message)


def safe_relative_path(value):
    path = PurePosixPath(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts and "." not in path.parts


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def classify(existing, incoming):
    by_identity = {(int(row["accountPeerId"]), str(row["eventId"])): json.dumps(row, sort_keys=True, separators=(",", ":")) for row in existing}
    result = {"duplicate": 0, "new": 0, "conflict": 0}
    for row in incoming:
        identity = (int(row["accountPeerId"]), str(row["eventId"]))
        canonical = json.dumps(row, sort_keys=True, separators=(",", ":"))
        if identity not in by_identity:
            result["new"] += 1
        elif by_identity[identity] == canonical:
            result["duplicate"] += 1
        else:
            result["conflict"] += 1
    return result


def accounts_available(selected, available):
    return set(selected).issubset(set(available))


def main():
    require(DEST.is_dir(), "JerkgramCore must be materialized first")
    for name in ("JerkgramArchiveV2.swift", "JerkgramArchiveTransaction.swift"):
        source = PAYLOAD / name
        target = DEST / name
        require(source.is_file(), "payload missing: " + name)
        require(not target.exists(), "owner already exists: " + name)
        shutil.copy2(source, target)
    print("[Build118 Archive v2] account-scoped manifest, checksum validation and rollback transaction materialized")


if __name__ == "__main__":
    main()
