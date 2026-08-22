#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET

SCRIPT_DIR = Path(__file__).resolve().parent

BUILDER = Path(
    os.environ.get(
        "GHOSTBASE_BUILDER_ROOT",
        str(SCRIPT_DIR.parent)
    )
).resolve()

ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        str(Path.cwd())
    )
).resolve()


PROFILE_BG = (
    ROOT
    / "submodules/TelegramUI/Components/PeerInfo"
    / "PeerInfoScreen/Sources"
    / "GhostBaseProfileFullscreenBackground.swift"
)

PANE_CONTAINER = (
    ROOT
    / "submodules/TelegramUI/Components/PeerInfo"
    / "PeerInfoScreen/Sources"
    / "PeerInfoPaneContainerNode.swift"
)

JG_SETTINGS = (
    ROOT
    / "submodules/SettingsUI/Sources/GhostBase"
    / "GhostBaseSettingsController.swift"
)

MAIN_ITEMS = (
    ROOT
    / "submodules/TelegramUI/Components/PeerInfo"
    / "PeerInfoScreen/Sources"
    / "PeerInfoSettingsItems.swift"
)

PACKAGE_ZIP = (
    BUILDER
    / "assets/JerkgramGlass"
    / "JerkgramGlassIconComposerPackages.zip"
)

EXPECTED_REVEAL_PLANE = (
    "9dc83c22a01878aac9f8494c509a7862"
    "fdd1679d7e7f7f0026afc367d3a7e304"
)

PRIVATE_BASE = "app.pumpkin6584.lion7414"
PRIVATE_TEAM = "5VZ6BJLW8Q"

PUBLIC_BASE = "ph.telegra.Telegraph"
PUBLIC_TEAM = "C67CF9S4VU"
PUBLIC_GROUP = "group.ph.telegra.Telegraph"

LUMINANCE_KEY = (
    "Jerkgram.ProfileBackdrop.SourceLuminance"
)

OLD_ICONS = {
    "GhostBaseHome":
        "Jerkgram/Settings/Airplane",

    "GhostBaseGhostMode":
        "Chat/Context Menu/Eye",

    "GhostBaseMessages":
        "Chat/Context Menu/MessageBubble",

    "GhostBaseProtectedContent":
        "Premium/CopyProtection/NoForward",

    "GhostBaseMediaStories":
        "Item List/Icons/Stories",

    "GhostBaseAppearance":
        "Chat/Context Menu/ApplyTheme",

    "GhostBaseDebugResearch":
        "Chat/Context Menu/FormatCode",

    "GhostBaseAbout":
        "Chat/Context Menu/Info",
}

ICON_COLORS = {
    "Jerkgram/Settings/Airplane":
        0x53606A,

    "Chat/Context Menu/Eye":
        0x4B5064,

    "Chat/Context Menu/MessageBubble":
        0x4B6F83,

    "Premium/CopyProtection/NoForward":
        0x87452F,

    "Item List/Icons/Stories":
        0x6A5C78,

    "Chat/Context Menu/ApplyTheme":
        0x676C43,

    "Chat/Context Menu/FormatCode":
        0x8A6138,

    "Chat/Context Menu/Info":
        0x4B4F54,
}


def require(value, message):
    if not value:
        raise RuntimeError(
            "[Build114] " + message
        )


def read(path):
    require(
        path.is_file(),
        f"missing source: {path}"
    )

    return path.read_text(
        encoding="utf-8"
    )


def write(path, text):
    path.write_text(
        text,
        encoding="utf-8"
    )


def normalize_public_identity():
    roots = [
        ROOT / "Telegram",
        ROOT / "Swiftgram",
        ROOT / "submodules/TelegramUI",
        ROOT / "submodules/WidgetItems",
        ROOT / "build-system/example-configuration",
        ROOT / "build-input/configuration-repository",
    ]

    suffixes = {
        ".swift",
        ".bzl",
        ".plist",
        ".entitlements",
        ".json",
        ".m",
        ".mm",
        ".h",
    }

    private_group = re.compile(
        r"group\.4a348a9b186b700c\.\d+"
    )

    changed = []

    for root in roots:
        if not root.exists():
            continue

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            if (
                path.name
                not in {"BUILD", "BUILD.bazel"}
                and path.suffix not in suffixes
            ):
                continue

            try:
                text = path.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )
            except Exception:
                continue

            old = text

            text = text.replace(
                PRIVATE_BASE,
                PUBLIC_BASE
            )

            text = text.replace(
                PRIVATE_TEAM,
                PUBLIC_TEAM
            )

            text = private_group.sub(
                PUBLIC_GROUP,
                text
            )

            if text != old:
                path.write_text(
                    text,
                    encoding="utf-8"
                )

                changed.append(
                    str(
                        path.relative_to(ROOT)
                    )
                )

    print(
        "[Build114] public identity "
        f"normalized in {len(changed)} files"
    )


