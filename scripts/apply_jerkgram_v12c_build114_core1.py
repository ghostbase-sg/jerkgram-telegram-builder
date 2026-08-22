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

OFFICIAL = (
    BUILDER
    / "ports/ghostbase_12_9_2_port"
    / "telegram-ios-12.9.2-official"
)

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

    Late-patch after the Build113 legacy materialization.

    Exact runtime identity declarations were audited
    against clean Official Telegram iOS 12.9.2,
    commit 6ad963e5b62d354da79040f388ae2b9132fb17b8.

    CI operates only on the already-materialized source.
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
                list(zip(matches, expressions))
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

            text = re.sub(
                rf"^[ \t]*_[ \t]*=[ \t]*"
                rf"{re.escape(name)}[ \t]*\n?",
                "",
                text,
                flags=re.M
            )

        path.write_text(
            text,
            encoding="utf-8"
        )

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
        "[Build114] dynamic identity: "
        "7 owners / 13 base-ID sites / "
        "9 AppGroup sites"
    )



def restore_pre_build113_profile():
    text = read(PROFILE_BG)

    build113 = '''            // MARK: Jerkgram v1.2B BUILD113_STATIC_AVATAR_BLUR_OWNER1
            // Keep the later decoded-avatar/cache/reopen pipeline, but restore
            // the Build97 visual owner for static avatars. Do not lower the
            // UIVisualEffectView alpha: that reveals the sharp image below it.
            //
            // Static profile photos always use the normal systemMaterial
            // family so Low Power / reduced-cost policy cannot silently turn
            // the fullscreen profile into an almost-sharp stretched avatar.
            if animatedSource == nil {
                self.blurView.effect = UIBlurEffect(
                    style: isDark
                        ? .systemMaterialDark
                        : .systemMaterialLight
                )
            } else {
                self.blurView.effect = UIBlurEffect(style: effectStyle)
            }
            self.blurView.alpha = 1.0
'''

    build106 = '''            // MARK: GhostBase v1.1U BUILD106_STATIC_AVATAR_BLUR1
            // Build105 runtime proved that lowering UIVisualEffectView.alpha
            // does not lower blur intensity: it exposes the sharp stretched
            // image beneath it. Keep the persistent blur owner fully opaque.
            //
            // Reduced mode still affects the existing tint/cost policy; it
            // must not turn the scene back into an almost-unblurred avatar.
            self.blurView.alpha = 1.0
'''

    require(
        (
            build113 in text
            or build106 in text
        ),
        "Build113/Build106 blur owner missing"
    )

    if build113 in text:
        text = text.replace(
            build113,
            build106,
            1
        )

    require(
        "BUILD113_STATIC_AVATAR_BLUR_OWNER1"
        not in text,
        "Build113 global blur override survived"
    )

    write(
        PROFILE_BG,
        text
    )

    print(
        "[Build114] removed ONLY "
        "Build113 profile dark/blur regression"
    )


def install_source_luminance_bridge():
    text = read(PROFILE_BG)

    marker = (
        "// MARK: Jerkgram v1.2C "
        "BUILD114_SOURCE_LUMINANCE1"
    )

    if marker in text:
        return

    anchor = '''        let sourceColor = color
        let luminance = Self.colorLuminance(sourceColor)
'''

    require(
        anchor in text,
        "Build110 real-source luminance anchor missing"
    )

    replacement = anchor + f'''        // MARK: Jerkgram v1.2C BUILD114_SOURCE_LUMINANCE1
        // Read-only bridge for Links readability.
        // It does NOT alter profile tint / blur / source.
        UserDefaults.standard.set(
            Double(luminance),
            forKey: "{LUMINANCE_KEY}"
        )
'''

    text = text.replace(
        anchor,
        replacement,
        1
    )

    write(
        PROFILE_BG,
        text
    )

    print(
        "[Build114] actual profile-source "
        "luminance exposed for Links only"
    )


