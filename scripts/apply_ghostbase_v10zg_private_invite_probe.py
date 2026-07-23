#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"
if not path.is_file():
    raise SystemExit(f"[V10ZG PRIVATELINK1] missing source: {path}")

text = path.read_text(encoding="utf-8")
marker = "// MARK: GhostBase v1.0ZG PRIVATELINK1 cached exported invite"

if marker not in text:
    function_start = text.find("func infoItems(\n")
    if function_start == -1:
        raise SystemExit("[V10ZG PRIVATELINK1] infoItems function not found")
    result_anchor = "    var result: [(AnyHashable, [PeerInfoScreenItem])] = []\n"
    insert_at = text.find(result_anchor, function_start)
    if insert_at == -1:
        raise SystemExit("[V10ZG PRIVATELINK1] infoItems result anchor not found")

    block = r'''    // MARK: GhostBase v1.0ZG PRIVATELINK1 cached exported invite
    switch data.peer {
    case .channel, .legacyGroup:
        var ghostBaseInviteLink: String?
        if let cachedData = data.cachedData as? CachedChannelData {
            ghostBaseInviteLink = cachedData.exportedInvitation?.link
        } else if let cachedData = data.cachedData as? CachedGroupData {
            ghostBaseInviteLink = cachedData.exportedInvitation?.link
        }

        let ghostBaseInviteStatusKey =
            "GhostBase.PrivateInvite.LastStatus.\(context.account.peerId.toInt64()).\(data.peer.id.toInt64())"
        if let ghostBaseInviteLink {
            items[.peerInfoTrailing]!.append(
                PeerInfoScreenActionItem(
                    id: 9871001,
                    text: "Скопировать пригласительную ссылку",
                    color: .accent,
                    icon: nil,
                    alignment: .natural,
                    action: {
                        UIPasteboard.general.string = ghostBaseInviteLink
                        UserDefaults.standard.set(
                            ghostBaseInviteLink,
                            forKey: ghostBaseInviteStatusKey
                        )
                    }
                )
            )
        } else {
            items[.peerInfoTrailing]!.append(
                PeerInfoScreenActionItem(
                    id: 9871001,
                    text: "Пригласительная ссылка не получена Telegram",
                    color: .destructive,
                    icon: nil,
                    alignment: .natural,
                    action: {
                        UserDefaults.standard.set(
                            "nil",
                            forKey: ghostBaseInviteStatusKey
                        )
                    }
                )
            )
        }
    default:
        break
    }

'''
    text = text[:insert_at] + block + text[insert_at:]
    path.write_text(text, encoding="utf-8")

text = path.read_text(encoding="utf-8")
for proof in (
    marker,
    "cachedData.exportedInvitation?.link",
    "Скопировать пригласительную ссылку",
    "Пригласительная ссылка не получена Telegram",
    "UIPasteboard.general.string",
):
    if proof not in text:
        raise SystemExit(f"[V10ZG PRIVATELINK1] proof missing: {proof}")

print("[V10ZG] PRIVATELINK1 read-only cached invite probe applied")
print("[V10ZG] no exportChatInvite/getExportedChatInvites RPC added")
