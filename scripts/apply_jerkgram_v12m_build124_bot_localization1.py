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
        raise RuntimeError("[Build124 bot localization] " + message)


STRINGS_EXTENSION = r'''

// MARK: Jerkgram v1.2M BUILD124_BOT_LOCALIZATION1
// Bot-account UI follows Telegram's selected interface language through the
// same JerkgramStrings owner as the rest of Jerkgram. Persisted diagnostic
// status values remain semantic English tokens and are translated only here.
public extension JerkgramStrings {
    private var botIsRussian: Bool { self.languageCode == "ru" }

    var botLoginButton: String { self.botIsRussian ? "Войти как бот — Экспериментально" : "Log in as Bot — Experimental" }
    var botLoginAccessibility: String { self.botIsRussian ? "Войти как бот" : "Log in as Bot" }
    var botLoginTitle: String { self.botIsRussian ? "Вход как бот" : "Bot Login" }
    var botTokenNotice: String { self.botIsRussian ? "Введите токен, выданный BotFather. Токен не сохраняется." : "Enter the token issued by BotFather. The token is not stored." }

    var botInvalidToken: String { self.botIsRussian ? "Токен бота недействителен." : "The bot token is invalid." }
    var botFloodWait: String { self.botIsRussian ? "Слишком много попыток. Попробуйте позже." : "Too many attempts. Try again later." }
    var botApiIdInvalid: String { self.botIsRussian ? "Telegram отклонил API ID клиента." : "Telegram rejected this client's API ID." }
    var botMethodInvalid: String { self.botIsRussian ? "Сервер не разрешил авторизацию бота." : "The server did not allow bot authorization." }
    var botSignUpRequired: String { self.botIsRussian ? "Сервер запросил регистрацию вместо входа." : "The server requested registration instead of login." }
    func botRpcRejected(_ code: String) -> String { self.botIsRussian ? "Сервер отклонил вход: \(code)" : "The server rejected login: \(code)" }
    var botGenericLoginError: String { self.botIsRussian ? "Не удалось войти в аккаунт бота." : "Couldn't log in to the bot account." }
    var botAlreadyAdded: String { self.botIsRussian ? "Этот бот уже добавлен в Jerkgram." : "This bot is already added to Jerkgram." }

    var botLogoutTitle: String { self.botIsRussian ? "Выйти из аккаунта бота?" : "Log out of the bot account?" }
    var botLogoutText: String { self.botIsRussian ? "Аккаунт будет удалён только из Jerkgram. Сам бот и его токен в BotFather не удаляются." : "The account will be removed only from Jerkgram. The bot itself and its BotFather token are not deleted." }
    var botLogoutAction: String { self.botIsRussian ? "Выйти" : "Log Out" }

    var botCapabilityTitle: String { self.botIsRussian ? "Возможности бот-аккаунта" : "Bot Account Capabilities" }
    var botCapabilityAction: String { self.botIsRussian ? "Проверить RPC бот-аккаунта" : "Check Bot Account RPC" }
    var botDifferenceAction: String { self.botIsRussian ? "Проверить updates.getDifference" : "Check updates.getDifference" }
    var botNoResults: String { self.botIsRussian ? "Результатов пока нет." : "No results yet." }

    func botDiagnosticReport(status: String, updated: String, report: String) -> String {
        let localizedStatus: String
        switch status {
        case "not tested": localizedStatus = self.botIsRussian ? "не проверено" : "not tested"
        case "running": localizedStatus = self.botIsRussian ? "выполняется" : "running"
        case "completed": localizedStatus = self.botIsRussian ? "завершено" : "completed"
        default: localizedStatus = status
        }
        let localizedUpdated = updated == "none" ? (self.botIsRussian ? "нет" : "none") : updated
        let statusLabel = self.botIsRussian ? "Статус" : "Status"
        let updatedLabel = self.botIsRussian ? "Обновлено" : "Updated"
        return "\(statusLabel): \(localizedStatus)\n\(updatedLabel): \(localizedUpdated)\n\n\(report)"
    }
}
'''


def patch_strings(text: str) -> str:
    if MARKER in text:
        return text
    require("public struct JerkgramStrings" in text, "JerkgramStrings owner missing")
    return text.rstrip() + STRINGS_EXTENSION + "\n"


