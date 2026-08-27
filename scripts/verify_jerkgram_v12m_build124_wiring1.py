#!/usr/bin/env python3

from pathlib import Path
import os

from install_jerkgram_v12m_build124_probe_hook import (
    APPLY_ORDERED,
    VERIFY_ORDERED,
    FINAL_ORDERED,
    SOURCE_MARKER,
    FINAL_MARKER,
    API_APPLY,
    API_VERIFY,
    BAZEL_ANCHOR,
)


PROBE = Path(
    os.environ.get(
        "JERKGRAM_PROBE_PATH",
        str(Path(__file__).resolve().parent / "bazel_build_probe_official.sh"),
    )
).resolve()


def fail(message: str) -> None:
    raise SystemExit("[verify Build124 wiring] ERROR: " + message)


def require(value: bool, message: str) -> None:
    if not value:
        fail(message)


def main() -> None:
    require(PROBE.is_file(), f"probe missing: {PROBE}")
    text = PROBE.read_text(encoding="utf-8")

    require(text.count(SOURCE_MARKER) == 1, "Build124 source marker count")
    require(text.count(FINAL_MARKER) == 1, "Build124 final marker count")
    require("verify_jerkgram_v12l_build123_release_recovery1.py" in text, "Build123 source base missing")
    require("verify_jerkgram_v12l_build123_final_ipa.py" in text, "Build123 final base missing")

    apply_positions = []
    for name in APPLY_ORDERED:
        require(text.count(name) == 1, f"apply hook count for {name}")
        apply_positions.append(text.index(name))
    require(apply_positions == sorted(apply_positions), "Build124 apply order")

    verifier_positions = []
    for name in VERIFY_ORDERED:
        require(text.count(name) == 1, f"verifier hook count for {name}")
        verifier_positions.append(text.index(name))
    require(verifier_positions == sorted(verifier_positions), "Build124 verifier order")
    require(max(apply_positions) < min(verifier_positions), "source verifier runs before all Build124 applies")

    bazel = text.index(BAZEL_ANCHOR)
    require(max(verifier_positions) < bazel, "Build124 source gate must finish before Bazel")
    require(text.index(API_APPLY) < text.index(API_VERIFY) < bazel, "private Telegram API canary order")

    require(
        text.index("apply_jerkgram_v12m_build124_onetime_persistence1.py")
        < text.index("apply_jerkgram_v12m_build124_onetime_viewed1.py"),
        "one-time persistence/viewed dependency order",
    )

    final_positions = []
    for name in FINAL_ORDERED:
        require(text.count(name) == 1, f"final hook count for {name}")
        final_positions.append(text.index(name))
    require(final_positions == sorted(final_positions), "Build124 final identity order")
    require(text.index("verify_jerkgram_v12l_build123_final_ipa.py") < final_positions[0], "Build124 final identity must follow Build123 IPA verifier")

    print("[verify Build124 wiring] SOURCE VERIFIED")
    print(f"[verify Build124 wiring] {len(APPLY_ORDERED)} late source overlays + {len(VERIFY_ORDERED)} source verifiers wired before Bazel")
    print("[verify Build124 wiring] private Telegram API canary remains configuration-scoped")
    print("[verify Build124 wiring] final IPA identity advances to Build124 after the Build123 baseline verifier")


if __name__ == "__main__":
    main()
