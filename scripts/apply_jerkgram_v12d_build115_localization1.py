#!/usr/bin/env python3

from pathlib import Path
import os


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

SWIFT = r'''import Foundation
import PresentationStrings

// MARK: Jerkgram v1.2D BUILD115_LOCALIZATION_FOUNDATION1
//
// Jerkgram user-facing text must follow Telegram's selected interface
// language, not the device language. English is the canonical source and
// universal fallback. Persisted Jerkgram data must store semantic keys/enums,
// never localized display strings.
public enum JerkgramStringKey: String, CaseIterable {
    case settingsTitle
    case ghostMode
    case messages
    case protectedContent
    case mediaAndStories
    case appearance
    case debugResearch
    case about

    case information
    case telegramId
    case registrationDate

    case deletedMessage
    case editedMessage
    case sticker
    case photo
    case video
    case gif
    case audio
    case voiceMessage
    case document
    case album

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
    public var ghostMode: String { self.text(.ghostMode) }
    public var messages: String { self.text(.messages) }
    public var protectedContent: String { self.text(.protectedContent) }
    public var mediaAndStories: String { self.text(.mediaAndStories) }
    public var appearance: String { self.text(.appearance) }
    public var debugResearch: String { self.text(.debugResearch) }
    public var about: String { self.text(.about) }

    public var information: String { self.text(.information) }
    public var telegramId: String { self.text(.telegramId) }
    public var registrationDate: String { self.text(.registrationDate) }

    public var deletedMessage: String { self.text(.deletedMessage) }
    public var editedMessage: String { self.text(.editedMessage) }
    public var sticker: String { self.text(.sticker) }
    public var photo: String { self.text(.photo) }
    public var video: String { self.text(.video) }
    public var gif: String { self.text(.gif) }
    public var audio: String { self.text(.audio) }
    public var voiceMessage: String { self.text(.voiceMessage) }
    public var document: String { self.text(.document) }
    public var album: String { self.text(.album) }

    public var importSettings: String { self.text(.importSettings) }
    public var exportSettings: String { self.text(.exportSettings) }
    public var importArchive: String { self.text(.importArchive) }
    public var exportArchive: String { self.text(.exportArchive) }

    private static let english: [JerkgramStringKey: String] = [
        .settingsTitle: "Jerkgram",
        .ghostMode: "Ghost Mode",
        .messages: "Messages",
        .protectedContent: "Protected Content",
        .mediaAndStories: "Media & Stories",
        .appearance: "Appearance",
        .debugResearch: "Debug / Research",
        .about: "About",

        .information: "Information",
        .telegramId: "Telegram ID",
        .registrationDate: "Registration Date",

        .deletedMessage: "Deleted Message",
        .editedMessage: "Edited Message",
        .sticker: "Sticker",
        .photo: "Photo",
        .video: "Video",
        .gif: "GIF",
        .audio: "Audio",
        .voiceMessage: "Voice Message",
        .document: "Document",
        .album: "Album",

        .importSettings: "Import Settings",
        .exportSettings: "Export Settings",
        .importArchive: "Import Jerkgram Archive",
        .exportArchive: "Export Jerkgram Archive"
    ]

    private static let russian: [JerkgramStringKey: String] = [
        .settingsTitle: "Jerkgram",
        .ghostMode: "Режим призрака",
        .messages: "Сообщения",
        .protectedContent: "Защищённый контент",
        .mediaAndStories: "Медиа и истории",
        .appearance: "Оформление",
        .debugResearch: "Отладка / Исследования",
        .about: "О Jerkgram",

        .information: "Сведения",
        .telegramId: "Telegram ID",
        .registrationDate: "Дата регистрации",

        .deletedMessage: "Удалённое сообщение",
        .editedMessage: "Изменённое сообщение",
        .sticker: "Стикер",
        .photo: "Фото",
        .video: "Видео",
        .gif: "GIF",
        .audio: "Аудио",
        .voiceMessage: "Голосовое сообщение",
        .document: "Документ",
        .album: "Альбом",

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
        print(
            "[Build115 localization] already installed"
        )
        return

    TARGET.write_text(
        SWIFT,
        encoding="utf-8"
    )

    print(
        "[Build115 localization] JerkgramStrings installed"
    )
    print(
        "[Build115 localization] language owner: "
        "PresentationStrings.baseLanguageCode"
    )
    print(
        "[Build115 localization] English canonical/fallback + Russian"
    )


if __name__ == "__main__":
    main()
