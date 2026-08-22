#!/usr/bin/env python3

from pathlib import Path
import json
import os
import re

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

PRIVATE = (
    "app.pumpkin6584.lion7414",
    "5VZ6BJLW8Q",
    "group.4a348a9b186b700c.",
)

MAPPING = {
    "Jerkgram/Settings/Airplane":
        "53606A",

    "Chat/Context Menu/Eye":
        "4B5064",

    "Chat/Context Menu/MessageBubble":
        "4B6F83",

    "Premium/CopyProtection/NoForward":
        "87452F",

    "Item List/Icons/Stories":
        "6A5C78",

    "Chat/Context Menu/ApplyTheme":
        "676C43",

    "Chat/Context Menu/FormatCode":
        "8A6138",

    "Chat/Context Menu/Info":
        "4B4F54",
}

OLD = (
    "GhostBaseHome",
    "GhostBaseGhostMode",
    "GhostBaseMessages",
    "GhostBaseProtectedContent",
    "GhostBaseMediaStories",
    "GhostBaseAppearance",
    "GhostBaseDebugResearch",
    "GhostBaseAbout",
)


def require(value, message):
    if not value:
        raise RuntimeError(
            "[verify Build114] "
            + message
        )


def read(path):
    require(
        path.is_file(),
        f"missing: {path}"
    )

    return path.read_text(
        encoding="utf-8"
    )


bg = read(PROFILE_BG)
pane = read(PANE_CONTAINER)
settings = read(JG_SETTINGS)
main_items = read(MAIN_ITEMS)

require(
    "BUILD113_STATIC_AVATAR_BLUR_OWNER1"
    not in bg,
    "Build113 profile darkness survived"
)

require(
    "GhostBase v1.1U "
    "BUILD106_STATIC_AVATAR_BLUR1"
    in bg,
    "pre-Build113 blur owner missing"
)

require(
    "BUILD114_SOURCE_LUMINANCE1"
    in bg,
    "real source luminance bridge missing"
)

require(
    "BUILD114_LINKS_ONLY_READABILITY1"
    in pane,
    "Links-only owner missing"
)

start = pane.find(
    "BUILD114_LINKS_ONLY_READABILITY1"
)

owner = pane[
    start:start + 2400
]

require(
    "self.currentPaneKey == .links"
    in owner,
    "Links predicate missing"
)

for forbidden in (
    "self.currentPaneKey == .files",
    "self.currentPaneKey == .voice",
    "self.currentPaneKey == .music",
    "overallDarkAppearance",
):
    require(
        forbidden not in owner,
        (
            "broad/theme based "
            "pane darkness survived: "
            + forbidden
        )
    )

require(
    "0.26 * lightness"
    in owner,
    "adaptive Links scrim missing"
)

entries_start = settings.find(
    "private func ghostBaseSettingsEntries("
)

controller_start = settings.find(
    "public func ghostBaseSettingsController",
    entries_start
)

require(
    entries_start >= 0
    and controller_start > entries_start,
    "Settings entries bounds missing"
)

entries = settings[
    entries_start:controller_start
]

for forbidden in (
    '"PROFILEINTEL1"',
    '"PROFILEINTEL2"',
    '"profileIntel1Probe"',
    '"profileIntel2Snapshot"',
):
    require(
        forbidden not in entries,
        (
            "visible PROFILEINTEL "
            "surface survived: "
            + forbidden
        )
    )

require(
    "ghostBaseProfileIntelReport"
    in settings,
    "PROFILEINTEL1 core/helper removed"
)

require(
    "ghostBaseProfileIntel2Report"
    in settings,
    "PROFILEINTEL2 core/helper removed"
)

for path, text in (
    (JG_SETTINGS, settings),
    (MAIN_ITEMS, main_items)
):
    require(
        "renderSettingsIcon("
        in text,
        (
            "canonical renderer missing: "
            f"{path.name}"
        )
    )

    require(
        "scaleFactor: 1.0"
        in text,
        (
            "scaleFactor != 1.0: "
            f"{path.name}"
        )
    )

    for glyph, color in (
        MAPPING.items()
    ):
        require(
            glyph in text,
            (
                "glyph missing: "
                + glyph
            )
        )

        require(
            f"0x{color}"
            in text,
            (
                "color missing for "
                + glyph
            )
        )

    for old in OLD:
        require(
            old not in text,
            (
                "old AI icon active: "
                + old
            )
        )

