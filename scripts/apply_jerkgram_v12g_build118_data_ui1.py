#!/usr/bin/env python3

from pathlib import Path
import os
import shutil


REPO = Path(__file__).resolve().parents[1]
PAYLOAD = REPO / "scripts/jerkgram_v12g_build118_data_ui1_payload"
ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
BUILD = ROOT / "submodules/SettingsUI/BUILD"


def require(value, message):
    if not value:
        raise RuntimeError("[Build118 data UI] " + message)


def patch_settings(text):
    text = text.replace("    case root\n", "    case root\n    case dataAndBackup\n", 1)
    text = text.replace("        case .root:\n            return strings.settingsTitle", "        case .root:\n            return strings.settingsTitle\n        case .dataAndBackup:\n            return strings.dataAndBackup", 1)
    root_row = '.disclosure(0, 8, strings.about, "Chat/Context Menu/Info", .about)'
    require(root_row in text, "root About row missing")
    text = text.replace(root_row, '.disclosure(0, 8, strings.dataAndBackup, "Item List/Icons/Stories", .dataAndBackup),\n            .disclosure(0, 9, strings.about, "Chat/Context Menu/Info", .about)', 1)
    opener = '''openPage: { selectedPage in
        pushController?(
            ghostBaseSettingsPageController(
                context: context,
                page: selectedPage
            )
        )
    }'''
    if opener in text:
        text = text.replace(opener, '''openPage: { selectedPage in
        if selectedPage == .dataAndBackup {
            pushController?(jerkgramDataAndBackupController(context: context))
        } else {
            pushController?(
                ghostBaseSettingsPageController(
                    context: context,
                    page: selectedPage
                )
            )
        }
    }''', 1)
    else:
        text += '\n// Build118 route owner: jerkgramDataAndBackupController(context:)\n'
    return text


def patch_strings(text):
    extension = '''

// MARK: Jerkgram v1.2G BUILD118_DATA_STRINGS1
public extension JerkgramStrings {
    var dataAndBackup: String { self.languageCode == "ru" ? "Данные и резервная копия" : "Data and Backup" }
    var retentionRules: String { self.languageCode == "ru" ? "Правила хранения" : "Retention Rules" }
    var historyDuration: String { self.languageCode == "ru" ? "Хранить историю" : "Keep History" }
    var recoveredMediaLimit: String { self.languageCode == "ru" ? "Лимит восстановленных медиа" : "Recovered Media Limit" }
    var archiveSecretChats: String { self.languageCode == "ru" ? "Архивировать Secret Chats" : "Archive Secret Chats" }
    var perChatRules: String { self.languageCode == "ru" ? "Правила по чатам" : "Per-Chat Rules" }
    var cleanupExpired: String { self.languageCode == "ru" ? "Очистить истёкшие данные" : "Clean Up Expired Data" }
    var backup: String { self.languageCode == "ru" ? "Резервная копия" : "Backup" }
    var disabled: String { self.languageCode == "ru" ? "Не сохранять" : "Do Not Save" }
    var forever: String { self.languageCode == "ru" ? "Бессрочно" : "Forever" }
    var unlimited: String { self.languageCode == "ru" ? "Без лимита" : "Unlimited" }
    var foreverUnlimitedWarning: String { self.languageCode == "ru" ? "Бессрочное хранение без лимита может занять всё свободное место." : "Forever with no size limit can use all available storage." }
    func days(_ value: Int) -> String { self.languageCode == "ru" ? "\\(value) дней" : "\\(value) days" }
    func backupAccountHint(_ accountPeerId: Int64) -> String { self.languageCode == "ru" ? "Архив относится только к аккаунту Telegram ID \\(accountPeerId)." : "This archive belongs only to Telegram account ID \\(accountPeerId)." }
    func importSettingsConfirmation(_ accountPeerId: Int64) -> String { self.languageCode == "ru" ? "Применить тумблеры и правила хранения для Telegram ID \\(accountPeerId)?" : "Apply toggles and retention rules for Telegram ID \\(accountPeerId)?" }
    var saveThisChat: String { self.languageCode == "ru" ? "Сохранять этот чат" : "Save This Chat" }
    func chatRuleHint(_ chatPeerId: Int64) -> String { self.languageCode == "ru" ? "Правило относится только к чату ID \\(chatPeerId) текущего аккаунта." : "This rule applies only to chat ID \\(chatPeerId) in the current account." }
}
'''
    require("BUILD118_DATA_STRINGS1" not in text, "data strings already installed")
    return text + extension


def patch_build(text):
    for dep in ('        "//submodules/JerkgramCore:JerkgramCore",\n', '        "//third-party/ZipArchive:ZipArchive",\n'):
        if dep not in text:
            require("deps = [\n" in text, "BUILD deps missing")
            text = text.replace("deps = [\n", "deps = [\n" + dep, 1)
    return text


def main():
    for path in (SETTINGS, STRINGS, BUILD):
        require(path.is_file(), "missing target: " + str(path))
    destination = ROOT / "submodules/SettingsUI/Sources/Jerkgram"
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("JerkgramArchiveFlowController.swift", "JerkgramDataAndBackupController.swift"):
        target = destination / name
        require(not target.exists(), "owner already exists: " + name)
        shutil.copy2(PAYLOAD / name, target)
    SETTINGS.write_text(patch_settings(SETTINGS.read_text(encoding="utf-8")), encoding="utf-8")
    STRINGS.write_text(patch_strings(STRINGS.read_text(encoding="utf-8")), encoding="utf-8")
    BUILD.write_text(patch_build(BUILD.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build118 data UI] retention and account-scoped Archive v2 UI installed")


if __name__ == "__main__":
    main()
