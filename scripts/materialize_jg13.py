#!/usr/bin/env python3
"""Apply the reviewed Stable delta to the one pinned clean Telegram 13.0 tree."""
from pathlib import Path
import hashlib
import json
import subprocess
from materialize_jg13_profile_cleanup import apply_cleanup

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work/swiftgram-src"


def main():
    config = json.loads((ROOT / "jerkgram-migration.json").read_text())
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True).strip()
    if sha != config["upstream_new_sha"]:
        raise RuntimeError("Wrong upstream SHA; refusing to patch")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=SOURCE):
        raise RuntimeError("Expected clean upstream before materialization")
    patch = ROOT / "patches/jg13-stable.product.patch"
    subprocess.run(["git", "apply", "--check", str(patch)], cwd=SOURCE, check=True)
    subprocess.run(["git", "apply", str(patch)], cwd=SOURCE, check=True)
    manifest = json.loads((ROOT / "patches/jg13-stable.product.sha256.json").read_text())
    for name, expected in manifest.items():
        actual = hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"Materialized owner hash mismatch: {name}")
    # Keep the reviewed Stable port immutable; the bounded follow-up is separately auditable.
    followup = ROOT / "patches/jg13-beta1-followup.patch"
    subprocess.run(["git", "apply", "--check", str(followup)], cwd=SOURCE, check=True)
    subprocess.run(["git", "apply", str(followup)], cwd=SOURCE, check=True)
    followup_manifest = json.loads((ROOT / "patches/jg13-beta1-followup.sha256.json").read_text())
    for name, expected in followup_manifest.items():
        if hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Follow-up owner hash mismatch: {name}")
    apply_cleanup(SOURCE)
    print(f"PATCHED / VERIFIED: {len(manifest)} Stable owners + {len(followup_manifest)} bounded follow-up owners + 7 cleanup owners; NOT COMPILED")


if __name__ == "__main__":
    main()
