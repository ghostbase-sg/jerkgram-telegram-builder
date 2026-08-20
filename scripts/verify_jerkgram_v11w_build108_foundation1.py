#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import os
import re
import struct


ROOT = Path(__file__).resolve().parents[1]

SRC = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get(
            "GHOSTBASE_SOURCE_ROOT",
            str(ROOT / "work/swiftgram-src"),
        ),
    )
)

ICON_MASTER_ROOT = (
    ROOT / "assets/JerkGram_Icons"
)

ICON_FILES = (
    ICON_MASTER_ROOT / "files"
)

ICON_ARCHIVE = (
    ICON_MASTER_ROOT / "JerkGram_Icons.zip"
)

APP_DELEGATE = (
    SRC / "submodules/TelegramUI/Sources/AppDelegate.swift"
)

INFO = (
    SRC / "Telegram/Telegram-iOS/Info.plist"
)

INFO_BAZEL = (
    SRC / "Telegram/Telegram-iOS/InfoBazel.plist"
)

BUILD = SRC / "Telegram/BUILD"

OFFICIAL_PRIMARY_ICON = (
    SRC / "Telegram/Telegram-iOS/Telegram.icon"
)

PRIMARY_ICON = (
    SRC
    / "Telegram/Telegram-iOS/"
    "JerkGramSteelReveal.icon"
)

PRIMARY_JSON = (
    PRIMARY_ICON / "icon.json"
)

PRIMARY_PNG = (
    PRIMARY_ICON
    / "Assets/JerkGramSteelReveal.png"
)

MIGRATION_BEGIN = (
    "// JERKGRAM_LEGACY_NAMESPACE_BEGIN"
)

MIGRATION_END = (
    "// JERKGRAM_LEGACY_NAMESPACE_END"
)

SOURCE_EXTENSIONS = {
    ".swift",
    ".m",
    ".mm",
    ".h",
    ".hpp",
    ".c",
    ".cc",
}

EXPECTED = {
    "JerkGramInkReveal.png":
        "5767216fdf8234225619cef3be3e36198437557eb2b5b960887d44ea927d8622",

    "JerkGramInkSolid.png":
        "972e449b046c5163dc197856e7ad9e9b081c06339fbad8191e3a2476361305ec",

    "JerkGramOliveReveal.png":
        "ae40ec84da398a632573cb20e356a6822247448ea0960bb7194470a4d4627e90",

    "JerkGramOliveSolid.png":
        "7bcd6f0a1d907cc5b3808bc67acbd878eaab8ceb45051ed3f99c350bf5eabd2e",

    "JerkGramRustReveal.png":
        "cef86467b91614a4451e9832c0526ceb7f021e8cec953b56c11b876dd5e37364",

    "JerkGramRustSolid.png":
        "624d4f4a17a66ae9d4f1a98e03370e3144b2144d3037f0c2fadba59cceb78d11",

    "JerkGramSteelReveal.png":
        "e1a72196d6ff5a4d86d1653d3c368d0c40c51bc7240218cd3082b2f2f3c61097",

    "JerkGramSteelSolid.png":
        "0c1eea56e5f30db5d69ee1ef1069dbad5bd4fb39180975176f30678c22a96c77",
}


def fail(message):
    raise RuntimeError(
        "[verify Build108] " + message
    )


def require(condition, message):
    if not condition:
        fail(message)


def sha256(path: Path):
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            h.update(chunk)

    return h.hexdigest()


def png_size(path: Path):
    data = path.read_bytes()

    require(
        data[:8] == b"\x89PNG\r\n\x1a\n",
        f"not PNG: {path}",
    )

    require(
        len(data) >= 24
        and data[12:16] == b"IHDR",
        f"invalid PNG: {path}",
    )

    return struct.unpack(
        ">II",
        data[16:24],
    )


# ------------------------------------------------------------
# Canonical icon masters.
# ------------------------------------------------------------

require(
    ICON_ARCHIVE.is_file(),
    "JerkGram_Icons.zip missing",
)

for name, expected_hash in EXPECTED.items():
    path = ICON_FILES / name

    require(
        path.is_file(),
        f"icon MASTER missing: {name}",
    )

    require(
        png_size(path) == (1254, 1254),
        f"icon MASTER size changed: {name}",
    )

    require(
        sha256(path) == expected_hash,
        f"icon MASTER hash changed: {name}",
    )


