#!/usr/bin/env python3

from pathlib import Path
import os
import shutil
import unicodedata


REPO = Path(__file__).resolve().parents[1]
PAYLOAD = REPO / "scripts/jerkgram_v12g_build118_time_machine1_payload"
ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
DEST = ROOT / "submodules/JerkgramCore/Sources"


def require(value, message):
    if not value:
        raise RuntimeError("[Build118 Time Machine] " + message)


def query_records(records, account, chat, kinds=None, sender=None, text=None):
    needle = unicodedata.normalize("NFKD", text or "").casefold()
    result = []
    identities = set()
    for row in records:
        identity = (int(row["account"]), str(row["eventId"]))
        if identity in identities:
            continue
        identities.add(identity)
        if int(row["account"]) != account or int(row["chat"]) != chat:
            continue
        if kinds and row["kind"] not in kinds:
            continue
        if sender is not None and row.get("sender") != sender:
            continue
        if needle and needle not in unicodedata.normalize("NFKD", row.get("search", "")).casefold():
            continue
        result.append(row)
    return result


def _graphemes(value):
    result = []
    for character in value:
        if result and (unicodedata.combining(character) or character == "\u200d" or result[-1].endswith("\u200d")):
            result[-1] += character
        else:
            result.append(character)
    return result


def reference_diff(old, new):
    import difflib
    lhs = _graphemes(old)
    rhs = _graphemes(new)
    result = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=lhs, b=rhs, autojunk=False).get_opcodes():
        if tag == "equal":
            result.extend(("equal", value) for value in lhs[i1:i2])
        elif tag == "delete":
            result.append(("delete", "".join(lhs[i1:i2])))
        elif tag == "insert":
            result.append(("insert", "".join(rhs[j1:j2])))
        else:
            result.append(("replace", "".join(lhs[i1:i2]) + "→" + "".join(rhs[j1:j2])))
    return result


def main():
    require(DEST.is_dir(), "JerkgramCore must be materialized first")
    for name in ("JerkgramTimeMachineIndex.swift", "JerkgramTextDiff.swift"):
        source = PAYLOAD / name
        target = DEST / name
        require(source.is_file(), "payload missing: " + name)
        require(not target.exists(), "owner already exists: " + name)
        shutil.copy2(source, target)
    print("[Build118 Time Machine] reference index, Unicode diff and visit watermarks materialized")


if __name__ == "__main__":
    main()
