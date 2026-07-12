#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"

SETTINGS = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
TIMESTAMP = SRC / "submodules/TelegramUI/Components/Chat/ChatMessageDateAndStatusNode/Sources/StringForMessageTimestampStatus.swift"
PROFILE = SRC / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"
HEADER = SRC / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderNode.swift"

def need(value, message):
    if not value:
        raise RuntimeError(f"[v1.0U] {message}")

def once(text, old, new, label):
    need(old in text, f"missing anchor: {label}")
    return text.replace(old, new, 1)

for path in (SETTINGS, TIMESTAMP, PROFILE, HEADER):
    need(path.is_file(), f"missing file: {path}")

settings = SETTINGS.read_text()

settings_marker = "GhostBase v1.0U appearance settings"

if settings_marker not in settings:
    settings = once(
        settings,
        '''    static let showEditHistory = "GhostBase.Messages.ShowEditHistory"
''',
        '''    static let showEditHistory = "GhostBase.Messages.ShowEditHistory"

    // MARK: GhostBase v1.0U appearance settings
    static let messageSeconds = "GhostBase.Appearance.MessageSeconds"
    static let hideOwnPhone = "GhostBase.Appearance.HideOwnPhone"
''',
        "appearance keys"
    )

    settings = once(
        settings,
        '''    var sendTextStyle: String

    var protectedEnabled: Bool
''',
        '''    var sendTextStyle: String

    var messageSeconds: Bool
    var hideOwnPhone: Bool

    var protectedEnabled: Bool
''',
        "appearance state"
    )

    settings = once(
        settings,
        '''            sendTextStyle: ghostBaseString(
                ghostBaseSendTextStyleKey,
                defaultValue: "normal"
            ),
''',
        '''            sendTextStyle: ghostBaseString(
                ghostBaseSendTextStyleKey,
                defaultValue: "normal"
            ),

            messageSeconds: ghostBaseBool(
                GhostBaseKey.messageSeconds,
                defaultValue: false
            ),
            hideOwnPhone: ghostBaseBool(
                GhostBaseKey.hideOwnPhone,
                defaultValue: false
            ),
''',
        "appearance state load"
    )

    settings = once(
        settings,
        '''    if page == .appearance {
        return [
            .header(0, "Внешний вид"),
            .info(0, "Настройки оформления GhostBase будут добавляться в этот раздел.")
        ]
    }
''',
        '''    if page == .appearance {
        return [
            .header(0, "Внешний вид"),
            .toggle(
                0,
                1,
                GhostBaseKey.messageSeconds,
                "Показывать секунды в сообщениях",
                state.messageSeconds
            ),
            .toggle(
                0,
                2,
                GhostBaseKey.hideOwnPhone,
                "Скрывать мой номер",
                state.hideOwnPhone
            ),
            .info(
                0,
                "Номер скрывается только локально в интерфейсе GhostBase. Экран изменения профиля и смены номера остаётся доступен."
            )
        ]
    }
''',
        "appearance page"
    )

    settings = once(
        settings,
        '''            case GhostBaseKey.showEditHistory:
                updated.showEditHistory = value

            case GhostBaseKey.chatSave:
''',
        '''            case GhostBaseKey.showEditHistory:
                updated.showEditHistory = value

            case GhostBaseKey.messageSeconds:
                updated.messageSeconds = value
                UserDefaults.standard.set(
                    value,
                    forKey: GhostBaseKey.messageSeconds
                )

            case GhostBaseKey.hideOwnPhone:
                updated.hideOwnPhone = value
                UserDefaults.standard.set(
                    value,
                    forKey: GhostBaseKey.hideOwnPhone
                )

            case GhostBaseKey.chatSave:
''',
        "appearance toggle handler"
    )

    settings = settings.replace(
        "Version: v1.0S",
        "Version: v1.0U",
        1
    )

SETTINGS.write_text(settings)

timestamp = TIMESTAMP.read_text()
timestamp_marker = "GhostBase v1.0U message seconds"

