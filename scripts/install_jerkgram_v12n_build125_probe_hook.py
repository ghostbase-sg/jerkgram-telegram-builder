#!/usr/bin/env python3

from pathlib import Path
import os
import subprocess
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
PROBE = Path(
    os.environ.get(
        "JERKGRAM_PROBE_PATH",
        str(SCRIPT_DIR / "bazel_build_probe_official.sh"),
    )
).resolve()
BASE_INSTALLER = SCRIPT_DIR / "install_jerkgram_v12m_build124_probe_hook.py"

SOURCE_MARKER = "# JERKGRAM_V12N_BUILD125_SOURCE_HOOK"
FINAL_MARKER = "# JERKGRAM_V12N_BUILD125_FINAL_IDENTITY_HOOK"
BUILD124_SOURCE_ANCHOR = "python3 ../../scripts/verify_jerkgram_v12m_build124_settings_redesign1.py\n"
BUILD124_FINAL_ANCHOR = "python3 ../../scripts/verify_jerkgram_v12m_build124_final_ipa.py ghostbase-final/GhostBase.ipa"
BAZEL_ANCHOR = '"$BAZEL_BIN" build'

# These overlays are only useful if they execute in the materialized Official
# source tree. Keep their order explicit: several depend on Build124 owners.
APPLY_ORDERED = (
    "apply_jerkgram_v12n_build125_profile_edit1.py",
    "apply_jerkgram_v12n_build125_single_forward1.py",
    "apply_jerkgram_v12n_build125_circle_viewed1.py",
    "apply_jerkgram_v12n_build125_links_bounds1.py",
    "apply_jerkgram_v12n_build125_protected_cache1.py",
    "apply_jerkgram_v12n_build125_auth_ghost_localization1.py",
)

VERIFY_ORDERED = (
    "verify_jerkgram_v12n_build125_profile_edit1.py",
    "verify_jerkgram_v12n_build125_single_forward1.py",
    "verify_jerkgram_v12n_build125_circle_viewed1.py",
    "verify_jerkgram_v12n_build125_links_bounds1.py",
    "verify_jerkgram_v12n_build125_protected_cache1.py",
    "verify_jerkgram_v12n_build125_auth_ghost_localization1.py",
)

FINAL_ORDERED = (
    "jerkgram_finalize_build125_identity.py",
    "verify_jerkgram_v12n_build125_final_ipa.py",
)


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build125 probe hook] " + message)


def line(name: str, argument: str | None = None) -> str:
    result = "python3 ../../scripts/" + name
    if argument:
        result += " " + argument
    return result


def patch_probe(text: str) -> str:
    require(BUILD124_SOURCE_ANCHOR in text, "Build124 source verifier anchor missing")
    require(BUILD124_FINAL_ANCHOR in text, "Build124 final verifier anchor missing")

    hook_names = APPLY_ORDERED + VERIFY_ORDERED
    hook_counts = [text.count(name) for name in hook_names]
    if SOURCE_MARKER not in text and all(count == 0 for count in hook_counts):
        source_block = (
            BUILD124_SOURCE_ANCHOR
            + "\n"
            + SOURCE_MARKER
            + '\necho\necho "== Jerkgram v1.2N Build125 runtime fixes =="\n'
            + "\n".join(line(name) for name in APPLY_ORDERED)
            + "\n\n"
            + "\n".join(line(name) for name in VERIFY_ORDERED)
            + "\n"
        )
        text = text.replace(BUILD124_SOURCE_ANCHOR, source_block, 1)
    elif SOURCE_MARKER not in text and all(count == 1 for count in hook_counts):
        # The historical Build125 release block already lives in the probe on
        # this branch. It was unmarked, so a second installer used to append a
        # duplicate block and then abort on its own strict count gate. Adopt
        # the existing ordered block instead of materializing it a second time.
        require(
            text.index(BUILD124_SOURCE_ANCHOR.strip()) < min(text.index(name) for name in APPLY_ORDERED),
            "preexisting Build125 block must follow Build124 source verification",
        )
        require(
            max(text.index(name) for name in VERIFY_ORDERED) < text.index(BAZEL_ANCHOR),
            "preexisting Build125 block must finish before Bazel",
        )
        text = text.replace(
            BUILD124_SOURCE_ANCHOR,
            BUILD124_SOURCE_ANCHOR + "\n" + SOURCE_MARKER + "\n",
            1,
        )
    elif SOURCE_MARKER not in text:
        require(False, "incomplete preexisting Build125 source block")

    require(text.count(SOURCE_MARKER) == 1, "Build125 source marker count")
    apply_positions = [text.index(name) for name in APPLY_ORDERED]
    verify_positions = [text.index(name) for name in VERIFY_ORDERED]
    for name in hook_names:
        require(text.count(name) == 1, f"Build125 hook count for {name}")
    require(apply_positions == sorted(apply_positions), "Build125 apply order")
    require(verify_positions == sorted(verify_positions), "Build125 verifier order")
    require(max(apply_positions) < min(verify_positions), "all Build125 applies must precede source verifiers")
    require(text.index(BUILD124_SOURCE_ANCHOR.strip()) < min(apply_positions), "Build125 must run after Build124 source verification")
    require(max(verify_positions) < text.index(BAZEL_ANCHOR), "Build125 source verifier must run before Bazel")

    if FINAL_MARKER not in text:
        final_block = (
            BUILD124_FINAL_ANCHOR
            + "\n\n"
            + FINAL_MARKER
            + '\necho\necho "== Jerkgram v1.2N Build125 final identity =="\n'
            + "\n".join(line(name, "ghostbase-final/GhostBase.ipa") for name in FINAL_ORDERED)
        )
        text = text.replace(BUILD124_FINAL_ANCHOR, final_block, 1)

    require(text.count(FINAL_MARKER) == 1, "Build125 final marker count")
    final_positions = [text.index(name) for name in FINAL_ORDERED]
    for name in FINAL_ORDERED:
        require(text.count(name) == 1, f"Build125 final hook count for {name}")
    require(final_positions == sorted(final_positions), "Build125 final identity order")
    require(text.index(BUILD124_FINAL_ANCHOR) < final_positions[0], "Build125 final identity must follow Build124 IPA verification")
    return text


def main() -> None:
    require(BASE_INSTALLER.is_file(), f"base installer missing: {BASE_INSTALLER}")
    subprocess.check_call([sys.executable, str(BASE_INSTALLER)])
    require(PROBE.is_file(), f"probe missing: {PROBE}")
    PROBE.write_text(patch_probe(PROBE.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build125 probe hook] GREEN")
    print("[Build125 probe hook] Build124 -> Build125 applies -> Build125 verifiers -> Bazel")


if __name__ == "__main__":
    main()
