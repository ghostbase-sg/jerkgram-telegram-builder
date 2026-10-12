"""Exact three-owner recovery delta; original product stages remain immutable."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches/jg13-deleted-reply.patch"
MANIFEST = ROOT / "patches/jg13-deleted-reply.sha256.json"
ACCOUNT = "submodules/TelegramCore/Sources/Account/Account.swift"
ENQUEUE = "submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift"
HELPER = "submodules/TelegramCore/Sources/PendingMessages/JerkgramDeletedReplyText.swift"
OWNERS = {ACCOUNT, ENQUEUE, HELPER}


def read_manifest():
    manifest = json.loads(MANIFEST.read_text())
    config = json.loads((ROOT / "jerkgram-migration.json").read_text())
    parent = json.loads((ROOT / "patches/jg13-expanded-diagnostics.sha256.json").read_text())
    if manifest["upstream_sha"] != config["upstream_new_sha"] or manifest["upstream_sha"] != parent["upstream_sha"]:
        raise RuntimeError("Deleted reply upstream pin changed")
    if set(manifest["owners"]) != OWNERS or manifest["regression_locks"] != parent["regression_locks"]:
        raise RuntimeError("Deleted reply owner scope or regression locks changed")
    return manifest


def check(source, stage, final_owners=None):
    if stage not in ("before", "after"):
        raise ValueError(stage)
    if final_owners and stage != "after":
        raise RuntimeError("Final owner hashes are valid only after materialization")
    source = Path(source)
    manifest = read_manifest()
    for name, values in manifest["owners"].items():
        path = source / name
        expected = values[stage + "_sha256"]
        if final_owners and name in final_owners:
            expected = final_owners[name]["after_sha256"]
        if expected is None:
            if path.exists():
                raise RuntimeError("Deleted reply new owner already exists: " + name)
            continue
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise RuntimeError("Deleted reply " + stage + " hash mismatch: " + name)
        declarations = set(re.findall(r"(?m)^\s*(?:(?:public|private|fileprivate|internal|override|static|class|final|@objc)\s+)*func\s+(\w+)", data.decode()))
        if not set(values["survival_functions"]) <= declarations:
            raise RuntimeError("Deleted reply function lost: " + name)
    for name, expected in manifest["regression_locks"].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError("Deleted reply regression lock changed: " + name)


def apply_deleted_reply(source):
    source = Path(source).resolve()
    git_root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=source, text=True).strip()).resolve()
    if git_root != source:
        raise RuntimeError("Deleted reply source must be its own Git root")
    check(source, "before")
    names = {line.split("\t", 2)[2] for line in subprocess.check_output(["git", "apply", "--numstat", str(PATCH)], cwd=source, text=True).splitlines()}
    if names != OWNERS:
        raise RuntimeError("Deleted reply patch scope changed")
    subprocess.run(["git", "apply", "--check", str(PATCH)], cwd=source, check=True)
    subprocess.run(["git", "apply", str(PATCH)], cwd=source, check=True)
    check(source, "after")
    print("Deleted reply delta PATCHED / HASH VERIFIED; NOT COMPILED / NOT RUNTIME TESTED")
