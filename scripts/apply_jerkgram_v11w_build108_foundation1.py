#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import os
import re
import shutil
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

ICON_MASTER_ROOT = ROOT / "assets/JerkGram_Icons"
ICON_FILES = ICON_MASTER_ROOT / "files"
ICON_ARCHIVE = ICON_MASTER_ROOT / "JerkGram_Icons.zip"

STEEL_MASTER = ICON_FILES / "JerkGramSteelReveal.png"

INFO = SRC / "Telegram/Telegram-iOS/Info.plist"
INFO_BAZEL = SRC / "Telegram/Telegram-iOS/InfoBazel.plist"
BUILD = SRC / "Telegram/BUILD"

APP_DELEGATE = (
    SRC / "submodules/TelegramUI/Sources/AppDelegate.swift"
)

OFFICIAL_PRIMARY_ICON = (
    SRC / "Telegram/Telegram-iOS/Telegram.icon"
)

JERKGRAM_PRIMARY_ICON = (
    SRC / "Telegram/Telegram-iOS/JerkGramSteelReveal.icon"
)

JERKGRAM_PRIMARY_ASSETS = (
    JERKGRAM_PRIMARY_ICON / "Assets"
)

JERKGRAM_PRIMARY_JSON = (
    JERKGRAM_PRIMARY_ICON / "icon.json"
)

JERKGRAM_PRIMARY_PNG = (
    JERKGRAM_PRIMARY_ASSETS
    / "JerkGramSteelReveal.png"
)

APP_GROUP = "group.4a348a9b186b700c.1"

MIGRATION_BEGIN = (
    "// JERKGRAM_LEGACY_NAMESPACE_BEGIN"
)

MIGRATION_END = (
    "// JERKGRAM_LEGACY_NAMESPACE_END"
)

BUILD_MARKER = (
    "// MARK: JerkGram v1.1W "
    "BUILD108_FOUNDATION1"
)

