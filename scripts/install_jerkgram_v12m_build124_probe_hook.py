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
BASE_INSTALLER = SCRIPT_DIR / "install_jerkgram_v12l_build123_probe_hook.py"

SOURCE_MARKER = "# JERKGRAM_V12M_BUILD124_SOURCE_HOOK"
FINAL_MARKER = "# JERKGRAM_V12M_BUILD124_FINAL_IDENTITY_HOOK"
BUILD123_SOURCE_ANCHOR = "python3 ../../scripts/verify_jerkgram_v12l_build123_release_recovery1.py\n"
BUILD123_FINAL_ANCHOR = "python3 ../../scripts/verify_jerkgram_v12l_build123_final_ipa.py ghostbase-final/GhostBase.ipa"
BAZEL_ANCHOR = '"$BAZEL_BIN" build'
API_APPLY = "apply_jerkgram_build124_telegram_api_credentials1.py"
API_VERIFY = "verify_jerkgram_build124_telegram_api_credentials1.py"

# Late Build124 overlays. Every item here operates on the already-materialized
# Build123 tree. Keep dependency-sensitive pairs explicit instead of relying on
# filesystem ordering.
APPLY_ORDERED = (
    "apply_jerkgram_v12m_build124_profile_edit_glass1.py",
    "apply_jerkgram_v12m_build124_profile_more1.py",
    "apply_jerkgram_v12m_build124_links_glass1.py",
    "apply_jerkgram_v12m_build124_single_forward1.py",
    "apply_jerkgram_v12m_build124_sensitive_settings1.py",
    "apply_jerkgram_v12m_build124_archive_import_runtime1.py",
    "apply_jerkgram_v12m_build124_archive_export_runtime1.py",
    "apply_jerkgram_v12m_build124_protected_forward1.py",
    "apply_jerkgram_v12m_build124_deleted_entities1.py",
    "apply_jerkgram_v12m_build124_edit_history1.py",
    "apply_jerkgram_v12m_build124_auth_keyboard1.py",
    "apply_jerkgram_v12m_build124_bot_localization1.py",
    "apply_jerkgram_v12m_build124_lifecycle_freeze1.py",
    "apply_jerkgram_v12m_build124_onetime_persistence1.py",
    "apply_jerkgram_v12m_build124_onetime_viewed1.py",
)

VERIFY_ORDERED = (
    "verify_jerkgram_v12m_build124_profile_edit_glass1.py",
    "verify_jerkgram_v12m_build124_profile_more1.py",
    "verify_jerkgram_v12m_build124_links_glass1.py",
    "verify_jerkgram_v12m_build124_single_forward1.py",
    "verify_jerkgram_v12m_build124_sensitive_settings1.py",
    "verify_jerkgram_v12m_build124_archive_import_runtime1.py",
    "verify_jerkgram_v12m_build124_archive_export_runtime1.py",
    "verify_jerkgram_v12m_build124_protected_forward1.py",
    "verify_jerkgram_v12m_build124_deleted_entities1.py",
    "verify_jerkgram_v12m_build124_edit_history1.py",
    "verify_jerkgram_v12m_build124_auth_keyboard1.py",
    "verify_jerkgram_v12m_build124_bot_localization1.py",
    "verify_jerkgram_v12m_build124_lifecycle_freeze1.py",
    "verify_jerkgram_v12m_build124_onetime_persistence1.py",
    "verify_jerkgram_v12m_build124_onetime_viewed1.py",
)

FINAL_ORDERED = (
    "jerkgram_finalize_build124_identity.py",
    "verify_jerkgram_v12m_build124_final_ipa.py",
)


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 probe hook] " + message)


def line(name: str, argument: str | None = None) -> str:
    result = "python3 ../../scripts/" + name
    if argument:
        result += " " + argument
    return result


