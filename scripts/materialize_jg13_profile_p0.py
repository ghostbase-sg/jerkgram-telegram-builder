#!/usr/bin/env python3
"""Guarded profile diagnostics and secondary-timebase ownership compatibility."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from materialize_jg13_profile_cleanup import verify_cleanup

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches/jg13-profile-p0-diagnostics.patch"
MANIFEST = ROOT / "patches/jg13-profile-p0-diagnostics.sha256.json"

def check(source, stage, final_owners=None):
    manifest = json.loads(MANIFEST.read_text())
    config = json.loads((ROOT / "jerkgram-migration.json").read_text())
    if final_owners:
        if stage != "after":
            raise RuntimeError("Final owner override is only valid after materialization")
        # Later reviewed delta owners retain full exact output hashes, never
        # marker-only exceptions; untouched P0 owners keep their original gates.
        for name in set(manifest["owners"]) & set(final_owners):
            manifest["owners"][name]["after_sha256"] = final_owners[name]["after_sha256"]
    if config["upstream_new_sha"] != manifest["upstream_sha"]:
        raise RuntimeError("P0 diagnostics require the reviewed upstream pin")
    for name, hashes in manifest["owners"].items():
        file = source / name
        if stage == "before" and hashes.get("absent_before"):
            if file.exists():
                raise RuntimeError(f"P0 unexpected new owner already exists: {name}")
            data = b""
        else:
            data = file.read_bytes()
        if hashlib.sha256(data).hexdigest() != hashes[stage + "_sha256"]:
            raise RuntimeError(f"P0 {stage} owner hash mismatch: {name}")
        declarations = set(re.findall(r"(?m)^\s*(?:(?:public|private|fileprivate|internal|override|static|class|final|@objc)\s+)*func\s+(\w+)", data.decode()))
        if not set(hashes["survival_functions"]) <= declarations:
            raise RuntimeError(f"P0 function-survival failure: {name}")
    for name, expected in manifest["regression_locks"].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"P0 regression lock changed: {name}")
    return manifest

def verify_p0(source, final_owners=None):
    source = Path(source).resolve()
    manifest = check(source, "after", final_owners=final_owners)
    # All seven cleanup owners still have exact final hashes. Only the two
    # deliberately instrumented ones use the later reviewed stage's hashes.
    verify_cleanup(source, final_owners=manifest["owners"])
    env = dict(os.environ, JG13_SOURCE=str(source))
    subprocess.run([sys.executable, str(ROOT / "tests/test_jg13_profile_p0.py")], cwd=ROOT, env=env, check=True)
    subprocess.run([sys.executable, str(ROOT / "tests/test_jg13_performance_capture.py")], cwd=ROOT, env=env, check=True)
    subprocess.run([sys.executable, str(ROOT / "tests/test_jg13_secondary_timebase.py")], cwd=ROOT, env=env, check=True)

def apply_p0(source):
    source = Path(source).resolve()
    git_root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=source, text=True).strip()).resolve()
    if git_root != source:
        raise RuntimeError("P0 source must be its own Git root")
    manifest = check(source, "before")
    names = {line.split("\t", 2)[2] for line in subprocess.check_output(["git", "apply", "--numstat", str(PATCH)], cwd=source, text=True).splitlines()}
    if names != set(manifest["owners"]):
        raise RuntimeError("P0 patch owner set differs from manifest")
    subprocess.run(["git", "apply", "--check", str(PATCH)], cwd=source, check=True)
    subprocess.run(["git", "apply", str(PATCH)], cwd=source, check=True)
    verify_p0(source)
    print("P0 diagnostics PATCHED / VERIFIED; NOT COMPILED / NOT RUNTIME TESTED")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "work/swiftgram-src")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.apply:
        apply_p0(args.source)
    else:
        verify_p0(args.source)
        print("P0 final hashes, structural contracts and regression locks VERIFIED; NOT COMPILED")

if __name__ == "__main__":
    main()