def patch_links_only():
    text = read(PANE_CONTAINER)

    marker = (
        "// MARK: Jerkgram v1.2C "
        "BUILD114_LINKS_ONLY_READABILITY1"
    )

    if marker in text:
        return

    old = '''        // MARK: Jerkgram v1.1Z BUILD111_LIST_PANE_READABILITY1
        // One shared translucent readability surface for the
        // native Files / Links / Voice / Music profile panes.
        // No per-cell blur and no pane geometry changes.
        if self.ghostBaseGlassEnabled {
            let jerkgramNeedsReadabilitySurface =
                self.currentPaneKey == .files
                || self.currentPaneKey == .links
                || self.currentPaneKey == .voice
                || self.currentPaneKey == .music

            if jerkgramNeedsReadabilitySurface {
                let isDark =
                    presentationData
                        .theme
                        .overallDarkAppearance

                self.backgroundColor = UIColor(
                    white: isDark ? 0.0 : 1.0,
                    alpha: isDark ? 0.26 : 0.18
                )
            } else {
                self.backgroundColor = .clear
            }
        } else {
            self.backgroundColor = backgroundColor
        }
'''

    require(
        old in text,
        (
            "Build111 Files/Links/Voice/Music "
            "readability owner missing"
        )
    )

    new = f'''        // MARK: Jerkgram v1.2C BUILD114_LINKS_ONLY_READABILITY1
        // Files / Voice / Music are transparent.
        //
        // Links alone receives a LOCAL black scrim,
        // and only when the actual profile source is light.
        //
        // No scene-wide tint.
        // No per-cell blur.
        // No geometry changes.
        if self.ghostBaseGlassEnabled {{
            if self.currentPaneKey == .links,
               let value = UserDefaults.standard.object(
                   forKey: "{LUMINANCE_KEY}"
               ) as? NSNumber {{
                let luminance =
                    CGFloat(value.doubleValue)

                let lightness = max(
                    0.0,
                    min(
                        1.0,
                        (luminance - 0.55)
                            / 0.45
                    )
                )

                self.backgroundColor =
                    UIColor.black
                        .withAlphaComponent(
                            0.26 * lightness
                        )
            }} else {{
                self.backgroundColor = .clear
            }}
        }} else {{
            self.backgroundColor =
                backgroundColor
        }}
'''

    text = text.replace(
        old,
        new,
        1
    )

    write(
        PANE_CONTAINER,
        text
    )

    print(
        "[Build114] Links-only adaptive "
        "local scrim installed"
    )


def hide_profileintel_ui():
    text = read(JG_SETTINGS)

    blocks = [
        '''
        entries.append(.header(
            debug,
            "PROFILEINTEL1"
        ))
        entries.append(.researchAction(
            debug,
            950,
            "Проверить username из буфера",
            "profileIntel1Probe"
        ))
        entries.append(.researchInfo(
            debug,
            951,
            ghostBaseProfileIntelReport()
        ))
''',

        '''
        entries.append(.header(
            debug,
            "PROFILEINTEL2"
        ))
        entries.append(.researchAction(
            debug,
            952,
            "Снимок профиля + история фото",
            "profileIntel2Snapshot"
        ))
        entries.append(.researchInfo(
            debug,
            953,
            ghostBaseProfileIntel2Report()
        ))
''',
    ]

    removed = 0

    for block in blocks:
        if block in text:
            text = text.replace(
                block,
                "\n",
                1
            )

            removed += 1

    start = text.find(
        "private func ghostBaseSettingsEntries("
    )

    end = text.find(
        "public func ghostBaseSettingsController",
        start
    )

    require(
        start >= 0
        and end > start,
        "Settings entries bounds missing"
    )

    entries = text[start:end]

    require(
        '"profileIntel1Probe"'
        not in entries,
        "PROFILEINTEL1 visible action survived"
    )

    require(
        '"profileIntel2Snapshot"'
        not in entries,
        "PROFILEINTEL2 visible action survived"
    )

    write(
        JG_SETTINGS,
        text
    )

    print(
        "[Build114] PROFILEINTEL core kept; "
        "visible Settings logging removed"
    )


