#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd()))
    )
).resolve()
SETTINGS = (
    ROOT
    / "submodules/SettingsUI/Sources/GhostBase"
    / "GhostBaseSettingsController.swift"
)
STRINGS = (
    ROOT
    / "submodules/TelegramPresentationData/Sources"
    / "JerkgramResearchStrings.swift"
)

CANONICAL_MARKER = "// MARK: Jerkgram v1.2D BUILD115_RESEARCH_SETTINGS_CANONICAL1"
LOCALIZED_MARKER = "// MARK: Jerkgram v1.2D BUILD115_RESEARCH_SETTINGS_LOCALIZED1"
STRINGS_MARKER = "// MARK: Jerkgram v1.2D BUILD115_RESEARCH_STRINGS1"


def require(value, message):
    if not value:
        raise RuntimeError("[verify Build115 research settings] " + message)


def function_region(text, signature):
    start = text.find(signature)
    require(start >= 0, "function missing: " + signature)
    brace = text.find("{", start)
    require(brace >= 0, "function brace missing")
    depth = 0
    in_string = False
    escaped = False
    for index in range(brace, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise RuntimeError("[verify Build115 research settings] unterminated function")


def cyrillic_literals(text):
    pattern = re.compile(r'"""(.*?)"""|"(?:\\.|[^"\\])*"', re.S)
    return [
        match.group(0)
        for match in pattern.finditer(text)
        if re.search(r"[А-Яа-яЁё]", match.group(0))
    ]


require(SETTINGS.is_file(), "GhostBaseSettingsController.swift missing")
require(STRINGS.is_file(), "JerkgramResearchStrings.swift missing")
settings = SETTINGS.read_text(encoding="utf-8")
strings = STRINGS.read_text(encoding="utf-8")
entries = function_region(settings, "private func ghostBaseSettingsEntries(")

require(settings.count(CANONICAL_MARKER) == 1, "canonical marker count != 1")
require(settings.count(LOCALIZED_MARKER) == 1, "localized marker count != 1")
require(strings.count(STRINGS_MARKER) == 1, "research strings marker count != 1")
require("self.languageCode == \"ru\"" in strings, "Telegram-language selector missing")

required_properties = (
    "strings.researchCheckNineGiftsSelf",
    "strings.researchCheckUserGifts",
    "strings.researchHiddenGiftsSend",
    "strings.researchSendToSelf",
    "strings.researchSelectAnotherRecipient",
    "strings.researchHideSenderNameOn",
    "strings.researchHideSenderNameOff",
    "strings.researchConfirmGiftRecipient",
    "strings.researchPayAndSend",
    "strings.researchResetSelection",
    "strings.researchBotCapability",
    "strings.researchBotDifference",
    "strings.profileInformation",
    "strings.showProfileInformation",
    "strings.avatarDc",
)
for token in required_properties:
    require(token in entries, "active late localization token missing: " + token)

# Build114 deliberately removes PROFILEINTEL entries. If either returns in a
# future chain, it must be localized rather than hard-coded.
for token in (
    "profileIntel1Probe",
    "profileIntel2Snapshot",
):
    if token in entries:
        required = (
            "strings.researchProfileIntelClipboard"
            if token == "profileIntel1Probe"
            else "strings.researchProfileIntelSnapshot"
        )
        require(required in entries, "PROFILEINTEL action is not localized: " + token)

require(
    not cyrillic_literals(entries),
    "hard-coded Cyrillic survived in Settings entries after research localization"
)

for forbidden in (
    '"Проверить 9 подарков на себе"',
    '"Выбрать пользователя и проверить"',
    '"Hidden Gifts Send — реальное списание"',
    '"Отправить себе"',
    '"Выбрать другого получателя"',
    '"Скрыть имя отправителя: Вкл"',
    '"Скрыть имя отправителя: Выкл"',
    '"1. Подтвердить подарок и получателя"',
    '"2. СПИСАТЬ 50 STARS И ОТПРАВИТЬ"',
    '"Сбросить выбор"',
    '"Проверить RPC bot-аккаунта"',
    '"Проверить updates.getDifference"',
    '"Сведения профиля"',
    '"Показывать сведения"',
    '"DC аватара"',
):
    require(forbidden not in entries, "legacy late literal survived: " + forbidden)

print("[verify Build115 research settings] GREEN")
print("[verify Build115 research settings] legacy research/profile titles are semantic Jerkgram strings")
print("[verify Build115 research settings] RU/EN follows Telegram language")
