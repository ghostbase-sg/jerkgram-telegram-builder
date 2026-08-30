#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
PASSWORD_NODE = ROOT / "submodules/AuthorizationUI/Sources/AuthorizationSequencePasswordEntryControllerNode.swift"
PHONE_NODE = ROOT / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryControllerNode.swift"
PHONE_CONTROLLER = ROOT / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryController.swift"
ACTIONS = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenSettingsActions.swift"
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_BOT_LOCALIZATION1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 bot localization verify] " + message)


def main() -> None:
    strings = STRINGS.read_text(encoding="utf-8")
    password = PASSWORD_NODE.read_text(encoding="utf-8")
    phone = PHONE_NODE.read_text(encoding="utf-8")
    controller = PHONE_CONTROLLER.read_text(encoding="utf-8")
    actions = ACTIONS.read_text(encoding="utf-8")
    settings = SETTINGS.read_text(encoding="utf-8")

    require(strings.count(MARKER) == 1, "JerkgramStrings bot extension missing or duplicated")
    for proof in (
        "botLoginButton", "botLoginTitle", "botTokenNotice", "botInvalidToken",
        "botAlreadyAdded", "botLogoutTitle", "botCapabilityTitle",
        "botDifferenceAction", "botDiagnosticReport",
    ):
        require(proof in strings, f"string owner missing: {proof}")
    require("Log in as Bot — Experimental" in strings and "Войти как бот — Экспериментально" in strings, "English/Russian bot button translations missing")

    require("strings.jerkgram.botLoginTitle" in password, "bot token screen title is not localized")
    require("strings.jerkgram.botTokenNotice" in password, "bot token notice is not localized")
    require("strings.jerkgram.botLoginButton" in phone, "phone-screen bot login button is not localized")
    require("strings.jerkgram.botLoginAccessibility" in phone, "bot button accessibility is not localized")

    for proof in (
        "botInvalidToken", "botFloodWait", "botApiIdInvalid", "botMethodInvalid",
        "botSignUpRequired", "botRpcRejected", "botGenericLoginError", "botAlreadyAdded",
    ):
        require(proof in controller, f"bot authorization error is not localized: {proof}")
    require("title: self.presentationData.strings.jerkgram.botLoginTitle" in controller, "bot login alert title is not localized")

    require("botLogoutTitle" in actions and "botLogoutText" in actions and "botLogoutAction" in actions, "bot logout UI is not localized")
    has_legacy_bot_diagnostics = (
        "strings.jerkgram.botCapabilityTitle" in settings
        or "strings.jerkgram.botDifferenceAction" in settings
    )
    if has_legacy_bot_diagnostics:
        require("ghostBaseBotCapabilityReport(strings: PresentationStrings)" in settings, "capability report lacks selected-language owner")
        require("ghostBaseBotDifferenceReport(strings: PresentationStrings)" in settings, "difference report lacks selected-language owner")
        require("strings.jerkgram.botCapabilityTitle" in settings, "bot capability title is not localized")
        require("strings.jerkgram.botDifferenceAction" in settings, "bot difference action is not localized")

    forbidden = (
        'text = "Этот бот уже добавлен в GhostBase."',
        'title: "Выйти из аккаунта бота?",',
        'text: "Аккаунт будет удалён только из GhostBase.',
        'NSAttributedString(string: "Войти как бот — Экспериментально",',
    )
    combined = "\n".join((password, phone, controller, actions, settings))
    for value in forbidden:
        require(value not in combined, f"legacy hardcoded bot UI survived: {value}")

    print("[Build124 bot localization verify] GREEN")
    print("[Build124 bot localization verify] selected Telegram UI language owns bot login/logout/diagnostics")


if __name__ == "__main__":
    main()
