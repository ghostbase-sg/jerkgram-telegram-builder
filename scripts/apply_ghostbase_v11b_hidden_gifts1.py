#!/usr/bin/env python3
import os
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/ports/ghostbase_12_9_2_port/telegram-ios-12.9.2-official"))
PATH = ROOT / "submodules/TelegramCore/Sources/TelegramEngine/Payments/StarGifts.swift"
MARKER = "// MARK: GhostBase v1.1B HIDDENGIFTS1 derived local archive"
if not PATH.is_file():
    raise SystemExit(f"[HIDDENGIFTS1] missing source: {PATH}")
text = PATH.read_text(encoding="utf-8")
if MARKER in text:
    print("[HIDDENGIFTS1] already applied")
    raise SystemExit(0)
anchor = "public func ghostBaseGiftHistoryReport(\n"
if anchor not in text or "public struct GhostBaseGiftHistoryEntry" not in text:
    raise SystemExit("[HIDDENGIFTS1] GIFTHISTORY1 prerequisite missing")
pos = text.index(anchor)
helper = r'''// MARK: GhostBase v1.1B HIDDENGIFTS1 derived local archive
public func ghostBaseHiddenGiftHistoryEntries(
    accountPeerId: EnginePeer.Id,
    peerId: EnginePeer.Id
) -> [GhostBaseGiftHistoryEntry] {
    return ghostBaseGiftHistoryEntries(
        accountPeerId: accountPeerId,
        peerId: peerId
    ).filter { entry in
        if !entry.savedToProfile {
            return true
        }
        guard let lastVisibility = entry.visibilityHistory.last else {
            return false
        }
        return !lastVisibility.savedToProfile
    }
}

public func ghostBaseHiddenGiftHistoryReport(
    accountPeerId: EnginePeer.Id,
    peerId: EnginePeer.Id
) -> String {
    let entries = ghostBaseHiddenGiftHistoryEntries(
        accountPeerId: accountPeerId,
        peerId: peerId
    )
    var lines: [String] = ["Скрытые подарки GhostBase: \(entries.count)"]
    for entry in entries {
        let sender = entry.nameHidden
            ? "анонимно"
            : (entry.fromPeerTitle ?? entry.fromPeerUsername ?? entry.fromPeerId.map(String.init) ?? "неизвестно")
        let title: String
        if let number = entry.number {
            title = "\(entry.title) #\(number)"
        } else {
            title = entry.title
        }
        var details: [String] = [
            "\(entry.giftDate)",
            title,
            "Отправитель: \(sender)"
        ]
        if let text = entry.text, !text.isEmpty {
            details.append("Подпись: \(text)")
        }
        if let slug = entry.slug, !slug.isEmpty {
            details.append("slug=\(slug)")
        }
        lines.append(details.joined(separator: " · "))
    }
    return lines.joined(separator: "\n")
}

'''
text = text[:pos] + helper + text[pos:]
PATH.write_text(text, encoding="utf-8")
updated = PATH.read_text(encoding="utf-8")
for proof in (MARKER, "ghostBaseHiddenGiftHistoryEntries", "ghostBaseHiddenGiftHistoryReport", ".filter { entry in"):
    if proof not in updated:
        raise SystemExit(f"[HIDDENGIFTS1] proof missing: {proof}")
print("[HIDDENGIFTS1] installed")
