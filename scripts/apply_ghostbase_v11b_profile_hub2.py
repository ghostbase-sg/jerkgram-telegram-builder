#!/usr/bin/env python3
import os
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/ports/ghostbase_12_9_2_port/telegram-ios-12.9.2-official"))
PATH = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"
MARKER = "// MARK: GhostBase v1.1B PROFILEHUB2 inline expandable profile block"
if not PATH.is_file():
    raise SystemExit(f"[PROFILEHUB2] missing source: {PATH}")
text = PATH.read_text(encoding="utf-8")
if MARKER in text:
    print("[PROFILEHUB2] already applied")
    raise SystemExit(0)
# Remove PROFILEHUB1 modal helper, if present.
old_marker = "// MARK: GhostBase v1.1A PROFILEHUB1 Telegram-style sheet"
if old_marker in text:
    start = text.index(old_marker)
    end = text.index("func infoItems(\n", start)
    text = text[:start] + text[end:]

# Remove PROFILEHUB1 row, if present.
row_marker = "    // MARK: GhostBase v1.1A PROFILEHUB1 profile row\n"
if row_marker in text:
    start = text.index(row_marker)
    end_candidates = [
        p for p in (
            text.find("    // MARK:", start + len(row_marker)),
            text.find("    var result: [(AnyHashable, [PeerInfoScreenItem])] = []", start),
        ) if p != -1
    ]
    if not end_candidates:
        raise SystemExit("[PROFILEHUB2] unable to remove PROFILEHUB1 row")
    text = text[:start] + text[min(end_candidates):]

insert_at = text.index("func infoItems(\n")
helper = r'''// MARK: GhostBase v1.1B PROFILEHUB2 inline expandable profile block
private enum GhostBaseProfileHubTab: Int, CaseIterable {
    case history = 0
    case gifts = 1
    case online = 2
    case channel = 3
    case info = 4

    var title: String {
        switch self {
        case .history: return "История"
        case .gifts: return "Подарки"
        case .online: return "Онлайн"
        case .channel: return "Канал"
        case .info: return "Сведения"
        }
    }
}

private func ghostBaseProfileHubStateKey(accountPeerId: EnginePeer.Id, peerId: EnginePeer.Id) -> String {
    return "GhostBase.ProfileHub2.\(accountPeerId.toInt64()).\(peerId.toInt64())"
}

private func ghostBaseProfileHubIsExpanded(accountPeerId: EnginePeer.Id, peerId: EnginePeer.Id) -> Bool {
    return UserDefaults.standard.bool(forKey: ghostBaseProfileHubStateKey(accountPeerId: accountPeerId, peerId: peerId) + ".expanded")
}

private func ghostBaseProfileHubSelectedTab(accountPeerId: EnginePeer.Id, peerId: EnginePeer.Id) -> GhostBaseProfileHubTab {
    let raw = UserDefaults.standard.integer(forKey: ghostBaseProfileHubStateKey(accountPeerId: accountPeerId, peerId: peerId) + ".tab")
    return GhostBaseProfileHubTab(rawValue: raw) ?? .history
}

private func ghostBaseProfileHubSetExpanded(_ value: Bool, accountPeerId: EnginePeer.Id, peerId: EnginePeer.Id) {
    UserDefaults.standard.set(value, forKey: ghostBaseProfileHubStateKey(accountPeerId: accountPeerId, peerId: peerId) + ".expanded")
}

private func ghostBaseProfileHubSetSelectedTab(_ value: GhostBaseProfileHubTab, accountPeerId: EnginePeer.Id, peerId: EnginePeer.Id) {
    UserDefaults.standard.set(value.rawValue, forKey: ghostBaseProfileHubStateKey(accountPeerId: accountPeerId, peerId: peerId) + ".tab")
}

private func ghostBaseProfileDateText(_ timestamp: Int64) -> String {
    let formatter = DateFormatter()
    formatter.locale = Locale(identifier: "ru_RU")
    formatter.dateFormat = "dd.MM.yyyy HH:mm"
    return formatter.string(from: Date(timeIntervalSince1970: TimeInterval(timestamp)))
}

private func ghostBaseProfileHubBody(_ report: String, empty: String) -> String {
    let lines = report.split(separator: "\n", omittingEmptySubsequences: true).map(String.init)
    let body = lines.first?.contains(":") == true ? Array(lines.dropFirst()) : lines
    if body.isEmpty {
        return empty
    }
    return body.prefix(40).joined(separator: "\n\n")
}

'''
text = text[:insert_at] + helper + text[insert_at:]

