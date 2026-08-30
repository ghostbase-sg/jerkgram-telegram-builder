#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
PHONE = ROOT / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryControllerNode.swift"
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
MARKER = "// MARK: Jerkgram v1.2N BUILD125_AUTH_GHOST_LOCALIZATION1"
BOT_MARKER = "// MARK: Jerkgram v1.2N BUILD125_AUTH_BOT_LOGIN_LOCALIZATION2"
BOT_STRINGS_MARKER = "// MARK: Jerkgram v1.2N BUILD125_AUTH_BOT_LOGIN_STRINGS2"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build125 auth ghost localization] " + message)


EXTENSION = r'''

// MARK: Jerkgram v1.2N BUILD125_AUTH_GHOST_LOCALIZATION1
// Login controls must follow Telegram's selected interface language before an
// account session exists. `strings` is supplied by the authorization flow and
// therefore tracks PresentationStrings.baseLanguageCode rather than iOS Locale.
public extension JerkgramStrings {
    private var authGhostIsRussian: Bool { self.languageCode == "ru" }

    func authGhostModeStatus(enabled: Bool) -> String {
        if self.authGhostIsRussian {
            return enabled ? "👻 Режим призрака: ВКЛ" : "👻 Режим призрака: ВЫКЛ"
        } else {
            return enabled ? "👻 Ghost Mode: ON" : "👻 Ghost Mode: OFF"
        }
    }

    var authGhostModeHint: String {
        return self.authGhostIsRussian
            ? "Включите до входа, чтобы оставаться невидимым с первой сессии."
            : "Enable before login to stay invisible from the first session."
    }
}
'''


BOT_EXTENSION = r'''

// MARK: Jerkgram v1.2N BUILD125_AUTH_BOT_LOGIN_STRINGS2
// This probe does not materialize the older Build124 bot-localization overlay,
// so the visible phone-entry control owns its small selected-language contract.
public extension JerkgramStrings {
    private var authBotIsRussian: Bool { self.languageCode == "ru" }

    var botLoginButton: String {
        return self.authBotIsRussian ? "Войти как бот" : "Log in as Bot"
    }

    var botLoginAccessibility: String {
        return self.authBotIsRussian ? "Войти как бот" : "Log in as Bot"
    }
}
'''


def patch_phone(text: str) -> str:
    if MARKER in text:
        return text
    replacements = {
        'return enabled ? "👻 Режим призрака: ВКЛ" : "👻 Режим призрака: ВЫКЛ"': 'return strings.jerkgram.authGhostModeStatus(enabled: enabled)',
        'return enabled ? "👻 Ghost Mode: ON" : "👻 Ghost Mode: OFF"': 'return strings.jerkgram.authGhostModeStatus(enabled: enabled)',
        'string: "Включите до входа, чтобы оставаться невидимым с первой сессии."': 'string: strings.jerkgram.authGhostModeHint',
        'string: "Enable before login to stay invisible from the first session."': 'string: strings.jerkgram.authGhostModeHint',
    }
    changed = 0
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new, 1)
            changed += 1
    require(changed == 2, f"expected Ghost Mode title and hint owners, patched {changed}")

    # This helper is file-private, outside the node instance; it has no
    # implicit `strings`. Pass PresentationStrings through both real call sites.
    require(text.count('private func ghostBaseSafeLoginButtonTitle(_ enabled: Bool) -> String {') == 1, "Ghost Mode title helper owner missing")
    require(text.count('ghostBaseSafeLoginButtonTitle(ghostBaseInitialSafeLoginEnabled)') == 1, "Ghost Mode initial title call missing")
    require(text.count('ghostBaseSafeLoginButtonTitle(strongSelf.ghostBaseSafeLoginEnabled)') == 1, "Ghost Mode toggle title call missing")
    text = text.replace(
        'private func ghostBaseSafeLoginButtonTitle(_ enabled: Bool) -> String {',
        'private func ghostBaseSafeLoginButtonTitle(_ enabled: Bool, strings: PresentationStrings) -> String {',
        1,
    ).replace(
        'ghostBaseSafeLoginButtonTitle(ghostBaseInitialSafeLoginEnabled)',
        'ghostBaseSafeLoginButtonTitle(ghostBaseInitialSafeLoginEnabled, strings: strings)',
        1,
    ).replace(
        'ghostBaseSafeLoginButtonTitle(strongSelf.ghostBaseSafeLoginEnabled)',
        'ghostBaseSafeLoginButtonTitle(strongSelf.ghostBaseSafeLoginEnabled, strings: strongSelf.strings)',
        1,
    )
    # This is a distinct visible control from Ghost Mode. It stayed Russian in
    # the published IPA because the first localisation pass only covered the
    # Safe Login title and its hint.
    if BOT_MARKER not in text:
        require(text.count('string: "Войти как бот"') == 1, "bot-login title owner missing")
        require(text.count('self.ghostBaseBotLoginNode.accessibilityLabel = "Войти как бот"') == 1, "bot-login accessibility owner missing")
        text = text.replace(
            'string: "Войти как бот"',
            'string: strings.jerkgram.botLoginButton',
            1,
        ).replace(
            'self.ghostBaseBotLoginNode.accessibilityLabel = "Войти как бот"',
            'self.ghostBaseBotLoginNode.accessibilityLabel = strings.jerkgram.botLoginAccessibility',
            1,
        )
        text += "\n" + BOT_MARKER + "\n"
    return text + "\n" + MARKER + "\n"


def patch_strings(text: str) -> str:
    require("public struct JerkgramStrings" in text, "JerkgramStrings owner missing")
    if MARKER not in text:
        text = text.rstrip() + EXTENSION + "\n"
    if BOT_STRINGS_MARKER not in text and "var botLoginButton: String" not in text:
        text = text.rstrip() + BOT_EXTENSION + "\n"
    return text


def main() -> None:
    require(PHONE.is_file(), f"missing phone entry owner: {PHONE}")
    require(STRINGS.is_file(), f"missing JerkgramStrings owner: {STRINGS}")
    PHONE.write_text(patch_phone(PHONE.read_text(encoding="utf-8")), encoding="utf-8")
    STRINGS.write_text(patch_strings(STRINGS.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build125 auth ghost localization] GREEN")


if __name__ == "__main__":
    main()
