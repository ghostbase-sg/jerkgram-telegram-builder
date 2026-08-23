#!/usr/bin/env python3

from pathlib import Path
import argparse
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
SETTINGS_MARKER = "// MARK: Jerkgram v1.2D BUILD115_SETTINGS_LOCALIZATION1"

# Late Debug / Research overlays historically injected Russian literals after
# the main Settings source was generated.  Canonicalize those literals before
# the strict Build115 Settings localization gate, then bind the canonical
# English values to Telegram-language Jerkgram strings after that gate.
RESEARCH = (
    (
        "researchHiddenGiftsProbe",
        "Hidden Gifts Direct Catalog Probe",
        "Проверка скрытых подарков",
        None,
    ),
    (
        "researchCheckNineGiftsSelf",
        "Check 9 Gifts on This Account",
        "Проверить 9 подарков на себе",
        "Проверить 9 подарков на себе",
    ),
    (
        "researchCheckUserGifts",
        "Select User and Check",
        "Выбрать пользователя и проверить",
        "Выбрать пользователя и проверить",
    ),
    (
        "researchHiddenGiftsSend",
        "Hidden Gifts Send — Real Payment",
        "Hidden Gifts Send — реальное списание",
        "Hidden Gifts Send — реальное списание",
    ),
    (
        "researchSendToSelf",
        "Send to Self",
        "Отправить себе",
        "Отправить себе",
    ),
    (
        "researchSelectAnotherRecipient",
        "Select Another Recipient",
        "Выбрать другого получателя",
        "Выбрать другого получателя",
    ),
    (
        "researchHideSenderNameOn",
        "Hide Sender Name: On",
        "Скрыть имя отправителя: Вкл",
        "Скрыть имя отправителя: Вкл",
    ),
    (
        "researchHideSenderNameOff",
        "Hide Sender Name: Off",
        "Скрыть имя отправителя: Выкл",
        "Скрыть имя отправителя: Выкл",
    ),
    (
        "researchConfirmGiftRecipient",
        "1. Confirm Gift and Recipient",
        "1. Подтвердить подарок и получателя",
        "1. Подтвердить подарок и получателя",
    ),
    (
        "researchPayAndSend",
        "2. SPEND 50 STARS AND SEND",
        "2. СПИСАТЬ 50 STARS И ОТПРАВИТЬ",
        "2. СПИСАТЬ 50 STARS И ОТПРАВИТЬ",
    ),
    (
        "researchResetSelection",
        "Reset Selection",
        "Сбросить выбор",
        "Сбросить выбор",
    ),
    (
        "researchBotCapability",
        "Check Bot Account RPC",
        "Проверить RPC bot-аккаунта",
        "Проверить RPC bot-аккаунта",
    ),
    (
        "researchBotDifference",
        "Check updates.getDifference",
        "Проверить updates.getDifference",
        "Проверить updates.getDifference",
    ),
    # PROFILEINTEL entries are removed by Build114, but keeping these mappings
    # makes the late overlay fail-safe if an older chain leaves either block.
    (
        "researchProfileIntelClipboard",
        "Check Username from Clipboard",
        "Проверить username из буфера",
        "Проверить username из буфера",
    ),
    (
        "researchProfileIntelSnapshot",
        "Profile Snapshot + Photo History",
        "Снимок профиля + история фото",
        "Снимок профиля + история фото",
    ),
    (
        "glassMaterialHint",
        "Glass changes only the interface material. Data, tabs, logging, and section heights do not depend on the effect. Reduced surfaces are used with Reduce Transparency and Low Power Mode.",
        "Glass меняет только материал интерфейса. Данные, вкладки, логирование и высота секций не зависят от эффекта. При Reduce Transparency и Low Power Mode используются облегчённые поверхности.",
        "Glass меняет только материал интерфейса. Данные, вкладки, логирование и высота секций не зависят от эффекта. При Reduce Transparency и Low Power Mode используются облегчённые поверхности.",
    ),
)