result_anchor = "    var result: [(AnyHashable, [PeerInfoScreenItem])] = []\n"
function_start = text.index("func infoItems(\n")
result_pos = text.index(result_anchor, function_start)
row = r'''    // MARK: GhostBase v1.1B PROFILEHUB2 inline rows
    if case let .user(user) = data.peer {
        let accountPeerId = context.account.peerId
        let targetPeerId = user.id
        let expanded = ghostBaseProfileHubIsExpanded(accountPeerId: accountPeerId, peerId: targetPeerId)
        let selectedTab = ghostBaseProfileHubSelectedTab(accountPeerId: accountPeerId, peerId: targetPeerId)
        let hiddenGiftCount = ghostBaseHiddenGiftHistoryEntries(accountPeerId: accountPeerId, peerId: targetPeerId).count

        items[.peerInfoTrailing]!.append(
            PeerInfoScreenDisclosureItem(
                id: 9911200,
                label: .text(expanded ? "Свернуть" : "Открыть"),
                text: "История и сведения",
                icon: nil,
                action: {
                    ghostBaseProfileHubSetExpanded(!expanded, accountPeerId: accountPeerId, peerId: targetPeerId)
                    interaction.requestLayout(true)
                }
            )
        )

        if expanded {
            for tab in GhostBaseProfileHubTab.allCases {
                let suffix: String
                if tab == .gifts && hiddenGiftCount > 0 {
                    suffix = " · скрытых: \(hiddenGiftCount)"
                } else {
                    suffix = ""
                }
                items[.peerInfoTrailing]!.append(
                    PeerInfoScreenActionItem(
                        id: 9911210 + tab.rawValue,
                        text: (tab == selectedTab ? "✓ " : "") + tab.title + suffix,
                        color: .accent,
                        icon: nil,
                        alignment: .natural,
                        action: {
                            ghostBaseProfileHubSetSelectedTab(tab, accountPeerId: accountPeerId, peerId: targetPeerId)
                            interaction.requestLayout(true)
                        }
                    )
                )
            }

            let report: String
            let empty: String
            switch selectedTab {
            case .history:
                let gifts = ghostBaseGiftHistoryReport(accountPeerId: accountPeerId, peerId: targetPeerId)
                let presence = ghostBasePresenceHistoryReport(accountPeerId: accountPeerId, peerId: targetPeerId) ?? ""
                let channel = ghostBasePersonalChannelReport(accountPeerId: accountPeerId, targetPeerId: targetPeerId) ?? ""
                report = [gifts, presence, channel].filter { !$0.isEmpty }.joined(separator: "\n")
                empty = "Пока нет сохранённых изменений."
            case .gifts:
                let hidden = ghostBaseHiddenGiftHistoryReport(accountPeerId: accountPeerId, peerId: targetPeerId)
                let all = ghostBaseGiftHistoryReport(accountPeerId: accountPeerId, peerId: targetPeerId)
                report = hiddenGiftCount > 0 ? hidden + "\n\n" + all : all
                empty = "Подарки пока не наблюдались."
            case .online:
                report = ghostBasePresenceHistoryReport(accountPeerId: accountPeerId, peerId: targetPeerId) ?? ""
                empty = "Статусы присутствия пока не получены."
            case .channel:
                report = ghostBasePersonalChannelReport(accountPeerId: accountPeerId, targetPeerId: targetPeerId) ?? ""
                empty = "Прикреплённый канал пока не наблюдался."
            case .info:
                let username = user.addressName.map { "@\($0)" } ?? "не указан"
                report = "Peer ID: \(user.id.toInt64())\nUsername: \(username)\nСкрытых подарков: \(hiddenGiftCount)"
                empty = "Сведения отсутствуют."
            }

            items[.peerInfoTrailing]!.append(
                PeerInfoScreenLabeledValueItem(
                    id: 9911299,
                    label: selectedTab.title,
                    text: ghostBaseProfileHubBody(report, empty: empty),
                    textColor: .primary,
                    textBehavior: .multiLine(maxLines: 100, enabledEntities: []),
                    action: nil,
                    requestLayout: { animated in
                        interaction.requestLayout(animated)
                    }
                )
            )
        }
    }

'''
text = text[:result_pos] + row + text[result_pos:]
PATH.write_text(text, encoding="utf-8")
updated = PATH.read_text(encoding="utf-8")
for proof in (MARKER, "PROFILEHUB2 inline rows", "ghostBaseProfileHubSetExpanded", "ghostBaseHiddenGiftHistoryReport", "interaction.requestLayout(true)"):
    if proof not in updated:
        raise SystemExit(f"[PROFILEHUB2] proof missing: {proof}")
for forbidden in ("GhostBaseHistoryHubController", "presentationAnimation: .modalSheet", "navigationPresentation = .modal"):
    if forbidden in updated:
        raise SystemExit(f"[PROFILEHUB2] modal residue remains: {forbidden}")
print("[PROFILEHUB2] inline expandable hub installed")
