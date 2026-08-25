#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

PROBE = Path(os.environ.get(
    "JERKGRAM_PROBE_PATH",
    str(Path(__file__).resolve().parent / "bazel_build_probe_official.sh"),
)).resolve()

SOURCE_ORDERED = (
    "apply_jerkgram_v12j_build121_sticker_recovery1.py",
    "verify_jerkgram_v12j_build121_sticker_recovery1.py",
)
SOURCE_ANCHOR = "python3 ../../scripts/verify_jerkgram_v12i_build120_sticker_alpha1.py\n"
BAZEL_ANCHOR = '"$BAZEL_BIN" build'

FINAL_ORDERED = (
    "jerkgram_finalize_build121_identity.py",
    "verify_jerkgram_v12j_build121_final_ipa.py",
)
FINAL_ANCHOR = (
    "python3 ../../scripts/verify_jerkgram_v12i_build120_final_ipa.py "
    "ghostbase-final/GhostBase.ipa"
)


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build121 probe hook] " + message)


def source_line(name: str) -> str:
    return "python3 ../../scripts/" + name


def final_line(name: str) -> str:
    return source_line(name) + " ghostbase-final/GhostBase.ipa"


def main() -> None:
    require(PROBE.is_file(), "probe missing: " + str(PROBE))
    text = PROBE.read_text(encoding="utf-8")

    counts = [text.count(name) for name in SOURCE_ORDERED]
    if all(count == 0 for count in counts):
        require(text.count(SOURCE_ANCHOR) == 1, "Build120 sticker verifier anchor count != 1")
        block = (
            SOURCE_ANCHOR
            + '\necho\necho "== Jerkgram v1.2J Build121 native sticker recovery =="\n'
            + "\n".join(source_line(name) for name in SOURCE_ORDERED)
            + "\n"
        )
        text = text.replace(SOURCE_ANCHOR, block, 1)
    else:
        require(all(count == 1 for count in counts), "partial Build121 source wiring")

    positions = [text.index(name) for name in SOURCE_ORDERED]
    require(positions == sorted(positions), "Build121 source order invalid")
    require(text.index("verify_jerkgram_v12i_build120_sticker_alpha1.py") < positions[0], "Build121 runs before Build120 sticker gate")
    require(positions[-1] < text.index(BAZEL_ANCHOR), "Build121 runs after Bazel")

    final_counts = [text.count(name) for name in FINAL_ORDERED]
    if all(count == 0 for count in final_counts):
        require(text.count(FINAL_ANCHOR) == 1, "Build120 final verifier anchor count != 1")
        block = (
            FINAL_ANCHOR
            + '\n\necho\necho "== Jerkgram v1.2J Build121 final identity =="\n'
            + final_line(FINAL_ORDERED[0])
            + "\n"
            + final_line(FINAL_ORDERED[1])
        )
        text = text.replace(FINAL_ANCHOR, block, 1)
    else:
        require(all(count == 1 for count in final_counts), "partial Build121 final wiring")

    final_positions = [text.index(name) for name in FINAL_ORDERED]
    require(final_positions == sorted(final_positions), "Build121 final order invalid")
    require(text.index("verify_jerkgram_v12i_build120_final_ipa.py") < final_positions[0], "Build121 identity runs before Build120 final gate")
    require(final_positions[0] > text.index(BAZEL_ANCHOR), "Build121 final identity runs before Bazel")

    PROBE.write_text(text, encoding="utf-8")
    print("[Build121 probe hook] GREEN")
    print("[Build121 probe hook] recovery follows Build120 and precedes Bazel")
    print("[Build121 probe hook] Build121 identity follows Build120 final verification")


if __name__ == "__main__":
    main()
