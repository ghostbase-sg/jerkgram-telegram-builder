#!/usr/bin/env python3

from pathlib import Path
import os


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

SWIFT = r'''import Foundation
import PresentationStrings

// MARK: Jerkgram v1.2D BUILD115_LOCALIZATION_FOUNDATION1
//
// Jerkgram user-facing text follows Telegram's selected interface language,
// never the device locale. English is the canonical source and universal
// fallback. Persisted Jerkgram data stores semantic values, not translations.
public enum JerkgramStringKey: String, CaseIterable {
    case settingsTitle
    case basicFunctions
    case ghostMode
    case messages
    case protectedContent
    case mediaAndStories
    case appearance
    case debugResearch
    case about

    case profileCard
    case showIds
    case showDcs
    case registrationDate
    case localStarsBalance
    case starsBalance
    case currentVisualBalance

    case readGhost
    case typing
    case recording
    case uploading
    case choosingSticker
    case gameActivity
    case choosingEmoji
    case hideOnline
    case scheduledSend

    case deletedMessages
    case saveDeletedMessages
    case showDeletedMessages
    case editHistory
    case saveEditHistory
    case showEditHistory
    case savedDataHint
    case textSending
    case sendStyle
    case sendStyleHint
    case deletedReplies
    case portableReply
    case saveDeletedMedia
    case portableReplyHint

    case protectionEnabled
    case shareFromGallery
    case saveFromGallery
    case copyFromGallery
    case saveFromChat
    case copyFromChat
    case forwardFromChat
    case allowScreenshots
    case allowScreenRecording

    case oneTimeScreenshots
    case oneTimeScreenRecording
    case oneTimeSave
    case oneTimeMedia
    case storySave
    case appearancePlaceholder
    case profileBackground
    case profileBackgroundEffect
    case blurProfileAvatar
    case preferAvatarAsBackground
    case animatedBackground
    case colorTint
    case reducedBlur
    case animatedBackgroundHint
    case profileEffectDisabledHint
    case other
    case interface
    case messageSeconds
    case hideMyPhone
    case showRamUnderClock
    case hidePhoneHint
    case presenceHistoryEmpty
    case knownUsersNoData
    case recentEvents
    case eventsEmpty
    case diagnosticsBufferHint

    case information
    case telegramId
    case rawIdNamespace
    case profile
    case mainMenu

    case deletedMessage
    case editedMessage
    case sticker
    case photo
    case video
    case gif
    case audio
    case voiceMessage
    case videoMessage
    case document
    case attachment
    case album
    case poll
    case location
    case contact
    case dice
    case taskList
    case user

    case importSettings
    case exportSettings
    case importArchive
    case exportArchive
}

public struct JerkgramStrings {
    public let languageCode: String

    public init(baseLanguageCode: String) {
        var value = baseLanguageCode.lowercased()

        let rawSuffix = "-raw"
        if value.hasSuffix(rawSuffix) {
            value = String(value.dropLast(rawSuffix.count))
        }

        if let separator = value.firstIndex(where: { character in
            character == "-" || character == "_"
        }) {
            value = String(value[..<separator])
        }

        self.languageCode = value
    }

    public func text(_ key: JerkgramStringKey) -> String {
        if self.languageCode == "ru",
           let value = Self.russian[key] {
            return value
        }

        return Self.english[key]!
    }

    public var settingsTitle: String { self.text(.settingsTitle) }
    public var basicFunctions: String { self.text(.basicFunctions) }
    public var ghostMode: String { self.text(.ghostMode) }
    public var messages: String { self.text(.messages) }
    public var protectedContent: String { self.text(.protectedContent) }
    public var mediaAndStories: String { self.text(.mediaAndStories) }
    public var appearance: String { self.text(.appearance) }
    public var debugResearch: String { self.text(.debugResearch) }
    public var about: String { self.text(.about) }

    public var profileCard: String { self.text(.profileCard) }
    public var showIds: String { self.text(.showIds) }
    public var showDcs: String { self.text(.showDcs) }
    public var registrationDate: String { self.text(.registrationDate) }
    public var localStarsBalance: String { self.text(.localStarsBalance) }
    public var starsBalance: String { self.text(.starsBalance) }
    public func currentVisualBalance(_ balance: String) -> String {
        return self.text(.currentVisualBalance).replacingOccurrences(
            of: "{balance}",
            with: balance
        )
    }

    public var readGhost: String { self.text(.readGhost) }
    public var typing: String { self.text(.typing) }
    public var recording: String { self.text(.recording) }
    public var uploading: String { self.text(.uploading) }
    public var choosingSticker: String { self.text(.choosingSticker) }
    public var gameActivity: String { self.text(.gameActivity) }
    public var choosingEmoji: String { self.text(.choosingEmoji) }
    public var hideOnline: String { self.text(.hideOnline) }
    public var scheduledSend: String { self.text(.scheduledSend) }

    public var deletedMessages: String { self.text(.deletedMessages) }
    public var saveDeletedMessages: String { self.text(.saveDeletedMessages) }
    public var showDeletedMessages: String { self.text(.showDeletedMessages) }
    public var editHistory: String { self.text(.editHistory) }
    public var saveEditHistory: String { self.text(.saveEditHistory) }
    public var showEditHistory: String { self.text(.showEditHistory) }
    public var savedDataHint: String { self.text(.savedDataHint) }
    public var textSending: String { self.text(.textSending) }
    public var sendStyle: String { self.text(.sendStyle) }
    public var sendStyleHint: String { self.text(.sendStyleHint) }
    public var deletedReplies: String { self.text(.deletedReplies) }
    public var portableReply: String { self.text(.portableReply) }
    public var saveDeletedMedia: String { self.text(.saveDeletedMedia) }
    public var portableReplyHint: String { self.text(.portableReplyHint) }

    public var protectionEnabled: String { self.text(.protectionEnabled) }
    public var shareFromGallery: String { self.text(.shareFromGallery) }
    public var saveFromGallery: String { self.text(.saveFromGallery) }
    public var copyFromGallery: String { self.text(.copyFromGallery) }
    public var saveFromChat: String { self.text(.saveFromChat) }
    public var copyFromChat: String { self.text(.copyFromChat) }
    public var forwardFromChat: String { self.text(.forwardFromChat) }
    public var allowScreenshots: String { self.text(.allowScreenshots) }
    public var allowScreenRecording: String { self.text(.allowScreenRecording) }

    public var oneTimeScreenshots: String { self.text(.oneTimeScreenshots) }
    public var oneTimeScreenRecording: String { self.text(.oneTimeScreenRecording) }
    public var oneTimeSave: String { self.text(.oneTimeSave) }
    public var oneTimeMedia: String { self.text(.oneTimeMedia) }
    public var storySave: String { self.text(.storySave) }
    public var appearancePlaceholder: String { self.text(.appearancePlaceholder) }
    public var profileBackground: String { self.text(.profileBackground) }
    public var profileBackgroundEffect: String { self.text(.profileBackgroundEffect) }
    public var blurProfileAvatar: String { self.text(.blurProfileAvatar) }
    public var preferAvatarAsBackground: String { self.text(.preferAvatarAsBackground) }
    public var animatedBackground: String { self.text(.animatedBackground) }
    public var colorTint: String { self.text(.colorTint) }
    public var reducedBlur: String { self.text(.reducedBlur) }
    public var animatedBackgroundHint: String { self.text(.animatedBackgroundHint) }
    public var profileEffectDisabledHint: String { self.text(.profileEffectDisabledHint) }
    public var other: String { self.text(.other) }
    public var interface: String { self.text(.interface) }
    public var messageSeconds: String { self.text(.messageSeconds) }
    public var hideMyPhone: String { self.text(.hideMyPhone) }
    public var showRamUnderClock: String { self.text(.showRamUnderClock) }
    public var hidePhoneHint: String { self.text(.hidePhoneHint) }
    public var presenceHistoryEmpty: String { self.text(.presenceHistoryEmpty) }
    public var knownUsersNoData: String { self.text(.knownUsersNoData) }
    public var recentEvents: String { self.text(.recentEvents) }
    public var eventsEmpty: String { self.text(.eventsEmpty) }
    public var diagnosticsBufferHint: String { self.text(.diagnosticsBufferHint) }

    public var information: String { self.text(.information) }
    public var telegramId: String { self.text(.telegramId) }
    public var rawIdNamespace: String { self.text(.rawIdNamespace) }
    public var profile: String { self.text(.profile) }
    public var mainMenu: String { self.text(.mainMenu) }

    public var deletedMessage: String { self.text(.deletedMessage) }
    public var editedMessage: String { self.text(.editedMessage) }
    public var sticker: String { self.text(.sticker) }
    public var photo: String { self.text(.photo) }
    public var video: String { self.text(.video) }
    public var gif: String { self.text(.gif) }
    public var audio: String { self.text(.audio) }
    public var voiceMessage: String { self.text(.voiceMessage) }
    public var videoMessage: String { self.text(.videoMessage) }
    public var document: String { self.text(.document) }
    public var attachment: String { self.text(.attachment) }
    public var album: String { self.text(.album) }
    public var poll: String { self.text(.poll) }
    public var location: String { self.text(.location) }
    public var contact: String { self.text(.contact) }
    public var dice: String { self.text(.dice) }
    public var taskList: String { self.text(.taskList) }
    public var user: String { self.text(.user) }

    public var importSettings: String { self.text(.importSettings) }
    public var exportSettings: String { self.text(.exportSettings) }
    public var importArchive: String { self.text(.importArchive) }
    public var exportArchive: String { self.text(.exportArchive) }

    private static let english: [JerkgramStringKey: String] = [
        .settingsTitle: "Jerkgram",
        .basicFunctions: "Basic Functions",
        .ghostMode: "Ghost Mode",
        .messages: "Messages",
        .protectedContent: "Protected Content",
        .mediaAndStories: "Media & Stories",
        .appearance: "Appearance",
        .debugResearch: "Debug / Research",
        .about: "About",

        .profileCard: "Profile Card",
        .showIds: "Show IDs",
        .showDcs: "Show DCs",
        .registrationDate: "Registration Date",
        .localStarsBalance: "Local Stars Balance",
        .starsBalance: "Stars Balance",
        .currentVisualBalance: "Current visual balance: {balance} ⭐",

        .readGhost: "Don't Mark as Read",
        .typing: "Typing",
        .recording: "Recording",
        .uploading: "Uploading",
        .choosingSticker: "Choosing Sticker",
        .gameActivity: "Game Activity",
        .choosingEmoji: "Choosing Emoji",
        .hideOnline: "Online Status",
        .scheduledSend: "Scheduled Send",

        .deletedMessages: "Deleted Messages",
        .saveDeletedMessages: "Save Deleted",
        .showDeletedMessages: "Show Deleted Messages",
        .editHistory: "Edit History",
        .saveEditHistory: "Save Edit History",
        .showEditHistory: "Show Edit History",
        .savedDataHint: "Disabling these features does not remove already saved data.",
        .textSending: "Text Sending",
        .sendStyle: "Send Style",
        .sendStyleHint: "The style is applied after tapping the send button.",
        .deletedReplies: "Deleted Replies",
        .portableReply: "Portable Reply",
        .saveDeletedMedia: "Save Deleted Media",
        .portableReplyHint: "The reply is materialized only after Send. Media is kept only in Jerkgram's internal cache: up to 1 GB for 30 days; if bytes are unavailable, a text fallback is used.",

        .protectionEnabled: "Bypass Protection",
        .shareFromGallery: "Share from Gallery",
        .saveFromGallery: "Save from Gallery",
        .copyFromGallery: "Copy from Gallery",
        .saveFromChat: "Save from Chat",
        .copyFromChat: "Copy from Chat",
        .forwardFromChat: "Forward from Chat",
        .allowScreenshots: "Allow Screenshots",
        .allowScreenRecording: "Allow Screen Recording",

        .oneTimeScreenshots: "One-Time Media Screenshots",
        .oneTimeScreenRecording: "One-Time Media Screen Recording",
        .oneTimeSave: "Save One-Time Media",
        .oneTimeMedia: "One-Time Media",
        .storySave: "Save Stories",
        .appearancePlaceholder: "Jerkgram appearance settings will be added here.",
        .profileBackground: "Profile Background",
        .profileBackgroundEffect: "Profile Background Effect",
        .blurProfileAvatar: "Blur Profile Avatar",
        .preferAvatarAsBackground: "Prefer Avatar as Background",
        .animatedBackground: "Animated Background",
        .colorTint: "Color Tint",
        .reducedBlur: "Reduced Blur",
        .animatedBackgroundHint: "The video avatar loops and uses Telegram's cache. In Low Power Mode or with Reduced Blur, a static frame is used.",
        .profileEffectDisabledHint: "When the main effect is disabled, Jerkgram creates no additional profile views, observers, or image/palette pipeline. New values apply the next time the profile opens.",
        .other: "Other",
        .interface: "Interface",
        .messageSeconds: "Message Seconds",
        .hideMyPhone: "Hide My Phone Number",
        .showRamUnderClock: "Show RAM Under Clock",
        .hidePhoneHint: "Your phone number is hidden only locally in Jerkgram. Profile editing and number changing remain available.",
        .presenceHistoryEmpty: "Presence history is empty",
        .knownUsersNoData: "Known users: no data",
        .recentEvents: "Recent Events",
        .eventsEmpty: "No events yet",
        .diagnosticsBufferHint: "The buffer is limited to 200 lines. Collection does not start when this page opens.",

        .information: "Information",
        .telegramId: "Telegram ID",
        .rawIdNamespace: "Raw ID / Namespace",
        .profile: "Profile",
        .mainMenu: "Main Menu",

        .deletedMessage: "Deleted Message",
        .editedMessage: "Edited Message",
        .sticker: "Sticker",
        .photo: "Photo",
        .video: "Video",
        .gif: "GIF",
        .audio: "Audio",
        .voiceMessage: "Voice Message",
        .videoMessage: "Video Message",
        .document: "Document",
        .attachment: "Attachment",
        .album: "Album",
        .poll: "Poll",
        .location: "Location",
        .contact: "Contact",
        .dice: "Dice",
        .taskList: "Task List",
        .user: "User",

        .importSettings: "Import Settings",
        .exportSettings: "Export Settings",
        .importArchive: "Import Jerkgram Archive",
        .exportArchive: "Export Jerkgram Archive"
    ]

    private static let russian: [JerkgramStringKey: String] = [
        .settingsTitle: "Jerkgram",
        .basicFunctions: "Основные функции",
        .ghostMode: "Режим призрака",
        .messages: "Сообщения",
        .protectedContent: "Защищённый контент",
        .mediaAndStories: "Медиа и истории",
        .appearance: "Оформление",
        .debugResearch: "Отладка / Исследования",
        .about: "О Jerkgram",

        .profileCard: "Карточка профиля",
        .showIds: "Показывать ID",
        .showDcs: "Показывать DC",
        .registrationDate: "Дата регистрации",
        .localStarsBalance: "Локальный баланс Stars",
        .starsBalance: "Баланс Stars",
        .currentVisualBalance: "Текущий визуальный баланс: {balance} ⭐",

        .readGhost: "Не отмечать прочитанным",
        .typing: "Набор текста",
        .recording: "Запись",
        .uploading: "Загрузка",
        .choosingSticker: "Выбор стикера",
        .gameActivity: "Игровая активность",
        .choosingEmoji: "Выбор эмодзи",
        .hideOnline: "Онлайн-статус",
        .scheduledSend: "Отложенная отправка",

        .deletedMessages: "Удалённые сообщения",
        .saveDeletedMessages: "Сохранять удалённые",
        .showDeletedMessages: "Показывать удалённые сообщения",
        .editHistory: "История изменений",
        .saveEditHistory: "Сохранять историю изменений",
        .showEditHistory: "Показывать историю изменений",
        .savedDataHint: "Выключение функций не удаляет уже сохранённые данные.",
        .textSending: "Отправка текста",
        .sendStyle: "Стиль отправки",
        .sendStyleHint: "Стиль применяется после нажатия кнопки отправки.",
        .deletedReplies: "Удалённые ответы",
        .portableReply: "Переносимый ответ",
        .saveDeletedMedia: "Сохранять удалённые медиа",
        .portableReplyHint: "Ответ материализуется только после Send. Медиа хранится только во внутреннем кэше Jerkgram: до 1 ГБ, 30 дней; если bytes недоступны, используется текстовый fallback.",

        .protectionEnabled: "Включить обход защиты",
        .shareFromGallery: "Поделиться из галереи",
        .saveFromGallery: "Сохранить из галереи",
        .copyFromGallery: "Копировать из галереи",
        .saveFromChat: "Сохранить из чата",
        .copyFromChat: "Копировать из чата",
        .forwardFromChat: "Переслать из чата",
        .allowScreenshots: "Разрешить скриншоты",
        .allowScreenRecording: "Разрешить запись экрана",

        .oneTimeScreenshots: "Скриншоты одноразовых медиа",
        .oneTimeScreenRecording: "Запись одноразовых медиа",
        .oneTimeSave: "Сохранение одноразовых медиа",
        .oneTimeMedia: "Одноразовые медиа",
        .storySave: "Сохранение историй",
        .appearancePlaceholder: "Настройки оформления Jerkgram будут добавляться в этот раздел.",
        .profileBackground: "Фон профиля",
        .profileBackgroundEffect: "Эффект фона профиля",
        .blurProfileAvatar: "Размывать аватар в профиле",
        .preferAvatarAsBackground: "Предпочитать аватар как фон",
        .animatedBackground: "Анимированный фон",
        .colorTint: "Цветовой оттенок",
        .reducedBlur: "Облегчённое размытие",
        .animatedBackgroundHint: "Видеоаватар зацикливается и использует кэш Telegram. В режиме энергосбережения или облегчённого размытия используется статический кадр.",
        .profileEffectDisabledHint: "Когда главный эффект выключен, Jerkgram не создаёт дополнительные profile views, observers или image/palette pipeline. Новые значения применяются при следующем открытии профиля.",
        .other: "Прочее",
        .interface: "Интерфейс",
        .messageSeconds: "Секунды в сообщениях",
        .hideMyPhone: "Скрывать мой номер",
        .showRamUnderClock: "Показывать RAM под часами",
        .hidePhoneHint: "Номер скрывается только локально в интерфейсе Jerkgram. Экран изменения профиля и смены номера остаётся доступен.",
        .presenceHistoryEmpty: "История присутствия пока пуста",
        .knownUsersNoData: "Известные пользователи: нет данных",
        .recentEvents: "Последние события",
        .eventsEmpty: "Событий пока нет",
        .diagnosticsBufferHint: "Буфер ограничен 200 строками. Сбор не запускается при открытии этой страницы.",

        .information: "Сведения",
        .telegramId: "Telegram ID",
        .rawIdNamespace: "Raw ID / Namespace",
        .profile: "Профиль",
        .mainMenu: "Главное меню",

        .deletedMessage: "Удалённое сообщение",
        .editedMessage: "Изменённое сообщение",
        .sticker: "Стикер",
        .photo: "Фото",
        .video: "Видео",
        .gif: "GIF",
        .audio: "Аудио",
        .voiceMessage: "Голосовое сообщение",
        .videoMessage: "Видеосообщение",
        .document: "Документ",
        .attachment: "Вложение",
        .album: "Альбом",
        .poll: "Опрос",
        .location: "Геолокация",
        .contact: "Контакт",
        .dice: "Бросок кубика",
        .taskList: "Список задач",
        .user: "Пользователь",

        .importSettings: "Импорт настроек",
        .exportSettings: "Экспорт настроек",
        .importArchive: "Импорт архива Jerkgram",
        .exportArchive: "Экспорт архива Jerkgram"
    ]
}

public extension PresentationStrings {
    var jerkgram: JerkgramStrings {
        return JerkgramStrings(
            baseLanguageCode: self.baseLanguageCode
        )
    }
}
'''


def require(value, message):
    if not value:
        raise RuntimeError(
            "[Build115 localization] "
            + message
        )


def main():
    require(
        TARGET.parent.is_dir(),
        "TelegramPresentationData/Sources missing"
    )

    if TARGET.exists():
        text = TARGET.read_text(encoding="utf-8")
        require(
            MARKER in text,
            "unexpected existing JerkgramStrings.swift"
        )
        print("[Build115 localization] already installed")
        return

    TARGET.write_text(SWIFT, encoding="utf-8")

    print("[Build115 localization] JerkgramStrings installed")
    print(
        "[Build115 localization] language owner: "
        "PresentationStrings.baseLanguageCode"
    )
    print(
        "[Build115 localization] English canonical/fallback + Russian"
    )


if __name__ == "__main__":
    main()