airplanes = [
    path
    for path
    in (
        ROOT
        / "submodules/TelegramUI"
    ).rglob(
        "Airplane.imageset"
    )
    if (
        "/Jerkgram/Settings/"
        "Airplane.imageset"
    )
    in (
        str(path)
        .replace("\\", "/")
    )
]

require(
    len(airplanes) == 1,
    (
        "Airplane imageset candidates="
        f"{airplanes}"
    )
)

airplane = airplanes[0]

contents = json.loads(
    (
        airplane
        / "Contents.json"
    ).read_text(
        encoding="utf-8"
    )
)

svg_files = [
    airplane / entry["filename"]
    for entry
    in contents.get(
        "images",
        []
    )
    if (
        isinstance(
            entry,
            dict
        )
        and entry.get(
            "filename"
        )
    )
]

require(
    svg_files,
    "Airplane SVG missing"
)

for path in svg_files:
    require(
        path.is_file(),
        f"missing vector: {path}"
    )

    raw = path.read_text(
        encoding="utf-8"
    )

    require(
        'width="24"'
        in raw
        and 'height="24"'
        in raw,
        "Airplane is not 24x24 vector"
    )

    require(
        'fill-rule="evenodd"'
        in raw,
        "Reveal cutout lost"
    )

    require(
        "<image"
        not in raw
        and "<filter"
        not in raw,
        "Airplane contains raster/effect"
    )

stock = (
    "Chat/Context Menu/Eye",
    "Chat/Context Menu/MessageBubble",
    "Premium/CopyProtection/NoForward",
    "Item List/Icons/Stories",
    "Chat/Context Menu/ApplyTheme",
    "Chat/Context Menu/FormatCode",
    "Chat/Context Menu/Info",
)

for logical in stock:
    parts = logical.split("/")

    leaf = (
        parts[-1]
        + ".imageset"
    )

    candidates = []

    for path in ROOT.rglob(
        leaf
    ):
        normalized = (
            str(path)
            .replace("\\", "/")
        )

        expected_suffix = (
            "/"
            + "/".join(
                parts[:-1]
                + [leaf]
            )
        )

        if (
            ".xcassets/"
            in normalized
            and normalized.endswith(
                expected_suffix
            )
        ):
            candidates.append(
                path
            )

    require(
        candidates,
        (
            "stock Telegram asset "
            "not found: "
            + logical
        )
    )


dynamic_targets = (
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

    "Telegram/NotificationService/Sources/"
    "NotificationService.swift",
)

resolved_occurrences = 0

for relative in dynamic_targets:
    text = read(
        ROOT / relative
    )

    require(
        "BUILD114_SIGNER_APPGROUP1"
        in text,
        (
            "signer-neutral AppGroup helper "
            "missing: "
            + relative
        )
    )

    resolved_occurrences += text.count(
        "jerkgramResolvedApplicationGroupIdentifier("
        'fallback: "group.\\(baseAppBundleId)"'
        ")"
    )

    require(
        'let appGroupName = '
        '"group.\\(baseAppBundleId)"'
        not in text,
        (
            "raw Official AppGroup lookup "
            "still active: "
            + relative
        )
    )

require(
    resolved_occurrences == 9,
    (
        "signer-neutral AppGroup owner count "
        f"!= 9: {resolved_occurrences}"
    )
)


print(
    "[verify Build114] GREEN"
)

print(
    "[verify Build114] "
    "profile scene restored to "
    "pre-Build113 visual owner"
)

print(
    "[verify Build114] "
    "Links only: adaptive local "
    "scrim from actual source luminance"
)

print(
    "[verify Build114] "
    "PROFILEINTEL visible UI removed; "
    "core/helper retained"
)

print(
    "[verify Build114] "
    "Settings icons = "
    "7 stock Telegram bundle glyphs "
    "+ canonical Reveal airplane"
)

print(
    "[verify Build114] "
    "old AI icon references absent"
)

print(
    "[verify Build114] "
    "signer-neutral AppGroup resolution "
    "from effective provisioning profile"
)

print(
    "[verify Build114] "
    "legacy internal build identity intentionally "
    "retained until Build113 final verifier"
)

print(
    "[verify Build114] "
    "RESOURCE CHANGE: "
    "+ Jerkgram/Settings/Airplane.imageset"
)
