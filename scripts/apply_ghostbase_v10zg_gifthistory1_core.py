#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramCore/Sources/TelegramEngine/Payments/StarGifts.swift"
if not path.is_file():
    raise SystemExit(f"[V10ZG GIFTHISTORY1] missing source: {path}")

text = path.read_text(encoding="utf-8")
helper_marker = "// MARK: GhostBase v1.0ZG GIFTHISTORY1 local archive"

if helper_marker not in text:
    anchor = """import Foundation
import Postbox
import MtProtoKit
import SwiftSignalKit
import TelegramApi
"""
    if anchor not in text:
        raise SystemExit("[V10ZG GIFTHISTORY1] imports anchor missing")
    helper = anchor + r'''

// MARK: GhostBase v1.0ZG GIFTHISTORY1 local archive
public struct GhostBaseGiftVisibilityEvent: Codable, Equatable {
    public let observedAt: Int64
    public let savedToProfile: Bool

    public init(observedAt: Int64, savedToProfile: Bool) {
        self.observedAt = observedAt
        self.savedToProfile = savedToProfile
    }
}

public struct GhostBaseGiftHistoryEntry: Codable, Equatable {
    public var key: String
    public var firstObservedAt: Int64
    public var lastObservedAt: Int64
    public var giftDate: Int32
    public var giftId: Int64
    public var uniqueId: Int64?
    public var title: String
    public var slug: String?
    public var number: Int32?
    public var fromPeerId: Int64?
    public var fromPeerTitle: String?
    public var fromPeerUsername: String?
    public var text: String?
    public var nameHidden: Bool
    public var savedToProfile: Bool
    public var modelName: String?
    public var patternName: String?
    public var backdropName: String?
    public var originalSenderPeerId: Int64?
    public var originalRecipientPeerId: Int64?
    public var originalDate: Int32?
    public var originalText: String?
    public var lastFilterRawValue: Int32
    public var visibilityHistory: [GhostBaseGiftVisibilityEvent]
}

private func ghostBaseGiftHistoryStorageKey(
    accountPeerId: EnginePeer.Id,
    peerId: EnginePeer.Id
) -> String {
    return "GhostBase.GiftHistory1.\(accountPeerId.toInt64()).\(peerId.toInt64())"
}

public func ghostBaseGiftHistoryEntries(
    accountPeerId: EnginePeer.Id,
    peerId: EnginePeer.Id
) -> [GhostBaseGiftHistoryEntry] {
    let key = ghostBaseGiftHistoryStorageKey(
        accountPeerId: accountPeerId,
        peerId: peerId
    )
    guard let data = UserDefaults.standard.data(forKey: key),
          let entries = try? JSONDecoder().decode(
            [GhostBaseGiftHistoryEntry].self,
            from: data
          ) else {
        return []
    }
    return entries.sorted { lhs, rhs in
        if lhs.giftDate != rhs.giftDate {
            return lhs.giftDate > rhs.giftDate
        }
        return lhs.lastObservedAt > rhs.lastObservedAt
    }
}

public func ghostBaseGiftHistoryReport(
    accountPeerId: EnginePeer.Id,
    peerId: EnginePeer.Id
) -> String {
    let entries = ghostBaseGiftHistoryEntries(
        accountPeerId: accountPeerId,
        peerId: peerId
    )
    var lines: [String] = ["История подарков GhostBase: \(entries.count)"]
    for entry in entries {
        let visibility = entry.savedToProfile ? "видимый" : "скрытый"
        let sender = entry.nameHidden
            ? "анонимно"
            : (entry.fromPeerTitle ?? entry.fromPeerUsername ?? entry.fromPeerId.map(String.init) ?? "nil")
        lines.append(
            "date=\(entry.giftDate) · \(visibility) · giftId=\(entry.giftId) · uniqueId=\(entry.uniqueId.map(String.init) ?? "nil") · title=\(entry.title) · slug=\(entry.slug ?? "nil") · number=\(entry.number.map(String.init) ?? "nil") · sender=\(sender) · senderId=\(entry.fromPeerId.map(String.init) ?? "nil") · username=\(entry.fromPeerUsername ?? "nil") · text=\(entry.text ?? "nil") · first=\(entry.firstObservedAt) · last=\(entry.lastObservedAt)"
        )
    }
    return lines.joined(separator: "\n")
}

private func ghostBaseGiftHistoryIdentity(
    gift: ProfileGiftsContext.State.StarGift
) -> String {
    if let reference = gift.reference {
        switch reference {
        case let .message(messageId):
            return "message:\(messageId.peerId.toInt64()):\(messageId.namespace):\(messageId.id)"
        case let .peer(peerId, id):
            return "peer:\(peerId.toInt64()):\(id)"
        case let .slug(slug):
            return "slug:\(slug)"
        }
    }
    return "fallback:\(gift.gift.giftId):\(gift.date):\(gift.fromPeer?.id.toInt64() ?? 0)"
}

private func ghostBaseGiftHistorySnapshot(
    gift: ProfileGiftsContext.State.StarGift,
    filterRawValue: Int32,
    observedAt: Int64
) -> GhostBaseGiftHistoryEntry {
    var uniqueId: Int64?
    var slug: String?
    var number = gift.number
    var modelName: String?
    var patternName: String?
    var backdropName: String?
    var originalSenderPeerId: Int64?
    var originalRecipientPeerId: Int64?
    var originalDate: Int32?
    var originalText: String?

    switch gift.gift {
    case let .generic(value):
        uniqueId = nil
        slug = nil
        if number == nil {
            number = nil
        }
        _ = value
    case let .unique(value):
        uniqueId = value.id
        slug = value.slug
        number = value.number
        for attribute in value.attributes {
            switch attribute {
            case let .model(name, _, _, _):
                modelName = name
            case let .pattern(name, _, _):
                patternName = name
            case let .backdrop(name, _, _, _, _, _, _):
                backdropName = name
            case let .originalInfo(senderPeerId, recipientPeerId, date, text, _):
                originalSenderPeerId = senderPeerId?.toInt64()
                originalRecipientPeerId = recipientPeerId.toInt64()
                originalDate = date
                originalText = text
            }
        }
    }

    return GhostBaseGiftHistoryEntry(
        key: ghostBaseGiftHistoryIdentity(gift: gift),
        firstObservedAt: observedAt,
        lastObservedAt: observedAt,
        giftDate: gift.date,
        giftId: gift.gift.giftId,
        uniqueId: uniqueId,
        title: gift.gift.title,
        slug: slug,
        number: number,
        fromPeerId: gift.fromPeer?.id.toInt64(),
        fromPeerTitle: gift.fromPeer?.compactDisplayTitle,
        fromPeerUsername: gift.fromPeer?.addressName,
        text: gift.text,
        nameHidden: gift.nameHidden,
        savedToProfile: gift.savedToProfile,
        modelName: modelName,
        patternName: patternName,
        backdropName: backdropName,
        originalSenderPeerId: originalSenderPeerId,
        originalRecipientPeerId: originalRecipientPeerId,
        originalDate: originalDate,
        originalText: originalText,
        lastFilterRawValue: filterRawValue,
        visibilityHistory: [
            GhostBaseGiftVisibilityEvent(
                observedAt: observedAt,
                savedToProfile: gift.savedToProfile
            )
        ]
    )
}

private func ghostBaseRecordGiftHistory(
    accountPeerId: EnginePeer.Id,
    peerId: EnginePeer.Id,
    gifts: [ProfileGiftsContext.State.StarGift],
    filterRawValue: Int32
) {
    guard !gifts.isEmpty else {
        Logger.shared.log(
            "GhostBase.GiftHistory1",
            "peer=\(peerId.toInt64()) returned=0 filter=\(filterRawValue)"
        )
        return
    }

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
    for gift in gifts {
        if !gift.savedToProfile {
            hiddenCount += 1
        }
        var snapshot = ghostBaseGiftHistorySnapshot(
            gift: gift,
            filterRawValue: filterRawValue,
            observedAt: observedAt
        )
        if let index = indexByKey[snapshot.key] {
            let previous = entries[index]
            snapshot.firstObservedAt = previous.firstObservedAt
            snapshot.visibilityHistory = previous.visibilityHistory
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

    entries.sort { $0.lastObservedAt > $1.lastObservedAt }
    if entries.count > 1000 {
        entries.removeLast(entries.count - 1000)
    }
    if let data = try? encoder.encode(entries) {
        UserDefaults.standard.set(data, forKey: storageKey)
    }
    Logger.shared.log(
        "GhostBase.GiftHistory1",
        "peer=\(peerId.toInt64()) returned=\(gifts.count) hidden=\(hiddenCount) stored=\(entries.count) filter=\(filterRawValue)"
    )
}
'''
    text = text.replace(anchor, helper, 1)

call_marker = "// MARK: GhostBase v1.0ZG GIFTHISTORY1 record server page"
if call_marker not in text:
    old = """            guard let self else {
                return
            }
            if isFiltered {
"""
    new = """            guard let self else {
                return
            }
            // MARK: GhostBase v1.0ZG GIFTHISTORY1 record server page
            ghostBaseRecordGiftHistory(
                accountPeerId: accountPeerId,
                peerId: peerId,
                gifts: gifts,
                filterRawValue: filter.rawValue
            )
            if isFiltered {
"""
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"[V10ZG GIFTHISTORY1] load callback anchor count: {count}")
    text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")

text = path.read_text(encoding="utf-8")
for proof in (
    helper_marker,
    call_marker,
    "GhostBaseGiftHistoryEntry",
    "visibilityHistory",
    "gift.fromPeer?.addressName",
    "originalSenderPeerId",
    "filterRawValue: filter.rawValue",
):
    if proof not in text:
        raise SystemExit(f"[V10ZG GIFTHISTORY1] proof missing: {proof}")

print("[V10ZG] GIFTHISTORY1 core archive applied")
print("[V10ZG] records displayed/hidden state, sender, date, text, IDs and unique metadata")
