#!/usr/bin/env python3
"""Extend the exact current Telegram13.2 product with the experimental observer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from materialize_jg132_product import materialize as materialize_product

ROOT = Path(__file__).resolve().parents[1]
PIN = "24638bc69bd083981b178dd1e7f921eebbf7fc46"


def verify_pin(source):
    source = Path(source).resolve()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    versions = json.loads(subprocess.check_output(["git", "show", "HEAD:versions.json"], cwd=source))
    if head != PIN or versions["app"] != "13.2" or versions["xcode"] != "27.1" or versions["bazel"].split(":")[0] != "9.2.0":
        raise RuntimeError("Observer requires exact current Telegram13.2 source and pinned toolchain")
    return source


def apply_observer(source):
    env = dict(os.environ, JERKGRAM_SOURCE_ROOT=str(source), GHOSTBASE_SOURCE_ROOT=str(source))
    for name in ("apply_jerkgram_profile_observer_v1.py", "verify_jerkgram_profile_observer_v1.py"):
        subprocess.run([sys.executable, str(ROOT / "scripts" / name)], cwd=source, env=env, check=True)


def materialize(source, *, baseline_only=False, require_native=False):
    source = verify_pin(source)
    evidence = ROOT / "artifacts/profile-observer-materialization.json"
    evidence.parent.mkdir(exist_ok=True)
    manifest = {"telegram_commit": PIN, "builder_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "base": "current-13.2-product", "baseline_materialized": False, "baseline_native_gate": "not-run",
                "observer_materialized": False, "native_app_compile": "not-run"}
    def save():
        evidence.write_text(json.dumps(manifest, indent=2) + "\n")
    save()
    materialize_product(source)
    manifest["baseline_materialized"] = True
    save()
    if require_native:
        # Exact product ownership hashes are verified before the observer successor.
        env = dict(os.environ, JG_STABLE182_SOURCE=str(source))
        subprocess.run([sys.executable, str(ROOT / "tests/run_jg132_post181.py"), "--require-native", "--require-full-source"], cwd=ROOT, env=env, check=True)
        manifest["baseline_native_gate"] = "passed"
        save()
    if not baseline_only:
        apply_observer(source)
        manifest["observer_materialized"] = True
        payload = ROOT / "scripts/jerkgram_profile_observer_v1_payload"
        manifest["observer_payload_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(payload.glob("*.swift"))}
        save()
    print("Telegram13.2 materialization complete; native app compilation remains separate.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT / "work/swiftgram-src")
    parser.add_argument("--baseline-only", action="store_true")
    parser.add_argument("--require-native", action="store_true")
    args = parser.parse_args()
    materialize(args.source_root, baseline_only=args.baseline_only, require_native=args.require_native)


if __name__ == "__main__":
    main()