for owner in (
    APP_DELEGATE,
    INFO,
    INFO_BAZEL,
    BUILD,
    PRIMARY_JSON,
    PRIMARY_PNG,
):
    require(
        owner.is_file(),
        f"missing owner: {owner}",
    )


# ------------------------------------------------------------
# Migration owner.
# ------------------------------------------------------------

app = APP_DELEGATE.read_text(
    encoding="utf-8"
)

for token in (
    MIGRATION_BEGIN,
    MIGRATION_END,
    (
        "// MARK: JerkGram v1.1W "
        "BUILD108_FOUNDATION1"
    ),
    (
        'private static let canonicalPrefix = '
        '"jerkgram."'
    ),
    (
        'lower.hasPrefix("ghostbase.")'
    ),
    (
        'lower.hasPrefix("gb.")'
    ),
    (
        'suiteName: '
        '"group.4a348a9b186b700c.1"'
    ),
    (
        "JerkGramLegacyDefaultsMigration.run()"
    ),
):
    require(
        token in app,
        f"migration token missing: {token}",
    )


# ------------------------------------------------------------
# Remove compatibility region before looking for forbidden
# active legacy key literals.
# ------------------------------------------------------------

def without_migration_region(
    path: Path,
    text: str,
):
    if path != APP_DELEGATE:
        return text

    if (
        MIGRATION_BEGIN not in text
        or MIGRATION_END not in text
    ):
        return text

    before, rest = text.split(
        MIGRATION_BEGIN,
        1,
    )

    _, after = rest.split(
        MIGRATION_END,
        1,
    )

    return before + after


# Anything beginning with any capitalization of
# GhostBase. or GB. is forbidden outside compatibility.
legacy_pattern = re.compile(
    r'"(?:(?i:ghostbase)|(?i:gb))\.'
)

legacy_hits = []
canonical_hits = 0

for path in SRC.rglob("*"):
    if (
        not path.is_file()
        or path.suffix not in SOURCE_EXTENSIONS
    ):
        continue

    try:
        text = path.read_text(
            encoding="utf-8"
        )
    except Exception:
        continue

    text = without_migration_region(
        path,
        text,
    )

    canonical_hits += text.count(
        '"jerkgram.'
    )

    for match in legacy_pattern.finditer(text):
        line_no = (
            text.count(
                "\n",
                0,
                match.start(),
            )
            + 1
        )

        line = text.splitlines()[
            line_no - 1
        ].strip()

        legacy_hits.append(
            f"{path}:{line_no}:{line}"
        )


require(
    not legacy_hits,
    (
        "active legacy branded key namespaces "
        "remain outside compatibility:\n"
        + "\n".join(
            legacy_hits[:100]
        )
    ),
)

require(
    canonical_hits >= 10,
    (
        "unexpectedly few jerkgram.* "
        f"literals: {canonical_hits}"
    ),
)


# ------------------------------------------------------------
# Product name.
# ------------------------------------------------------------

for plist in (
    INFO,
    INFO_BAZEL,
):
    text = plist.read_text(
        encoding="utf-8"
    )

    match = re.search(
        (
            r"<key>CFBundleDisplayName</key>"
            r"\s*<string>([^<]+)</string>"
        ),
        text,
    )

    require(
        match is not None,
        (
            "CFBundleDisplayName missing: "
            f"{plist}"
        ),
    )

    require(
        match.group(1) == "JerkGram",
        (
            "wrong CFBundleDisplayName "
            f"in {plist}: "
            f"{match.group(1)}"
        ),
    )


# Main-app localized names must not override JerkGram.
strings_root = (
    SRC / "Telegram/Telegram-iOS"
)

for path in strings_root.glob(
    "*.lproj/InfoPlist.strings"
):
    try:
        text = path.read_text(
            encoding="utf-8"
        )
    except Exception:
        continue

    match = re.search(
        (
            r'CFBundleDisplayName\s*=\s*'
            r'"([^"]*)"\s*;'
        ),
        text,
    )

    if match is not None:
        require(
            match.group(1) == "JerkGram",
            (
                "localized display name "
                f"still overrides JerkGram: {path}"
            ),
        )


# ------------------------------------------------------------
# Bundle ID / signing identity path must remain unchanged.
# ------------------------------------------------------------

