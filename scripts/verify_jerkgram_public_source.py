#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from jerkgram_public_source import build_manifest, load_policy, verify_export


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Verify Jerkgram public source export against materialized tree")
    parser.add_argument("--materialized-tree", required=True, type=Path)
    parser.add_argument("--export-dir", required=True, type=Path)
    parser.add_argument(
        "--policy",
        type=Path,
        default=script_dir / "jerkgram_public_source_policy.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    materialized = args.materialized_tree.resolve()
    export_dir = args.export_dir.resolve()
    public_root = export_dir / "source"
    if not materialized.is_dir():
        raise SystemExit(f"materialized tree does not exist: {materialized}")
    if not public_root.is_dir():
        raise SystemExit(f"public source tree does not exist: {public_root}")

    policy = load_policy(args.policy)
    result = verify_export(materialized, public_root, policy)
    errors = list(result["errors"])

    stored_manifest = export_dir / "public-source-manifest.json"
    if stored_manifest.exists():
        expected = json.loads(stored_manifest.read_text(encoding="utf-8"))
        current = build_manifest(public_root)
        if expected != current:
            errors.append("stored public-source-manifest.json mismatch")
    else:
        errors.append("missing public-source-manifest.json")

    if errors:
        print("public source verification FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("public source verification OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
