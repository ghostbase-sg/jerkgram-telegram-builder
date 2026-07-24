#!/usr/bin/env python3
import os
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
PATH = ROOT / "submodules/TelegramCore/Sources/UpdatePeers.swift"
if not PATH.is_file():
    raise SystemExit(f"[V11A PRESENCE] missing source: {PATH}")
text = PATH.read_text(encoding="utf-8")
if "// MARK: GhostBase v1.0ZH PRESENCEHISTORY1 observed presence archive" not in text:
    raise SystemExit("[V11A PRESENCE] Build 86 presence history missing")

marker = "// MARK: GhostBase v1.1A PRESENCEGLOBAL1 known-user registry"
if marker not in text:
    insert_at = text.index("func isPeerHiddenByCollapsedCommunity")
    helper = r'''// MARK: GhostBase v1.1A PRESENCEGLOBAL1 known-user registry
public struct GhostBaseKnownUser: Codable, Equatable {
    public let peerId: Int64
    public var title: String
    public var username: String?
    public var isBot: Bool
    public var firstSeen: Int64
    public var lastSeen: Int64
}

private func ghostBaseKnownUserIdsKey(_ accountPeerId: PeerId) -> String {
    return "GhostBase.PresenceGlobal1.KnownUserIds.\(accountPeerId.toInt64())"
}

private func ghostBaseKnownUserKey(
    accountPeerId: PeerId,
    peerId: PeerId
) -> String {
    return "GhostBase.PresenceGlobal1.KnownUser.\(accountPeerId.toInt64()).\(peerId.toInt64())"
}

private func ghostBaseRegisterKnownUser(
    accountPeerId: PeerId,
    user: TelegramUser
) {
    let key = ghostBaseKnownUserKey(
        accountPeerId: accountPeerId,
        peerId: user.id
    )
    let now = Int64(Date().timeIntervalSince1970)
    let decoder = JSONDecoder()
    let encoder = JSONEncoder()
    let previous: GhostBaseKnownUser?
    if let data = UserDefaults.standard.data(forKey: key) {
        previous = try? decoder.decode(GhostBaseKnownUser.self, from: data)
    } else {
        previous = nil
    }

    let record = GhostBaseKnownUser(
        peerId: user.id.toInt64(),
        title: user.nameOrPhone,
        username: user.addressName,
        isBot: user.botInfo != nil,
        firstSeen: previous?.firstSeen ?? now,
        lastSeen: now
    )
    if let data = try? encoder.encode(record) {
        UserDefaults.standard.set(data, forKey: key)
    }

    if previous == nil {
        let idsKey = ghostBaseKnownUserIdsKey(accountPeerId)
        var ids = (UserDefaults.standard.array(forKey: idsKey) as? [NSNumber])?.map { $0.int64Value } ?? []
        if !ids.contains(record.peerId) {
            ids.append(record.peerId)
            if ids.count > 20000 {
                ids.removeFirst(ids.count - 20000)
            }
            UserDefaults.standard.set(ids.map { NSNumber(value: $0) }, forKey: idsKey)
        }
    }

    if ghostBasePresenceHistoryEvents(
        accountPeerId: accountPeerId,
        peerId: user.id
    ).isEmpty {
        ghostBaseRecordPresence(
            accountPeerId: accountPeerId,
            peerId: user.id,
            presence: TelegramUserPresence(status: .none, lastActivity: 0)
        )
    }
}

public func ghostBaseKnownUsers(
    accountPeerId: PeerId
) -> [GhostBaseKnownUser] {
    let idsKey = ghostBaseKnownUserIdsKey(accountPeerId)
    let ids = (UserDefaults.standard.array(forKey: idsKey) as? [NSNumber])?.map { $0.int64Value } ?? []
    let decoder = JSONDecoder()
    var result: [GhostBaseKnownUser] = []
    result.reserveCapacity(ids.count)
    for rawId in ids {
        let peerId = PeerId(
            namespace: Namespaces.Peer.CloudUser,
            id: PeerId.Id._internalFromInt64Value(rawId)
        )
        let key = ghostBaseKnownUserKey(
            accountPeerId: accountPeerId,
            peerId: peerId
        )
        if let data = UserDefaults.standard.data(forKey: key),
           let user = try? decoder.decode(GhostBaseKnownUser.self, from: data) {
            result.append(user)
        }
    }
    return result.sorted { $0.lastSeen > $1.lastSeen }
}

public func ghostBaseKnownUsersReport(accountPeerId: PeerId) -> String {
    let users = ghostBaseKnownUsers(accountPeerId: accountPeerId)
    var lines = ["Известные пользователи: \(users.count)"]
    for user in users.prefix(500) {
        lines.append(
            "\(user.title) · id=\(user.peerId) · username=\(user.username ?? "nil") · bot=\(user.isBot)"
        )
    }
    return lines.joined(separator: "\n")
}

'''
    text = text[:insert_at] + helper + text[insert_at:]

anchor = '''        if let telegramUser = TelegramUser.merge(transaction.getPeer(user.peerId) as? TelegramUser, rhs: user) {
            parsedPeers.append(telegramUser)
'''
replacement = '''        if let telegramUser = TelegramUser.merge(transaction.getPeer(user.peerId) as? TelegramUser, rhs: user) {
            // MARK: GhostBase v1.1A PRESENCEGLOBAL1 register every received user
            ghostBaseRegisterKnownUser(
                accountPeerId: accountPeerId,
                user: telegramUser
            )
            parsedPeers.append(telegramUser)
'''
if replacement not in text:
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(f"[V11A PRESENCE] user registration anchor count: {count}")
    text = text.replace(anchor, replacement, 1)

PATH.write_text(text, encoding="utf-8")
updated = PATH.read_text(encoding="utf-8")
for proof in (
    marker,
    "public struct GhostBaseKnownUser",
    "ghostBaseRegisterKnownUser(",
    "register every received user",
    "TelegramUserPresence(status: .none",
    "public func ghostBaseKnownUsersReport",
):
    if proof not in updated:
        raise SystemExit(f"[V11A PRESENCE] proof missing: {proof}")
print("[V11A] global known-user presence registry installed")
