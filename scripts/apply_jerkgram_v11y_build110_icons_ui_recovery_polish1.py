#!/usr/bin/env python3

from pathlib import Path
import hashlib
import os
import os
import re
import shutil
import struct
import subprocess


BUILDER = Path(
    os.environ.get(
        "GHOSTBASE_BUILDER_ROOT",
        str(Path(__file__).resolve().parents[1]),
    )
).resolve()

ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        str(Path.cwd()),
    )
).resolve()

ASSETS = BUILDER / "assets/JerkGram_Icons/files"

TELEGRAM_BUILD = ROOT / "Telegram/BUILD"
TELEGRAM_IOS = ROOT / "Telegram/Telegram-iOS"

APP_DELEGATE = (
    ROOT
    / "submodules/TelegramUI/Sources/AppDelegate.swift"
)

THEME_SETTINGS = (
    ROOT
    / "submodules/SettingsUI/Sources/Themes/"
      "ThemeSettingsController.swift"
)

THEME_ICON_ITEM = (
    ROOT
    / "submodules/SettingsUI/Sources/Themes/"
      "ThemeSettingsAppIconItem.swift"
)

ENQUEUE = (
    ROOT
    / "submodules/TelegramCore/Sources/"
      "PendingMessages/EnqueueMessage.swift"
)

JG_SETTINGS = (
    ROOT
    / "submodules/SettingsUI/Sources/GhostBase/"
      "GhostBaseSettingsController.swift"
)

PROFILE_BG = (
    ROOT
    / "submodules/TelegramUI/Components/PeerInfo/"
      "PeerInfoScreen/Sources/"
      "GhostBaseProfileFullscreenBackground.swift"
)

PROFILE_REPORT = (
    ROOT
    / "submodules/TelegramUI/Components/PeerInfo/"
      "PeerInfoScreen/Sources/"
      "GhostBaseProfileReportPaneNode.swift"
)


ICONS = [
    (
        "JerkGramSteelReveal",
        "JerkGramSteelReveal.png",
        "e1a72196d6ff5a4d86d1653d3c368d0c40c51bc7240218cd3082b2f2f3c61097",
    ),
    (
        "JerkGramSteelSolid",
        "JerkGramSteelSolid.png",
        "0c1eea56e5f30db5d69ee1ef1069dbad5bd4fb39180975176f30678c22a96c77",
    ),
    (
        "JerkGramRustReveal",
        "JerkGramRustReveal.png",
        "cef86467b91614a4451e9832c0526ceb7f021e8cec953b56c11b876dd5e37364",
    ),
    (
        "JerkGramRustSolid",
        "JerkGramRustSolid.png",
        "624d4f4a17a66ae9d4f1a98e03370e3144b2144d3037f0c2fadba59cceb78d11",
    ),
    (
        "JerkGramInkReveal",
        "JerkGramInkReveal.png",
        "5767216fdf8234225619cef3be3e36198437557eb2b5b960887d44ea927d8622",
    ),
    (
        "JerkGramInkSolid",
        "JerkGramInkSolid.png",
        "972e449b046c5163dc197856e7ad9e9b081c06339fbad8191e3a2476361305ec",
    ),
    (
        "JerkGramOliveReveal",
        "JerkGramOliveReveal.png",
        "ae40ec84da398a632573cb20e356a6822247448ea0960bb7194470a4d4627e90",
    ),
    (
        "JerkGramOliveSolid",
        "JerkGramOliveSolid.png",
        "7bcd6f0a1d907cc5b3808bc67acbd878eaab8ceb45051ed3f99c350bf5eabd2e",
    ),
]


def require(condition, message):
    if not condition:
        raise RuntimeError(
            "[Build110] " + message
        )


def read(path):
    require(
        path.is_file(),
        f"missing file: {path}",
    )
    return path.read_text(
        encoding="utf-8"
    )


def write(path, text):
    path.write_text(
        text,
        encoding="utf-8",
    )


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def png_size(path):
    data = path.read_bytes()[:24]
    require(
        len(data) >= 24
        and data[:8]
        == b"\x89PNG\r\n\x1a\n"
        and data[12:16] == b"IHDR",
        f"invalid PNG: {path}",
    )
    return struct.unpack(
        ">II",
        data[16:24],
    )