# English-only headers injected by old research owners also need to follow the
# Telegram language once the function has a JerkgramStrings parameter.
ENGLISH_ONLY = (
    ("researchHiddenGiftsProbe", "Hidden Gifts Probe"),
    ("researchHiddenGiftsProbe", "Hidden Gifts Direct Catalog Probe"),
    ("researchBotCapabilityHeader", "Bot Account Capability Probe"),
)


SWIFT = r'''import Foundation

// MARK: Jerkgram v1.2D BUILD115_RESEARCH_STRINGS1
// Late legacy research UI remains available, but its labels follow Telegram's
// selected language instead of carrying Russian literals in generated source.
public extension JerkgramStrings {
    private func researchText(_ english: String, _ russian: String) -> String {
        return self.languageCode == "ru" ? russian : english
    }

    var researchHiddenGiftsProbe: String {
        self.researchText("Hidden Gifts Direct Catalog Probe", "Проверка скрытых подарков")
    }
    var researchCheckNineGiftsSelf: String {
        self.researchText("Check 9 Gifts on This Account", "Проверить 9 подарков на себе")
    }
    var researchCheckUserGifts: String {
        self.researchText("Select User and Check", "Выбрать пользователя и проверить")
    }
    var researchHiddenGiftsSend: String {
        self.researchText("Hidden Gifts Send — Real Payment", "Hidden Gifts Send — реальное списание")
    }
    var researchSendToSelf: String {
        self.researchText("Send to Self", "Отправить себе")
    }
    var researchSelectAnotherRecipient: String {
        self.researchText("Select Another Recipient", "Выбрать другого получателя")
    }
    var researchHideSenderNameOn: String {
        self.researchText("Hide Sender Name: On", "Скрыть имя отправителя: Вкл")
    }
    var researchHideSenderNameOff: String {
        self.researchText("Hide Sender Name: Off", "Скрыть имя отправителя: Выкл")
    }
    var researchConfirmGiftRecipient: String {
        self.researchText("1. Confirm Gift and Recipient", "1. Подтвердить подарок и получателя")
    }
    var researchPayAndSend: String {
        self.researchText("2. SPEND 50 STARS AND SEND", "2. СПИСАТЬ 50 STARS И ОТПРАВИТЬ")
    }
    var researchResetSelection: String {
        self.researchText("Reset Selection", "Сбросить выбор")
    }
    var researchBotCapabilityHeader: String {
        self.researchText("Bot Account Capability Probe", "Проверка возможностей bot-аккаунта")
    }
    var researchBotCapability: String {
        self.researchText("Check Bot Account RPC", "Проверить RPC bot-аккаунта")
    }
    var researchBotDifference: String {
        self.researchText("Check updates.getDifference", "Проверить updates.getDifference")
    }
    var researchProfileIntelClipboard: String {
        self.researchText("Check Username from Clipboard", "Проверить username из буфера")
    }
    var researchProfileIntelSnapshot: String {
        self.researchText("Profile Snapshot + Photo History", "Снимок профиля + история фото")
    }
    var glassMaterialHint: String {
        self.researchText(
            "Glass changes only the interface material. Data, tabs, logging, and section heights do not depend on the effect. Reduced surfaces are used with Reduce Transparency and Low Power Mode.",
            "Glass меняет только материал интерфейса. Данные, вкладки, логирование и высота секций не зависят от эффекта. При Reduce Transparency и Low Power Mode используются облегчённые поверхности."
        )
    }
}
'''


def require(value, message):
    if not value:
        raise RuntimeError("[Build115 research settings] " + message)


def block_bounds(text, signature):
    start = text.find(signature)
    require(start >= 0, "block missing: " + signature)
    brace = text.find("{", start)
    require(brace >= 0, "opening brace missing: " + signature)
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
                return start, index + 1
    raise RuntimeError("[Build115 research settings] unterminated block")