if timestamp_marker not in timestamp:
    timestamp = once(
        timestamp,
        '''    var dateText = stringForMessageTimestamp(timestamp: timestamp, dateTimeFormat: dateTimeFormat)
''',
        '''    // MARK: GhostBase v1.0U message seconds
    let ghostBaseMessageSeconds = (
        UserDefaults.standard.object(
            forKey: "GhostBase.Appearance.MessageSeconds"
        ) as? Bool
    ) ?? false

    var dateText = stringForMessageTimestamp(
        timestamp: timestamp,
        dateTimeFormat: dateTimeFormat,
        withSeconds: ghostBaseMessageSeconds
    )
''',
        "message timestamp"
    )

TIMESTAMP.write_text(timestamp)

profile = PROFILE.read_text()
profile_marker = "GhostBase v1.0U hide own phone profile"

if profile_marker not in profile:
    anchor = None

    for candidate in (
        '        if let phone = user.phone, !(SGSimpleSettings.shared.hidePhoneInSettings && isMyProfile) {\n',
        '        if let phone = user.phone {\n',
    ):
        if candidate in profile:
            anchor = candidate
            break

    need(anchor is not None, "missing anchor: profile phone row")

    replacement = """        // MARK: GhostBase v1.0U hide own phone profile
        let ghostBaseHideOwnPhone = (
            UserDefaults.standard.object(
                forKey: "GhostBase.Appearance.HideOwnPhone"
            ) as? Bool
        ) ?? false

        if let phone = user.phone, !(ghostBaseHideOwnPhone && isMyProfile) {
"""

    profile = profile.replace(anchor, replacement, 1)

PROFILE.write_text(profile)

header = HEADER.read_text()
header_marker = "GhostBase v1.0U hide own phone header"

if header_marker not in header:
    old = """            // MARK: Swiftgram
            if title.isEmpty {
                if let peer = peer as? TelegramUser, let phone = peer.phone, !self.hidePhoneInSettings {
                    title = formatPhoneNumber(context: self.context, number: phone)
                } else if let addressName = peer.addressName {
                    title = "@\\(addressName)"
                } else {
                    title = "_"
                }
            }

            titleStringText = title
            titleAttributes = MultiScaleTextState.Attributes(font: Font.medium(28.0), color: .white)
            smallTitleAttributes = MultiScaleTextState.Attributes(font: Font.medium(28.0), color: .white, shadowColor: titleShadowColor)
            
            if self.isSettings, let user = peer as? TelegramUser {
                // MARK: Swiftgram
                var formattedPhone = formatPhoneNumber(context: self.context, number: user.phone ?? "")
                if !formattedPhone.isEmpty && self.hidePhoneInSettings {
                    formattedPhone = ""
                }
"""

    new = """            // MARK: GhostBase v1.0U hide own phone header
            let ghostBaseHideOwnPhone = (
                (
                    UserDefaults.standard.object(
                        forKey: "GhostBase.Appearance.HideOwnPhone"
                    ) as? Bool
                ) ?? false
            ) && (
                self.isSettings
                || self.isMyProfile
                || peer.id == self.context.account.peerId
            )

            if title.isEmpty {
                if let peer = peer as? TelegramUser, let phone = peer.phone, !ghostBaseHideOwnPhone {
                    title = formatPhoneNumber(context: self.context, number: phone)
                } else if let addressName = peer.addressName {
                    title = "@\\(addressName)"
                } else {
                    title = "_"
                }
            }

            titleStringText = title
            titleAttributes = MultiScaleTextState.Attributes(font: Font.medium(28.0), color: .white)
            smallTitleAttributes = MultiScaleTextState.Attributes(font: Font.medium(28.0), color: .white, shadowColor: titleShadowColor)
            
            if self.isSettings, let user = peer as? TelegramUser {
                var formattedPhone = formatPhoneNumber(context: self.context, number: user.phone ?? "")
                if !formattedPhone.isEmpty && ghostBaseHideOwnPhone {
                    formattedPhone = ""
                }
"""

    need(old in header, "missing anchor: official header phone block")
    header = header.replace(old, new, 1)

HEADER.write_text(header)

need(settings_marker in SETTINGS.read_text(), "settings marker missing")
need(timestamp_marker in TIMESTAMP.read_text(), "timestamp marker missing")
need(profile_marker in PROFILE.read_text(), "profile marker missing")
need(header_marker in HEADER.read_text(), "header marker missing")

print("[v1.0U] appearance, seconds and own-phone hiding applied")