def patch_probe(text: str) -> str:
    # Build123 is the only accepted materialized base for this release line.
    require(
        "verify_jerkgram_v12l_build123_release_recovery1.py" in text,
        "Build123 source recovery hook missing",
    )
    require(
        "verify_jerkgram_v12l_build123_final_ipa.py" in text,
        "Build123 final identity hook missing",
    )

    # Credentials intentionally remain at their configuration-repository owner;
    # they are not source-tree overlays and must be verified before Bazel.
    require(API_APPLY in text, "private Telegram API credential apply hook missing")
    require(API_VERIFY in text, "private Telegram API credential verifier missing")
    require(text.index(API_APPLY) < text.index(API_VERIFY), "private Telegram API hook order")
    require(text.index(API_VERIFY) < text.index(BAZEL_ANCHOR), "private Telegram API verifier must run before Bazel")

    if SOURCE_MARKER not in text:
        require(text.count(BUILD123_SOURCE_ANCHOR) == 1, "Build123 source anchor count")
        source_block = (
            BUILD123_SOURCE_ANCHOR
            + "\n"
            + SOURCE_MARKER
            + '\necho\necho "== Jerkgram v1.2M Build124 runtime fixes =="\n'
            + "\n".join(line(name) for name in APPLY_ORDERED)
            + "\n\n"
            + "\n".join(line(name) for name in VERIFY_ORDERED)
            + "\n"
        )
        text = text.replace(BUILD123_SOURCE_ANCHOR, source_block, 1)

    require(text.count(SOURCE_MARKER) == 1, "Build124 source marker count")
    apply_positions = []
    for name in APPLY_ORDERED:
        require(text.count(name) == 1, f"Build124 apply hook count for {name}")
        apply_positions.append(text.index(name))
    require(apply_positions == sorted(apply_positions), "Build124 apply order")

    verify_positions = []
    for name in VERIFY_ORDERED:
        require(text.count(name) == 1, f"Build124 verifier hook count for {name}")
        verify_positions.append(text.index(name))
    require(verify_positions == sorted(verify_positions), "Build124 verifier order")
    require(max(apply_positions) < min(verify_positions), "all Build124 applies must precede source verifiers")

    build123_source = text.index("verify_jerkgram_v12l_build123_release_recovery1.py")
    bazel = text.index(BAZEL_ANCHOR)
    require(build123_source < min(apply_positions), "Build124 must run after Build123 source recovery")
    require(max(verify_positions) < bazel, "Build124 source verifier must run before Bazel")
    require(
        text.index("apply_jerkgram_v12m_build124_onetime_persistence1.py")
        < text.index("apply_jerkgram_v12m_build124_onetime_viewed1.py"),
        "one-time persistence must precede viewed-state overlay",
    )
    require(
        text.index("apply_jerkgram_v12m_build124_archive_import_runtime1.py")
        < text.index("apply_jerkgram_v12m_build124_archive_export_runtime1.py"),
        "archive import runtime overlay must precede export reliability overlay",
    )

    if FINAL_MARKER not in text:
        require(text.count(BUILD123_FINAL_ANCHOR) == 1, "Build123 final anchor count")
        final_block = (
            BUILD123_FINAL_ANCHOR
            + "\n\n"
            + FINAL_MARKER
            + '\necho\necho "== Jerkgram v1.2M Build124 final identity =="\n'
            + "\n".join(
                line(name, "ghostbase-final/GhostBase.ipa")
                for name in FINAL_ORDERED
            )
        )
        text = text.replace(BUILD123_FINAL_ANCHOR, final_block, 1)

    require(text.count(FINAL_MARKER) == 1, "Build124 final marker count")
    final_positions = []
    for name in FINAL_ORDERED:
        require(text.count(name) == 1, f"Build124 final hook count for {name}")
        final_positions.append(text.index(name))
    require(final_positions == sorted(final_positions), "Build124 final identity order")
    require(
        text.index("verify_jerkgram_v12l_build123_final_ipa.py") < final_positions[0],
        "Build124 final identity must follow verified Build123 IPA",
    )

    return text


def main() -> None:
    require(BASE_INSTALLER.is_file(), f"base installer missing: {BASE_INSTALLER}")

    # Materialize the canonical Build123 hook first. It also installs the
    # configuration-scoped private Telegram API canary at its correct owner.
    subprocess.check_call([sys.executable, str(BASE_INSTALLER)])

    require(PROBE.is_file(), f"probe missing: {PROBE}")
    original = PROBE.read_text(encoding="utf-8")
    updated = patch_probe(original)
    PROBE.write_text(updated, encoding="utf-8")

    print("[Build124 probe hook] GREEN")
    print("[Build124 probe hook] Build123 -> Build124 applies -> Build124 verifiers -> Bazel")
    print("[Build124 probe hook] private Telegram API canary remains configuration-scoped")


if __name__ == "__main__":
    main()
