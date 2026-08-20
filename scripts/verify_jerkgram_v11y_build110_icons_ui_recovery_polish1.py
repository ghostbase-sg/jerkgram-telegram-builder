#!/usr/bin/env python3

from pathlib import Path
import os
import re
import struct


ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        "/root/gb_builder/work/swiftgram-src",
    )
).resolve()

IOS = (
    ROOT
    / "Telegram/Telegram-iOS"
)

BUILD = (
    ROOT
    / "Telegram/BUILD"
)

APP = (
    ROOT
    / "submodules/TelegramUI/Sources/AppDelegate.swift"
)

THEME = (
    ROOT
    / "submodules/SettingsUI/Sources/Themes/"
      "ThemeSettingsController.swift"
)

ICON_ITEM = (
    ROOT
    / "submodules/SettingsUI/Sources/Themes/"
      "ThemeSettingsAppIconItem.swift"
)

ENQUEUE = (
    ROOT
    / "submodules/TelegramCore/Sources/"
      "PendingMessages/EnqueueMessage.swift"
)

SETTINGS = (
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


ICON_IDS = [
    "JerkGramSteelReveal",
    "JerkGramSteelSolid",
    "JerkGramRustReveal",
    "JerkGramRustSolid",
    "JerkGramInkReveal",
    "JerkGramInkSolid",
    "JerkGramOliveReveal",
    "JerkGramOliveSolid",
]


def require(condition, message):
    if not condition:
        raise RuntimeError(
            "[verify Build110] " + message
        )


def read(path):
    require(
        path.is_file(),
        f"missing file: {path}",
    )
    return path.read_text(
        encoding="utf-8"
    )


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


build = read(BUILD)
app = read(APP)
theme = read(THEME)
icon_item = read(ICON_ITEM)
enqueue = read(ENQUEUE)
settings = read(SETTINGS)
profile_bg = read(PROFILE_BG)
profile_report = read(PROFILE_REPORT)


require(
    'composer_icon_folders = ["JerkGramSteelReveal"]'
    in build,
    "Steel Reveal physical primary lost",
)

for icon_id in ICON_IDS:
    require(
        f'"{icon_id}"' in build,
        f"{icon_id} absent from alternate_icon_folders",
    )

    folder = (
        IOS
        / f"{icon_id}.alticon"
    )

    require(
        folder.is_dir(),
        f"{icon_id}.alticon missing",
    )

    pngs = sorted(
        folder.glob("*.png")
    )

    require(
        len(pngs) > 0,
        f"{icon_id}.alticon has no PNGs",
    )

    for png in pngs:
        width, height = png_size(png)

        require(
            width > 0 and height > 0,
            f"bad dimensions: {png}",
        )


require(
    (
        'PresentationAppIcon('
        'name: "JerkGramSteelReveal", '
        'imageName: "JerkGramSteelReveal", '
        'isDefault: true)'
    )
    in app,
    "Steel Reveal logical default missing",
)

require(
    (
        'PresentationAppIcon('
        'name: "BlueIcon", '
        'imageName: "BlueIcon", '
        'isDefault:'
    )
    not in app,
    "BlueIcon still marked default",
)

for icon_id in ICON_IDS:
    require(
        (
            f'name: "{icon_id}", '
            f'imageName: "{icon_id}"'
        )
        in app,
        f"PresentationAppIcon missing: {icon_id}",
    )


require(
    "JERKGRAM APP ICON"
    in theme,
    "JERKGRAM APP ICON header missing",
)

require(
    (
        'availableAppIcons.filter {\n'
        '        $0.name.hasPrefix("JerkGram")'
    )
    in theme,
    "JerkGram icon split missing",
)

require(
    (
        'availableAppIcons.filter {\n'
        '        !$0.name.hasPrefix("JerkGram")'
    )
    in theme,
    "stock Telegram icon split missing",
)

require(
    (
        'currentAppIcon?.name '
        '?? "JerkGramSteelReveal"'
    )
    in theme,
    "nil/default UI fallback is not Steel Reveal",
)

require(
    "BUILD110_ICON_STABLE_IDS1"
    in theme,
    "separate icon-grid stable IDs missing",
)

require(
    "? 9100 :"
    in theme
    and "? 9101 :"
    in theme,
    "JerkGram icon-grid stable IDs not unique",
)


labels = {
    "JerkGramSteelReveal": "Steel",
    "JerkGramSteelSolid": "Steel Solid",
    "JerkGramRustReveal": "Rust",
    "JerkGramRustSolid": "Rust Solid",
    "JerkGramInkReveal": "Ink",
    "JerkGramInkSolid": "Ink Solid",
    "JerkGramOliveReveal": "Olive",
    "JerkGramOliveSolid": "Olive Solid",
}

for icon_id, label in labels.items():
    require(
        (
            f'case "{icon_id}":'
            in icon_item
            and f'name = "{label}"'
            in icon_item
        ),
        f"selector label missing: {label}",
    )


start = enqueue.find(
    "private func "
    "ghostBaseBuildPortableDeletedReply("
)

require(
    start >= 0,
    "deleted-reply materializer missing",
)

end = enqueue.find(
    "\nprivate func ",
    start + 32,
)

require(
    end >= 0,
    "deleted-reply materializer end missing",
)

portable = enqueue[start:end]

require(
    "BUILD110_RECOVERED_AUTHOR_NO_WEB_PREVIEW1"
    in portable,
    "recovered-author preview marker missing",
)

require(
    "tg://resolve?domain="
    in portable,
    "internal portable author link missing",
)

require(
    "https://t.me/"
    not in portable
    and "http://t.me/"
    not in portable
    and "https://telegram.me/"
    not in portable,
    "HTTP author URL survived in recovery path",
)

require(
    "userEntities"
    in portable
    and "ghostBaseShiftEntities"
    in portable,
    (
        "normal user entities were accidentally "
        "removed from deleted-reply materializer"
    ),
)


for bad in (
    "Показывать секунды в сообщениях",
    "Показывать удалённые сообщения",
    "Сохранять удалённые сообщения",
    "Показывать историю изменений",
    "Сохранение одноразовых медиа",
    "Allow One-Time Screen Recording",
    "Enable Protected Content Bypass",
):
    require(
        f'"{bad}"' not in settings,
        f"long toggle title survived: {bad}",
    )

require(
    "BUILD110_SHORT_TOGGLE_TITLES1"
    in settings,
    "short-toggle marker missing",
)


require(
    "BUILD110_PROFILE_READABILITY1"
    in profile_bg,
    "adaptive profile contrast missing",
)

require(
    "Self.colorLuminance(sourceColor)"
    in profile_bg,
    "profile luminance sampling missing",
)

require(
    "UIColor.black"
    in profile_bg
    and "UIColor.white"
    in profile_bg,
    "two-sided profile contrast missing",
)

require(
    "BUILD110_REPORT_CONTRAST1"
    in profile_report,
    "report-card contrast marker missing",
)

require(
    "white: isDark ? 0.0 : 1.0"
    in profile_report,
    "report card is not contrast-oriented",
)

require(
    "alpha: isDark ? 0.26 : 0.18"
    in profile_report,
    "report-card readability alpha mismatch",
)


require(
    "jerkgram.runtime.namespaceMigration.v1"
    in app,
    "Build109 one-shot migration disappeared",
)


print(
    "[verify Build110] GREEN"
)
print(
    "  8 JerkGram icons registered"
)
print(
    "  Steel Reveal = physical + logical default"
)
print(
    "  JerkGram selector above stock Telegram selector"
)
print(
    "  shared currentAppIconName preserved"
)
print(
    "  recovered author uses non-web internal link"
)
print(
    "  ordinary user URL entities preserved"
)
print(
    "  long toggle labels shortened"
)
print(
    "  profile background contrast adaptive"
)
print(
    "  report/log cards contrast-safe"
)