def path_bbox(d):
    tokens = re.findall(
        (
            r"[AaCcHhLlMmQqSsTtVvZz]"
            r"|[-+]?(?:\d*\.\d+|\d+\.?)"
            r"(?:[eE][-+]?\d+)?"
        ),
        d
    )

    require(
        tokens,
        "Reveal Plane tokenization failed"
    )

    index = 0
    command = None

    x = 0.0
    y = 0.0
    sx = 0.0
    sy = 0.0

    xs = []
    ys = []

    def add(px, py):
        xs.append(px)
        ys.append(py)

    def number():
        nonlocal index

        require(
            (
                index < len(tokens)
                and not re.fullmatch(
                    r"[A-Za-z]",
                    tokens[index]
                )
            ),
            "unexpected SVG command/end"
        )

        value = float(
            tokens[index]
        )

        index += 1

        return value

    while index < len(tokens):
        if re.fullmatch(
            r"[A-Za-z]",
            tokens[index]
        ):
            command = tokens[index]
            index += 1

        require(
            command is not None,
            "SVG path missing command"
        )

        relative = command.islower()
        kind = command.upper()

        if kind == "Z":
            x = sx
            y = sy
            add(x, y)
            command = None
            continue

        if kind == "M":
            nx = number()
            ny = number()

            if relative:
                nx += x
                ny += y

            x = nx
            y = ny

            sx = x
            sy = y

            add(x, y)

            command = (
                "l"
                if relative
                else "L"
            )

        elif kind == "L":
            nx = number()
            ny = number()

            if relative:
                nx += x
                ny += y

            x = nx
            y = ny

            add(x, y)

        elif kind == "H":
            nx = number()

            if relative:
                nx += x

            x = nx
            add(x, y)

        elif kind == "V":
            ny = number()

            if relative:
                ny += y

            y = ny
            add(x, y)

        elif kind == "C":
            values = [
                number()
                for _ in range(6)
            ]

            if relative:
                values = [
                    values[0] + x,
                    values[1] + y,
                    values[2] + x,
                    values[3] + y,
                    values[4] + x,
                    values[5] + y,
                ]

            add(
                values[0],
                values[1]
            )

            add(
                values[2],
                values[3]
            )

            add(
                values[4],
                values[5]
            )

            x = values[4]
            y = values[5]

        elif kind == "S":
            values = [
                number()
                for _ in range(4)
            ]

            if relative:
                values = [
                    values[0] + x,
                    values[1] + y,
                    values[2] + x,
                    values[3] + y,
                ]

            add(
                values[0],
                values[1]
            )

            add(
                values[2],
                values[3]
            )

            x = values[2]
            y = values[3]

        elif kind == "Q":
            values = [
                number()
                for _ in range(4)
            ]

            if relative:
                values = [
                    values[0] + x,
                    values[1] + y,
                    values[2] + x,
                    values[3] + y,
                ]

            add(
                values[0],
                values[1]
            )

            add(
                values[2],
                values[3]
            )

            x = values[2]
            y = values[3]

        elif kind == "T":
            nx = number()
            ny = number()

            if relative:
                nx += x
                ny += y

            x = nx
            y = ny

            add(x, y)

        elif kind == "A":
            rx = number()
            ry = number()

            rotation = number()
            large = number()
            sweep = number()

            nx = number()
            ny = number()

            if relative:
                nx += x
                ny += y

            for px, py in (
                (x - rx, y - ry),
                (x + rx, y + ry),
                (nx - rx, ny - ry),
                (nx + rx, ny + ry),
                (nx, ny),
            ):
                add(px, py)

            x = nx
            y = ny

        else:
            raise RuntimeError(
                "[Build114] unsupported SVG "
                f"command: {command}"
            )

    require(
        xs and ys,
        "Reveal Plane bbox empty"
    )

    return (
        min(xs),
        min(ys),
        max(xs),
        max(ys),
    )


