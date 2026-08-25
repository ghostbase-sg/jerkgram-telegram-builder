#!/usr/bin/env python3

from pathlib import Path


PROBE = Path(__file__).resolve().parent / "bazel_build_probe_official.sh"

SOURCE_ORDERED = (
    "apply_jerkgram_v12i_build120_profile_blur_lifecycle1.py",
    "verify_jerkgram_v12i_build120_profile_blur_lifecycle1.py",
)
SOURCE_ANCHOR = "python3 ../../scripts/verify_jerkgram_v12h_build119_hybrid_ui1.py\n"
BAZEL_ANCHOR = '"$BAZEL_BIN" build'

FINAL_ORDERED = (
    "jerkgram_finalize_build120_identity.py",
    "verify_jerkgram_v12i_build120_final_ipa.py",
)
FINAL_ANCHOR = "python3 ../../scripts/verify_jerkgram_v12h_build119_final_ipa.py ghostbase-final/GhostBase.ipa"


def require(value, message):
    if not value:
        raise RuntimeError("[Build120 probe hook] " + message)


def source_line(name):
    return "python3 ../../scripts/" + name


def final_line(name):
    return source_line(name) + " ghostbase-final/GhostBase.ipa"


def main():
    require(PROBE.is_file(), "probe missing")
    text = PROBE.read_text(encoding="utf-8")

    source_counts = [text.count(name) for name in SOURCE_ORDERED]
    if all(count == 0 for count in source_counts):
        require(text.count(SOURCE_ANCHOR) == 1, "Build119 source verifier anchor count != 1")
        block = (
            SOURCE_ANCHOR
            + '\necho\necho "== Jerkgram v1.2I Build120 profile blur lifecycle =="\n'
            + "\n".join(source_line(name) for name in SOURCE_ORDERED)
            + "\n"
        )
        text = text.replace(SOURCE_ANCHOR, block, 1)
    else:
        require(all(count == 1 for count in source_counts), "partial Build120 source wiring")

    source_positions = [text.index(name) for name in SOURCE_ORDERED]
    require(source_positions == sorted(source_positions), "Build120 source overlay order invalid")
    require(text.index("verify_jerkgram_v12h_build119_hybrid_ui1.py") < source_positions[0], "Build120 source runs before Build119 gate")
    require(source_positions[-1] < text.index(BAZEL_ANCHOR), "Build120 source runs after Bazel")

    final_counts = [text.count(name) for name in FINAL_ORDERED]
    if all(count == 0 for count in final_counts):
        require(text.count(FINAL_ANCHOR) == 1, "Build119 final verifier anchor count != 1")
        block = (
            FINAL_ANCHOR
            + '\n\necho\necho "== Jerkgram v1.2I Build120 final identity =="\n'
            + final_line(FINAL_ORDERED[0])
            + "\n"
            + final_line(FINAL_ORDERED[1])
        )
        text = text.replace(FINAL_ANCHOR, block, 1)
    else:
        require(all(count == 1 for count in final_counts), "partial Build120 final identity wiring")

    final_positions = [text.index(name) for name in FINAL_ORDERED]
    require(final_positions == sorted(final_positions), "Build120 final identity order invalid")
    require(final_positions[0] > text.index(FINAL_ANCHOR), "Build120 identity runs before Build119 final verification")
    require(final_positions[0] > text.index(BAZEL_ANCHOR), "Build120 final identity unexpectedly runs before Bazel")

    PROBE.write_text(text, encoding="utf-8")
    print("[Build120 probe hook] GREEN")
    print("[Build120 probe hook] profile lifecycle overlay follows Build119 and precedes Bazel")
    print("[Build120 probe hook] embedded Build120 identity follows Build119 final verification")


if __name__ == "__main__":
    main()