def validate_masters():
    for icon_id, filename, expected_hash in ICONS:
        path = ASSETS / filename

        require(
            path.is_file(),
            f"missing icon master: {path}",
        )

        require(
            sha256(path) == expected_hash,
            f"master hash changed: {filename}",
        )

        require(
            png_size(path) == (1254, 1254),
            f"unexpected master size: {filename}",
        )

    print(
        "[Build110] 8 canonical icon masters OK"
    )


def build_alternate_icons():
    template = (
        TELEGRAM_IOS
        / "BlueIcon.alticon"
    )

    require(
        template.is_dir(),
        "official BlueIcon.alticon template missing",
    )

    template_pngs = sorted(
        template.glob("*.png")
    )

    require(
        len(template_pngs) > 0,
        "BlueIcon.alticon contains no PNG files",
    )

    # Stock Telegram alternate icons use the icon name as the
    # resource basename. rules_apple flattens these PNG resources
    # into the application bundle, so every alternate icon must
    # have unique basenames.
    for path in template_pngs:
        require(
            path.name.startswith("Blue"),
            (
                "unexpected BlueIcon template filename: "
                f"{path.name}"
            ),
        )

    dimensions = {
        path.name: png_size(path)
        for path in template_pngs
    }

    # Keep the macOS release default, while allowing the materialization
    # verifier to provide a compatible image resizer on non-macOS hosts.
    sips = Path(os.environ.get("SIPS_BIN", "/usr/bin/sips"))

    require(
        sips.is_file(),
        "/usr/bin/sips missing on macOS builder",
    )

    # Steel Reveal is already the physical primary icon from
    # Build108. It is represented by alternateIconName == nil
    # and must not be redundantly registered as an alternate.
    primary_alt = (
        TELEGRAM_IOS
        / "JerkGramSteelReveal.alticon"
    )

    if primary_alt.exists():
        shutil.rmtree(primary_alt)

    alternate_icons = [
        entry
        for entry in ICONS
        if entry[0] != "JerkGramSteelReveal"
    ]

    for icon_id, filename, _ in alternate_icons:
        master = ASSETS / filename

        target = (
            TELEGRAM_IOS
            / f"{icon_id}.alticon"
        )

        if target.exists():
            shutil.rmtree(target)

        # Preserve any non-PNG metadata from the official folder.
        shutil.copytree(
            template,
            target,
        )

        # Remove copied BlueIcon PNGs: their duplicate basenames
        # are what caused the first Build110 Bazel failure.
        for copied_png in target.glob("*.png"):
            copied_png.unlink()

        generated = []

        for template_png in template_pngs:
            if template_png.name.startswith("BlueIcon"):
                suffix = template_png.name[
                    len("BlueIcon"):
                ]

                output_name = (
                    icon_id + suffix
                )

            elif template_png.name.startswith("Blue"):
                suffix = template_png.name[
                    len("Blue"):
                ]

                output_name = (
                    icon_id + suffix
                )

            else:
                raise RuntimeError(
                    "[Build110] unexpected alternate "
                    "icon template resource: "
                    f"{template_png.name}"
                )

            target_png = (
                target
                / output_name
            )

            width, height = (
                dimensions[template_png.name]
            )

            subprocess.run(
                [
                    str(sips),
                    "-z",
                    str(height),
                    str(width),
                    str(master),
                    "--out",
                    str(target_png),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            require(
                png_size(target_png)
                == (width, height),
                (
                    "resized icon dimension "
                    f"mismatch: {target_png}"
                ),
            )

            require(
                target_png.name.startswith(icon_id),
                (
                    "alternate icon resource "
                    f"basename mismatch: {target_png.name}"
                ),
            )

            generated.append(
                target_png.name
            )

        require(
            len(generated)
            == len(template_pngs),
            (
                "alternate icon resource "
                f"count mismatch: {icon_id}"
            ),
        )

        require(
            not any(
                name.startswith("BlueIcon")
                for name in generated
            ),
            (
                "BlueIcon resource basename leaked into "
                f"{icon_id}"
            ),
        )

    print(
        "[Build110] 7 alternate .alticon folders "
        "materialized with unique resource basenames; "
        "Steel Reveal remains primary"
    )


def patch_build():
    text = read(TELEGRAM_BUILD)

    require(
        'composer_icon_folders = ["JerkGramSteelReveal"]'
        in text,
        (
            "Build108 Steel Reveal primary "
            "owner missing"
        ),
    )

    start = text.find(
        "alternate_icon_folders = ["
    )
    require(
        start >= 0,
        "alternate_icon_folders owner missing",
    )

    end = text.find(
        "\n]",
        start,
    )
    require(
        end >= 0,
        "alternate_icon_folders closing bracket missing",
    )

    block = text[start:end]

    missing = [
        icon_id
        for icon_id, _, _ in ICONS
        if icon_id != "JerkGramSteelReveal"
        and f'"{icon_id}"' not in block
    ]

    if missing:
        line_end = text.find(
            "\n",
            start,
        )
        require(
            line_end >= 0,
            "alternate icon list first line missing",
        )

        addition = "".join(
            f'    "{icon_id}",\n'
            for icon_id in missing
        )

        text = (
            text[:line_end + 1]
            + addition
            + text[line_end + 1:]
        )

        write(
            TELEGRAM_BUILD,
            text,
        )

    print(
        "[Build110] Telegram BUILD alternate "
        "icon registration OK"
    )


def patch_app_delegate():
    text = read(APP_DELEGATE)

    marker = (
        "// MARK: JerkGram v1.1Y "
        "BUILD110_APP_ICONS1"
    )

    if marker not in text:
        pattern = re.compile(
            r'(?m)^(?P<i>\s*)'
            r'PresentationAppIcon'
            r'\(name: "BlueIcon", '
            r'imageName: "BlueIcon", '
            r'isDefault: '
            r'buildConfig\.isAppStoreBuild\),$'
        )

        match = pattern.search(text)

        require(
            match is not None,
            (
                "stock BlueIcon default "
                "anchor missing"
            ),
        )

        indent = match.group("i")

        rows = [
            (
                "JerkGramSteelReveal",
                True,
            ),
            (
                "JerkGramSteelSolid",
                False,
            ),
            (
                "JerkGramRustReveal",
                False,
            ),
            (
                "JerkGramRustSolid",
                False,
            ),
            (
                "JerkGramInkReveal",
                False,
            ),
            (
                "JerkGramInkSolid",
                False,
            ),
            (
                "JerkGramOliveReveal",
                False,
            ),
            (
                "JerkGramOliveSolid",
                False,
            ),
        ]

        replacement = (
            indent
            + marker
            + "\n"
        )

        for name, is_default in rows:
            default_part = (
                ", isDefault: true"
                if is_default
                else ""
            )

            replacement += (
                indent
                + "PresentationAppIcon("
                + f'name: "{name}", '
                + f'imageName: "{name}"'
                + default_part
                + "),\n"
            )

        replacement += (
            indent
            + 'PresentationAppIcon('
              'name: "BlueIcon", '
              'imageName: "BlueIcon"),'
        )

        text = (
            text[:match.start()]
            + replacement
            + text[match.end():]
        )

        write(
            APP_DELEGATE,
            text,
        )

    text = read(APP_DELEGATE)

    require(
        (
            'PresentationAppIcon('
            'name: "JerkGramSteelReveal", '
            'imageName: "JerkGramSteelReveal", '
            'isDefault: true)'
        )
        in text,
        "Steel Reveal logical default missing",
    )

    require(
        (
            'PresentationAppIcon('
            'name: "BlueIcon", '
            'imageName: "BlueIcon", '
            'isDefault:'
        )
        not in text,
        "BlueIcon is still logical default",
    )

    print(
        "[Build110] AppDelegate logical default "
        "= JerkGram Steel Reveal"
    )


def patch_icon_stable_ids(text):
    marker = (
        "// MARK: JerkGram v1.1Y "
        "BUILD110_ICON_STABLE_IDS1"
    )

    if marker in text:
        return text

    stable_match = re.search(
        r"(?m)^\s*var stableId:\s*Int32\s*\{",
        text,
    )

    require(
        stable_match is not None,
        "ThemeSettings stableId owner missing",
    )

    possible_ends = []

    for token in (
        "\n    static func ==",
        "\n    func item(",
        "\n    var section:",
    ):
        value = text.find(
            token,
            stable_match.end(),
        )
        if value >= 0:
            possible_ends.append(value)

    require(
        possible_ends,
        "ThemeSettings stableId end missing",
    )

    end = min(possible_ends)

    region = text[
        stable_match.start():end
    ]

    header_pattern = re.compile(
        r"(?m)^"
        r"(?P<i>\s*)case \.iconHeader:"
        r"\s*\n"
        r"(?P<r>\s*)return "
        r"(?P<v>[^\n]+)$"
    )

    item_pattern = re.compile(
        r"(?m)^"
        r"(?P<i>\s*)case \.iconItem:"
        r"\s*\n"
        r"(?P<r>\s*)return "
        r"(?P<v>[^\n]+)$"
    )

    hm = header_pattern.search(region)
    im = item_pattern.search(region)

    require(
        hm is not None,
        "iconHeader stableId branch missing",
    )
    require(
        im is not None,
        "iconItem stableId branch missing",
    )

    header_replacement = (
        hm.group("i")
        + marker
        + "\n"
        + hm.group("i")
        + "case let .iconHeader(_, text):\n"
        + hm.group("r")
        + 'return text == "JERKGRAM APP ICON" '
          '? 9100 : '
        + hm.group("v").strip()
    )

    region = (
        region[:hm.start()]
        + header_replacement
        + region[hm.end():]
    )

    im = item_pattern.search(region)
    require(
        im is not None,
        "iconItem stableId branch lost",
    )

    item_replacement = (
        im.group("i")
        + "case let .iconItem("
          "_, _, icons, _, _):\n"
        + im.group("r")
        + "return "
          "icons.first?.name.hasPrefix("
          '"JerkGram") == true '
          "? 9101 : "
        + im.group("v").strip()
    )

    region = (
        region[:im.start()]
        + item_replacement
        + region[im.end():]
    )

    return (
        text[:stable_match.start()]
        + region
        + text[end:]
    )


def patch_theme_settings():
    text = read(THEME_SETTINGS)

    text = patch_icon_stable_ids(
        text
    )

    text = text.replace(
        (
            'currentAppIconName.set('
            'currentAppIcon?.name ?? "Blue")'
        ),
        (
            'currentAppIconName.set('
            'currentAppIcon?.name '
            '?? "JerkGramSteelReveal")'
        ),
        1,
    )

    marker = (
        "// MARK: JerkGram v1.1Y "
        "BUILD110_ICON_SECTIONS1"
    )

    if marker not in text:
        old = '''    if !availableAppIcons.isEmpty {
        entries.append(.iconHeader(presentationData.theme, strings.Appearance_AppIcon.uppercased()))
        entries.append(.iconItem(presentationData.theme, presentationData.strings, availableAppIcons, isPremium, currentAppIconName))
    }
'''

        require(
            old in text,
            (
                "official Appearance icon "
                "entries block missing"
            ),
        )

        new = '''    // MARK: JerkGram v1.1Y BUILD110_ICON_SECTIONS1
    let jerkGramAppIcons = availableAppIcons.filter {
        $0.name.hasPrefix("JerkGram")
    }
    let telegramAppIcons = availableAppIcons.filter {
        !$0.name.hasPrefix("JerkGram")
    }

    if !jerkGramAppIcons.isEmpty {
        entries.append(.iconHeader(
            presentationData.theme,
            "JERKGRAM APP ICON"
        ))
        entries.append(.iconItem(
            presentationData.theme,
            presentationData.strings,
            jerkGramAppIcons,
            isPremium,
            currentAppIconName
        ))
    }

    if !telegramAppIcons.isEmpty {
        entries.append(.iconHeader(
            presentationData.theme,
            strings.Appearance_AppIcon.uppercased()
        ))
        entries.append(.iconItem(
            presentationData.theme,
            presentationData.strings,
            telegramAppIcons,
            isPremium,
            currentAppIconName
        ))
    }
'''

        text = text.replace(
            old,
            new,
            1,
        )

    write(
        THEME_SETTINGS,
        text,
    )

    print(
        "[Build110] JERKGRAM APP ICON section "
        "installed above stock APP ICON"
    )


def patch_icon_labels():
    text = read(THEME_ICON_ITEM)

    marker = (
        "// MARK: JerkGram v1.1Y "
        "BUILD110_ICON_LABELS1"
    )

    if marker in text:
        return

    switch_pos = text.find(
        "switch icon.name {"
    )

    require(
        switch_pos >= 0,
        "app-icon label switch missing",
    )

    blue_match = re.search(
        r'(?m)^(?P<i>\s*)case "BlueIcon":',
        text[switch_pos:],
    )

    require(
        blue_match is not None,
        "BlueIcon label case missing",
    )

    absolute = (
        switch_pos
        + blue_match.start()
    )

    indent = blue_match.group("i")

    addition = (
        indent
        + marker
        + "\n"
        + indent
        + 'case "JerkGramSteelReveal":\n'
        + indent
        + '    name = "Steel"\n'
        + indent
        + 'case "JerkGramSteelSolid":\n'
        + indent
        + '    name = "Steel Solid"\n'
        + indent
        + 'case "JerkGramRustReveal":\n'
        + indent
        + '    name = "Rust"\n'
        + indent
        + 'case "JerkGramRustSolid":\n'
        + indent
        + '    name = "Rust Solid"\n'
        + indent
        + 'case "JerkGramInkReveal":\n'
        + indent
        + '    name = "Ink"\n'
        + indent
        + 'case "JerkGramInkSolid":\n'
        + indent
        + '    name = "Ink Solid"\n'
        + indent
        + 'case "JerkGramOliveReveal":\n'
        + indent
        + '    name = "Olive"\n'
        + indent
        + 'case "JerkGramOliveSolid":\n'
        + indent
        + '    name = "Olive Solid"\n'
    )

    text = (
        text[:absolute]
        + addition
        + text[absolute:]
    )

    write(
        THEME_ICON_ITEM,
        text,
    )

    print(
        "[Build110] JerkGram icon labels installed"
    )


def patch_deleted_reply_author_link():
    text = read(ENQUEUE)

    marker = (
        "// MARK: JerkGram v1.1Y "
        "BUILD110_RECOVERED_AUTHOR_NO_WEB_PREVIEW1"
    )

    if marker in text:
        return

    start = text.find(
        "private func "
        "ghostBaseBuildPortableDeletedReply("
    )

    require(
        start >= 0,
        "deleted-reply materializer missing",
    )

    end = text.find(
        "\nprivate func ",
        start + 32,
    )

    require(
        end >= 0,
        (
            "deleted-reply materializer "
            "end missing"
        ),
    )

    block = text[start:end]

    build106_marker = (
        "// MARK: GhostBase v1.1U "
        "BUILD106_PORTABLE_AUTHOR1"
    )

    require(
        build106_marker in block,
        (
            "Build106 portable-author "
            "owner missing"
        ),
    )

    replacements = 0

    mappings = (
        (
            "https://t.me/",
            "tg://resolve?domain=",
        ),
        (
            "http://t.me/",
            "tg://resolve?domain=",
        ),
        (
            "https://telegram.me/",
            "tg://resolve?domain=",
        ),
    )

    for old, new in mappings:
        count = block.count(old)

        if count:
            block = block.replace(
                old,
                new,
            )
            replacements += count

    require(
        replacements > 0
        or "tg://resolve?domain="
        in block,
        (
            "portable author contains no "
            "recognized Telegram HTTP URL; "
            "refusing broad preview patch"
        ),
    )

    block = block.replace(
        build106_marker,
        (
            marker
            + "\n        "
            + build106_marker
        ),
        1,
    )

    text = (
        text[:start]
        + block
        + text[end:]
    )

    write(
        ENQUEUE,
        text,
    )

    print(
        "[Build110] recovered-author HTTP link "
        "-> internal tg://resolve link; "
        "normal user URL previews untouched"
    )


def patch_long_toggle_titles():
    text = read(JG_SETTINGS)

    marker = (
        "// MARK: JerkGram v1.1Y "
        "BUILD110_SHORT_TOGGLE_TITLES1"
    )

    replacements = {
        (
            "Показывать секунды "
            "в сообщениях"
        ): "Секунды в сообщениях",

        (
            "Показывать удалённые "
            "сообщения"
        ): "Удалённые сообщения",

        (
            "Сохранять удалённые "
            "сообщения"
        ): "Сохранять удалённые",

        (
            "Показывать историю "
            "изменений"
        ): "История изменений",

        (
            "Сохранение одноразовых "
            "медиа"
        ): "Одноразовые медиа",

        (
            "Allow One-Time "
            "Screen Recording"
        ): "One-Time Recording",

        (
            "Enable Protected "
            "Content Bypass"
        ): "Protected Content Bypass",
    }

    changed = 0

    for old, new in replacements.items():
        count = text.count(
            f'"{old}"'
        )

        if count:
            text = text.replace(
                f'"{old}"',
                f'"{new}"',
            )
            changed += count

    require(
        changed > 0
        or marker in text,
        (
            "none of the known long toggle "
            "titles were found"
        ),
    )

    if marker not in text:
        anchor = (
            "private enum "
            "GhostBaseSettingsEntry"
        )

        pos = text.find(anchor)

        require(
            pos >= 0,
            "settings entry owner missing",
        )

        line_start = text.rfind(
            "\n",
            0,
            pos,
        ) + 1

        text = (
            text[:line_start]
            + marker
            + "\n"
            + text[line_start:]
        )

    write(
        JG_SETTINGS,
        text,
    )

    print(
        "[Build110] long toggle titles shortened "
        "so text cannot run under switches"
    )


def patch_profile_readability():
    text = read(PROFILE_BG)

    marker = (
        "// MARK: JerkGram v1.1Y "
        "BUILD110_PROFILE_READABILITY1"
    )

    if marker not in text:
        pattern = re.compile(
            r"    private func applyTint\("
            r"[\s\S]*?"
            r"\n    \}\n\n"
            r"    private func "
            r"wallpaperEntrySignal\("
        )

        match = pattern.search(text)

        require(
            match is not None,
            "profile applyTint owner missing",
        )

        replacement = '''    private func applyTint(
        _ color: UIColor,
        fallback: UIColor,
        isDark: Bool,
        reduced: Bool
    ) {
        // MARK: JerkGram v1.1Y BUILD110_PROFILE_READABILITY1
        //
        // The fullscreen background stays visible, but the single existing
        // tint layer now also provides adaptive contrast. This is deliberately
        // one scene-wide layer, not per-cell blur/glass.
        let sourceColor = color
        let luminance = Self.colorLuminance(sourceColor)

        let contrastColor: UIColor
        let contrastAlpha: CGFloat

        if isDark {
            let brightBoost = max(
                0.0,
                min(
                    1.0,
                    (luminance - 0.32) / 0.68
                )
            )

            contrastColor = sourceColor.mixedWith(
                UIColor.black,
                alpha: 0.72
            )

            contrastAlpha = min(
                reduced ? 0.24 : 0.32,
                (reduced ? 0.10 : 0.14)
                    + brightBoost
                    * (reduced ? 0.12 : 0.17)
            )
        } else {
            let darkBoost = max(
                0.0,
                min(
                    1.0,
                    (0.48 - luminance) / 0.48
                )
            )

            contrastColor = sourceColor.mixedWith(
                UIColor.white,
                alpha: 0.70
            )

            contrastAlpha = min(
                reduced ? 0.17 : 0.23,
                (reduced ? 0.055 : 0.075)
                    + darkBoost
                    * (reduced ? 0.10 : 0.14)
            )
        }

        if self.settings.tintEnabled {
            self.tintView.backgroundColor =
                contrastColor.withAlphaComponent(
                    contrastAlpha
                )
        } else {
            self.tintView.backgroundColor =
                (isDark ? UIColor.black : UIColor.white)
                    .withAlphaComponent(
                        contrastAlpha
                    )
        }
    }

    private func wallpaperEntrySignal('''

        text = (
            text[:match.start()]
            + replacement
            + text[match.end():]
        )

        write(
            PROFILE_BG,
            text,
        )

    report = read(PROFILE_REPORT)

    report_marker = (
        "// MARK: JerkGram v1.1Y "
        "BUILD110_REPORT_CONTRAST1"
    )

    if report_marker not in report:
        old = '''        let isDark = presentationData.theme.overallDarkAppearance
        self.backgroundColor = UIColor(
            white: isDark ? 1.0 : 0.0,
            alpha: isDark ? 0.075 : 0.035
        )
'''

        require(
            old in report,
            "profile report-card background owner missing",
        )

        new = '''        // MARK: JerkGram v1.1Y BUILD110_REPORT_CONTRAST1
        let isDark = presentationData.theme.overallDarkAppearance
        self.backgroundColor = UIColor(
            white: isDark ? 0.0 : 1.0,
            alpha: isDark ? 0.26 : 0.18
        )
'''

        report = report.replace(
            old,
            new,
            1,
        )

        write(
            PROFILE_REPORT,
            report,
        )

    print(
        "[Build110] adaptive profile readability "
        "+ report-card contrast installed"
    )


def main():
    validate_masters()

    build_alternate_icons()
    patch_build()
    patch_app_delegate()

    patch_theme_settings()
    patch_icon_labels()

    patch_deleted_reply_author_link()
    patch_long_toggle_titles()

    patch_profile_readability()

    print(
        "[Build110] GREEN: "
        "icons + selector + recovered-author "
        "preview fix + settings readability "
        "+ profile contrast applied"
    )


if __name__ == "__main__":
    main()
