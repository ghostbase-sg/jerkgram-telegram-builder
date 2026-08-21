#!/usr/bin/env python3

import hashlib
import json
import os
import re
from pathlib import Path


SCRIPT = Path(__file__).resolve()
BUILDER = SCRIPT.parent.parent

ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get(
            "GHOSTBASE_SOURCE_ROOT",
            str(Path.cwd()),
        ),
    )
).resolve()

OFFICIAL = (
    BUILDER
    / "ports"
    / "ghostbase_12_9_2_port"
    / "telegram-ios-12.9.2-official"
)

BUILD = ROOT / "Telegram/BUILD"
PROBE = BUILDER / "scripts/bazel_build_probe_official.sh"

MANIFEST = (
    BUILDER
    / "scripts"
    / "jerkgram_build112_official_12_9_2_extensions_manifest.json"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("[verify Build112] " + message)


def read_text(path: Path) -> str:
    require(
        path.is_file(),
        f"missing file: {path}",
    )

    return path.read_text(
        encoding="utf-8",
        errors="strict",
    )


def sha256(path: Path) -> str:
    require(
        path.is_file(),
        f"file missing for SHA-256: {path}",
    )

    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            h.update(chunk)

    return h.hexdigest()


def main_application_block(build: str) -> str:
    match = re.search(
        r'ios_application\(\s*\n\s*'
        r'name\s*=\s*"Telegram",',
        build,
    )

    require(
        match is not None,
        "main ios_application(name = Telegram) missing",
    )

    end = build.find(
        "\nxcodeproj(",
        match.start(),
    )

    require(
        end > match.start(),
        "could not delimit main Telegram ios_application",
    )

    return build[match.start():end]


def validate_extension_build_semantics(
    build: str,
    manifest: dict,
    owner: str,
) -> None:
    for token in manifest["flag_declarations"]:
        require(
            build.count(token) == 1,
            f"{owner}: build-setting declaration count "
            f"!= 1 for {token!r}: {build.count(token)}",
        )

    for name, token in (
        manifest["target_declaration_tokens"].items()
    ):
        require(
            build.count(token) == 1,
            f"{owner}: extension target declaration "
            f"count != 1 for {name}: "
            f"{build.count(token)}",
        )

    main = main_application_block(build)

    require(
        "extensions = select({" in main,
        f"{owner}: main extensions select missing",
    )

    for name, token in (
        manifest["main_extension_labels"].items()
    ):
        require(
            main.count(token) == 1,
            f"{owner}: main application embedding "
            f"count != 1 for {name}: "
            f"{main.count(token)}",
        )

    broadcast = manifest["broadcast_upload"]

    require(
        broadcast["build_owner"] == "Telegram/BUILD",
        "portable manifest has unexpected Broadcast owner",
    )

    for token in broadcast["build_tokens"]:
        require(
            token in build,
            f"{owner}: Broadcast Upload build semantic "
            f"missing: {token!r}",
        )


def validate_local_official(
    manifest: dict,
) -> None:
    official_build = OFFICIAL / manifest[
        "telegram_build"
    ]["path"]

    require(
        sha256(official_build)
        == manifest["telegram_build"]["sha256"],
        "portable manifest no longer matches "
        "local pristine Official Telegram/BUILD",
    )

    official_build_text = read_text(
        official_build
    )

    validate_extension_build_semantics(
        official_build_text,
        manifest,
        "Official 12.9.2",
    )

    source_spec = manifest[
        "broadcast_upload"
    ]["sample_handler"]

    official_source = (
        OFFICIAL
        / source_spec["path"]
    )

    require(
        sha256(official_source)
        == source_spec["sha256"],
        "portable manifest no longer matches "
        "local pristine Official Telegram/BUILD",
    )

    official_build_text = read_text(
        official_build
    )

    validate_extension_build_semantics(
        official_build_text,
        manifest,
        "Official 12.9.2",
    )

    source_spec = manifest[
        "broadcast_upload"
    ]["sample_handler"]

    official_source = (
        OFFICIAL
        / source_spec["path"]
    )

    require(
        sha256(official_source)
        == source_spec["sha256"],
        "portable manifest Broadcast source hash "
        "does not match local pristine Official",
    )

    source_text = read_text(
        official_source
    )

    class_pattern = (
        r'\bclass\s+'
        + re.escape(source_spec["class_name"])
        + r'\s*:\s*'
        + re.escape(source_spec["superclass"])
        + r'\b'
    )

    require(
        re.search(
            class_pattern,
            source_text,
        ) is not None,
        "local pristine Official Broadcast handler "
        "declaration does not match manifest",
    )

    print(
        "[verify Build112] GREEN: portable audit manifest "
        "revalidated against local pristine Official 12.9.2"
    )


# Build112 verify unsigned ios_extension provisioning gate
def verify_rules_apple_unsigned_ios_extensions() -> None:
    path = ROOT / (
        "build-system/bazel-rules/rules_apple/"
        "apple/internal/ios_rules.bzl"
    )

    require(
        path.is_file(),
        f"missing materialized rules_apple file: {path}",
    )

    text = path.read_text(encoding="utf-8")

    start_token = "def _ios_extension_impl(ctx):"
    end_token = "\ndef _ios_dynamic_framework_impl(ctx):"

    start = text.find(start_token)
    end = text.find(end_token, start)

    require(
        start >= 0 and end > start,
        "ios_extension function boundary missing in rules_apple",
    )

    block = text[start:end]

    patched = (
        "    if platform_prerequisites.platform.is_device "
        "and provisioning_profile:\n"
        "        processor_partials.append(\n"
        "            partials.provisioning_profile_partial(\n"
    )

    stale = (
        "    if platform_prerequisites.platform.is_device:\n"
        "        processor_partials.append(\n"
        "            partials.provisioning_profile_partial(\n"
    )

    require(
        block.count(patched) == 1,
        "conditional ios_extension provisioning gate "
        "missing or duplicated",
    )

    require(
        block.count(stale) == 0,
        "stale unconditional ios_extension "
        "provisioning gate remains",
    )

    require(
        block.count(
            "profile_artifact = provisioning_profile"
        ) == 1,
        "unexpected ios_extension profile_artifact ownership",
    )

    print(
        "[verify Build112] rules_apple unsigned "
        "ios_extension provisioning gate OK"
    )


# Build112 verify unsigned ios_application provisioning gate
def verify_rules_apple_unsigned_ios_application() -> None:
    path = ROOT / (
        "build-system/bazel-rules/rules_apple/"
        "apple/internal/ios_rules.bzl"
    )

    require(
        path.is_file(),
        f"missing materialized rules_apple file: {path}",
    )

    text = path.read_text(encoding="utf-8")

    start_token = "def _ios_application_impl(ctx):"
    end_token = "\ndef _ios_extension_impl(ctx):"

    start = text.find(start_token)
    end = text.find(end_token, start)

    require(
        start >= 0 and end > start,
        "ios_application function boundary missing in rules_apple",
    )

    block = text[start:end]

    patched = (
        "    if platform_prerequisites.platform.is_device "
        "and provisioning_profile:\n"
        "        processor_partials.append(\n"
        "            partials.provisioning_profile_partial(\n"
        "                actions = actions,\n"
        "                profile_artifact = provisioning_profile,\n"
        "                rule_label = label,\n"
        "            ),\n"
        "        )\n"
    )

    stale = (
        "    if platform_prerequisites.platform.is_device:\n"
        "        processor_partials.append(\n"
        "            partials.provisioning_profile_partial(\n"
        "                actions = actions,\n"
        "                profile_artifact = provisioning_profile,\n"
        "                rule_label = label,\n"
        "            ),\n"
        "        )\n"
    )

    require(
        block.count(patched) == 1,
        "conditional ios_application provisioning gate "
        "missing or duplicated",
    )

    require(
        block.count(stale) == 0,
        "stale unconditional ios_application "
        "provisioning gate remains",
    )

    require(
        block.count(
            "partials.provisioning_profile_partial("
        ) == 1,
        "unexpected ios_application provisioning partial ownership",
    )

    require(
        block.count(
            "profile_artifact = provisioning_profile"
        ) == 1,
        "unexpected ios_application profile_artifact ownership",
    )

    print(
        "[verify Build112] rules_apple unsigned "
        "ios_application provisioning gate OK"
    )


def main() -> None:
    verify_rules_apple_unsigned_ios_extensions()
    verify_rules_apple_unsigned_ios_application()
    require(
        MANIFEST.is_file(),
        f"Official audit manifest missing: {MANIFEST}",
    )

    manifest = json.loads(
        MANIFEST.read_text(
            encoding="utf-8",
        )
    )

    require(
        manifest.get("schema") == 4,
        "unexpected Official audit manifest schema",
    )

    require(
        manifest.get("official_release") == "12.9.2",
        "Official audit manifest release != 12.9.2",
    )

    broadcast = manifest.get(
        "broadcast_upload"
    )

    require(
        isinstance(broadcast, dict),
        "Broadcast manifest section missing",
    )

    require(
        broadcast.get("extension_point")
        == "com.apple.broadcast-services-upload",
        "portable manifest ReplayKit point changed",
    )

    require(
        broadcast.get("principal_class")
        == "BroadcastUploadSampleHandler",
        "portable manifest Broadcast principal changed",
    )

    require(
        broadcast.get("process_mode")
        == "RPBroadcastProcessModeSampleBuffer",
        "portable manifest Broadcast process mode changed",
    )

    build = read_text(BUILD)
    probe = read_text(PROBE)

    # If the large pristine tree exists, cryptographically revalidate
    # the committed portable audit. GitHub Actions intentionally does
    # not need that tree.
    if OFFICIAL.is_dir():
        validate_local_official(
            manifest
        )
    else:
        print(
            "[verify Build112] NOTE: pristine Official "
            "12.9.2 tree absent in CI checkout; "
            "using committed locally-audited manifest"
        )

    # ----- Native Xcode 26 Icon Composer ownership -----

    require(
        'primary_app_icon = "Telegram"' in build,
        "Telegram primary Composer icon changed",
    )

    composer_match = re.search(
        r'composer_icon_folders\s*=\s*'
        r'\[(.*?)\]',
        build,
        re.DOTALL,
    )

    require(
        composer_match is not None,
        "composer_icon_folders missing",
    )

    composer = composer_match.group(1)

    for name in (
        "Telegram",
        "JerkgramGlassReveal",
        "JerkgramGlassSolid",
    ):
        require(
            f'"{name}"' in composer,
            f"native Composer app_icons owner "
            f"missing: {name}",
        )

    require(
        re.search(
            r'app_icons\s*=\s*\[\s*'
            r'":\{\}_icon"\.format\(name\)'
            r'\s+for\s+name\s+in\s+'
            r'composer_icon_folders\s*\]',
            build,
        ) is not None,
        "ios_application no longer consumes "
        "composer_icon_folders via app_icons",
    )

    require(
        (
            "Telegram-iOS/JerkgramGlassReveal.alticon" not in build
            and "Telegram-iOS/JerkgramGlassSolid.alticon" not in build
        ),
        "Glass was incorrectly converted to .alticon",
    )

    require(
        'ipa_post_processor = '
        '":JerkgramIconComposerPostProcessor"'
        not in build,
        "obsolete Build112 main-app "
        "ipa_post_processor bridge survived",
    )

    require(
        'name = "JerkgramIconComposerPostProcessor"'
        not in build,
        "obsolete Build112 postprocessor "
        "target survived",
    )

    # ----- Extension build mode -----

    require(
        probe.count(
            "--//Telegram:disableExtensions=false"
        ) == 1,
        "canonical probe must contain exactly one "
        "disableExtensions=false",
    )

    require(
        "--//Telegram:disableExtensions=true"
        not in probe,
        "disableExtensions=true survived",
    )

    require(
        probe.count(
            "--//Telegram:disableProvisioningProfiles=true"
        ) >= 1,
        "disableProvisioningProfiles=true missing",
    )

    # ----- Build112 unsigned signing mode -----

    require(
        probe.count(
            "--features=disable_legacy_signing"
        ) == 1,
        "canonical probe must contain exactly one "
        "disable_legacy_signing feature",
    )

    finalizer = (
        "jerkgram_finalize_composer_alternates_build112.py"
    )

    final_verifier = (
        "verify_jerkgram_v12a_build112_final_ipa.py"
    )

    require(
        probe.count(finalizer) == 1,
        "Build112 Composer finalizer "
        "must execute exactly once",
    )

    require(
        probe.count(final_verifier) == 1,
        "Build112 final verifier "
        "must execute exactly once",
    )

    require(
        probe.find(finalizer)
        < probe.find(final_verifier),
        "Build112 Composer finalizer "
        "must run before final IPA verifier",
    )

    require(
        "python3 ../../scripts/"
        "verify_jerkgram_v11z_build111_final_ipa.py"
        not in probe,
        "stale Build111 final verifier "
        "is still executed",
    )

    # ----- Portable Official 12.9.2 audit -----

    validate_extension_build_semantics(
        build,
        manifest,
        "materialized source",
    )

    source_spec = broadcast[
        "sample_handler"
    ]

    materialization = source_spec.get(
        "canonical_materialization"
    )

    require(
        isinstance(materialization, dict),
        "canonical Broadcast materialization audit missing",
    )

    require(
        materialization.get("patcher_path")
        == "scripts/gb_patch_swift.py",
        "unexpected Broadcast canonical patcher owner",
    )

    canonical_patcher = (
        BUILDER
        / materialization["patcher_path"]
    )

    require(
        sha256(canonical_patcher)
        == materialization.get("patcher_sha256"),
        "gb_patch_swift.py changed since Broadcast "
        "materialization audit was recorded",
    )

    expected_materialized_sha = (
        materialization.get("expected_sha256")
    )

    require(
        isinstance(expected_materialized_sha, str)
        and re.fullmatch(
            r"[0-9a-f]{64}",
            expected_materialized_sha,
        ) is not None,
        "invalid expected materialized Broadcast SHA-256",
    )

    generated_source = (
        ROOT
        / source_spec["path"]
    )

    generated_source_sha = sha256(
        generated_source
    )

    require(
        generated_source_sha
        == expected_materialized_sha,
        "materialized Broadcast Upload implementation "
        "does not match audited canonical result: "
        f"expected={expected_materialized_sha}, "
        f"actual={generated_source_sha}",
    )

    generated_source_text = read_text(
        generated_source
    )

    class_pattern = (
        r'\bclass\s+'
        + re.escape(source_spec["class_name"])
        + r'\s*:\s*'
        + re.escape(source_spec["superclass"])
        + r'\b'
    )

    require(
        re.search(
            class_pattern,
            generated_source_text,
        ) is not None,
        "materialized BroadcastUploadSampleHandler "
        "is no longer an RPBroadcastSampleHandler",
    )

    print(
        "[verify Build112] GREEN: native Glass "
        "Composer assets preserved"
    )

    print(
        "[verify Build112] GREEN: extensions enabled; "
        "provisioning profiles disabled"
    )

    print(
        "[verify Build112] GREEN: all six Official "
        "Telegram extension targets and main-app "
        "embedding wiring preserved"
    )

    print(
        "[verify Build112] GREEN: Telegram "
        "BroadcastUploadSampleHandler matches audited "
        "Official 12.9.2 after canonical "
        "gb_patch_swift Bundle/AppGroup normalization"
    )

    print(
        "[verify Build112] GREEN: Broadcast metadata = "
        "com.apple.broadcast-services-upload / "
        "BroadcastUploadSampleHandler / "
        "RPBroadcastProcessModeSampleBuffer"
    )


if __name__ == "__main__":
    main()
