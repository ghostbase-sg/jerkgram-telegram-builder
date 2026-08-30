#!/usr/bin/env python3

from pathlib import Path
import os

from install_jerkgram_v12n_build125_probe_hook import (
    APPLY_ORDERED,
    VERIFY_ORDERED,
    FINAL_ORDERED,
    SOURCE_MARKER,
    FINAL_MARKER,
    BAZEL_ANCHOR,
)


PROBE = Path(
    os.environ.get(
        "JERKGRAM_PROBE_PATH",
        str(Path(__file__).resolve().parent / "bazel_build_probe_official.sh"),
    )
).resolve()


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit("[verify Build125 wiring] ERROR: " + message)


def main() -> None:
    require(PROBE.is_file(), f"probe missing: {PROBE}")
    text = PROBE.read_text(encoding="utf-8")
    require(text.count(SOURCE_MARKER) == 1, "Build125 source marker count")
    require(text.count(FINAL_MARKER) == 1, "Build125 final marker count")

    apply_positions = []
    for name in APPLY_ORDERED:
        require(text.count(name) == 1, f"apply hook count for {name}")
        apply_positions.append(text.index(name))
    verifier_positions = []
    for name in VERIFY_ORDERED:
        require(text.count(name) == 1, f"source verifier hook count for {name}")
        verifier_positions.append(text.index(name))
    require(apply_positions == sorted(apply_positions), "Build125 apply order")
    require(verifier_positions == sorted(verifier_positions), "Build125 verifier order")
    require(max(apply_positions) < min(verifier_positions), "source verifier runs before all Build125 applies")
    require(max(verifier_positions) < text.index(BAZEL_ANCHOR), "Build125 source gate must finish before Bazel")

    final_positions = []
    for name in FINAL_ORDERED:
        require(text.count(name) == 1, f"final hook count for {name}")
        final_positions.append(text.index(name))
    require(final_positions == sorted(final_positions), "Build125 final identity order")
    require(
        text.index("verify_jerkgram_v12m_build124_final_ipa.py") < final_positions[0],
        "Build125 final identity must follow Build124 IPA verifier",
    )
    print("[verify Build125 wiring] SOURCE VERIFIED")
    print(f"[verify Build125 wiring] {len(APPLY_ORDERED)} source overlays + {len(VERIFY_ORDERED)} source verifiers wired before Bazel")


if __name__ == "__main__":
    main()
