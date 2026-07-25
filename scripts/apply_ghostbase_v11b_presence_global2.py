#!/usr/bin/env python3
import os
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
PATH = ROOT / "submodules/TelegramCore/Sources/UpdatePeers.swift"
if not PATH.is_file():
    raise SystemExit(f"[V11B PRESENCEGLOBAL2] missing source: {PATH}")

text = PATH.read_text(encoding="utf-8")
old_marker = "// MARK: GhostBase v1.0ZH PRESENCEHISTORY1 observed presence archive"
new_marker = "// MARK: GhostBase v1.1B PRESENCEGLOBAL2 transition archive"
if new_marker in text:
    print("[V11B] PRESENCEGLOBAL2 already applied")
    raise SystemExit(0)
if old_marker not in text:
    raise SystemExit("[V11B PRESENCEGLOBAL2] PRESENCEHISTORY1 prerequisite missing")

start = text.index(old_marker)
end_anchor = "\nprivate func ghostBaseRecordPresence("
record_start = text.index(end_anchor, start)
# Replace the old data model + conversion helper, keeping the storage key name compatible.
replacement = r'''// MARK: GhostBase v1.1B PRESENCEGLOBAL2 transition archive
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
    // Keep the v1 key so existing local history is migrated instead of abandoned.
    return "GhostBase.PresenceHistory1.\(accountPeerId.toInt64()).\(peerId.toInt64())"
}

private func ghostBasePresenceTransitionKey(
    _ event: GhostBasePresenceHistoryEvent
) -> String {
    // lastActivity and online-until are payload details, not distinct transitions.
    return "\(event.status)|hidden=\(event.isHidden)"
}

private func ghostBasePresenceEvent(
    _ presence: TelegramUserPresence
) -> GhostBasePresenceHistoryEvent? {
    let status: String
    let until: Int32?
    let isHidden: Bool
    switch presence.status {
    case .none:
        // Absence of server data is not an observed offline transition.
        return nil
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

private func ghostBaseCompactPresenceEvents(
    _ source: [GhostBasePresenceHistoryEvent]
) -> [GhostBasePresenceHistoryEvent] {
    var result: [GhostBasePresenceHistoryEvent] = []
    result.reserveCapacity(source.count)
    for event in source {
        // Migrate away synthetic/legacy "нет данных" entries.
        if event.status == "нет данных" {
            continue
        }
        if let previous = result.last,
           ghostBasePresenceTransitionKey(previous) == ghostBasePresenceTransitionKey(event) {
            // Retain the first observation of a stable state. A changed lastActivity
            // or online expiration must not flood the timeline with duplicates.
            continue
        }
        result.append(event)
    }
    if result.count > 1000 {
        result.removeFirst(result.count - 1000)
    }
    return result
}
'''
text = text[:start] + replacement + text[record_start:]

old_record = r'''private func ghostBaseRecordPresence(
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
'''
new_record = r'''private func ghostBaseRecordPresence(
    accountPeerId: PeerId,
    peerId: PeerId,
    presence: TelegramUserPresence
) {
    guard let event = ghostBasePresenceEvent(presence) else {
        return
    }
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
        events = ghostBaseCompactPresenceEvents(value)
    }

    if let previous = events.last,
       ghostBasePresenceTransitionKey(previous) == ghostBasePresenceTransitionKey(event) {
        // Persist migration even when the current observation adds no transition.
        if let data = try? JSONEncoder().encode(events) {
            UserDefaults.standard.set(data, forKey: key)
        }
        return
    }
    events.append(event)
    events = ghostBaseCompactPresenceEvents(events)
    if let data = try? JSONEncoder().encode(events) {
        UserDefaults.standard.set(data, forKey: key)
    }
}
'''
if text.count(old_record) != 1:
    raise SystemExit(f"[V11B PRESENCEGLOBAL2] record anchor count: {text.count(old_record)}")
text = text.replace(old_record, new_record, 1)

old_return = r'''    return events
}

public func ghostBasePresenceHistoryReport('''
new_return = r'''    let compacted = ghostBaseCompactPresenceEvents(events)
    if compacted != events,
       let migrated = try? JSONEncoder().encode(compacted) {
        UserDefaults.standard.set(migrated, forKey: key)
    }
    return compacted
}

public func ghostBasePresenceHistoryReport('''
if text.count(old_return) != 1:
    raise SystemExit(f"[V11B PRESENCEGLOBAL2] events return anchor count: {text.count(old_return)}")
text = text.replace(old_return, new_return, 1)

old_lines = r'''    var lines = ["История присутствия GhostBase: \(events.count)"]
    for event in events.reversed() {
        lines.append(
            "\(dateText(event.observedAt)) · \(event.status) · until=\(apiDateText(event.until)) · lastActivity=\(apiDateText(event.lastActivity > 0 ? event.lastActivity : nil)) · hidden=\(event.isHidden)"
        )
    }
'''
new_lines = r'''    var lines = ["История присутствия: \(events.count) переходов"]
    for event in events.reversed() {
        var details: [String] = []
        if event.status == "онлайн", let until = event.until, until > 0 {
            details.append("до \(apiDateText(until))")
        }
        if event.isHidden {
            details.append("скрытый статус")
        }
        let suffix = details.isEmpty ? "" : " · " + details.joined(separator: " · ")
        lines.append("\(dateText(event.observedAt)) · \(event.status)\(suffix)")
    }
'''
if text.count(old_lines) != 1:
    raise SystemExit(f"[V11B PRESENCEGLOBAL2] report anchor count: {text.count(old_lines)}")
text = text.replace(old_lines, new_lines, 1)

PATH.write_text(text, encoding="utf-8")
updated = PATH.read_text(encoding="utf-8")
proofs = (
    new_marker,
    "private func ghostBasePresenceTransitionKey(",
    "private func ghostBaseCompactPresenceEvents(",
    "case .none:\n        // Absence of server data",
    "История присутствия: \\(events.count) переходов",
)
for proof in proofs:
    if proof not in updated:
        raise SystemExit(f"[V11B PRESENCEGLOBAL2] proof missing: {proof}")
if 'status = "нет данных"' in updated:
    raise SystemExit("[V11B PRESENCEGLOBAL2] synthetic none-state writer still present")
print("[V11B] PRESENCEGLOBAL2 applied: real observations only, transition dedupe, legacy compaction")