def restore_resign_dynamic_identity():
    r"""
    BUILD114_RESIGN_DYNAMIC_IDENTITY1

    Deterministic late-patch applied after the legacy
    Build113 source verifiers.

    gb_patch_swift.py intentionally hardcodes Telegram
    identity during the legacy materialization chain.
    Build114 reverses only the known runtime identity
    declarations required by the main app and six
    extensions.

    No clean Official checkout is required at CI runtime.
    The exact declaration matrix below was audited against
    clean Official Telegram iOS 12.9.2 / 6ad963e5.
    """

    plans = (
        (
            "submodules/TelegramUI/Sources/AppDelegate.swift",
            {
                "baseAppBundleId": (
                    "Bundle.main.bundleIdentifier!",
                    "Bundle.main.bundleIdentifier!",
                    "Bundle.main.bundleIdentifier!",
                    "Bundle.main.bundleIdentifier!",
                    "Bundle.main.bundleIdentifier!",
                ),
                "appGroupName": (
                    r'"group.\(baseAppBundleId)"',
                    r'"group.\(baseAppBundleId)"',
                ),
            },
        ),
        (
            "Telegram/SiriIntents/IntentHandler.swift",
            {
                "baseAppBundleId": (
                    "String(appBundleIdentifier[..<lastDotRange.lowerBound])",
                    "String(appBundleIdentifier[..<lastDotRange.lowerBound])",
                ),
                "appGroupName": (
                    r'"group.\(baseAppBundleId)"',
                    r'"group.\(baseAppBundleId)"',
                ),
            },
        ),
        (
            "Telegram/WidgetKitWidget/TodayViewController.swift",
            {
                "baseAppBundleId": (
                    "String(appBundleIdentifier[..<lastDotRange.lowerBound])",
                    "String(appBundleIdentifier[..<lastDotRange.lowerBound])",
                ),
                "appGroupName": (
                    r'"group.\(baseAppBundleId)"',
                ),
            },
        ),
        (
            "Telegram/BroadcastUpload/BroadcastUploadExtension.swift",
            {
                "baseAppBundleId": (
                    "String(appBundleIdentifier[..<lastDotRange.lowerBound])",
                ),
                "appGroupName": (
                    r'"group.\(baseAppBundleId)"',
                ),
            },
        ),
        (
            "Telegram/Share/ShareRootController.swift",
            {
                "baseAppBundleId": (
                    "String(appBundleIdentifier[..<lastDotRange.lowerBound])",
                ),
                "appGroupName": (
                    r'"group.\(baseAppBundleId)"',
                ),
            },
        ),
        (
            "Telegram/NotificationContent/NotificationViewController.swift",
            {
                "baseAppBundleId": (
                    "String(appBundleIdentifier[..<lastDotRange.lowerBound])",
                ),
                "appGroupName": (
                    r'"group.\(baseAppBundleId)"',
                ),
            },
        ),
        (
            "Telegram/NotificationService/Sources/NotificationService.swift",
            {
                "baseAppBundleId": (
                    "String(appBundleIdentifier[..<lastDotRange.lowerBound])",
                ),
                "appGroupName": (
                    r'"group.\(baseAppBundleId)"',
                ),
            },
        ),
    )

    restored = 0

    for relative, declarations in plans:
        path = ROOT / relative

        require(
            path.is_file(),
            (
                "materialized identity target "
                f"missing: {relative}"
            )
        )

        text = path.read_text(
            encoding="utf-8"
        )

        for name, expressions in declarations.items():
            pattern = re.compile(
                rf"^(?P<indent>[ \t]*)"
                rf"let[ \t]+{re.escape(name)}"
                rf"(?:[ \t]*:[^=\n]+)?"
                rf"[ \t]*=[^\n]*$",
                re.M
            )

            matches = list(
                pattern.finditer(text)
            )

            require(
                len(matches) == len(expressions),
                (
                    f"{relative}: {name} declaration "
                    f"count current={len(matches)} "
                    f"expected={len(expressions)}"
                )
            )

            for match, expression in reversed(
                list(
                    zip(
                        matches,
                        expressions
                    )
                )
            ):
                replacement = (
                    match.group("indent")
                    + f"let {name} = {expression}"
                )

                if match.group(0) != replacement:
                    restored += 1

                text = (
                    text[:match.start()]
                    + replacement
                    + text[match.end():]
                )

            # Legacy hardcoding may leave dummy usages solely
            # to silence warnings after replacing dynamic code.
            dummy = re.compile(
                rf"^[ \t]*_[ \t]*=[ \t]*"
                rf"{re.escape(name)}[ \t]*\n?",
                re.M
            )

            text = dummy.sub(
                "",
                text
            )

        path.write_text(
            text,
            encoding="utf-8"
        )

        # Fail closed: after the rewrite every audited
        # declaration must exactly match the canonical RHS.
        check = path.read_text(
            encoding="utf-8"
        )

        for name, expressions in declarations.items():
            pattern = re.compile(
                rf"^[ \t]*let[ \t]+{re.escape(name)}"
                rf"(?:[ \t]*:[^=\n]+)?"
                rf"[ \t]*=[ \t]*(?P<rhs>[^\n]+)$",
                re.M
            )

            actual = tuple(
                match.group("rhs").strip()
                for match in pattern.finditer(check)
            )

            require(
                actual == expressions,
                (
                    f"{relative}: canonical {name} "
                    f"restore mismatch: "
                    f"actual={actual!r} "
                    f"expected={expressions!r}"
                )
            )

    print(
        "[Build114] restored",
        restored,
        "legacy-hardcoded identity declarations"
    )

    print(
        "[Build114] canonical dynamic owners: "
        "7 files / 13 base-ID sites / "
        "9 AppGroup sites"
    )


