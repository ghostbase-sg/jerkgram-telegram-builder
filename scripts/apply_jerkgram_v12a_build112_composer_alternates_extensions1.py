#!/usr/bin/env python3

import os
import re
from pathlib import Path

ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()

BUILD = ROOT / "Telegram/BUILD"

OLD_MARKER = "# MARK: Jerkgram v1.2A BUILD112_COMPOSER_ALTERNATES1"
OLD_POST = ROOT / "Telegram/Telegram-iOS/JerkgramIconComposerPostProcessor.sh"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("[Build112] " + message)


# Build112 unsigned ios_extension provisioning gate
def patch_rules_apple_unsigned_ios_extensions() -> None:
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

    old = (
        "    if platform_prerequisites.platform.is_device:\n"
        "        processor_partials.append(\n"
        "            partials.provisioning_profile_partial(\n"
    )

    new = (
        "    if platform_prerequisites.platform.is_device "
        "and provisioning_profile:\n"
        "        processor_partials.append(\n"
        "            partials.provisioning_profile_partial(\n"
    )

    old_count = block.count(old)
    new_count = block.count(new)

    if old_count == 0 and new_count == 1:
        print(
            "[Build112] rules_apple unsigned ios_extension "
            "provisioning gate already applied"
        )
        return

    require(
        old_count == 1 and new_count == 0,
        "unexpected ios_extension provisioning partial shape: "
        f"old={old_count}, new={new_count}",
    )

    require(
        block.count(
            "profile_artifact = provisioning_profile"
        ) == 1,
        "unexpected ios_extension profile_artifact ownership",
    )

    block = block.replace(old, new, 1)
    updated = text[:start] + block + text[end:]

    path.write_text(updated, encoding="utf-8")

    verify_text = path.read_text(encoding="utf-8")
    verify_start = verify_text.find(start_token)
    verify_end = verify_text.find(
        end_token,
        verify_start,
    )

    require(
        verify_start >= 0 and verify_end > verify_start,
        "patched ios_extension boundary missing",
    )

    verify_block = verify_text[
        verify_start:verify_end
    ]

    require(
        verify_block.count(new) == 1,
        "conditional provisioning gate did not materialize",
    )

    require(
        verify_block.count(old) == 0,
        "stale unconditional provisioning gate survived",
    )

    print(
        "[Build112] rules_apple ios_extension now skips "
        "provisioning_profile_partial when profile is disabled"
    )