build = BUILD.read_text(
    encoding="utf-8"
)

require(
    (
        'bundle_id = '
        '"{telegram_bundle_id}".format('
    )
    in build,
    (
        "main bundle_id configuration "
        "owner changed"
    ),
)

require(
    (
        "telegram_bundle_id = "
        "telegram_bundle_id"
    )
    in build,
    (
        "telegram_bundle_id passthrough "
        "changed"
    ),
)


# ------------------------------------------------------------
# JerkGram Steel Reveal is the ONE primary JerkGram icon
# registered by Build108.
# ------------------------------------------------------------

require(
    (
        'composer_icon_folders = '
        '["JerkGramSteelReveal"]'
    )
    in build,
    (
        "JerkGramSteelReveal primary "
        "owner missing"
    ),
)

require(
    (
        'composer_icon_folders = ["Telegram"]'
    )
    not in build,
    (
        "Telegram still registered "
        "as primary icon"
    ),
)


require(
    sha256(PRIMARY_PNG)
    == EXPECTED["JerkGramSteelReveal.png"],
    (
        "materialized Steel Reveal "
        "does not match MASTER"
    ),
)

require(
    png_size(PRIMARY_PNG)
    == (1254, 1254),
    (
        "materialized Steel Reveal "
        "dimensions changed"
    ),
)


icon = json.loads(
    PRIMARY_JSON.read_text(
        encoding="utf-8"
    )
)

groups = icon.get("groups")

require(
    isinstance(groups, list)
    and len(groups) == 1,
    "unexpected Icon Composer groups",
)

layers = groups[0].get(
    "layers"
)

require(
    isinstance(layers, list)
    and len(layers) == 1,
    (
        "Build108 primary icon must "
        "contain one artwork layer"
    ),
)

layer = layers[0]

require(
    (
        layer.get("image-name")
        == "JerkGramSteelReveal.png"
    ),
    "wrong primary icon artwork",
)

require(
    (
        layer.get("name")
        == "JerkGramSteelReveal"
    ),
    "wrong primary icon layer name",
)

require(
    layer.get("glass") is False,
    (
        "Composer glass unexpectedly "
        "enabled on finished MASTER"
    ),
)


# Original Telegram Icon Composer source remains intact.
require(
    (
        OFFICIAL_PRIMARY_ICON
        / "Assets/Plane.svg"
    ).is_file(),
    "original Telegram Plane.svg disappeared",
)

require(
    (
        OFFICIAL_PRIMARY_ICON
        / "Assets/Oval.svg"
    ).is_file(),
    "original Telegram Oval.svg disappeared",
)

require(
    (
        OFFICIAL_PRIMARY_ICON
        / "icon.json"
    ).is_file(),
    "original Telegram.icon disappeared",
)


# ------------------------------------------------------------
# Stock Telegram alternates stay registered.
# ------------------------------------------------------------

for stock in (
    "BlackIcon",
    "BlackClassicIcon",
    "BlackFilledIcon",
    "BlueIcon",
    "BlueClassicIcon",
    "BlueFilledIcon",
    "WhiteFilledIcon",
    "New1",
    "New2",
    "Premium",
    "PremiumBlack",
    "PremiumTurbo",
):
    require(
        f'"{stock}"' in build,
        (
            "stock alternate icon "
            f"missing: {stock}"
        ),
    )


# ------------------------------------------------------------
# The seven future JerkGram variants MUST NOT be registered yet.
# They only exist in canonical /assets storage.
# ------------------------------------------------------------

for future in (
    "JerkGramSteelSolid",
    "JerkGramRustReveal",
    "JerkGramRustSolid",
    "JerkGramInkReveal",
    "JerkGramInkSolid",
    "JerkGramOliveReveal",
    "JerkGramOliveSolid",
):
    require(
        future not in build,
        (
            "Build108 unexpectedly "
            f"registered future icon: {future}"
        ),
    )


print(
    "[verify Build108] GREEN: "
    f"{canonical_hits} jerkgram.* literals; "
    "GhostBase/ghostBase/ghostbase/GB "
    "legacy namespaces isolated; "
    "JerkGram display name; "
    "Steel Reveal primary; "
    "7 future icons storage-only; "
    "Bundle ID path unchanged"
)