EXPECTED_STEEL_SHA256 = (
    "e1a72196d6ff5a4d86d1653d3c368d0"
    "c40c51bc7240218cd3082b2f2f3c61097"
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


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
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


def validate_icon_masters():
    expected = {
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
            EXPECTED_STEEL_SHA256,

        "JerkGramSteelSolid.png":
            "0c1eea56e5f30db5d69ee1ef1069dbad5bd4fb39180975176f30678c22a96c77",
    }

    require(
        ICON_ARCHIVE.is_file(),
        f"MASTER icon archive missing: {ICON_ARCHIVE}",
    )

    for name, expected_hash in expected.items():
        path = ICON_FILES / name

        require(
            path.is_file(),
            f"MASTER icon missing: {path}",
        )

        require(
            png_size(path) == (1254, 1254),
            f"unexpected MASTER size: {path}",
        )

        require(
            sha256(path) == expected_hash,
            f"MASTER hash mismatch: {path}",
        )

    print(
        "[Build108] all 8 canonical JerkGram "
        "icon masters OK"
    )


def rewrite_legacy_namespace_fragment(text: str):
    total = 0

    ghost_pattern = re.compile(
        r'"(?i:ghostbase)\.'
    )

    text, count = ghost_pattern.subn(
        '"jerkgram.',
        text,
    )
    total += count

    gb_pattern = re.compile(
        r'"(?i:gb)\.'
    )

    text, count = gb_pattern.subn(
        '"jerkgram.',
        text,
    )
    total += count

    return text, total


def rewrite_file_preserving_migration(path: Path):
    try:
        text = path.read_text(
            encoding="utf-8"
        )
    except Exception:
        return 0, 0

    original = text

    replacement_count = 0
    title_count = 0

    if (
        MIGRATION_BEGIN in text
        and MIGRATION_END in text
    ):
        before, rest = text.split(
            MIGRATION_BEGIN,
            1,
        )

        protected, after = rest.split(
            MIGRATION_END,
            1,
        )

        before, count1 = (
            rewrite_legacy_namespace_fragment(
                before
            )
        )

        after, count2 = (
            rewrite_legacy_namespace_fragment(
                after
            )
        )

        replacement_count += count1 + count2

        title_count += before.count('"GhostBase"')
        title_count += after.count('"GhostBase"')

        before = before.replace(
            '"GhostBase"',
            '"JerkGram"',
        )

        after = after.replace(
            '"GhostBase"',
            '"JerkGram"',
        )

        text = (
            before
            + MIGRATION_BEGIN
            + protected
            + MIGRATION_END
            + after
        )

    else:
        text, replacement_count = (
            rewrite_legacy_namespace_fragment(
                text
            )
        )

        title_count = text.count(
            '"GhostBase"'
        )

        text = text.replace(
            '"GhostBase"',
            '"JerkGram"',
        )

    if text != original:
        path.write_text(
            text,
            encoding="utf-8",
        )

    return replacement_count, title_count


def rewrite_active_namespaces():
    files_changed = 0
    key_replacements = 0
    title_replacements = 0

    for path in SRC.rglob("*"):
        if (
            not path.is_file()
            or path.suffix not in SOURCE_EXTENSIONS
        ):
            continue

        try:
            before = path.read_bytes()
        except Exception:
            continue

        keys, titles = (
            rewrite_file_preserving_migration(
                path
            )
        )

        try:
            after = path.read_bytes()
        except Exception:
            continue

        if before != after:
            files_changed += 1

        key_replacements += keys
        title_replacements += titles

    require(
        key_replacements > 0,
        (
            "no active legacy branded "
            "key namespaces were found"
        ),
    )

    print(
        "[Build108] legacy key namespaces -> "
        f"jerkgram.*: {key_replacements}"
    )

    print(
        "[Build108] exact visible GhostBase "
        f"titles -> JerkGram: {title_replacements}"
    )

    print(
        "[Build108] changed active source files: "
        f"{files_changed}"
    )


def install_legacy_defaults_migration():
    text = APP_DELEGATE.read_text(
        encoding="utf-8"
    )

    if (
        MIGRATION_BEGIN in text
        and MIGRATION_END in text
    ):
        require(
            "JerkGramLegacyDefaultsMigration.run()"
            in text,
            (
                "migration block exists but "
                "startup call is missing"
            ),
        )

        print(
            "[Build108] legacy defaults migration "
            "already installed"
        )
        return

    class_match = re.search(
        r"(?m)^.*\bclass\s+AppDelegate\b.*$",
        text,
    )

    require(
        class_match is not None,
        "AppDelegate class owner not found",
    )

    helper = f'''{MIGRATION_BEGIN}
{BUILD_MARKER}
//
// Compatibility bridge for every historical branded
// JerkGram/GhostBase defaults namespace.
//
// Build108+ canonical destination is always:
//
//     jerkgram.<suffix>
//
// Examples:
//
//     GhostBase.Profile.Enabled
//     ghostBase.Profile.Enabled
//     ghostbase.Profile.Enabled
//     GB.Profile.Enabled
//
// all become:
//
//     jerkgram.Profile.Enabled
//
// Existing canonical values always win.
// Legacy values are copied, never deleted.
//
private enum JerkGramLegacyDefaultsMigration {{
    private static let canonicalPrefix = "jerkgram."

    private static func legacyPrefixLength(
        _ key: String
    ) -> Int? {{
        let lower = key.lowercased()

        if lower.hasPrefix("ghostbase.") {{
            return "ghostbase.".count
        }}

        if lower.hasPrefix("gb.") {{
            return "gb.".count
        }}

        return nil
    }}

    private static func migrate(
        _ defaults: UserDefaults
    ) {{
        let values = defaults.dictionaryRepresentation()

        let orderedKeys = values.keys.sorted {{ lhs, rhs in
            let lhsLower = lhs.lowercased()
            let rhsLower = rhs.lowercased()

            let lhsRank =
                lhsLower.hasPrefix("ghostbase.") ? 0 : 1

            let rhsRank =
                rhsLower.hasPrefix("ghostbase.") ? 0 : 1

            if lhsRank != rhsRank {{
                return lhsRank < rhsRank
            }}

            return lhs < rhs
        }}

        for legacyKey in orderedKeys {{
            guard
                let prefixLength =
                    self.legacyPrefixLength(legacyKey),
                let value = values[legacyKey]
            else {{
                continue
            }}

            let suffix = String(
                legacyKey.dropFirst(prefixLength)
            )

            let canonicalKey =
                self.canonicalPrefix + suffix

            if defaults.object(
                forKey: canonicalKey
            ) == nil {{
                defaults.set(
                    value,
                    forKey: canonicalKey
                )
            }}
        }}
    }}

    static func run() {{
        self.migrate(UserDefaults.standard)

        if let sharedDefaults = UserDefaults(
            suiteName: "{APP_GROUP}"
        ) {{
            self.migrate(sharedDefaults)
        }}
    }}
}}
{MIGRATION_END}

'''

    text = (
        text[:class_match.start()]
        + helper
        + text[class_match.start():]
    )

    launch_token = (
        "didFinishLaunchingWithOptions"
    )

    launch_index = text.find(
        launch_token
    )

    require(
        launch_index >= 0,
        (
            "AppDelegate "
            "didFinishLaunchingWithOptions "
            "owner not found"
        ),
    )

    function_index = text.rfind(
        "func application",
        0,
        launch_index,
    )

    require(
        function_index >= 0,
        (
            "AppDelegate launch application "
            "function not found"
        ),
    )

    brace_index = text.find(
        "{",
        launch_index,
    )

    require(
        brace_index >= 0,
        "launch function opening brace missing",
    )

    startup_call = (
        "\n        "
        "JerkGramLegacyDefaultsMigration.run()"
    )

    text = (
        text[:brace_index + 1]
        + startup_call
        + text[brace_index + 1:]
    )

    APP_DELEGATE.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "[Build108] multi-prefix legacy "
        "defaults migration installed"
    )