# Build112 unsigned ios_application provisioning gate
def patch_rules_apple_unsigned_ios_application() -> None:
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

    old = (
        "    if platform_prerequisites.platform.is_device:\n"
        "        processor_partials.append(\n"
        "            partials.provisioning_profile_partial(\n"
        "                actions = actions,\n"
        "                profile_artifact = provisioning_profile,\n"
        "                rule_label = label,\n"
        "            ),\n"
        "        )\n"
    )

    new = (
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

    old_count = block.count(old)
    new_count = block.count(new)

    if old_count == 0 and new_count == 1:
        print(
            "[Build112] rules_apple unsigned ios_application "
            "provisioning gate already applied"
        )
        return

    require(
        old_count == 1 and new_count == 0,
        "unexpected ios_application provisioning partial shape: "
        f"old={old_count}, new={new_count}",
    )

    block = block.replace(old, new, 1)

    updated = (
        text[:start]
        + block
        + text[end:]
    )

    path.write_text(updated, encoding="utf-8")

    check = path.read_text(encoding="utf-8")
    check_start = check.find(start_token)
    check_end = check.find(
        end_token,
        check_start,
    )

    require(
        check_start >= 0 and check_end > check_start,
        "patched ios_application boundary missing",
    )

    check_block = check[
        check_start:check_end
    ]

    require(
        check_block.count(new) == 1,
        "conditional ios_application provisioning gate "
        "did not materialize",
    )

    require(
        check_block.count(old) == 0,
        "stale unconditional ios_application "
        "provisioning gate survived",
    )

    print(
        "[Build112] rules_apple ios_application now skips "
        "provisioning_profile_partial when profile is disabled"
    )


# Build112 Widget lastDotRange no-usage repair
def patch_widget_last_dot_range_no_usage() -> None:
    path = (
        ROOT
        / "Telegram"
        / "WidgetKitWidget"
        / "TodayViewController.swift"
    )

    require(
        path.is_file(),
        f"missing materialized Widget source: {path}",
    )

    text = path.read_text(encoding="utf-8")

    old = (
        '    guard let appBundleIdentifier = Bundle.main.bundleIdentifier, '
        'let lastDotRange = appBundleIdentifier.range('
        'of: ".", options: [.backwards]) else {\n'
    )

    new = (
        '    guard let appBundleIdentifier = Bundle.main.bundleIdentifier, '
        'appBundleIdentifier.range('
        'of: ".", options: [.backwards]) != nil else {\n'
    )

    old_count = text.count(old)
    new_count = text.count(new)

    if old_count == 0 and new_count == 1:
        print(
            "[Build112] Widget lastDotRange no-usage "
            "repair already applied"
        )
        return

    require(
        old_count == 1 and new_count == 0,
        "unexpected Widget combined bundle-id guard shape: "
        f"old={old_count}, new={new_count}",
    )

    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")

    check = path.read_text(encoding="utf-8")

    require(
        check.count(old) == 0,
        "stale Widget lastDotRange guard survived",
    )

    require(
        check.count(new) == 1,
        "Widget no-usage repair did not materialize",
    )

    print(
        "[Build112] Widget lastDotRange no-usage repaired"
    )


def main() -> None:
    patch_rules_apple_unsigned_ios_extensions()
    patch_rules_apple_unsigned_ios_application()
    patch_widget_last_dot_range_no_usage()
    require(BUILD.is_file(), f"missing {BUILD}")

    build = BUILD.read_text(encoding="utf-8")

    # Build111 is the canonical owner of the native Xcode 26 Composer assets.
    # Build112 must not convert Glass to PNG/.alticon or re-own actool.
    require(
        'primary_app_icon = "Telegram"' in build,
        "Build111 Telegram primary_app_icon missing",
    )

    for name in ("JerkgramGlassReveal", "JerkgramGlassSolid"):
        require(
            f'"{name}"' in build,
            f"Build111 native Composer icon missing: {name}",
        )

    require(
        "Telegram-iOS/JerkgramGlassReveal.alticon" not in build
        and "Telegram-iOS/JerkgramGlassSolid.alticon" not in build,
        "Glass must never use legacy .alticon",
    )

    # Cleanup only the exact obsolete Build112 bridge if this patcher is
    # re-applied to a tree that already contains the previous Build112 attempt.
    old_inline = re.compile(
        r'(?m)^[ \t]*'
        + re.escape(OLD_MARKER)
        + r'[ \t]*\n'
        r'[ \t]*ipa_post_processor[ \t]*=[ \t]*'
        r'":JerkgramIconComposerPostProcessor",[ \t]*\n?'
    )
    build, inline_count = old_inline.subn("", build)

    old_target = re.compile(
        r'\n?'
        + re.escape(OLD_MARKER)
        + r'\n'
        r'sh_binary\(\n'
        r'[ \t]*name = "JerkgramIconComposerPostProcessor",\n'
        r'[ \t]*srcs = \["Telegram-iOS/JerkgramIconComposerPostProcessor\.sh"\],\n'
        r'[ \t]*visibility = \["//visibility:private"\],\n'
        r'\)\n?',
        re.MULTILINE,
    )
    build, target_count = old_target.subn("\n", build)

    require(
        'ipa_post_processor = ":JerkgramIconComposerPostProcessor"' not in build,
        "obsolete Build112 main-app ipa_post_processor survived cleanup",
    )
    require(
        'name = "JerkgramIconComposerPostProcessor"' not in build,
        "obsolete Build112 sh_binary survived cleanup",
    )

    BUILD.write_text(build, encoding="utf-8")

    if OLD_POST.exists():
        payload = OLD_POST.read_text(encoding="utf-8", errors="ignore")
        require(
            "Jerkgram Build112 Icon Composer alternate registration bridge"
            in payload,
            "refusing to delete a non-Build112 postprocessor file",
        )
        OLD_POST.unlink()

    print("[Build112] native Build111 Composer assets preserved")
    print("[Build112] obsolete ipa_post_processor bridge removed")
    print(
        "[Build112] cleanup counts: "
        f"inline={inline_count}, target={target_count}"
    )
    print("[Build112] no Glass PNG/.alticon fallback introduced")


if __name__ == "__main__":
    main()
