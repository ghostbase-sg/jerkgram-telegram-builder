#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
text = (root / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift").read_text(encoding="utf-8")
if text.count("Version: v1.1D-reference") != 2:
    raise SystemExit(f"[VERIFY V11D VERSION] expected 2 labels, got {text.count('Version: v1.1D-reference')}")

builder_root = Path(os.environ.get("GHOSTBASE_BUILDER_ROOT", Path(__file__).resolve().parents[1]))
canonical_path = builder_root / "scripts/bazel_build_probe_official.sh"
if canonical_path.is_file():
    canonical = canonical_path.read_text(encoding="utf-8")
    proofs = [
        'echo "-- verify Version: v1.1D-reference --"',
        'Final IPA does not contain Version: v1.1D-reference',
        '== v1.1C version verifier superseded by v1.1D ==',
        '# MARK: GhostBase v1.1D reference rebuild candidate',
    ]
    for proof in proofs:
        if canonical.count(proof) != 1:
            raise SystemExit(f"[VERIFY V11D VERSION] canonical proof count invalid: {proof!r} -> {canonical.count(proof)}")
    if 'echo "-- verify Version: v1.1C-stage1 --"' in canonical:
        raise SystemExit("[VERIFY V11D VERSION] stale v1.1C final IPA gate remains")

print("[VERIFY V11D VERSION] OK")
