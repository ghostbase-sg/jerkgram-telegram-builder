#!/usr/bin/env python3

from pathlib import Path
import os

from install_jerkgram_build124_telegram_api_probe_hook1 import patch_probe as patch_telegram_api_probe


PROBE = Path(os.environ.get("JERKGRAM_PROBE_PATH", str(Path(__file__).resolve().parent / "bazel_build_probe_official.sh"))).resolve()
SOURCE_ORDERED = (
    "apply_jerkgram_v12l_build123_state_runtime1.py",
    "apply_jerkgram_v12l_build123_message_fidelity1.py",
    "apply_jerkgram_v12l_build123_profile_ui1.py",
    "apply_jerkgram_v12l_build123_settings_ui1.py",
    "verify_jerkgram_v12l_build123_release_recovery1.py",
)
SOURCE_ANCHOR = "python3 ../../scripts/verify_jerkgram_v12k_build122_settings_release1.py\n"
BAZEL_ANCHOR = '"$BAZEL_BIN" build'
FINAL_ORDERED = (
    "jerkgram_finalize_build123_identity.py",
    "verify_jerkgram_v12l_build123_final_ipa.py",
)
FINAL_ANCHOR = "python3 ../../scripts/verify_jerkgram_v12k_build122_final_ipa.py ghostbase-final/GhostBase.ipa"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build123 probe hook] " + message)


def line(name: str) -> str:
    return "python3 ../../scripts/" + name


def main() -> None:
    text = PROBE.read_text(encoding="utf-8")
    if not all(name in text for name in SOURCE_ORDERED):
        require(text.count(SOURCE_ANCHOR) == 1, "Build122 source anchor count")
        block = SOURCE_ANCHOR + '\necho\necho "== Jerkgram v1.2L Build123 release recovery =="\n' + "\n".join(line(name) for name in SOURCE_ORDERED) + "\n"
        text = text.replace(SOURCE_ANCHOR, block, 1)
    positions = [text.index(name) for name in SOURCE_ORDERED]
    require(positions == sorted(positions), "Build123 source order")
    require(positions[-1] < text.index(BAZEL_ANCHOR), "Build123 runs after Bazel")

    if not all(name in text for name in FINAL_ORDERED):
        require(text.count(FINAL_ANCHOR) == 1, "Build122 final anchor count")
        block = FINAL_ANCHOR + '\n\necho\necho "== Jerkgram v1.2L Build123 final identity =="\n' + "\n".join(line(name) + " ghostbase-final/GhostBase.ipa" for name in FINAL_ORDERED)
        text = text.replace(FINAL_ANCHOR, block, 1)

    # Build124 credential hook: insert private Telegram API material only after
    # the active configuration repository has been created, and verify it
    # before Bazel sees that configuration.
    text = patch_telegram_api_probe(text)

    PROBE.write_text(text, encoding="utf-8")
    print("[Build123 probe hook] GREEN")


if __name__ == "__main__":
    main()
