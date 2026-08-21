#!/usr/bin/env python3
import os
from pathlib import Path

BUILDER = Path(
    os.environ.get(
        "GHOSTBASE_BUILDER_ROOT",
        str(Path(__file__).resolve().parents[1]),
    )
).resolve()
ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()
OFFICIAL = BUILDER / "ports/ghostbase_12_9_2_port/telegram-ios-12.9.2-official"

BUILD = ROOT / "Telegram/BUILD"
PROBE = BUILDER / "scripts/bazel_build_probe_official.sh"

EXTENSIONS = (
    "BroadcastUploadExtension",
    "ShareExtension",
    "WidgetExtension",
    "NotificationContentExtension",
    "NotificationServiceExtension",
    "IntentsExtension",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("[verify Build112] " + message)


def text(path: Path) -> str:
    require(path.is_file(), f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def unique_named(root: Path, name: str):
    return [p for p in root.rglob(name) if p.is_file()]


def build_files_containing(root: Path, token: str):
    hits = []
    for name in ("BUILD", "BUILD.bazel"):
        for path in root.rglob(name):
            if not path.is_file():
                continue
            if token in path.read_text(encoding="utf-8", errors="ignore"):
                hits.append(path)
    return hits


def main() -> None:
    require(OFFICIAL.is_dir(), f"official 12.9.2 tree missing: {OFFICIAL}")

    build = text(BUILD)
    probe = text(PROBE)
    official_build = text(OFFICIAL / "Telegram/BUILD")

    # Icon blocker correction.
    # Local Official rules_apple proves that app_icons + primary_app_icon
    # is the native Icon Composer owner. Build112 therefore preserves the
    # Build111 .icon inputs and patches only final IPA registration metadata.
    require(
        'primary_app_icon = "Telegram"' in build,
        "Telegram primary Composer icon changed unexpectedly",
    )

    composer_start = build.find("composer_icon_folders = [")
    require(
        composer_start >= 0,
        "composer_icon_folders block missing",
    )
    composer_end = build.find("]", composer_start)
    require(
        composer_end > composer_start,
        "composer_icon_folders block malformed",
    )
    composer_block = build[composer_start:composer_end + 1]

    for name in (
        "Telegram",
        "JerkgramGlassReveal",
        "JerkgramGlassSolid",
    ):
        require(
            f'"{name}"' in composer_block,
            f"native Composer app_icons owner missing: {name}",
        )

    require(
        'app_icons = [ ":{}_icon".format(name) for name in composer_icon_folders ]'
        in build,
        "ios_application no longer consumes composer_icon_folders via app_icons",
    )

    require(
        "Telegram-iOS/JerkgramGlassReveal.alticon" not in build
        and "Telegram-iOS/JerkgramGlassSolid.alticon" not in build,
        "Glass was incorrectly converted to legacy .alticon",
    )

    require(
        'ipa_post_processor = ":JerkgramIconComposerPostProcessor"' not in build,
        "obsolete Build112 main-app ipa_post_processor bridge survived",
    )
    require(
        'name = "JerkgramIconComposerPostProcessor"' not in build,
        "obsolete Build112 postprocessor target survived",
    )

    finalizer_token = "jerkgram_finalize_composer_alternates_build112.py"
    final_verifier_token = "verify_jerkgram_v12a_build112_final_ipa.py"

    require(
        probe.count(finalizer_token) == 1,
        "Build112 final-IPA Composer finalizer must run exactly once",
    )
    require(
        probe.count(final_verifier_token) == 1,
        "Build112 final verifier must run exactly once",
    )
    require(
        probe.find(finalizer_token) < probe.find(final_verifier_token),
        "Build112 Composer finalizer must run before final IPA verifier",
    )

    # Canonical build-mode requirement from the TЗ.
    require(
        probe.count("--//Telegram:disableExtensions=false") == 1,
        "canonical probe must contain exactly one disableExtensions=false",
    )
    require(
        "--//Telegram:disableExtensions=true" not in probe,
        "disableExtensions=true survived in canonical probe",
    )
    require(
        probe.count("--//Telegram:disableProvisioningProfiles=true") >= 1,
        "disableProvisioningProfiles=true missing from canonical probe",
    )
    for token in (
        "apply_jerkgram_v12a_build112_composer_alternates_extensions1.py",
        "verify_jerkgram_v12a_build112_composer_alternates_extensions1.py",
        "verify_jerkgram_v12a_build112_final_ipa.py",
    ):
        require(token in probe, f"canonical probe integration missing: {token}")
    require(
        "python3 ../../scripts/verify_jerkgram_v11z_build111_final_ipa.py" not in probe,
        "stale Build111 final verifier is still executed",
    )

    # Source truth: Official Telegram 12.9.2 owns two independent build flags.
    require(
        'name = "disableExtensions"' in official_build,
        "Official disableExtensions build setting missing",
    )
    require(
        'name = "disableProvisioningProfiles"' in official_build,
        "Official disableProvisioningProfiles build setting missing",
    )
    require(
        'name = "disableExtensionsSetting"' in official_build,
        "Official disableExtensions config_setting missing",
    )
    require(
        'name = "disableProvisioningProfilesSetting"' in official_build,
        "Official disableProvisioningProfiles config_setting missing",
    )

    # Keep every stock Official extension target in the materialized source.
    # Resolve target ownership across Official BUILD files instead of assuming
    # all six targets live in one specific BUILD file.
    for name in EXTENSIONS:
        token = f'name = "{name}"'
        official_hits = build_files_containing(OFFICIAL, token)
        generated_hits = build_files_containing(ROOT, token)
        require(official_hits, f"Official target missing: {name}")
        require(generated_hits, f"materialized source lost Official target: {name}")

    # Broadcast Upload must remain Telegram's own ReplayKit implementation.
    off_handlers = unique_named(OFFICIAL, "BroadcastUploadSampleHandler.swift")
    gen_handlers = unique_named(ROOT, "BroadcastUploadSampleHandler.swift")
    require(
        len(off_handlers) == 1,
        f"Official BroadcastUploadSampleHandler count != 1: {off_handlers}",
    )
    require(
        len(gen_handlers) == 1,
        f"materialized BroadcastUploadSampleHandler count != 1: {gen_handlers}",
    )
    off_rel = off_handlers[0].relative_to(OFFICIAL)
    gen_rel = gen_handlers[0].relative_to(ROOT)
    require(
        off_rel == gen_rel,
        f"BroadcastUploadSampleHandler path changed: official={off_rel}, generated={gen_rel}",
    )
    require(
        off_handlers[0].read_bytes() == gen_handlers[0].read_bytes(),
        "BroadcastUploadSampleHandler differs from Official 12.9.2",
    )

    point = "com.apple.broadcast-services-upload"
    off_plists = [
        p for p in OFFICIAL.rglob("*.plist")
        if p.is_file() and point in p.read_text(encoding="utf-8", errors="ignore")
    ]
    gen_plists = [
        p for p in ROOT.rglob("*.plist")
        if p.is_file() and point in p.read_text(encoding="utf-8", errors="ignore")
    ]
    require(
        len(off_plists) == 1,
        f"Official broadcast extension-point plist count != 1: {off_plists}",
    )
    require(
        len(gen_plists) == 1,
        f"materialized broadcast extension-point plist count != 1: {gen_plists}",
    )
    require(
        off_plists[0].relative_to(OFFICIAL) == gen_plists[0].relative_to(ROOT),
        "Broadcast Upload Info.plist owner path changed",
    )
    require(
        off_plists[0].read_bytes() == gen_plists[0].read_bytes(),
        "Broadcast Upload Info.plist differs from Official 12.9.2",
    )

    print("[verify Build112] GREEN: native Glass Composer assets preserved; final IPA registration finalizer scheduled")
    print("[verify Build112] GREEN: extensions enabled + provisioning profiles disabled")
    print("[verify Build112] GREEN: six Official extension targets preserved")
    print("[verify Build112] GREEN: BroadcastUploadSampleHandler is byte-identical to Official 12.9.2")


if __name__ == "__main__":
    main()