def find_eye_imageset():
    candidates = []

    base = (
        ROOT
        / "submodules/TelegramUI"
    )

    for path in base.rglob(
        "Eye.imageset"
    ):
        normalized = (
            str(path)
            .replace("\\", "/")
        )

        if (
            ".xcassets/"
            in normalized
            and (
                "/Chat/Context Menu/"
                "Eye.imageset"
            )
            in normalized
        ):
            candidates.append(
                path
            )

    require(
        len(candidates) == 1,
        (
            "canonical Eye.imageset "
            f"candidates={candidates}"
        )
    )

    return candidates[0]


def materialize_airplane():
    require(
        PACKAGE_ZIP.is_file(),
        (
            "missing canonical Composer package: "
            f"{PACKAGE_ZIP}"
        )
    )

    with zipfile.ZipFile(
        PACKAGE_ZIP,
        "r"
    ) as archive:
        matches = [
            name
            for name
            in archive.namelist()
            if name.endswith(
                "JerkgramGlassReveal.icon/"
                "Assets/Plane.svg"
            )
        ]

        require(
            len(matches) == 1,
            (
                "Reveal Plane candidates="
                f"{matches}"
            )
        )

        raw = archive.read(
            matches[0]
        )

    digest = hashlib.sha256(
        raw
    ).hexdigest()

    require(
        digest
        == EXPECTED_REVEAL_PLANE,
        "canonical Reveal Plane hash mismatch"
    )

    root = ET.fromstring(
        raw.decode("utf-8")
    )

    paths = [
        node
        for node in root.iter()
        if (
            node.tag.split("}")[-1]
            == "path"
        )
    ]

    require(
        len(paths) == 1,
        "Reveal Plane must contain one path"
    )

    path = paths[0]

    d = path.attrib.get(
        "d",
        ""
    )

    require(
        d,
        "Reveal Plane d empty"
    )

    require(
        (
            path.attrib.get(
                "fill-rule"
            )
            == "evenodd"
        ),
        "Reveal cutout must stay evenodd"
    )

    minx, miny, maxx, maxy = (
        path_bbox(d)
    )

    width = maxx - minx
    height = maxy - miny

    require(
        width > 0
        and height > 0,
        "Reveal bbox invalid"
    )

    size = max(
        width,
        height
    ) * 1.08

    cx = (
        minx + maxx
    ) / 2.0

    cy = (
        miny + maxy
    ) / 2.0

    vx = cx - size / 2.0
    vy = cy - size / 2.0

    svg = (
        '<?xml version="1.0" '
        'encoding="UTF-8"?>\n'

        '<svg '
        'xmlns="http://www.w3.org/2000/svg" '
        'width="24" '
        'height="24" '
        f'viewBox="{vx:.6f} '
        f'{vy:.6f} '
        f'{size:.6f} '
        f'{size:.6f}">\n'

        f'  <path d="{d}" '
        'fill="#000000" '
        'fill-rule="evenodd"/>\n'

        '</svg>\n'
    )

    eye = find_eye_imageset()

    contents_path = (
        eye
        / "Contents.json"
    )

    require(
        contents_path.is_file(),
        "Eye Contents.json missing"
    )

    contents = json.loads(
        contents_path.read_text(
            encoding="utf-8"
        )
    )

    catalog = eye

    while (
        catalog.suffix
        != ".xcassets"
    ):
        require(
            catalog.parent
            != catalog,
            "owning xcassets not found"
        )

        catalog = (
            catalog.parent
        )

    jerkgram_group = (
        catalog
        / "Jerkgram"
    )

    settings_group = (
        jerkgram_group
        / "Settings"
    )

    target = (
        settings_group
        / "Airplane.imageset"
    )

    if target.exists():
        shutil.rmtree(
            target
        )

    target.mkdir(
        parents=True
    )

    namespace = {
        "info": {
            "author": "xcode",
            "version": 1,
        },

        "properties": {
            "provides-namespace": True,
        },
    }

    jerkgram_group.mkdir(
        parents=True,
        exist_ok=True
    )

    settings_group.mkdir(
        parents=True,
        exist_ok=True
    )

    for group in (
        jerkgram_group,
        settings_group
    ):
        (
            group
            / "Contents.json"
        ).write_text(
            json.dumps(
                namespace,
                indent=2
            )
            + "\n",
            encoding="utf-8"
        )

    images = contents.get(
        "images"
    )

    require(
        isinstance(
            images,
            list
        )
        and images,
        "Eye images list missing"
    )

    output_images = []
    file_index = 0

    for entry in images:
        require(
            isinstance(
                entry,
                dict
            ),
            "Eye image entry malformed"
        )

        copied = dict(entry)

        if "filename" in copied:
            name = (
                "Airplane_"
                f"{file_index}.svg"
            )

            file_index += 1

            copied[
                "filename"
            ] = name

            (
                target
                / name
            ).write_text(
                svg,
                encoding="utf-8"
            )

        output_images.append(
            copied
        )

    require(
        file_index > 0,
        "Eye imageset has no file"
    )

    out_contents = dict(
        contents
    )

    out_contents[
        "images"
    ] = output_images

    (
        target
        / "Contents.json"
    ).write_text(
        json.dumps(
            out_contents,
            indent=2,
            ensure_ascii=False
        )
        + "\n",
        encoding="utf-8"
    )

    for old_name in OLD_ICONS:
        for candidate in (
            catalog.rglob(
                old_name
                + ".imageset"
            )
        ):
            shutil.rmtree(
                candidate
            )

    print(
        "[Build114] custom Settings asset: "
        f"{target.relative_to(ROOT)}"
    )

    print(
        "[Build114] airplane viewBox: "
        f"{vx:.3f} "
        f"{vy:.3f} "
        f"{size:.3f} "
        f"{size:.3f}"
    )


