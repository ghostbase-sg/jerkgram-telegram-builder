#!/usr/bin/env python3

import os
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
PATH = ROOT / "submodules/TelegramCore/Sources/UpdatePeers.swift"
if not PATH.is_file():
    raise SystemExit(f"[V10ZH PRESENCEHISTORY1] missing source: {PATH}")

text = PATH.read_text(encoding="utf-8")
marker = "// MARK: GhostBase v1.0ZH PRESENCEHISTORY1 observed presence archive"


def replace_once(value: str, old: str, new: str, label: str) -> str:
    count = value.count(old)
    if count != 1:
        raise SystemExit(f"[V10ZH PRESENCEHISTORY1] {label} anchor count: {count}")
    return value.replace(old, new, 1)


if marker not in text:
    imports = """import Foundation
import Postbox
import TelegramApi
"""
    if imports not in text:
        raise SystemExit("[V10ZH PRESENCEHISTORY1] import anchor missing")
    helper = imports + r'''

// MARK: GhostBase v1.0ZH PRESENCEHISTORY1 observed presence archive
public struct GhostBasePresenceHistoryEvent: Codable, Equatable {
    public let observedAt: Int64
    public let status: String
    public let until: Int32?
    public let lastActivity: Int32
    public let isHidden: Bool

    public init(
        observedAt: Int64,
        status: String,
        until: Int32?,
        lastActivity: Int32,
        isHidden: Bool
    ) {
        self.observedAt = observedAt
        self.status = status
        self.until = until
        self.lastActivity = lastActivity
        self.isHidden = isHidden
    }
}

private func ghostBasePresenceHistoryKey(
    accountPeerId: PeerId,
    peerId: PeerId
) -> String {
    return "GhostBase.PresenceHistory1.\(accountPeerId.toInt64()).\(peerId.toInt64())"
}

private func ghostBasePresenceEvent(
    _ presence: TelegramUserPresence
) -> GhostBasePresenceHistoryEvent {
    let status: String
    let until: Int32?
    let isHidden: Bool
    switch presence.status {
    case .none:
        status = "нет данных"
        until = nil
        isHidden = false
    case let .present(value):
        status = "онлайн"
        until = value
        isHidden = false
    case let .recently(hidden):
        status = "был недавно"
        until = nil
        isHidden = hidden
    case let .lastWeek(hidden):
        status = "был на этой неделе"
        until = nil
        isHidden = hidden
    case let .lastMonth(hidden):
        status = "был в этом месяце"
        until = nil
        isHidden = hidden
    }
    return GhostBasePresenceHistoryEvent(
        observedAt: Int64(Date().timeIntervalSince1970),
        status: status,
        until: until,
        lastActivity: presence.lastActivity,
        isHidden: isHidden
    )
}

private func ghostBaseRecordPresence(
    accountPeerId: PeerId,
    peerId: PeerId,
    presence: TelegramUserPresence
) {
    let key = ghostBasePresenceHistoryKey(
        accountPeerId: accountPeerId,
        peerId: peerId
    )
    var events: [GhostBasePresenceHistoryEvent] = []
    if let data = UserDefaults.standard.data(forKey: key),
       let value = try? JSONDecoder().decode(
        [GhostBasePresenceHistoryEvent].self,
        from: data
       ) {
        events = value
    }

    let event = ghostBasePresenceEvent(presence)
    if let previous = events.last,
       previous.status == event.status,
       previous.until == event.until,
       previous.lastActivity == event.lastActivity,
       previous.isHidden == event.isHidden {
        return
    }
    events.append(event)
    if events.count > 1000 {
        events.removeFirst(events.count - 1000)
    }
    if let data = try? JSONEncoder().encode(events) {
        UserDefaults.standard.set(data, forKey: key)
    }
}

public func ghostBasePresenceHistoryEvents(
    accountPeerId: PeerId,
    peerId: PeerId
) -> [GhostBasePresenceHistoryEvent] {
    let key = ghostBasePresenceHistoryKey(
        accountPeerId: accountPeerId,
        peerId: peerId
    )
    guard let data = UserDefaults.standard.data(forKey: key),
          let events = try? JSONDecoder().decode(
            [GhostBasePresenceHistoryEvent].self,
            from: data
          ) else {
        return []
    }
    return events
}

public func ghostBasePresenceHistoryReport(
    accountPeerId: PeerId,
    peerId: PeerId
) -> String? {
    let events = ghostBasePresenceHistoryEvents(
        accountPeerId: accountPeerId,
        peerId: peerId
    )
    guard !events.isEmpty else {
        return nil
    }
    let formatter = DateFormatter()
    formatter.locale = Locale(identifier: "ru_RU")
    formatter.dateFormat = "dd.MM.yyyy HH:mm:ss"
    func dateText(_ value: Int64) -> String {
        return formatter.string(
            from: Date(timeIntervalSince1970: TimeInterval(value))
        )
    }
    func apiDateText(_ value: Int32?) -> String {
        guard let value, value > 0 else {
            return "nil"
        }
        return formatter.string(
            from: Date(timeIntervalSince1970: TimeInterval(value))
        )
    }

    var lines = ["История присутствия GhostBase: \(events.count)"]
    for event in events.reversed() {
        lines.append(
            "\(dateText(event.observedAt)) · \(event.status) · until=\(apiDateText(event.until)) · lastActivity=\(apiDateText(event.lastActivity > 0 ? event.lastActivity : nil)) · hidden=\(event.isHidden)"
        )
    }
    return lines.joined(separator: "\n")
}
'''
    text = text.replace(imports, helper, 1)

    first = """        guard let presence = TelegramUserPresence(apiUser: user) else {
            continue
        }
        switch presence.status {
"""
    first_new = """        guard let presence = TelegramUserPresence(apiUser: user) else {
            continue
        }
        ghostBaseRecordPresence(
            accountPeerId: accountPeerId,
            peerId: peerId,
            presence: presence
        )
        switch presence.status {
"""
    text = replace_once(text, first, first_new, "api user observation")

    second = """    for (peerId, status) in peerPresences {
        let presence = TelegramUserPresence(apiStatus: status.status)
        switch presence.status {
"""
    second_new = """    for (peerId, status) in peerPresences {
        let presence = TelegramUserPresence(apiStatus: status.status)
        ghostBaseRecordPresence(
            accountPeerId: accountPeerId,
            peerId: peerId,
            presence: presence
        )
        switch presence.status {
"""
    text = replace_once(text, second, second_new, "clean presence observation")

    activity_old = """                return TelegramUserPresence(status: updatedStatus, lastActivity: timestamp)
"""
    activity_new = """                let updatedPresence = TelegramUserPresence(
                    status: updatedStatus,
                    lastActivity: timestamp
                )
                ghostBaseRecordPresence(
                    accountPeerId: accountPeerId,
                    peerId: peerId,
                    presence: updatedPresence
                )
                return updatedPresence
"""
    text = replace_once(text, activity_old, activity_new, "activity observation")

PATH.write_text(text, encoding="utf-8")
updated = PATH.read_text(encoding="utf-8")
for proof in (
    marker,
    "public struct GhostBasePresenceHistoryEvent",
    "public func ghostBasePresenceHistoryReport(",
    "GhostBase.PresenceHistory1.",
    "ghostBaseRecordPresence(",
    "status = \"был недавно\"",
):
    if proof not in updated:
        raise SystemExit(f"[V10ZH PRESENCEHISTORY1] proof missing: {proof}")
print("[V10ZH] PRESENCEHISTORY1 applied: stores every presence state actually received by the client")
