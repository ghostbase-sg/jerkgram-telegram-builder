#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

path = root / (
    "submodules/TelegramCore/Sources/TelegramEngine/Peers/"
    "TelegramEnginePeers.swift"
)

if not path.is_file():
    raise SystemExit(f"[PROFILEINTEL2] missing TelegramEnginePeers: {path}")

text = path.read_text(encoding="utf-8")
marker = "// MARK: GhostBase v1.0ZF PROFILEINTEL2 Core"


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[PROFILEINTEL2] {message}")


require(
    "// MARK: GhostBase v1.0ZD PROFILEINTEL1 Core" in text,
    "PROFILEINTEL1 must be applied first"
)

if marker not in text:
    helper_anchor = "public extension TelegramEngine {\n"
    require(text.count(helper_anchor) == 1, "TelegramEngine extension anchor mismatch")

    helpers = r'''// MARK: GhostBase v1.0ZF PROFILEINTEL2 Core

private struct GhostBaseProfileIntel2Security {
    let registrationMonth: String?
    let phoneCountry: String?
    let nameChangeDate: Int32?
    let photoChangeDate: Int32?
}

private struct GhostBaseProfileIntel2Status {
    let kind: String
    let timestamp: Int32?
    let report: String
    let reliability: String
}

private func ghostBaseProfileIntel2Clean(_ value: String?) -> String {
    guard let value else {
        return "nil"
    }
    return value
        .replacingOccurrences(of: "\\", with: "\\\\")
        .replacingOccurrences(of: "\n", with: "\\n")
        .replacingOccurrences(of: "\r", with: "\\r")
        .replacingOccurrences(of: "=", with: "\\=")
}

private func ghostBaseProfileIntel2Security(
    _ settings: Api.PeerSettings?
) -> GhostBaseProfileIntel2Security {
    guard let settings else {
        return GhostBaseProfileIntel2Security(
            registrationMonth: nil,
            phoneCountry: nil,
            nameChangeDate: nil,
            photoChangeDate: nil
        )
    }

    switch settings {
    case let .peerSettings(data):
        return GhostBaseProfileIntel2Security(
            registrationMonth:
                (data.flags & (1 << 15)) != 0
                ? data.registrationMonth
                : nil,
            phoneCountry:
                (data.flags & (1 << 16)) != 0
                ? data.phoneCountry
                : nil,
            nameChangeDate:
                (data.flags & (1 << 17)) != 0
                ? data.nameChangeDate
                : nil,
            photoChangeDate:
                (data.flags & (1 << 18)) != 0
                ? data.photoChangeDate
                : nil
        )
    }
}

private func ghostBaseProfileIntel2Status(
    _ user: Api.User?
) -> GhostBaseProfileIntel2Status {
    guard let user else {
        return GhostBaseProfileIntel2Status(
            kind: "missing",
            timestamp: nil,
            report: "user missing",
            reliability: "Недоступно"
        )
    }

    switch user {
    case .userEmpty:
        return GhostBaseProfileIntel2Status(
            kind: "empty",
            timestamp: nil,
            report: "user empty",
            reliability: "Недоступно"
        )

    case let .user(data):
        guard let status = data.status else {
            return GhostBaseProfileIntel2Status(
                kind: "nil",
                timestamp: nil,
                report: "status nil",
                reliability: "Недоступно"
            )
        }

        switch status {
        case .userStatusEmpty:
            return GhostBaseProfileIntel2Status(
                kind: "empty",
                timestamp: nil,
                report: "status empty",
                reliability: "Недоступно"
            )

        case let .userStatusOnline(value):
            return GhostBaseProfileIntel2Status(
                kind: "online",
                timestamp: value.expires,
                report: "online expires=\(value.expires)",
                reliability: "Наблюдалось"
            )

        case let .userStatusOffline(value):
            return GhostBaseProfileIntel2Status(
                kind: "offline",
                timestamp: value.wasOnline,
                report: "offline wasOnline=\(value.wasOnline)",
                reliability: "Точно"
            )

        case let .userStatusRecently(value):
            return GhostBaseProfileIntel2Status(
                kind: "recently",
                timestamp: nil,
                report: "recently flags=\(value.flags) bit0IsHidden=\((value.flags & 1) != 0)",
                reliability: "Приблизительно"
            )

        case let .userStatusLastWeek(value):
            return GhostBaseProfileIntel2Status(
                kind: "lastWeek",
                timestamp: nil,
                report: "lastWeek flags=\(value.flags) bit0IsHidden=\((value.flags & 1) != 0)",
                reliability: "Приблизительно"
            )

        case let .userStatusLastMonth(value):
            return GhostBaseProfileIntel2Status(
                kind: "lastMonth",
                timestamp: nil,
                report: "lastMonth flags=\(value.flags) bit0IsHidden=\((value.flags & 1) != 0)",
                reliability: "Приблизительно"
            )
        }
    }
}

private func ghostBaseProfileIntel2Canonical(
    _ fields: [String: String]
) -> String {
    return fields.keys.sorted().map { key in
        return "\(key)=\(fields[key] ?? "")"
    }.joined(separator: "\n")
}

private func ghostBaseProfileIntel2ParseCanonical(
    _ value: String
) -> [String: String] {
    var result: [String: String] = [:]
    for line in value.split(separator: "\n", omittingEmptySubsequences: false) {
        guard let separator = line.firstIndex(of: "=") else {
            continue
        }
        let key = String(line[..<separator])
        let rawValue = String(line[line.index(after: separator)...])
        result[key] = rawValue
    }
    return result
}

private func ghostBaseProfileIntel2AppendHistory(
    defaults: UserDefaults,
    key: String,
    events: [String],
    timestamp: String
) -> String {
    var lines: [String] = []
    for event in events {
        lines.append("\(timestamp) · \(event)")
    }

    if let previous = defaults.string(forKey: key), !previous.isEmpty {
        lines.append(contentsOf: previous.split(separator: "\n").map(String.init))
    }

    let limited = Array(lines.prefix(120))
    let result = limited.joined(separator: "\n")
    defaults.set(result, forKey: key)
    return result
}

private func ghostBaseProfileIntel2DifferenceEvents(
    previous: [String: String],
    current: [String: String]
) -> [String] {
    var events: [String] = []

    func changed(
        _ key: String,
        title: String,
        reliability: String = "Обнаружено позже"
    ) {
        let oldValue = previous[key] ?? "nil"
        let newValue = current[key] ?? "nil"
        if oldValue != newValue {
            events.append(
                "[\(reliability)] \(title): \(oldValue) → \(newValue)"
            )
        }
    }

    changed("displayName", title: "Имя")
    changed("firstName", title: "Имя (поле)")
    changed("lastName", title: "Фамилия")
    changed("username", title: "Основной username")
    changed("usernames", title: "Публичные usernames")
    changed("about", title: "BIO")
    changed("photoFingerprint", title: "Текущая фотография")
    changed("emojiStatus", title: "Emoji-status")
    changed("premium", title: "Premium")
    changed("userFlags", title: "Служебные флаги")

    let oldStatus = previous["statusKind"] ?? "missing"
    let newStatus = current["statusKind"] ?? "missing"
    if oldStatus != newStatus {
        if newStatus == "online" {
            events.append("[Наблюдалось] Вошёл в сеть")
        } else if newStatus == "offline" {
            let timestamp = current["statusTimestamp"] ?? "nil"
            events.append("[Точно] Вышел из сети: \(timestamp)")
        } else {
            events.append(
                "[Приблизительно] Статус: \(oldStatus) → \(newStatus)"
            )
        }
    }

    for (key, title) in [
        ("registrationMonth", "Месяц регистрации"),
        ("phoneCountry", "Страна телефонного номера"),
        ("nameChangeDate", "Дата изменения имени"),
        ("photoChangeDate", "Дата изменения фото"),
    ] {
        let oldValue = previous[key] ?? "nil"
        let newValue = current[key] ?? "nil"
        if oldValue != newValue, newValue != "nil" {
            events.append("[Точно] \(title): \(newValue)")
        }
    }

    changed(
        "serverPhotoDates",
        title: "Серверная история фотографий",
        reliability: "Точно"
    )

    return events
}

'''
    text = text.replace(helper_anchor, helpers + helper_anchor, 1)

    method_anchor = "        public func ghostBaseProfileIntelProbe(\n"
    require(method_anchor in text, "PROFILEINTEL1 method anchor missing")

    method = r'''        public func ghostBaseProfileIntel2Snapshot(
            username rawUsername: String
        ) -> Signal<String, NoError> {
            let username = ghostBaseProfileIntelNormalizedUsername(rawUsername)

            guard !username.isEmpty else {
                return .single("PROFILEINTEL2\nerror: EMPTY_USERNAME")
            }

            return _internal_resolvePeerByName(
                account: self.account,
                name: username,
                referrer: nil,
                ageLimit: 0
            )
            |> mapToSignal { result -> Signal<String, NoError> in
                switch result {
                case .progress:
                    return .complete()

                case let .result(peerId):
                    guard let peerId else {
                        return .single("PROFILEINTEL2\ntarget: @\(username)\nresolve: not found")
                    }

                    return self.account.postbox.transaction {
                        transaction -> (TelegramUser?, Api.InputUser?) in
                        let user = transaction.getPeer(peerId) as? TelegramUser
                        return (user, user.flatMap(apiInputUser))
                    }
                    |> mapToSignal { user, inputUser -> Signal<String, NoError> in
                        guard let user, let inputUser else {
                            return .single("""
                            PROFILEINTEL2
                            target: @\(username)
                            peerId: \(String(describing: peerId))
                            error: INPUT_USER_UNAVAILABLE
                            """)
                        }

                        let fullUser = self.account.network.request(
                            Api.functions.users.getFullUser(id: inputUser),
                            automaticFloodWait: false
                        )
                        |> map(Optional.init)
                        |> `catch` { _ -> Signal<Api.users.UserFull?, NoError> in
                            return .single(nil)
                        }

                        let photos = _internal_requestPeerPhotos(
                            accountPeerId: self.account.peerId,
                            postbox: self.account.postbox,
                            network: self.account.network,
                            peerId: peerId
                        )

                        return combineLatest(fullUser, photos)
                        |> map { fullUser, photos -> String in
                            var about: String? = nil
                            var settings: Api.PeerSettings? = nil
                            var apiUser: Api.User? = nil
                            var fullSuccess = false

                            if let fullUser {
                                switch fullUser {
                                case let .userFull(data):
                                    fullSuccess = true
                                    apiUser = data.users.first(where: {
                                        $0.peerId == peerId
                                    })
                                    switch data.fullUser {
                                    case let .userFull(value):
                                        about = value.about
                                        settings = value.settings
                                    }
                                }
                            }

                            let security = ghostBaseProfileIntel2Security(settings)
                            let status = ghostBaseProfileIntel2Status(apiUser)
                            let photoFingerprint = user.photo.map {
                                $0.resource.id.stringRepresentation
                            }.joined(separator: ",")
                            let usernames = user.usernames.map {
                                "\($0.flags.rawValue):\($0.username)"
                            }.joined(separator: ",")
                            let photoDates = photos.map {
                                String($0.date)
                            }.joined(separator: ",")
                            let photoTotal = photos.first?.totalCount ?? photos.count

                            let fields: [String: String] = [
                                "displayName": ghostBaseProfileIntel2Clean(user.nameOrPhone),
                                "firstName": ghostBaseProfileIntel2Clean(user.firstName),
                                "lastName": ghostBaseProfileIntel2Clean(user.lastName),
                                "username": ghostBaseProfileIntel2Clean(user.username),
                                "usernames": ghostBaseProfileIntel2Clean(usernames),
                                "about": ghostBaseProfileIntel2Clean(about),
                                "photoFingerprint": ghostBaseProfileIntel2Clean(photoFingerprint),
                                "emojiStatus": ghostBaseProfileIntel2Clean(String(describing: user.emojiStatus)),
                                "premium": user.flags.contains(.isPremium) ? "true" : "false",
                                "userFlags": String(user.flags.rawValue),
                                "isBot": user.botInfo == nil ? "false" : "true",
                                "statusKind": status.kind,
                                "statusTimestamp": status.timestamp.map(String.init) ?? "nil",
                                "registrationMonth": ghostBaseProfileIntel2Clean(security.registrationMonth),
                                "phoneCountry": ghostBaseProfileIntel2Clean(security.phoneCountry),
                                "nameChangeDate": security.nameChangeDate.map(String.init) ?? "nil",
                                "photoChangeDate": security.photoChangeDate.map(String.init) ?? "nil",
                                "serverPhotoDates": ghostBaseProfileIntel2Clean(photoDates),
                                "serverPhotoCount": String(photoTotal),
                            ]

                            let canonical = ghostBaseProfileIntel2Canonical(fields)
                            let defaults = UserDefaults.standard
                            let baseKey = "GhostBase.ProfileIntel2.\(self.account.peerId.toInt64()).\(peerId.toInt64())."
                            let snapshotKey = baseKey + "Snapshot"
                            let historyKey = baseKey + "History"
                            let startedKey = baseKey + "Started"
                            let sessionStartKey = baseKey + "SessionStart"
                            let now = Int64(Date().timeIntervalSince1970)
                            let nowText = ISO8601DateFormatter().string(from: Date())

                            var events: [String] = []
                            if let previousCanonical = defaults.string(forKey: snapshotKey),
                               !previousCanonical.isEmpty {
                                let previous = ghostBaseProfileIntel2ParseCanonical(previousCanonical)
                                events.append(contentsOf: ghostBaseProfileIntel2DifferenceEvents(
                                    previous: previous,
                                    current: fields
                                ))

                                let previousStatus = previous["statusKind"] ?? "missing"
                                if previousStatus == "online", status.kind == "offline" {
                                    let start = defaults.object(forKey: sessionStartKey) as? NSNumber
                                    if let start {
                                        let end = Int64(status.timestamp ?? Int32(now))
                                        let seconds = max(Int64(0), end - start.int64Value)
                                        events.append(
                                            "[Наблюдалось] Наблюдаемая сессия: \(seconds / 60) мин."
                                        )
                                    }
                                    defaults.removeObject(forKey: sessionStartKey)
                                }
                            } else {
                                defaults.set(nowText, forKey: startedKey)
                                events.append("[Наблюдалось] Наблюдение начато")
                            }

                            if status.kind == "online",
                               defaults.object(forKey: sessionStartKey) == nil {
                                defaults.set(NSNumber(value: now), forKey: sessionStartKey)
                            }

                            if events.isEmpty {
                                events.append("[Наблюдалось] Изменений с прошлого снимка нет")
                            }

                            defaults.set(canonical, forKey: snapshotKey)
                            defaults.set(nowText, forKey: baseKey + "Updated")
                            let history = ghostBaseProfileIntel2AppendHistory(
                                defaults: defaults,
                                key: historyKey,
                                events: events,
                                timestamp: nowText
                            )

                            let started = defaults.string(forKey: startedKey) ?? nowText
                            let latestPhotoDate = photos.first?.date

                            return """
                            PROFILEINTEL2
                            target: @\(username)
                            peerId: \(String(describing: peerId))
                            fullUserSuccess: \(fullSuccess)

                            SNAPSHOT
                            name: \(user.nameOrPhone)
                            firstName: \(user.firstName ?? "nil")
                            lastName: \(user.lastName ?? "nil")
                            username: \(user.username ?? "nil")
                            usernames: \(usernames.isEmpty ? "nil" : usernames)
                            about: \(about ?? "nil")
                            premium: \(user.flags.contains(.isPremium))
                            bot: \(user.botInfo != nil)
                            userFlags: \(user.flags.rawValue)
                            emojiStatus: \(String(describing: user.emojiStatus))
                            currentPhotoResources: \(photoFingerprint.isEmpty ? "nil" : photoFingerprint)

                            ACTIVITY
                            status: \(status.report)
                            reliability: \(status.reliability)

                            TELEGRAM_SECURITY
                            registrationMonth: \(security.registrationMonth ?? "nil")
                            phoneCountryNumber: \(security.phoneCountry ?? "nil")
                            nameChangeDate: \(security.nameChangeDate.map(String.init) ?? "nil")
                            photoChangeDate: \(security.photoChangeDate.map(String.init) ?? "nil")

                            PHOTOS
                            returned: \(photos.count)
                            totalCount: \(photoTotal)
                            latestDate: \(latestPhotoDate.map(String.init) ?? "nil")
                            dates: \(photoDates.isEmpty ? "nil" : photoDates)

                            LOCAL_HISTORY
                            observationStarted: \(started)
                            newEvents: \(events.count)
                            \(history)

                            NOTE
                            phoneCountryNumber is the country of the phone number, not residence.
                            Exact-status privacy mutation was not performed by this read-only snapshot.
                            """
                        }
                    }
                }
            }
        }

'''
    text = text.replace(method_anchor, method + method_anchor, 1)

for proof in (
    marker,
    "ghostBaseProfileIntel2Snapshot(",
    "_internal_requestPeerPhotos(",
    "GhostBase.ProfileIntel2.",
    "Наблюдение начато",
    "Наблюдаемая сессия",
    "phoneCountryNumber",
    "serverPhotoDates",
    "Exact-status privacy mutation was not performed",
):
    require(proof in text, f"proof missing: {proof}")

section = text[text.index(marker):]
require("account.setPrivacy" not in section, "unexpected privacy mutation")
require("updateSelectiveAccountPrivacySettings" not in section, "unexpected privacy mutation helper")

path.write_text(text, encoding="utf-8")
print("[PROFILEINTEL2] local profile snapshots enabled")
print("[PROFILEINTEL2] field-change and observed-session history enabled")
print("[PROFILEINTEL2] server photo history probe enabled")
print("[PROFILEINTEL2] Telegram PeerSettings preservation enabled")
print("[PROFILEINTEL2] exact-status privacy mutation remains read-only for safety")
