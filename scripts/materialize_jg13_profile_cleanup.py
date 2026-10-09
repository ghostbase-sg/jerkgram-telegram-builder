#!/usr/bin/env python3
"""Guarded seven-owner delta after Stable + Beta follow-up; supports partial fixtures."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches/jg13-profile-cleanup.patch"
MANIFEST = ROOT / "patches/jg13-profile-cleanup.sha256.json"

def check_hashes(source, stage):
    manifest = json.loads(MANIFEST.read_text())
    config = json.loads((ROOT / "jerkgram-migration.json").read_text())
    if manifest["upstream_sha"] != config["upstream_new_sha"]:
        raise RuntimeError("Cleanup delta belongs to a different pinned upstream")
    for name, hashes in manifest["owners"].items():
        actual = hashlib.sha256((source / name).read_bytes()).hexdigest()
        if actual != hashes[stage + "_sha256"]:
            raise RuntimeError(f"Profile cleanup {stage} owner hash mismatch: {name}")

def verify_cleanup(source):
    check_hashes(source, "after")
    env = dict(os.environ, JG13_SOURCE=str(source.resolve()))
    subprocess.run([sys.executable, str(ROOT / "tests/test_jg13_profile_cleanup.py")],
                   cwd=ROOT, env=env, check=True)

def apply_cleanup(source):
    source = Path(source).resolve()
    git_root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                            cwd=source, text=True).strip()).resolve()
    if git_root != source:
        raise RuntimeError("Cleanup source must be its own Git root; refusing nested-prefix application")
    check_hashes(source, "before")
    changed_paths = {line.split("\t", 2)[2] for line in subprocess.check_output(
        ["git", "apply", "--numstat", str(PATCH)], cwd=source, text=True).splitlines()}
    if changed_paths != set(json.loads(MANIFEST.read_text())["owners"]):
        raise RuntimeError("Cleanup patch owner set differs from the guarded manifest")
    subprocess.run(["git", "apply", "--check", str(PATCH)], cwd=source, check=True)
    subprocess.run(["git", "apply", str(PATCH)], cwd=source, check=True)
    verify_cleanup(source)
    print("PATCHED / VERIFIED: 7 profile/gifting cleanup owners; NOT COMPILED / NOT RUNTIME TESTED")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "work/swiftgram-src")
    parser.add_argument("--apply", action="store_true", help="Require exact current canonical parent hashes, then apply")
    args = parser.parse_args()
    if args.apply:
        apply_cleanup(args.source)
    else:
        verify_cleanup(args.source)
        print("VERIFIED: target-only structural contracts; NOT COMPILED / NOT RUNTIME TESTED")

if __name__ == "__main__":
    main()
