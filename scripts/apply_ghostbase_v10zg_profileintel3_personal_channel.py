#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"
if not path.is_file():
    raise SystemExit(f"[V10ZG PROFILEINTEL3] missing source: {path}")

text = path.read_text(encoding="utf-8")
helper_marker = "// MARK: GhostBase v1.0ZG PROFILEINTEL3 personal channel storage"

if helper_marker not in text:
    anchor = """private let enabledPublicBioEntities: EnabledEntityTypes = [.allUrl, .mention, .hashtag]
private let enabledPrivateBioEntities: EnabledEntityTypes = [.internalUrl, .mention, .hashtag]
"""
    if anchor not in text:
        raise SystemExit("[V10ZG PROFILEINTEL3] top-level helper anchor missing")
    helper = anchor + r'''

// MARK: GhostBase v1.0ZG PROFILEINTEL3 personal channel storage
private struct GhostBasePersonalChannelObservation: Codable, Equatable {
    let observedAt: Int64
    let channelPeerId: Int64?
    let title: String?
    let username: String?
    let link: String?
    let subscriberCount: Int?
    let topMessageId: Int32?
}

private struct GhostBasePersonalChannelHistory: Codable {
    var current: GhostBasePersonalChannelObservation
    var events: [GhostBasePersonalChannelObservation]
}

private func ghostBasePersonalChannelKey(
    accountPeerId: EnginePeer.Id,
    targetPeerId: EnginePeer.Id
) -> String {
    return "GhostBase.ProfileIntel3.PersonalChannel.\(accountPeerId.toInt64()).\(targetPeerId.toInt64())"
}

private func ghostBasePersonalChannelObservation(
    _ personalChannel: PeerInfoPersonalChannelData?
) -> GhostBasePersonalChannelObservation {
    let channelPeer = personalChannel?.peer.peer
    let username = channelPeer?.addressName
    return GhostBasePersonalChannelObservation(
        observedAt: Int64(Date().timeIntervalSince1970),
        channelPeerId: channelPeer?.id.toInt64(),
        title: channelPeer?.compactDisplayTitle,
        username: username,
        link: username.flatMap { "https://t.me/\($0)" },
        subscriberCount: personalChannel?.subscriberCount,
        topMessageId: personalChannel?.topMessages.first?.id.id
    )
}

private func ghostBaseRecordPersonalChannel(
    accountPeerId: EnginePeer.Id,
    targetPeerId: EnginePeer.Id,
    personalChannel: PeerInfoPersonalChannelData?
) {
    let key = ghostBasePersonalChannelKey(
        accountPeerId: accountPeerId,
        targetPeerId: targetPeerId
    )
    let current = ghostBasePersonalChannelObservation(personalChannel)
    let decoder = JSONDecoder()
    let encoder = JSONEncoder()

    var history: GhostBasePersonalChannelHistory
    if let data = UserDefaults.standard.data(forKey: key),
       let value = try? decoder.decode(GhostBasePersonalChannelHistory.self, from: data) {
        history = value
    } else {
        history = GhostBasePersonalChannelHistory(current: current, events: [])
    }

    let previous = history.current
    let meaningfulChange =
        previous.channelPeerId != current.channelPeerId
        || previous.title != current.title
        || previous.username != current.username

    if history.events.isEmpty || meaningfulChange {
        history.events.append(current)
        if history.events.count > 200 {
            history.events.removeFirst(history.events.count - 200)
        }
    }
    history.current = current

    if let data = try? encoder.encode(history) {
        UserDefaults.standard.set(data, forKey: key)
    }
}

private func ghostBasePersonalChannelReport(
    accountPeerId: EnginePeer.Id,
    targetPeerId: EnginePeer.Id
) -> String? {
    let key = ghostBasePersonalChannelKey(
        accountPeerId: accountPeerId,
        targetPeerId: targetPeerId
    )
    guard let data = UserDefaults.standard.data(forKey: key),
          let history = try? JSONDecoder().decode(
            GhostBasePersonalChannelHistory.self,
            from: data
          ) else {
        return nil
    }
    guard history.current.channelPeerId != nil
        || history.events.contains(where: { $0.channelPeerId != nil }) else {
        return nil
    }

    var lines: [String] = ["История прикреплённого канала"]
    for event in history.events.reversed() {
        if let channelPeerId = event.channelPeerId {
            lines.append(
                "\(event.observedAt) · id=\(channelPeerId) · title=\(event.title ?? "nil") · username=\(event.username ?? "nil") · link=\(event.link ?? "nil") · subscribers=\(event.subscriberCount.map(String.init) ?? "nil") · topMessageId=\(event.topMessageId.map(String.init) ?? "nil")"
            )
        } else {
            lines.append("\(event.observedAt) · канал откреплён")
        }
    }
    return lines.joined(separator: "\n")
}
'''
    text = text.replace(anchor, helper, 1)

record_marker = "// MARK: GhostBase v1.0ZG PROFILEINTEL3 observe personal channel"
if record_marker not in text:
    anchor = """        let ItemVerification = 9004
        let ItemCommunity = 10000
"""
    replacement = anchor + """
        // MARK: GhostBase v1.0ZG PROFILEINTEL3 observe personal channel
        ghostBaseRecordPersonalChannel(
            accountPeerId: context.account.peerId,
            targetPeerId: user.id,
            personalChannel: data.personalChannel
        )
"""
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(f"[V10ZG PROFILEINTEL3] user item anchor count: {count}")
    text = text.replace(anchor, replacement, 1)

ui_marker = "// MARK: GhostBase v1.0ZG PROFILEINTEL3 history action"
if ui_marker not in text:
    function_start = text.find("func infoItems(\n")
    result_anchor = "    var result: [(AnyHashable, [PeerInfoScreenItem])] = []\n"
    insert_at = text.find(result_anchor, function_start)
    if function_start == -1 or insert_at == -1:
        raise SystemExit("[V10ZG PROFILEINTEL3] infoItems result anchor missing")
    block = r'''    // MARK: GhostBase v1.0ZG PROFILEINTEL3 history action
    if case let .user(user) = data.peer,
       let ghostBaseChannelReport = ghostBasePersonalChannelReport(
        accountPeerId: context.account.peerId,
        targetPeerId: user.id
       ) {
        items[.peerInfoTrailing]!.append(
            PeerInfoScreenActionItem(
                id: 9871002,
                text: "Скопировать историю прикреплённого канала",
                color: .accent,
                icon: nil,
                alignment: .natural,
                action: {
                    UIPasteboard.general.string = ghostBaseChannelReport
                }
            )
        )
    }

'''
    text = text[:insert_at] + block + text[insert_at:]

path.write_text(text, encoding="utf-8")

text = path.read_text(encoding="utf-8")
for proof in (
    helper_marker,
    record_marker,
    ui_marker,
    "channelPeerId",
    "subscriberCount",
    "topMessageId",
    "Скопировать историю прикреплённого канала",
):
    if proof not in text:
        raise SystemExit(f"[V10ZG PROFILEINTEL3] proof missing: {proof}")

print("[V10ZG] PROFILEINTEL3 personal-channel storage/history applied")
