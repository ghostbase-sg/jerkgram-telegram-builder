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
    "apply_jerkgram_v12k_build122_edit_caption_history1.py",
    "verify_jerkgram_v12k_build122_edit_caption_history1.py",
    "apply_jerkgram_v12k_build122_settings_release1.py",
    "verify_jerkgram_v12k_build122_settings_release1.py",
)
SOURCE_ANCHOR = "python3 ../../scripts/verify_jerkgram_v12j_build121_sticker_recovery1.py\n"
BAZEL_ANCHOR = '"$BAZEL_BIN" build'
FINAL_ORDERED = (
    "jerkgram_finalize_build122_identity.py",
    "verify_jerkgram_v12k_build122_final_ipa.py",
)
FINAL_ANCHOR = (
    "python3 ../../scripts/verify_jerkgram_v12j_build121_final_ipa.py "
    "ghostbase-final/GhostBase.ipa"
)


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build122 probe hook] " + message)


def source_line(name: str) -> str:
    return "python3 ../../scripts/" + name


def final_line(name: str) -> str:
    return source_line(name) + " ghostbase-final/GhostBase.ipa"


def main() -> None:
    require(PROBE.is_file(), "probe missing: " + str(PROBE))
    text = PROBE.read_text(encoding="utf-8")

    counts = [text.count(name) for name in SOURCE_ORDERED]
    require(all(count in (0, 1) for count in counts), "duplicate Build122 source wiring")
    present_names = [name for name, count in zip(SOURCE_ORDERED, counts) if count == 1]
    require(present_names == list(SOURCE_ORDERED[:len(present_names)]), "partial Build122 source wiring is not an ordered prefix")
    missing_names = SOURCE_ORDERED[len(present_names):]
    if missing_names:
        if present_names:
            anchor = source_line(present_names[-1]) + "\n"
            require(text.count(anchor) == 1, "last installed Build122 anchor count != 1")
            block = anchor + "\n".join(source_line(name) for name in missing_names) + "\n"
        else:
            anchor = SOURCE_ANCHOR
            require(text.count(anchor) == 1, "Build121 verifier anchor count != 1")
            block = (
                anchor
                + '\necho\necho "== Jerkgram v1.2K Build122 release contracts =="\n'
                + "\n".join(source_line(name) for name in missing_names)
                + "\n"
            )
        text = text.replace(anchor, block, 1)

    source_positions = [text.index(name) for name in SOURCE_ORDERED]
    require(source_positions == sorted(source_positions), "Build122 source order invalid")
    require(text.index("verify_jerkgram_v12j_build121_sticker_recovery1.py") < source_positions[0], "Build122 runs before Build121 gate")
    require(source_positions[-1] < text.index(BAZEL_ANCHOR), "Build122 runs after Bazel")

    final_counts = [text.count(name) for name in FINAL_ORDERED]
    if all(count == 0 for count in final_counts):
        require(text.count(FINAL_ANCHOR) == 1, "Build121 final verifier anchor count != 1")
        block = (
            FINAL_ANCHOR
            + '\n\necho\necho "== Jerkgram v1.2K Build122 final identity =="\n'
            + "\n".join(final_line(name) for name in FINAL_ORDERED)
        )
        text = text.replace(FINAL_ANCHOR, block, 1)
    else:
        require(all(count == 1 for count in final_counts), "partial Build122 final wiring")

    final_positions = [text.index(name) for name in FINAL_ORDERED]
    require(final_positions == sorted(final_positions), "Build122 final order invalid")
    require(text.index("verify_jerkgram_v12j_build121_final_ipa.py") < final_positions[0], "Build122 identity runs before Build121 final gate")
    require(final_positions[0] > text.index(BAZEL_ANCHOR), "Build122 final identity runs before Bazel")

    PROBE.write_text(text, encoding="utf-8")
    print("[Build122 probe hook] GREEN")
    print("[Build122 probe hook] reply/sticker and Settings release overlays follow Build121 and precede Bazel")
    print("[Build122 probe hook] Build122 identity follows Build121 final verification")


if __name__ == "__main__":
    main()
