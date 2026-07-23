#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"
if not path.is_file():
    raise SystemExit(f"[V10ZG GIFTHISTORY1 UI] missing source: {path}")

text = path.read_text(encoding="utf-8")
marker = "// MARK: GhostBase v1.0ZG GIFTHISTORY1 profile action"
if marker not in text:
    function_start = text.find("func infoItems(\n")
    result_anchor = "    var result: [(AnyHashable, [PeerInfoScreenItem])] = []\n"
    insert_at = text.find(result_anchor, function_start)
    if function_start == -1 or insert_at == -1:
        raise SystemExit("[V10ZG GIFTHISTORY1 UI] infoItems result anchor missing")
    block = r'''    // MARK: GhostBase v1.0ZG GIFTHISTORY1 profile action
    if case let .user(user) = data.peer {
        let ghostBaseGiftEntries = ghostBaseGiftHistoryEntries(
            accountPeerId: context.account.peerId,
            peerId: user.id
        )
        if !ghostBaseGiftEntries.isEmpty {
            items[.peerInfoTrailing]!.append(
                PeerInfoScreenActionItem(
                    id: 9871003,
                    text: "История подарков GhostBase (\(ghostBaseGiftEntries.count))",
                    color: .accent,
                    icon: nil,
                    alignment: .natural,
                    action: {
                        UIPasteboard.general.string = ghostBaseGiftHistoryReport(
                            accountPeerId: context.account.peerId,
                            peerId: user.id
                        )
                    }
                )
            )
        }
    }

'''
    text = text[:insert_at] + block + text[insert_at:]
    path.write_text(text, encoding="utf-8")

text = path.read_text(encoding="utf-8")
for proof in (
    marker,
    "ghostBaseGiftHistoryEntries(",
    "ghostBaseGiftHistoryReport(",
    "История подарков GhostBase",
):
    if proof not in text:
        raise SystemExit(f"[V10ZG GIFTHISTORY1 UI] proof missing: {proof}")
print("[V10ZG] GIFTHISTORY1 profile action applied")