def icon_helper(function_name):
    cases = "\n".join(
        (
            f'    case "{name}":\n'
            f'        background = '
            f'0x{color:06X}'
        )
        for name, color
        in ICON_COLORS.items()
    )

    return f'''// MARK: Jerkgram v1.2C BUILD114_SETTINGS_ICONS1
private func {function_name}(
    _ name: String
) -> UIImage? {{
    let background: UInt32

    switch name {{
{cases}

    default:
        return nil
    }}

    return renderSettingsIcon(
        name: name,
        scaleFactor: 1.0,
        backgroundColors: [
            UIColor(
                rgb: background
            )
        ]
    )
}}

'''


def ensure_import(text, module):
    line = (
        f"import {module}"
    )

    if line in text:
        return text

    imports = list(
        re.finditer(
            r"^import [^\n]+$",
            text,
            re.M
        )
    )

    require(
        imports,
        "Swift imports missing"
    )

    position = (
        imports[-1].end()
    )

    return (
        text[:position]
        + "\n"
        + line
        + text[position:]
    )


def patch_settings_icons():
    text = read(
        JG_SETTINGS
    )

    text = ensure_import(
        text,
        "TelegramPresentationData"
    )

    for old, new in (
        OLD_ICONS.items()
    ):
        text = text.replace(
            f'"{old}"',
            f'"{new}"'
        )

    text = text.replace(
        (
            "icon: UIImage("
            "bundleImageName: iconName),"
        ),
        (
            "icon: "
            "jerkgramSettingsMenuIcon("
            "iconName),"
        )
    )

    marker = (
        "// MARK: Jerkgram v1.2C "
        "BUILD114_SETTINGS_ICONS1"
    )

    if marker not in text:
        anchor = (
            "private enum "
            "GhostBaseSettingsPage: "
            "Equatable {"
        )

        require(
            anchor in text,
            "Settings page enum missing"
        )

        text = text.replace(
            anchor,
            (
                icon_helper(
                    "jerkgramSettingsMenuIcon"
                )
                + anchor
            ),
            1
        )

    for old in OLD_ICONS:
        require(
            old not in text,
            (
                "old AI icon active: "
                f"{old}"
            )
        )

    write(
        JG_SETTINGS,
        text
    )

    text = read(
        MAIN_ITEMS
    )

    text = ensure_import(
        text,
        "TelegramPresentationData"
    )

    for old, new in (
        OLD_ICONS.items()
    ):
        text = text.replace(
            f'"{old}"',
            f'"{new}"'
        )

    for name in ICON_COLORS:
        pattern = re.compile(
            (
                r"icon:\s*UIImage\("
                r"\s*bundleImageName:\s*"
            )
            + re.escape(
                f'"{name}"'
            )
            + r"\s*\),",
            re.S
        )

        text = pattern.sub(
            (
                "icon: "
                "jerkgramMainSettingsIcon("
                f'"{name}"),'
            ),
            text
        )

    if marker not in text:
        declaration = re.search(
            (
                r"^(?:public |private |"
                r"internal |final |enum |"
                r"struct |class |func |"
                r"let |var )"
            ),
            text,
            re.M
        )

        require(
            declaration is not None,
            "main Settings declaration missing"
        )

        position = (
            declaration.start()
        )

        text = (
            text[:position]
            + icon_helper(
                "jerkgramMainSettingsIcon"
            )
            + text[position:]
        )

    for old in OLD_ICONS:
        require(
            old not in text,
            (
                "old AI main Settings "
                f"icon active: {old}"
            )
        )

    for name in ICON_COLORS:
        require(
            name in text,
            (
                "canonical glyph missing: "
                f"{name}"
            )
        )

    write(
        MAIN_ITEMS,
        text
    )

    print(
        "[Build114] 8 Settings icons: "
        "canonical Telegram renderer"
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

    marker = (
        "// MARK: Jerkgram v1.2C "
        "BUILD114_SIGNER_APPGROUP1"
    )

    helper_name = (
        "jerkgramResolvedApplicationGroupIdentifier"
    )

    resolved_call = (
        "let appGroupName = "
        "jerkgramResolvedApplicationGroupIdentifier("
    )

    fallback = (
        'fallback: "group.\\(baseAppBundleId)"'
    )

    expected_sites = {
        "submodules/TelegramUI/Sources/"
        "AppDelegate.swift": 2,

        "Telegram/SiriIntents/"
        "IntentHandler.swift": 2,

        "Telegram/WidgetKitWidget/"
        "TodayViewController.swift": 1,

        "Telegram/BroadcastUpload/"
        "BroadcastUploadExtension.swift": 1,

        "Telegram/Share/"
        "ShareRootController.swift": 1,

        "Telegram/NotificationContent/"
        "NotificationViewController.swift": 1,

        "Telegram/NotificationService/"
        "Sources/NotificationService.swift": 1,
    }

    total_sites = 0

    for relative in targets:
        text = read(
            ROOT / relative
        )

        require(
            marker in text,
            (
                "signer-neutral AppGroup marker "
                f"missing: {relative}"
            )
        )

        require(
            text.count(
                f"private func {helper_name}("
            ) == 1,
            (
                "signer-neutral AppGroup helper "
                f"count invalid: {relative}"
            )
        )

        actual_sites = text.count(
            resolved_call
        )

        require(
            actual_sites
            == expected_sites[relative],
            (
                "signer-neutral AppGroup call-site "
                f"count invalid: {relative}: "
                f"{actual_sites} != "
                f"{expected_sites[relative]}"
            )
        )

        total_sites += actual_sites

        require(
            fallback in text,
            (
                "dynamic Official AppGroup fallback "
                f"missing: {relative}"
            )
        )

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
        total_sites == 9,
        (
            "unexpected signer-neutral "
            f"AppGroup call-site count: {total_sites}"
        )
    )

    print(
        "[Build114] extension identity "
        "is signer-neutral / resign-dynamic: "
        "7 processes / 9 AppGroup sites"
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
