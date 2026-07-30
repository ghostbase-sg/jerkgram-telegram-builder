#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        "/root/gb_builder/work/swiftgram-src"
    )
)

settings_path = (
    root
    / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
)

text = settings_path.read_text(encoding="utf-8")

# At the v1.1D checkpoint, before v1.1E is applied, both visible labels
# must still contain the v1.1D version.
count = text.count("Version: v1.1D-reference")
if count != 2:
    raise SystemExit(
        f"[VERIFY V11D VERSION] expected 2 labels, got {count}"
    )

builder_root = Path(
    os.environ.get(
        "GHOSTBASE_BUILDER_ROOT",
        Path(__file__).resolve().parents[1]
    )
)

canonical_path = builder_root / "scripts/bazel_build_probe_official.sh"

if canonical_path.is_file():
    canonical = canonical_path.read_text(encoding="utf-8")

    # Verify only ownership of the historical v1.1D stage.
    # The final IPA version gate may legitimately be superseded by v1.1E+.
    required = [
        "# MARK: GhostBase v1.1D reference rebuild candidate",
        "# END MARK: GhostBase v1.1D reference rebuild candidate",
        'python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11d_version.py"',
    ]

    for proof in required:
        proof_count = canonical.count(proof)
        if proof_count != 1:
            raise SystemExit(
                "[VERIFY V11D VERSION] canonical stage proof "
                f"count invalid: {proof!r} -> {proof_count}"
            )

    has_v11d_gate = (
        'echo "-- verify Version: v1.1D-reference --"' in canonical
        and "Final IPA does not contain Version: v1.1D-reference" in canonical
    )

    has_successor_gate = (
        'echo "-- verify Version: v1.1E-audit --"' in canonical
        and "Final IPA does not contain Version: v1.1E-audit" in canonical
        and "# MARK: GhostBase v1.1E audit rebuild candidate" in canonical
    )

    has_v11f_successor_gate = (
        'echo "-- verify Version: v1.1F-profile-header --"' in canonical
        and "Final IPA does not contain Version: v1.1F-profile-header" in canonical
        and "# MARK: GhostBase v1.1F profile header blur" in canonical
    )

    has_v11g_successor_gate = (
        'echo "-- verify Version: v1.1G-unified-recovery --"' in canonical
        and "Final IPA does not contain Version: v1.1G-unified-recovery" in canonical
        and "# MARK: GhostBase v1.1G unified recovery" in canonical
    )

    if (
        not has_v11d_gate
        and not has_successor_gate
        and not has_v11f_successor_gate
        and not has_v11g_successor_gate
    ):
        raise SystemExit(
            "[VERIFY V11D VERSION] neither the original v1.1D final "
            "gate nor a valid v1.1E/v1.1F/v1.1G successor gate exists"
        )

    if 'echo "-- verify Version: v1.1C-stage1 --"' in canonical:
        raise SystemExit(
            "[VERIFY V11D VERSION] stale v1.1C final IPA gate remains"
        )

print("[VERIFY V11D VERSION] OK")