def replace_display_name(path: Path):
    text = path.read_text(
        encoding="utf-8"
    )

    pattern = re.compile(
        r"(<key>CFBundleDisplayName</key>\s*)"
        r"<string>[^<]*</string>"
    )

    new_text, count = pattern.subn(
        r"\1<string>JerkGram</string>",
        text,
        count=1,
    )

    require(
        count == 1,
        (
            "CFBundleDisplayName owner "
            f"missing: {path}"
        ),
    )

    path.write_text(
        new_text,
        encoding="utf-8",
    )


def patch_localized_display_names():
    root = (
        SRC / "Telegram/Telegram-iOS"
    )

    changed = 0

    for path in root.glob(
        "*.lproj/InfoPlist.strings"
    ):
        try:
            text = path.read_text(
                encoding="utf-8"
            )
        except Exception:
            continue

        original = text

        text = re.sub(
            (
                r'CFBundleDisplayName\s*=\s*'
                r'"[^"]*"\s*;'
            ),
            (
                'CFBundleDisplayName = '
                '"JerkGram";'
            ),
            text,
        )

        if text != original:
            path.write_text(
                text,
                encoding="utf-8",
            )
            changed += 1

    print(
        "[Build108] localized display-name "
        f"files changed: {changed}"
    )


def create_primary_icon():
    official_json_path = (
        OFFICIAL_PRIMARY_ICON / "icon.json"
    )

    require(
        official_json_path.is_file(),
        (
            "official Telegram.icon owner "
            "missing"
        ),
    )

    if JERKGRAM_PRIMARY_ICON.exists():
        shutil.rmtree(
            JERKGRAM_PRIMARY_ICON
        )

    JERKGRAM_PRIMARY_ASSETS.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        STEEL_MASTER,
        JERKGRAM_PRIMARY_PNG,
    )

    official = json.loads(
        official_json_path.read_text(
            encoding="utf-8"
        )
    )

    require(
        isinstance(
            official.get("groups"),
            list,
        )
        and len(official["groups"]) >= 1,
        "official Icon Composer schema invalid",
    )

    group = dict(
        official["groups"][0]
    )

    group.pop(
        "blur-material",
        None,
    )

    group["layers"] = [
        {
            "blend-mode-specializations": [
                {
                    "value": "normal"
                },
                {
                    "appearance": "dark",
                    "value": "normal"
                }
            ],
            "glass": False,
            "image-name":
                "JerkGramSteelReveal.png",
            "name":
                "JerkGramSteelReveal",
            "position-specializations": [
                {
                    "idiom": "watchOS",
                    "value": {
                        "scale": 1,
                        "translation-in-points": [
                            0,
                            0
                        ]
                    }
                }
            ]
        }
    ]

    group["shadow"] = {
        "kind": "layer-color",
        "opacity": 0,
    }

    group["specular"] = False

    group["translucency"] = {
        "enabled": False,
        "value": 1,
    }

    icon = {
        "fill": official.get(
            "fill",
            "system-light",
        ),
        "groups": [group],
        "supported-platforms": (
            official.get(
                "supported-platforms",
                {
                    "circles": ["watchOS"],
                    "squares": "shared",
                },
            )
        ),
    }

    JERKGRAM_PRIMARY_JSON.write_text(
        json.dumps(
            icon,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    require(
        sha256(JERKGRAM_PRIMARY_PNG)
        == EXPECTED_STEEL_SHA256,
        "materialized Steel Reveal changed",
    )

    print(
        "[Build108] "
        "JerkGramSteelReveal.icon created"
    )


def switch_primary_icon_owner():
    text = BUILD.read_text(
        encoding="utf-8"
    )

    old = (
        'composer_icon_folders = ["Telegram"]'
    )

    new = (
        'composer_icon_folders = '
        '["JerkGramSteelReveal"]'
    )

    if new in text:
        print(
            "[Build108] primary icon owner "
            "already JerkGramSteelReveal"
        )
        return

    require(
        old in text,
        (
            "official composer_icon_folders "
            "anchor missing"
        ),
    )

    BUILD.write_text(
        text.replace(
            old,
            new,
            1,
        ),
        encoding="utf-8",
    )

    print(
        "[Build108] primary icon owner -> "
        "JerkGramSteelReveal"
    )


def main():
    for owner in (
        INFO,
        INFO_BAZEL,
        BUILD,
        APP_DELEGATE,
    ):
        require(
            owner.is_file(),
            f"source owner missing: {owner}",
        )

    validate_icon_masters()
    rewrite_active_namespaces()
    install_legacy_defaults_migration()
    replace_display_name(INFO)
    replace_display_name(INFO_BAZEL)
    patch_localized_display_names()

    print(
        "[Build108] app display name -> JerkGram"
    )

    create_primary_icon()
    switch_primary_icon_owner()

    print(
        "[Build108] JERKGRAM_FOUNDATION1 applied"
    )


if __name__ == "__main__":
    main()
