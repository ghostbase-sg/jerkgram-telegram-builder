#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        str(Path.cwd())
    )
).resolve()

TARGET = (
    ROOT
    / "submodules/TelegramPresentationData/Sources"
    / "JerkgramStrings.swift"
)

MARKER = (
    "// MARK: Jerkgram v1.2D "
    "BUILD115_LOCALIZATION_FOUNDATION1"
)


def require(value, message):
    if not value:
        raise RuntimeError(
            "[verify Build115 localization] "
            + message
        )


def normalize(code):
    value = code.lower()

    if value.endswith("-raw"):
        value = value[:-4]

    for separator in ("-", "_"):
        if separator in value:
            value = value.split(separator, 1)[0]
            break

    return value


require(normalize("ru") == "ru", "ru normalization failed")
require(normalize("ru-RU") == "ru", "ru-RU normalization failed")
require(normalize("ru-raw") == "ru", "ru-raw normalization failed")
require(normalize("en-US") == "en", "en-US normalization failed")
require(normalize("de_DE") == "de", "de_DE normalization failed")

require(TARGET.is_file(), "JerkgramStrings.swift missing")
text = TARGET.read_text(encoding="utf-8")

require(text.count(MARKER) == 1, "marker count != 1")
require("import PresentationStrings" in text, "PresentationStrings import missing")
require("self.baseLanguageCode" in text, "Telegram language owner missing")
require('let rawSuffix = "-raw"' in text, "-raw normalization missing")
require('self.languageCode == "ru"' in text, "Russian selection missing")
require("return Self.english[key]!" in text, "English fallback missing")

for forbidden in (
    "Locale.current",
    "Bundle.main.preferredLocalizations",
    "AppleLanguages",
):
    require(
        forbidden not in text,
        "device-language dependency found: " + forbidden
    )

required_keys = (
    "sticker",
    "photo",
    "video",
    "gif",
    "audio",
    "voiceMessage",
    "document",
    "album",
    "deletedMessage",
    "editedMessage",
    "ghostMode",
    "messages",
    "protectedContent",
    "mediaAndStories",
    "appearance",
    "debugResearch",
    "about",
    "importSettings",
    "exportSettings",
    "importArchive",
    "exportArchive",
)

for key in required_keys:
    require(
        re.search(
            rf"\bcase\s+{re.escape(key)}\b",
            text
        ) is not None,
        "missing localization key: " + key
    )

english_start = text.index(
    "private static let english:"
)
russian_start = text.index(
    "private static let russian:"
)
english = text[english_start:russian_start]
russian = text[russian_start:]

require(
    re.search(r"[А-Яа-яЁё]", english) is None,
    "English canonical table contains Cyrillic"
)
require(
    re.search(r"[А-Яа-яЁё]", russian) is not None,
    "Russian table contains no Cyrillic"
)

print("[verify Build115 localization] GREEN")
print("[verify Build115 localization] Telegram language drives Jerkgram")
print("[verify Build115 localization] English canonical fallback")
print("[verify Build115 localization] recovery/settings/archive keys seeded")
