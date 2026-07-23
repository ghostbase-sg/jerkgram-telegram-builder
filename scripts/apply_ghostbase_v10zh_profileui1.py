#!/usr/bin/env python3

import os
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
PATH = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"
if not PATH.is_file():
    raise SystemExit(f"[V10ZH PROFILEUI1] missing source: {PATH}")

text = PATH.read_text(encoding="utf-8")
for required in (
    "// MARK: GhostBase v1.0ZG GIFTHISTORY1 profile action",
    "// MARK: GhostBase v1.0ZG PROFILEINTEL3 personal channel storage",
):
    if required not in text:
        raise SystemExit(f"[V10ZH PROFILEUI1] Build 85 marker missing: {required}")


def replace_optional(value: str, old: str, new: str) -> str:
    if old in value:
        return value.replace(old, new, 1)
    return value


marker = "// MARK: GhostBase v1.0ZH PROFILEUI1 integrated profile cards"
if marker not in text:
    anchor = """private let enabledPublicBioEntities: EnabledEntityTypes = [.allUrl, .mention, .hashtag]
private let enabledPrivateBioEntities: EnabledEntityTypes = [.internalUrl, .mention, .hashtag]
"""
    if anchor not in text:
        raise SystemExit("[V10ZH PROFILEUI1] top helper anchor missing")
    helper = anchor + r'''

// MARK: GhostBase v1.0ZH PROFILEUI1 integrated profile cards
private func ghostBaseProfilePreview(
    _ report: String,
    maxLines: Int
) -> String {
    let lines = report.split(separator: "\n", omittingEmptySubsequences: true)
    guard !lines.isEmpty else {
        return report
    }
    let body = lines.dropFirst().prefix(maxLines)
    if body.isEmpty {
        return String(lines[0])
    }
    return body.joined(separator: "\n")
}

private func ghostBaseProfileDateText(_ timestamp: Int64) -> String {
    let formatter = DateFormatter()
    formatter.locale = Locale(identifier: "ru_RU")
    formatter.dateFormat = "dd.MM.yyyy HH:mm"
    return formatter.string(
        from: Date(timeIntervalSince1970: TimeInterval(timestamp))
    )
}
'''
    text = text.replace(anchor, helper, 1)

    # Human-readable dates in the already installed personal-channel report.
    text = replace_optional(
        text,
        '"\\(event.observedAt) · id=\\(channelPeerId) · title=\\(event.title ?? "nil")',
        '"\\(ghostBaseProfileDateText(event.observedAt)) · id=\\(channelPeerId) · title=\\(event.title ?? "nil")',
    )
    text = replace_optional(
        text,
        'lines.append("\\(event.observedAt) · канал откреплён")',
        'lines.append("\\(ghostBaseProfileDateText(event.observedAt)) · канал откреплён")',
    )

    function_start = text.find("func infoItems(\n")
    result_anchor = "    var result: [(AnyHashable, [PeerInfoScreenItem])] = []\n"
    insert_at = text.find(result_anchor, function_start)
    if function_start == -1 or insert_at == -1:
        raise SystemExit("[V10ZH PROFILEUI1] infoItems result anchor missing")

    block = r'''    // MARK: GhostBase v1.0ZH PROFILEUI1 integrated profile cards
    if case let .user(user) = data.peer {
        let ghostBaseGiftEntries = ghostBaseGiftHistoryEntries(
            accountPeerId: context.account.peerId,
            peerId: user.id
        )
        if !ghostBaseGiftEntries.isEmpty {
            let report = ghostBaseGiftHistoryReport(
                accountPeerId: context.account.peerId,
                peerId: user.id
            )
            items[.peerInfoTrailing]!.append(
                PeerInfoScreenInfoItem(
                    id: 9872001,
                    title: "GhostBase · Подарки",
                    text: .markdown(ghostBaseProfilePreview(report, maxLines: 4)),
                    style: .compact,
                    linkAction: nil
                )
            )
        }

        if let report = ghostBasePersonalChannelReport(
            accountPeerId: context.account.peerId,
            targetPeerId: user.id
        ) {
            items[.peerInfoTrailing]!.append(
                PeerInfoScreenInfoItem(
                    id: 9872002,
                    title: "GhostBase · Прикреплённый канал",
                    text: .markdown(ghostBaseProfilePreview(report, maxLines: 4)),
                    style: .compact,
                    linkAction: nil
                )
            )
        }

        if let report = ghostBasePresenceHistoryReport(
            accountPeerId: context.account.peerId,
            peerId: user.id
        ) {
            items[.peerInfoTrailing]!.append(
                PeerInfoScreenInfoItem(
                    id: 9872003,
                    title: "GhostBase · Присутствие",
                    text: .markdown(ghostBaseProfilePreview(report, maxLines: 6)),
                    style: .compact,
                    linkAction: nil
                )
            )
            items[.peerInfoTrailing]!.append(
                PeerInfoScreenActionItem(
                    id: 9871004,
                    text: "Скопировать полную историю присутствия",
                    color: .accent,
                    icon: nil,
                    alignment: .natural,
                    action: {
                        UIPasteboard.general.string = report
                    }
                )
            )
        }
    }

'''
    text = text[:insert_at] + block + text[insert_at:]

    text = replace_optional(
        text,
        'text: "История подарков GhostBase (\\(ghostBaseGiftEntries.count))",',
        'text: "Скопировать полный отчёт о подарках (\\(ghostBaseGiftEntries.count))",',
    )
    text = replace_optional(
        text,
        'text: "Скопировать историю прикреплённого канала",',
        'text: "Скопировать полный отчёт о прикреплённом канале",',
    )

PATH.write_text(text, encoding="utf-8")
updated = PATH.read_text(encoding="utf-8")
for proof in (
    marker,
    "GhostBase · Подарки",
    "GhostBase · Прикреплённый канал",
    "GhostBase · Присутствие",
    "ghostBasePresenceHistoryReport(",
    "Скопировать полную историю присутствия",
    "PeerInfoScreenInfoItem(",
):
    if proof not in updated:
        raise SystemExit(f"[V10ZH PROFILEUI1] proof missing: {proof}")
print("[V10ZH] PROFILEUI1 applied: gifts, personal channel and presence are visible as profile cards")
