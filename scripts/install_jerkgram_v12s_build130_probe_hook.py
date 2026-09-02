#!/usr/bin/env python3

from pathlib import Path
import os
import subprocess
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
PROBE = Path(os.environ.get("JERKGRAM_PROBE_PATH", str(SCRIPT_DIR / "bazel_build_probe_official.sh"))).resolve()
BASE_INSTALLER = SCRIPT_DIR / "install_jerkgram_v12n_build125_probe_hook.py"

SOURCE_MARKER = "# JERKGRAM_V12S_BUILD130_SIRI_FAILCLOSED_HOOK"
FINAL_MARKER = "# JERKGRAM_V12S_BUILD130_FINAL_IDENTITY_HOOK"
BUILD129_SOURCE_ANCHOR = "python3 ../../scripts/apply_jerkgram_v12r_build129_protected_chat_forward1.py"
BUILD128_FINAL_ANCHOR = "python3 ../../scripts/verify_jerkgram_v12s_build128_final_ipa.py ghostbase-final/GhostBase.ipa"
BAZEL_ANCHOR = '"$BAZEL_BIN" build'
SOURCE_ORDERED = (
    "apply_jerkgram_v12s_build130_siri_failclosed1.py",
    "verify_jerkgram_v12s_build130_siri_failclosed1.py",
)
FINAL_ORDERED = (
    "jerkgram_finalize_build130_identity.py",
    "verify_jerkgram_v12s_build130_final_ipa.py",
)


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build130 probe hook] " + message)


def line(name: str, argument: str | None = None) -> str:
    value = "python3 ../../scripts/" + name
    return value if argument is None else value + " " + argument


def patch_probe(text: str) -> str:
    require(text.count(BUILD129_SOURCE_ANCHOR) == 1, "Build129 source anchor count")
    require(text.count(BUILD128_FINAL_ANCHOR) == 1, "Build128 final verifier anchor count")
    require(text.count(BAZEL_ANCHOR) == 1, "Bazel anchor count")

    if SOURCE_MARKER not in text:
        require(all(text.count(name) == 0 for name in SOURCE_ORDERED), "partial preexisting Build130 source block")
        source_block = (
            BUILD129_SOURCE_ANCHOR
            + "\n\n" + SOURCE_MARKER
            + '\necho\necho "== Jerkgram v1.2S Build130 Siri runtime fail-closed =="\n'
            + "\n".join(line(name) for name in SOURCE_ORDERED)
        )
        text = text.replace(BUILD129_SOURCE_ANCHOR, source_block, 1)

    require(text.count(SOURCE_MARKER) == 1, "Build130 source marker count")
    source_positions = [text.index(name) for name in SOURCE_ORDERED]
    require(source_positions == sorted(source_positions), "Build130 apply/verifier order")
    require(all(text.count(name) == 1 for name in SOURCE_ORDERED), "Build130 source hook count")
    require(text.index(BUILD129_SOURCE_ANCHOR) < source_positions[0], "Build130 must follow Build129")
    require(source_positions[-1] < text.index(BAZEL_ANCHOR), "Build130 source verifier must precede Bazel")

    if FINAL_MARKER not in text:
        require(all(text.count(name) == 0 for name in FINAL_ORDERED), "partial preexisting Build130 final block")
        final_block = (
            BUILD128_FINAL_ANCHOR
            + "\n\n" + FINAL_MARKER
            + '\necho\necho "== Jerkgram Build130 final identity =="\n'
            + "\n".join(line(name, "ghostbase-final/GhostBase.ipa") for name in FINAL_ORDERED)
        )
        text = text.replace(BUILD128_FINAL_ANCHOR, final_block, 1)

    require(text.count(FINAL_MARKER) == 1, "Build130 final marker count")
    final_positions = [text.index(name) for name in FINAL_ORDERED]
    require(final_positions == sorted(final_positions), "Build130 final identity order")
    require(all(text.count(name) == 1 for name in FINAL_ORDERED), "Build130 final hook count")
    require(text.index(BUILD128_FINAL_ANCHOR) < final_positions[0], "Build130 final identity must follow Build128 verification")
    return text


def main() -> None:
    require(BASE_INSTALLER.is_file(), "base installer missing: " + str(BASE_INSTALLER))
    subprocess.check_call([sys.executable, str(BASE_INSTALLER)])
    require(PROBE.is_file(), "probe missing: " + str(PROBE))
    PROBE.write_text(patch_probe(PROBE.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build130 probe hook] GREEN")
    print("[Build130 probe hook] Build125 -> Build126/127/128/129 -> Build130 -> Bazel")


if __name__ == "__main__":
    main()