def string_token(value):
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def cyrillic_literals(text):
    pattern = re.compile(r'"""(.*?)"""|"(?:\\.|[^"\\])*"', re.S)
    return [
        match.group(0).replace("\n", "\\n")[:220]
        for match in pattern.finditer(text)
        if re.search(r"[А-Яа-яЁё]", match.group(0))
    ]


def ensure_strings_file():
    if STRINGS.exists():
        current = STRINGS.read_text(encoding="utf-8")
        require(STRINGS_MARKER in current, "unexpected JerkgramResearchStrings.swift")
        return
    require(STRINGS.parent.is_dir(), "TelegramPresentationData Sources missing")
    STRINGS.write_text(SWIFT, encoding="utf-8")


def canonicalize():
    require(SETTINGS.is_file(), "GhostBaseSettingsController.swift missing")
    ensure_strings_file()
    text = SETTINGS.read_text(encoding="utf-8")
    require(SETTINGS_MARKER not in text, "canonical phase must run before Settings localization")
    require(CANONICAL_MARKER not in text, "canonical phase already applied")

    start, end = block_bounds(text, "private func ghostBaseSettingsEntries(")
    entries = text[start:end]
    for _, english, _, russian_source in RESEARCH:
        if russian_source is not None:
            entries = entries.replace(string_token(russian_source), string_token(english))

    leftovers = cyrillic_literals(entries)
    require(
        not leftovers,
        "unmapped Cyrillic after research canonicalization: " + " | ".join(leftovers[:24])
    )

    entries = CANONICAL_MARKER + "\n" + entries
    SETTINGS.write_text(text[:start] + entries + text[end:], encoding="utf-8")
    print("[Build115 research settings] canonical phase GREEN")
    print("[Build115 research settings] late research entries contain no Cyrillic literals")


def localize():
    require(SETTINGS.is_file(), "GhostBaseSettingsController.swift missing")
    require(STRINGS.is_file(), "JerkgramResearchStrings.swift missing")
    text = SETTINGS.read_text(encoding="utf-8")
    require(CANONICAL_MARKER in text, "canonical research phase missing")
    require(SETTINGS_MARKER in text, "Settings localization must run before localized phase")
    require(LOCALIZED_MARKER not in text, "localized phase already applied")

    start, end = block_bounds(text, "private func ghostBaseSettingsEntries(")
    entries = text[start:end]
    require("strings: JerkgramStrings" in entries, "JerkgramStrings parameter missing")

    for property_name, english, _, _ in RESEARCH:
        entries = entries.replace(string_token(english), "strings." + property_name)
    for property_name, english in ENGLISH_ONLY:
        entries = entries.replace(string_token(english), "strings." + property_name)

    leftovers = cyrillic_literals(entries)
    require(
        not leftovers,
        "Cyrillic reappeared after localized phase: " + " | ".join(leftovers[:24])
    )

    # Every canonical research label that actually survived to this point must
    # either have been converted to a semantic property or have been removed by
    # an earlier Build114 cleanup. No silent English-only fallback for these.
    surviving = []
    for _, english, _, _ in RESEARCH:
        if string_token(english) in entries:
            surviving.append(english)
    for _, english in ENGLISH_ONLY:
        if string_token(english) in entries:
            surviving.append(english)
    require(not surviving, "unlocalized canonical research labels: " + " | ".join(surviving))

    entries = LOCALIZED_MARKER + "\n" + entries
    SETTINGS.write_text(text[:start] + entries + text[end:], encoding="utf-8")
    print("[Build115 research settings] localized phase GREEN")
    print("[Build115 research settings] research labels follow Telegram language")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("canonical", "localized"), required=True)
    args = parser.parse_args()
    if args.phase == "canonical":
        canonicalize()
    else:
        localize()


if __name__ == "__main__":
    main()