def install_signer_neutral_appgroup_resolver():
    r"""
    Official Telegram derives:
        group.\(baseAppBundleId)

    That is correct for App Store Telegram, but not
    necessarily for sideload signing: a signer can replace
    CFBundleIdentifier while provisioning a completely
    different allowed App Group.

    Build114 therefore reads the actual App Group from the
    embedded provisioning profile produced by the user's
    signer. No Team ID / App Group owned by the builder is
    baked into this runtime path.

    If a signer provides no readable profile, fall back to
    the pristine Official Telegram derivation.
    """

    targets = (
        "submodules/TelegramUI/Sources/AppDelegate.swift",

        "Telegram/SiriIntents/IntentHandler.swift",

        "Telegram/WidgetKitWidget/"
        "TodayViewController.swift",

        "Telegram/BroadcastUpload/"
        "BroadcastUploadExtension.swift",

        "Telegram/Share/"
        "ShareRootController.swift",

        "Telegram/NotificationContent/"
        "NotificationViewController.swift",

        "Telegram/NotificationService/Sources/"
        "NotificationService.swift",
    )

    marker = (
        "// MARK: Jerkgram v1.2C "
        "BUILD114_SIGNER_APPGROUP1"
    )

    helper = r'''
// MARK: Jerkgram v1.2C BUILD114_SIGNER_APPGROUP1
private func jerkgramResolvedApplicationGroupIdentifier(
    fallback: String
) -> String {
    let bundleURL = Bundle.main.bundleURL

    var profileURLs: [URL] = [
        bundleURL.appendingPathComponent(
            "embedded.mobileprovision"
        )
    ]

    // For an extension:
    //
    // Foo.app/PlugIns/Bar.appex
    //                 ↓
    // Foo.app/embedded.mobileprovision
    //
    // Some signers embed a profile in every .appex,
    // others only keep the main-app profile. Support both.
    let possibleContainingAppURL =
        bundleURL
            .deletingLastPathComponent()
            .deletingLastPathComponent()

    if possibleContainingAppURL.pathExtension == "app" {
        profileURLs.append(
            possibleContainingAppURL
                .appendingPathComponent(
                    "embedded.mobileprovision"
                )
        )
    }

    var visited = Set<String>()

    for profileURL in profileURLs {
        if visited.contains(profileURL.path) {
            continue
        }

        visited.insert(profileURL.path)

        guard let profileData =
            try? Data(contentsOf: profileURL)
        else {
            continue
        }

        // A .mobileprovision is CMS-wrapped, but the plist
        // payload itself is embedded as XML. We only read
        // that plist; no private Security API is required.
        let profileText = String(
            decoding: profileData,
            as: UTF8.self
        )

        guard
            let plistStart = profileText.range(
                of: "<plist"
            ),
            let plistEnd = profileText.range(
                of: "</plist>",
                options: [.backwards]
            ),
            plistStart.lowerBound
                < plistEnd.upperBound
        else {
            continue
        }

        let plistText = String(
            profileText[
                plistStart.lowerBound
                ..< plistEnd.upperBound
            ]
        )

        guard
            let plistData = plistText.data(
                using: .utf8
            ),
            let root = try?
                PropertyListSerialization
                    .propertyList(
                        from: plistData,
                        options: [],
                        format: nil
                    ) as? [String: Any],
            let entitlements =
                root["Entitlements"]
                    as? [String: Any],
            let groups =
                entitlements[
                    "com.apple.security.application-groups"
                ] as? [String],
            let group =
                groups.first(
                    where: {
                        !$0.isEmpty
                    }
                )
        else {
            continue
        }

        return group
    }

    return fallback
}

'''

    replacement_expression = (
        'let appGroupName = '
        'jerkgramResolvedApplicationGroupIdentifier('
        'fallback: "group.\\(baseAppBundleId)"'
        ')'
    )

    # Accept both states that can legitimately exist here:
    #
    # 1. clean Official:
    #    let appGroupName = "group.\(baseAppBundleId)"
    #
    # 2. legacy GhostBase-materialized:
    #    let appGroupName = "group.<hardcoded-id>"
    #
    # AppDelegate.swift is a materialized/custom owner and has
    # no same-path counterpart in clean Official 12.9.2, so it
    # must be normalized here rather than in the Official-copy
    # restoration pass.
    appgroup_pattern = re.compile(
        r'let appGroupName\s*=\s*"group\.[^"\n]+"'
    )

    total_replacements = 0

    for relative in targets:
        path = ROOT / relative

        require(
            path.is_file(),
            (
                "AppGroup runtime owner missing: "
                f"{relative}"
            )
        )

        text = path.read_text(
            encoding="utf-8"
        )

        if marker not in text:
            imports = list(
                re.finditer(
                    r"^import [^\n]+\n",
                    text,
                    re.M
                )
            )

            require(
                imports,
                (
                    "Swift imports missing: "
                    f"{relative}"
                )
            )

            position = imports[-1].end()

            text = (
                text[:position]
                + "\n"
                + helper
                + text[position:]
            )

        text, count = appgroup_pattern.subn(
            replacement_expression,
            text
        )

        require(
            count >= 1,
            (
                "AppGroup owner expression "
                f"missing: {relative}"
            )
        )

        total_replacements += count

        path.write_text(
            text,
            encoding="utf-8"
        )

    require(
        total_replacements == 9,
        (
            "unexpected AppGroup owner count: "
            f"{total_replacements}"
        )
    )

    print(
        "[Build114] signer-neutral AppGroup "
        "resolver installed in 7 processes / "
        "9 Official call sites"
    )