def patch_auth_sources(files: dict[str, str]) -> dict[str, str]:
    result = dict(files)

    if "passwordNode" in result:
        text = result["passwordNode"]
        text = text.replace('mode == .ghostBaseBotToken ? "Вход как бот" : strings.LoginPassword_Title', 'mode == .ghostBaseBotToken ? strings.jerkgram.botLoginTitle : strings.LoginPassword_Title')
        text = text.replace('mode == .ghostBaseBotToken ? "Введите токен, выданный BotFather. Токен не сохраняется." : strings.TwoStepAuth_EnterPasswordHelp', 'mode == .ghostBaseBotToken ? strings.jerkgram.botTokenNotice : strings.TwoStepAuth_EnterPasswordHelp')
        text = text.replace('self.mode == .ghostBaseBotToken ? "Вход как бот" : self.strings.LoginPassword_Title', 'self.mode == .ghostBaseBotToken ? self.strings.jerkgram.botLoginTitle : self.strings.LoginPassword_Title')
        result["passwordNode"] = text

    if "phoneNode" in result:
        text = result["phoneNode"]
        text = text.replace('NSAttributedString(string: "Войти как бот — Экспериментально",', 'NSAttributedString(string: strings.jerkgram.botLoginButton,')
        text = text.replace('self.ghostBaseBotLoginNode.accessibilityLabel = "Войти как бот"', 'self.ghostBaseBotLoginNode.accessibilityLabel = strings.jerkgram.botLoginAccessibility')
        result["phoneNode"] = text

    if "controller" in result:
        text = result["controller"]
        text = text.replace('text = "Этот бот уже добавлен в GhostBase."', 'text = self.presentationData.strings.jerkgram.botAlreadyAdded')
        text = text.replace('text = "Токен бота недействителен."', 'text = self.presentationData.strings.jerkgram.botInvalidToken')
        text = text.replace('text = "Telegram отклонил API ID клиента."', 'text = self.presentationData.strings.jerkgram.botApiIdInvalid')
        text = text.replace('text = "Сервер не разрешил авторизацию бота."', 'text = self.presentationData.strings.jerkgram.botMethodInvalid')
        text = text.replace('text = "Не удалось войти в аккаунт бота."', 'text = self.presentationData.strings.jerkgram.botGenericLoginError')
        text = text.replace('title: "Вход как бот",', 'title: self.presentationData.strings.jerkgram.botLoginTitle,')
        text = text.replace('''text =
                                "Слишком много попыток. "
                                + "Попробуйте позже."''', 'text = self.presentationData.strings.jerkgram.botFloodWait')
        text = text.replace('''text =
                                "Сервер запросил регистрацию "
                                + "вместо входа."''', 'text = self.presentationData.strings.jerkgram.botSignUpRequired')
        text = text.replace('''text =
                                "Сервер отклонил вход: \\(code)"''', 'text = self.presentationData.strings.jerkgram.botRpcRejected(code)')
        result["controller"] = text

    if "actions" in result:
        text = result["actions"]
        text = text.replace('title: "Выйти из аккаунта бота?",', 'title: self.presentationData.strings.jerkgram.botLogoutTitle,')
        text = text.replace('text: "Аккаунт будет удалён только из GhostBase. Сам бот и его токен в BotFather не удаляются.",', 'text: self.presentationData.strings.jerkgram.botLogoutText,')
        text = text.replace('title: "Выйти",', 'title: self.presentationData.strings.jerkgram.botLogoutAction,')
        result["actions"] = text

    return result


def patch_settings(text: str) -> str:
    text = text.replace("private func ghostBaseBotCapabilityReport() -> String {", "private func ghostBaseBotCapabilityReport(strings: PresentationStrings) -> String {")
    text = text.replace("private func ghostBaseBotDifferenceReport() -> String {", "private func ghostBaseBotDifferenceReport(strings: PresentationStrings) -> String {")
    text = text.replace('?? "Результатов пока нет."', '?? strings.jerkgram.botNoResults')
    report_template = '''return """
    Status: \\(status)
    Updated: \\(updated)

    \\(report)
    """'''
    text = text.replace(report_template, 'return strings.jerkgram.botDiagnosticReport(status: status, updated: updated, report: report)')
    text = text.replace('"Bot Account Capability Probe"', 'strings.jerkgram.botCapabilityTitle')
    text = text.replace('"Проверить RPC bot-аккаунта"', 'strings.jerkgram.botCapabilityAction')
    text = text.replace('"Проверить RPC бот-аккаунта"', 'strings.jerkgram.botCapabilityAction')
    text = text.replace('"Проверить updates.getDifference"', 'strings.jerkgram.botDifferenceAction')
    text = text.replace("ghostBaseBotCapabilityReport()", "ghostBaseBotCapabilityReport(strings: strings)")
    text = text.replace("ghostBaseBotDifferenceReport()", "ghostBaseBotDifferenceReport(strings: strings)")
    return text


def main() -> None:
    paths = [STRINGS, PASSWORD_NODE, PHONE_NODE, PHONE_CONTROLLER, ACTIONS, SETTINGS]
    for path in paths:
        require(path.is_file(), f"missing materialized source: {path}")

    STRINGS.write_text(patch_strings(STRINGS.read_text(encoding="utf-8")), encoding="utf-8")

    auth = patch_auth_sources({
        "passwordNode": PASSWORD_NODE.read_text(encoding="utf-8"),
        "phoneNode": PHONE_NODE.read_text(encoding="utf-8"),
        "controller": PHONE_CONTROLLER.read_text(encoding="utf-8"),
        "actions": ACTIONS.read_text(encoding="utf-8"),
    })
    PASSWORD_NODE.write_text(auth["passwordNode"], encoding="utf-8")
    PHONE_NODE.write_text(auth["phoneNode"], encoding="utf-8")
    PHONE_CONTROLLER.write_text(auth["controller"], encoding="utf-8")
    ACTIONS.write_text(auth["actions"], encoding="utf-8")
    SETTINGS.write_text(patch_settings(SETTINGS.read_text(encoding="utf-8")), encoding="utf-8")

    combined = "\n".join(path.read_text(encoding="utf-8") for path in (PASSWORD_NODE, PHONE_NODE, PHONE_CONTROLLER, ACTIONS, SETTINGS))
    require("strings.jerkgram.botLoginButton" in combined, "localized bot login button missing")
    require("botAlreadyAdded" in combined, "localized duplicate bot message missing")
    require("botLogoutTitle" in combined, "localized bot logout missing")
    require("botCapabilityTitle" in combined and "botDifferenceAction" in combined, "localized bot diagnostics missing")

    print("[Build124 bot localization] GREEN")
    print("[Build124 bot localization] bot login/logout/diagnostics follow PresentationStrings.baseLanguageCode")


if __name__ == "__main__":
    main()
