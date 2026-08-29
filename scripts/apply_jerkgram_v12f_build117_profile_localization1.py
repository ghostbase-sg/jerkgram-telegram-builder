#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
REPORT = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileReportPaneNode.swift"
TABS = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoPaneContainerNode.swift"


def require(value, message):
    if not value:
        raise RuntimeError("[Build117 profile localization] " + message)


def replace_once(text, old, new, label):
    count = text.count(old)
    require(count == 1, f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)


def patch_strings(text):
    if (
        "BUILD117_PROFILE_REPORT_LOCALIZATION1" in text
        and "case profileHistoryTab" in text
        and "case profileReportLoading" in text
        and '.profileHistoryTab: "History"' in text
        and '.profileHistoryTab: "История"' in text
    ):
        return text
    text = replace_once(
        text,
        "    case communityNoPosts\n}",
        '''    case communityNoPosts
    case profileHistoryTab
    case presenceHistoryTab
    case giftHistoryTab
    case personalChannelTab
    case profileReportLoading
}''',
        "profile localization keys",
    )
    accessor = '''    public var communityNoPosts: String { self.text(.communityNoPosts) }'''
    methods = r'''    public var communityNoPosts: String { self.text(.communityNoPosts) }
    public var profileHistoryTab: String { self.text(.profileHistoryTab) }
    public var presenceHistoryTab: String { self.text(.presenceHistoryTab) }
    public var giftHistoryTab: String { self.text(.giftHistoryTab) }
    public var personalChannelTab: String { self.text(.personalChannelTab) }
    public var profileReportLoading: String { self.text(.profileReportLoading) }

    // MARK: Jerkgram v1.2F BUILD117_PROFILE_REPORT_LOCALIZATION1
    public func localizedProfileReport(_ raw: String) -> String {
        guard self.languageCode != "ru" else {
            return raw
        }

        let exact: [String: String] = [
            "История изменений профиля": "Profile change history",
            "Изменений после первого наблюдения пока нет.": "No changes since first observation.",
            "История личного канала": "Personal channel history",
            "История подарков пока пуста.": "Gift history is empty.",
            "История подарков": "Gift history",
            "История присутствия пока пуста.": "Presence history is empty.",
            "История профиля пока пуста.": "Profile history is empty.",
            "Личный канал": "Personal channel",
            "Личный канал не найден.": "Personal channel was not found.",
            "онлайн": "online",
            "был недавно": "last seen recently",
            "был на этой неделе": "last seen within a week",
            "был в этом месяце": "last seen within a month",
            "скрытый статус": "hidden status",
            "видимый": "visible",
            "исчез из публичного профиля": "removed from public profile",
            "скрытый владельцем": "hidden by owner",
            "анонимно": "anonymous",
            "Мишка": "Teddy Bear"
        ]
        let prefixes: [(String, String)] = [
            ("История присутствия:", "Presence history:"),
            ("Зафиксировано изменений:", "Recorded changes:"),
            ("Первое наблюдение:", "First observed:"),
            ("Последнее наблюдение:", "Last observed:"),
            ("Последние сообщения:", "Latest messages:"),
            ("Имя:", "Name:"),
            ("Аватар: установлен", "Avatar: set"),
            ("Аватар: удалён", "Avatar: removed"),
            ("Аватар: изменён", "Avatar: changed"),
            ("Личный канал: откреплён", "Personal channel: detached"),
            ("Личный канал: прикреплён", "Personal channel: attached"),
            ("Канал ID:", "Channel ID:"),
            ("Название:", "Title:"),
            ("Ссылка:", "Link:"),
            ("Подписчики:", "Subscribers:"),
            ("Последний message ID:", "Latest message ID:"),
            ("Записей:", "Entries:"),
            ("ID подарка:", "Gift ID:"),
            ("Уникальный ID:", "Unique ID:"),
            ("Номер:", "Number:"),
            ("Отправитель:", "Sender:"),
            ("ID отправителя:", "Sender ID:"),
            ("Сообщение:", "Message:"),
            ("Статус: видимый", "Status: visible"),
            ("Подарок ", "Gift "),
            ("до ", "until ")
        ]

        func translateSegment(_ segment: String) -> String {
            if let value = exact[segment] {
                return value
            }
            for (source, target) in prefixes where segment.hasPrefix(source) {
                return target + String(segment.dropFirst(source.count))
            }
            return segment
        }

        return raw.components(separatedBy: "\n").map { line in
            let bullet = line.hasPrefix("• ") ? "• " : ""
            let content = bullet.isEmpty ? line : String(line.dropFirst(2))
            let translated = content.components(separatedBy: " · ")
                .map(translateSegment)
                .joined(separator: " · ")
            return bullet + translated
        }.joined(separator: "\n")
    }'''
    text = replace_once(text, accessor, methods, "profile localization accessors")
    text = replace_once(
        text,
        '        .communityNoPosts: "No posts yet"\n',
        '''        .communityNoPosts: "No posts yet",
        .profileHistoryTab: "History",
        .presenceHistoryTab: "Presence",
        .giftHistoryTab: "Gift History",
        .personalChannelTab: "Channel",
        .profileReportLoading: "Loading…"
''',
        "English profile localization",
    )
    return replace_once(
        text,
        '        .communityNoPosts: "Публикаций пока нет"\n',
        '''        .communityNoPosts: "Публикаций пока нет",
        .profileHistoryTab: "История",
        .presenceHistoryTab: "Присутствие",
        .giftHistoryTab: "Подарки · история",
        .personalChannelTab: "Канал",
        .profileReportLoading: "Загрузка…"
''',
        "Russian profile localization",
    )


def patch_report(text):
    if "strings.localizedProfileReport(rawText)" in text:
        return text
    return replace_once(
        text,
        '''        let text = self.reportText ?? "Загрузка…"
        let sections = Self.reportSections(text)''',
        '''        let strings = presentationData.strings.jerkgram
        let rawText = self.reportText ?? strings.profileReportLoading
        let text = strings.localizedProfileReport(rawText)
        let sections = Self.reportSections(text)''',
        "profile report render localization",
    )


def patch_tabs(text):
    if all(
        token in text
        for token in (
            "presentationData.strings.jerkgram.profileHistoryTab",
            "presentationData.strings.jerkgram.presenceHistoryTab",
            "presentationData.strings.jerkgram.giftHistoryTab",
            "presentationData.strings.jerkgram.personalChannelTab",
        )
    ):
        return text
    replacements = (
        ('text: "История"', "text: presentationData.strings.jerkgram.profileHistoryTab"),
        ('text: "Присутствие"', "text: presentationData.strings.jerkgram.presenceHistoryTab"),
        ('text: "Подарки · история"', "text: presentationData.strings.jerkgram.giftHistoryTab"),
        ('text: "Канал"', "text: presentationData.strings.jerkgram.personalChannelTab"),
    )
    for old, new in replacements:
        text = replace_once(text, old, new, "profile tab " + old)
    return text


def main():
    for path in (STRINGS, REPORT, TABS):
        require(path.is_file(), "source owner missing: " + str(path))
    STRINGS.write_text(patch_strings(STRINGS.read_text(encoding="utf-8")), encoding="utf-8")
    REPORT.write_text(patch_report(REPORT.read_text(encoding="utf-8")), encoding="utf-8")
    TABS.write_text(patch_tabs(TABS.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build117 profile localization] tabs and full reports follow Telegram language")


if __name__ == "__main__":
    main()
