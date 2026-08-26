#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

PROBE = Path(os.environ.get(
    "JERKGRAM_PROBE_PATH",
    str(Path(__file__).resolve().parent / "bazel_build_probe_official.sh"),
)).resolve()

SOURCE_ORDERED = (
    "apply_jerkgram_v12k_build122_reply_sticker_contract1.py",
    "verify_jerkgram_v12k_build122_reply_sticker_contract1.py",
)
SOURCE_ANCHOR = "python3 ../../scripts/verify_jerkgram_v12j_build121_sticker_recovery1.py\n"
BAZEL_ANCHOR = '"$BAZEL_BIN" build'


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build122 probe hook] " + message)


def source_line(name: str) -> str:
    return "python3 ../../scripts/" + name


def main() -> None:
    require(PROBE.is_file(), "probe missing: " + str(PROBE))
    text = PROBE.read_text(encoding="utf-8")

    counts = [text.count(name) for name in SOURCE_ORDERED]
    if all(count == 0 for count in counts):
        require(text.count(SOURCE_ANCHOR) == 1, "Build121 verifier anchor count != 1")
        block = (
            SOURCE_ANCHOR
            + '\necho\necho "== Jerkgram v1.2K Build122 reply/sticker runtime contracts =="\n'
            + "\n".join(source_line(name) for name in SOURCE_ORDERED)
            + "\n"
        )
        text = text.replace(SOURCE_ANCHOR, block, 1)
    else:
        require(all(count == 1 for count in counts), "partial Build122 source wiring")

    positions = [text.index(name) for name in SOURCE_ORDERED]
    require(positions == sorted(positions), "Build122 source order invalid")
    require(text.index("verify_jerkgram_v12j_build121_sticker_recovery1.py") < positions[0], "Build122 runs before Build121 gate")
    require(positions[-1] < text.index(BAZEL_ANCHOR), "Build122 runs after Bazel")

    PROBE.write_text(text, encoding="utf-8")
    print("[Build122 probe hook] GREEN")
    print("[Build122 probe hook] reply/sticker contract overlay follows Build121 and precedes Bazel")


if __name__ == "__main__":
    main()
