#!/usr/bin/env python3

import os
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
PATH = ROOT / "submodules/TelegramCore/Sources/TelegramEngine/Payments/StarGifts.swift"
if not PATH.is_file():
    raise SystemExit(f"[V10ZH GIFTHISTORY2] missing source: {PATH}")

text = PATH.read_text(encoding="utf-8")
if "// MARK: GhostBase v1.0ZG GIFTHISTORY1 local archive" not in text:
    raise SystemExit("[V10ZH GIFTHISTORY2] Build 85 GIFTHISTORY1 must run first")


def replace_once(value: str, old: str, new: str, label: str) -> str:
    count = value.count(old)
    if count != 1:
        raise SystemExit(f"[V10ZH GIFTHISTORY2] {label} anchor count: {count}")
    return value.replace(old, new, 1)


def function_span(value: str, signature: str) -> tuple[int, int]:
    start = value.find(signature)
    if start == -1:
        raise SystemExit(f"[V10ZH GIFTHISTORY2] function not found: {signature}")
    brace = value.find("{", start)
    if brace == -1:
        raise SystemExit(f"[V10ZH GIFTHISTORY2] function brace not found: {signature}")
    depth = 0
    in_string = False
    escaped = False
    for index in range(brace, len(value)):
        char = value[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                if end < len(value) and value[end] == "\n":
                    end += 1
                return start, end
    raise SystemExit(f"[V10ZH GIFTHISTORY2] unbalanced function: {signature}")


marker = "// MARK: GhostBase v1.0ZH GIFTHISTORY2 disappearance state"
if marker not in text:
    text = replace_once(
        text,
        "    public var lastObservedAt: Int64\n    public var giftDate: Int32\n",
        "    public var lastObservedAt: Int64\n"
        "    // MARK: GhostBase v1.0ZH GIFTHISTORY2 disappearance state\n"
        "    public var lastSeenVisibleAt: Int64?\n"
        "    public var missingSince: Int64?\n"
        "    public var giftDate: Int32\n",
        "history fields",
    )

    text = replace_once(
        text,
        "        lastObservedAt: observedAt,\n        giftDate: gift.date,\n",
        "        lastObservedAt: observedAt,\n"
        "        lastSeenVisibleAt: gift.savedToProfile ? observedAt : nil,\n"
        "        missingSince: nil,\n"
        "        giftDate: gift.date,\n",
        "snapshot fields",
    )

    report_start, report_end = function_span(text, "public func ghostBaseGiftHistoryReport(")
    report = r'''public func ghostBaseGiftHistoryReport(
    accountPeerId: EnginePeer.Id,
    peerId: EnginePeer.Id
) -> String {
    let entries = ghostBaseGiftHistoryEntries(
        accountPeerId: accountPeerId,
        peerId: peerId
    )
    let formatter = DateFormatter()
    formatter.locale = Locale(identifier: "ru_RU")
    formatter.dateFormat = "dd.MM.yyyy HH:mm"
    func dateText(_ value: Int64?) -> String {
        guard let value else {
            return "nil"
        }
        return formatter.string(from: Date(timeIntervalSince1970: TimeInterval(value)))
    }

    var lines: [String] = ["История подарков GhostBase: \(entries.count)"]
    for entry in entries {
        let visibility: String
        if entry.missingSince != nil {
            visibility = "исчез из публичного профиля"
        } else if entry.savedToProfile {
            visibility = "видимый"
        } else {
            visibility = "скрытый владельцем"
        }
        let sender = entry.nameHidden
            ? "анонимно"
            : (entry.fromPeerTitle ?? entry.fromPeerUsername ?? entry.fromPeerId.map(String.init) ?? "nil")
        let title = entry.title.isEmpty ? "Подарок \(entry.giftId)" : entry.title
        lines.append(
            "\(dateText(Int64(entry.giftDate))) · \(visibility) · \(title) · giftId=\(entry.giftId) · uniqueId=\(entry.uniqueId.map(String.init) ?? "nil") · slug=\(entry.slug ?? "nil") · number=\(entry.number.map(String.init) ?? "nil") · sender=\(sender) · senderId=\(entry.fromPeerId.map(String.init) ?? "nil") · username=\(entry.fromPeerUsername ?? "nil") · text=\(entry.text ?? "nil") · first=\(dateText(entry.firstObservedAt)) · lastVisible=\(dateText(entry.lastSeenVisibleAt)) · missingSince=\(dateText(entry.missingSince))"
        )
    }
    return lines.joined(separator: "\n")
}
'''
    text = text[:report_start] + report + text[report_end:]

    record_start, record_end = function_span(text, "private func ghostBaseRecordGiftHistory(")
    record = r'''private func ghostBaseRecordGiftHistory(
    accountPeerId: EnginePeer.Id,
    peerId: EnginePeer.Id,
    gifts: [ProfileGiftsContext.State.StarGift],
    filterRawValue: Int32,
    snapshotComplete: Bool
) {
    let storageKey = ghostBaseGiftHistoryStorageKey(
        accountPeerId: accountPeerId,
        peerId: peerId
    )
    let decoder = JSONDecoder()
    let encoder = JSONEncoder()
    var entries: [GhostBaseGiftHistoryEntry] = []
    if let data = UserDefaults.standard.data(forKey: storageKey),
       let value = try? decoder.decode([GhostBaseGiftHistoryEntry].self, from: data) {
        entries = value
    }

    var indexByKey: [String: Int] = [:]
    for index in entries.indices {
        indexByKey[entries[index].key] = index
    }

    let observedAt = Int64(Date().timeIntervalSince1970)
    var hiddenCount = 0
    var observedKeys = Set<String>()
    for gift in gifts {
        if !gift.savedToProfile {
            hiddenCount += 1
        }
        var snapshot = ghostBaseGiftHistorySnapshot(
            gift: gift,
            filterRawValue: filterRawValue,
            observedAt: observedAt
        )
        observedKeys.insert(snapshot.key)
        if let index = indexByKey[snapshot.key] {
            let previous = entries[index]
            snapshot.firstObservedAt = previous.firstObservedAt
            snapshot.visibilityHistory = previous.visibilityHistory
            snapshot.lastSeenVisibleAt = snapshot.savedToProfile
                ? observedAt
                : previous.lastSeenVisibleAt
            snapshot.missingSince = nil
            if snapshot.visibilityHistory.last?.savedToProfile != snapshot.savedToProfile {
                snapshot.visibilityHistory.append(
                    GhostBaseGiftVisibilityEvent(
                        observedAt: observedAt,
                        savedToProfile: snapshot.savedToProfile
                    )
                )
                if snapshot.visibilityHistory.count > 50 {
                    snapshot.visibilityHistory.removeFirst(
                        snapshot.visibilityHistory.count - 50
                    )
                }
            }
            entries[index] = snapshot
        } else {
            indexByKey[snapshot.key] = entries.count
            entries.append(snapshot)
        }
    }

    var disappearedCount = 0
    if snapshotComplete {
        for index in entries.indices {
            if entries[index].savedToProfile
                && !observedKeys.contains(entries[index].key)
                && entries[index].missingSince == nil {
                entries[index].missingSince = observedAt
                disappearedCount += 1
            }
        }
    }

    entries.sort { lhs, rhs in
        if lhs.giftDate != rhs.giftDate {
            return lhs.giftDate > rhs.giftDate
        }
        return lhs.lastObservedAt > rhs.lastObservedAt
    }
    if entries.count > 1000 {
        entries.removeLast(entries.count - 1000)
    }
    if let data = try? encoder.encode(entries) {
        UserDefaults.standard.set(data, forKey: storageKey)
    }
    Logger.shared.log(
        "GhostBase.GiftHistory2",
        "peer=\(peerId.toInt64()) returned=\(gifts.count) hidden=\(hiddenCount) disappeared=\(disappearedCount) complete=\(snapshotComplete) stored=\(entries.count) filter=\(filterRawValue)"
    )
}
'''
    text = text[:record_start] + record + text[record_end:]

    old_call = """            ghostBaseRecordGiftHistory(
                accountPeerId: accountPeerId,
                peerId: peerId,
                gifts: gifts,
                filterRawValue: filter.rawValue
            )
"""
    new_call = """            ghostBaseRecordGiftHistory(
                accountPeerId: accountPeerId,
                peerId: peerId,
                gifts: gifts,
                filterRawValue: filter.rawValue,
                snapshotComplete: initialNextOffset == nil && nextOffset == nil
            )
"""
    text = replace_once(text, old_call, new_call, "record call")

PATH.write_text(text, encoding="utf-8")

updated = PATH.read_text(encoding="utf-8")
for proof in (
    marker,
    "public var lastSeenVisibleAt: Int64?",
    "public var missingSince: Int64?",
    "snapshotComplete: initialNextOffset == nil && nextOffset == nil",
    "исчез из публичного профиля",
    "entries[index].missingSince = observedAt",
):
    if proof not in updated:
        raise SystemExit(f"[V10ZH GIFTHISTORY2] proof missing: {proof}")

print("[V10ZH] GIFTHISTORY2 applied: complete one-page snapshots mark disappeared gifts")
print("[V10ZH] hidden-before-first-observation gifts remain outside public-server visibility")
