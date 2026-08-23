#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get(
            "GHOSTBASE_SOURCE_ROOT",
            str(Path.cwd())
        )
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


for raw, expected in (
    ("ru", "ru"),
    ("ru-RU", "ru"),
    ("ru-raw", "ru"),
    ("en-US", "en"),
    ("de_DE", "de"),
):
    require(normalize(raw) == expected, raw + " normalization failed")

require(TARGET.is_file(), "JerkgramStrings.swift missing")
text = TARGET.read_text(encoding="utf-8")

require(text.count(MARKER) == 1, "marker count != 1")
require("import PresentationStrings" in text, "PresentationStrings import missing")
require("self.baseLanguageCode" in text, "Telegram language owner missing")
require('let rawSuffix = "-raw"' in text, "-raw normalization missing")
require('self.languageCode == "ru"' in text, "Russian selection missing")
require("return Self.english[key]!" in text, "English fallback missing")
require("currentVisualBalance(_ balance: String)" in text, "balance formatter missing")

for forbidden in (
    "Locale.current",
    "Bundle.main.preferredLocalizations",
    "AppleLanguages",
):
    require(forbidden not in text, "device-language dependency found: " + forbidden)

required_keys = (
    "settingsTitle", "basicFunctions", "ghostMode", "messages",
    "protectedContent", "mediaAndStories", "appearance", "debugResearch", "about",
    "profileCard", "showIds", "showDcs", "registrationDate", "localStarsBalance",
    "starsBalance", "currentVisualBalance", "readGhost", "typing", "recording",
    "uploading", "choosingSticker", "gameActivity", "choosingEmoji", "hideOnline",
    "scheduledSend", "deletedMessages", "saveDeletedMessages", "showDeletedMessages",
    "editHistory", "saveEditHistory", "showEditHistory", "savedDataHint",
    "protectionEnabled", "shareFromGallery", "saveFromGallery", "copyFromGallery",
    "saveFromChat", "copyFromChat", "forwardFromChat", "allowScreenshots",
    "allowScreenRecording", "oneTimeScreenshots", "oneTimeScreenRecording",
    "oneTimeSave", "storySave", "appearancePlaceholder", "information", "telegramId",
    "rawIdNamespace", "profile", "mainMenu", "deletedMessage", "editedMessage",
    "sticker", "photo", "video", "gif", "audio", "voiceMessage", "videoMessage",
    "document", "attachment", "album", "poll", "location", "contact", "dice",
    "taskList", "user", "importSettings", "exportSettings", "importArchive", "exportArchive",
)

for key in required_keys:
    require(
        re.search(rf"\bcase\s+{re.escape(key)}\b", text) is not None,
        "missing localization key: " + key
    )

english_start = text.index("private static let english:")
russian_start = text.index("private static let russian:")
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

for key in required_keys:
    require(
        re.search(rf"\.{re.escape(key)}:\s*\"", english) is not None,
        "English value missing: " + key
    )
    require(
        re.search(rf"\.{re.escape(key)}:\s*\"", russian) is not None,
        "Russian value missing: " + key
    )

print("[verify Build115 localization] GREEN")
print("[verify Build115 localization] Telegram language drives Jerkgram")
print("[verify Build115 localization] English canonical fallback")
print("[verify Build115 localization] settings/recovery/archive catalog complete")
