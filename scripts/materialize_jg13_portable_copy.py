"""Guarded follow-up to immutable Build158 recovery owners."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from materialize_jg13_deleted_reply import check as check_parent

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches/jg13-portable-copy.patch"
MANIFEST = ROOT / "patches/jg13-portable-copy.sha256.json"
ACCOUNT = "submodules/TelegramCore/Sources/Account/Account.swift"
ENQUEUE = "submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift"
HELPER = "submodules/TelegramCore/Sources/PendingMessages/JerkgramDeletedReplyText.swift"
STATE = "submodules/TelegramCore/Sources/State/AccountStateManager.swift"
UI = "submodules/TelegramUI/Sources/ChatControllerForwardMessages.swift"
CORE_PARENT_OWNERS = {ENQUEUE, HELPER}
OWNERS = CORE_PARENT_OWNERS | {STATE, UI}
REMOVED_UI_FUNCTIONS = {
    "jerkgramRequiresPortableForward", "jerkgramPortableForwardBaseMessage",
    "jerkgramProtectedResourceData", "jerkgramPortableForwardMessage",
}


def read_manifest():
    manifest = json.loads(MANIFEST.read_text())
    parent = json.loads((ROOT / "patches/jg13-deleted-reply.sha256.json").read_text())
    stable = json.loads((ROOT / "patches/jg13-stable.product.sha256.json").read_text())
    config = json.loads((ROOT / "jerkgram-migration.json").read_text())
    if manifest["upstream_sha"] != parent["upstream_sha"] or manifest["upstream_sha"] != config["upstream_new_sha"]:
        raise RuntimeError("Portable copy upstream pin changed")
    if set(manifest["owners"]) != OWNERS or manifest["regression_locks"] != parent["regression_locks"]:
        raise RuntimeError("Portable copy scope/locks changed")
    for name, values in manifest["owners"].items():
        expected = parent["owners"][name]["after_sha256"] if name in CORE_PARENT_OWNERS else stable[name]
        if values["before_sha256"] != expected:
            raise RuntimeError("Portable copy parent hash changed: " + name)
        removed = set(values.get("removed_functions", []))
        if removed != (REMOVED_UI_FUNCTIONS if name == UI else set()):
            raise RuntimeError("Unreviewed removed functions: " + name)
    return manifest


def check(source, stage):
    if stage not in ("before", "after"):
        raise ValueError(stage)
    manifest = read_manifest()
    source = Path(source)
    for name, values in manifest["owners"].items():
        data = (source / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != values[stage + "_sha256"]:
            raise RuntimeError("Portable copy " + stage + " owner changed: " + name)
        functions = set(re.findall(r"(?m)^\s*(?:(?:public|private|fileprivate|internal|override|static|class|final|@objc)\s+)*func\s+(\w+)", data.decode()))
        required = set(values["survival_functions"])
        removed = set(values.get("removed_functions", []))
        if not required <= functions or (stage == "before" and not removed <= functions) or (stage == "after" and removed & functions):
            raise RuntimeError("Portable copy function contract changed: " + name)
    for name, expected in manifest["regression_locks"].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError("Portable copy regression lock changed: " + name)
    return manifest


def verify_portable_copy(source):
    manifest = check(source, "after")
    check_parent(source, "after", final_owners=manifest["owners"])


def apply_portable_copy(source):
    source = Path(source).resolve()
    git_root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=source, text=True).strip()).resolve()
    if git_root != source:
        raise RuntimeError("Portable copy source must be its own Git root")
    check(source, "before")
    check_parent(source, "after")
    names = {line.split("\t", 2)[2] for line in subprocess.check_output(["git", "apply", "--numstat", str(PATCH)], cwd=source, text=True).splitlines()}
    if names != OWNERS:
        raise RuntimeError("Portable copy patch scope differs")
    subprocess.run(["git", "apply", "--check", str(PATCH)], cwd=source, check=True)
    subprocess.run(["git", "apply", str(PATCH)], cwd=source, check=True)
    verify_portable_copy(source)
    print("Portable copy delta PATCHED / HASH VERIFIED; NOT COMPILED / NOT RUNTIME TESTED")
