#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

from jerkgram_public_source import (
    build_manifest,
    create_deterministic_tar_xz,
    export_public_tree,
    load_policy,
    verify_export,
    write_json,
    write_release_metadata,
)


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Export deterministic Jerkgram public release source")
    parser.add_argument("--materialized-tree", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--build-number", required=True)
    parser.add_argument("--source-tag")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ipa", type=Path)
    parser.add_argument(
        "--policy",
        type=Path,
        default=script_dir / "jerkgram_public_source_policy.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    materialized = args.materialized_tree.resolve()
    if not materialized.is_dir():
        raise SystemExit(f"materialized tree does not exist: {materialized}")
    if args.ipa is not None and not args.ipa.is_file():
        raise SystemExit(f"IPA does not exist: {args.ipa}")

    policy = load_policy(args.policy)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    public_root = output / "source"

    # Secret scanning occurs inside export_public_tree before any exclusion.
    export_result = export_public_tree(materialized, public_root, policy, env=os.environ)

    verification = verify_export(materialized, public_root, policy)
    if not verification["ok"]:
        raise SystemExit("public source verification failed:\n" + "\n".join(verification["errors"]))

    internal_manifest_path = output / "internal-materialized-manifest.json"
    public_manifest_path = output / "public-source-manifest.json"
    exclusions_path = output / "excluded-paths.json"
    write_json(internal_manifest_path, build_manifest(materialized, policy=policy))
    write_json(public_manifest_path, verification["public_manifest"])
    write_json(exclusions_path, export_result["excluded"])

    archive_name = f"Jerkgram-{args.version}-source.tar.xz"
    archive_path = output / archive_name
    archive_hash = create_deterministic_tar_xz(
        public_root,
        archive_path,
        arc_prefix=f"Jerkgram-{args.version}-source",
    )
    (output / f"{archive_name}.sha256").write_text(
        f"{archive_hash}  {archive_name}\n",
        encoding="utf-8",
    )

    write_release_metadata(
        output / "JERKGRAM_RELEASE.json",
        version=args.version,
        build_number=args.build_number,
        archive_path=archive_path,
        public_manifest_path=public_manifest_path,
        ipa_path=args.ipa.resolve() if args.ipa is not None else None,
        source_tag=args.source_tag,
    )

    print(f"public source export OK: {public_root}")
    print(f"archive: {archive_path.name}")
    print(f"sha256: {archive_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