def verify_dynamic_extensions():
    targets = (
        "submodules/TelegramUI/Sources/"
        "AppDelegate.swift",

        "Telegram/SiriIntents/"
        "IntentHandler.swift",

        "Telegram/WidgetKitWidget/"
        "TodayViewController.swift",

        "Telegram/BroadcastUpload/"
        "BroadcastUploadExtension.swift",

        "Telegram/Share/"
        "ShareRootController.swift",

        "Telegram/NotificationContent/"
        "NotificationViewController.swift",

        "Telegram/NotificationService/"
        "Sources/NotificationService.swift",
    )

    dynamic_hits = 0

    for relative in targets:
        text = read(
            ROOT / relative
        )

        if (
            'let appGroupName = '
            '"group.\\(baseAppBundleId)"'
            in text
        ):
            dynamic_hits += 1

        require(
            (
                f'let appGroupName = '
                f'"{PUBLIC_GROUP}"'
            )
            not in text,
            (
                "static AppGroup remains: "
                f"{relative}"
            )
        )

    require(
        dynamic_hits >= 5,
        (
            "too few resign-dynamic "
            f"extension owners: {dynamic_hits}"
        )
    )

    print(
        "[Build114] extension identity "
        "is resign-dynamic"
    )


def main():
    for path in (
        PROFILE_BG,
        PANE_CONTAINER,
        JG_SETTINGS,
        MAIN_ITEMS
    ):
        require(
            path.is_file(),
            f"owner missing: {path}"
        )

    restore_resign_dynamic_identity()

    install_signer_neutral_appgroup_resolver()

    restore_pre_build113_profile()

    install_source_luminance_bridge()

    patch_links_only()

    hide_profileintel_ui()

    materialize_airplane()

    patch_settings_icons()

    verify_dynamic_extensions()

    print(
        "[Build114] GREEN: "
        "source/runtime/UI materialized"
    )


if __name__ == "__main__":
    main()
