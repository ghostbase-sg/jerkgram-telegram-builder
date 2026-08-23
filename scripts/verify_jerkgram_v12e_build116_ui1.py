#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()

PROFILE = ROOT / (
    "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/"
    "Sources/PeerInfoData.swift"
)
CHAT = ROOT / "submodules/TelegramUI/Sources/ChatController.swift"
SETTINGS = ROOT / (
    "submodules/SettingsUI/Sources/GhostBase/"
    "GhostBaseSettingsController.swift"
)
STRINGS = ROOT / (
    "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
)


def require(value, message):
    if not value:
        raise RuntimeError("[verify Build116 UI] " + message)


def block_region(text, opening, after=0):
    start = text.find(opening, after)
    require(start >= 0, "block missing: " + opening)
    brace = text.find("{", start)
    depth = 0
    in_string = False
    escaped = False
    for index in range(brace, len(text)):
        character = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise RuntimeError("[verify Build116 UI] unbalanced block: " + opening)


def verify(profile, chat, settings, strings):
    for marker, owner in (
        ("BUILD116_PROFILE_SCOPE1", profile),
        ("BUILD116_CHAT_NUMERIC_MENTION1", chat),
        ("BUILD116_SETTINGS_RUNTIME_CLEANUP1", settings),
        ("BUILD116_STYLE_LOCALIZATION1", settings),
        ("BUILD116_ABOUT_COMMUNITY1", settings),
    ):
        require(owner.count(marker) == 1, "marker count != 1: " + marker)

    for token in (
        "PeerInfoPaneKey.ghostBaseProfileHistory",
        "PeerInfoPaneKey.ghostBasePresence",
        "PeerInfoPaneKey.ghostBaseGiftHistory",
        ".ghostBasePersonalChannel",
    ):
        require(token in profile, "profile pane missing: " + token)
    require("BUILD115_HIDE_RESEARCH_PANES1" not in profile, "Build115 pane suppression survived")

    require("jerkgramNumericMentionPeerId(name)" in chat, "numeric chat route missing")
    require('self.openUrl("https://t.me/@id\\(idValue)"' in chat, "numeric deep link missing")
    require("resolvePeerByName(name: name" in chat, "normal username path missing")

    require("jerkgram.Runtime.Diagnostics.V11G" not in settings, "raw Runtime list survived")
    require('header(0, "Runtime")' not in settings, "raw Runtime header survived")
    require("https://t.me/JerkgramApp" in settings, "community URL missing")
    require("strings.community" in settings, "community title is not localized")
    require("strings.communityHint" in settings, "community hint is not localized")
    about_start = settings.index("BUILD116_ABOUT_COMMUNITY1")
    about = block_region(settings, "if page == .about", about_start)
    require(
        "Bundle ID:" not in about,
        "Bundle ID is still exposed in About",
    )

    style_literals = (
        "Обычный", "Жирный", "Курсив", "Моноширинный",
        "Зачёркнутый", "Подчёркнутый", "Спойлер", "Пример:",
        "Стиль отправки",
    )
    for literal in style_literals:
        require(
            not re.search(r'"(?:\\.|[^"\\])*' + re.escape(literal), settings),
            "hard-coded style literal survived: " + literal,
        )

    for key in (
        "sendStyleNormal", "sendStyleBold", "sendStyleItalic",
        "sendStyleMonospace", "sendStyleStrikethrough",
        "sendStyleUnderline", "sendStyleSpoiler",
        "sendStyleExamplePrefix", "sendStyleExampleBody",
        "community", "communityHint", "copyExtensionDiagnostics",
    ):
        require("case " + key in strings, "string key missing: " + key)
        require("self.text(." + key + ")" in strings, "string accessor missing: " + key)

    require('.community: "Jerkgram Community"' in strings, "English community text missing")
    require('.community: "Сообщество Jerkgram"' in strings, "Russian community text missing")


def main():
    for path in (PROFILE, CHAT, SETTINGS, STRINGS):
        require(path.is_file(), "source owner missing: " + str(path))
    verify(
        PROFILE.read_text(encoding="utf-8"),
        CHAT.read_text(encoding="utf-8"),
        SETTINGS.read_text(encoding="utf-8"),
        STRINGS.read_text(encoding="utf-8"),
    )
    print("[verify Build116 UI] GREEN: profile/chat/localization/About invariants")


if __name__ == "__main__":
    main()
