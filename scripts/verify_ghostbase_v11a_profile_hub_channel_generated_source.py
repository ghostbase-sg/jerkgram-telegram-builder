#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"
text = path.read_text(encoding="utf-8")
for proof in (
    "GhostBase v1.1A PERSONALCHANNEL2 confirmed observation",
    "case .unknown:",
    "GhostBase v1.1A PROFILEHUB1 Telegram-style sheet",
    'self.titleLabel.text = "История и сведения"',
    'text: "История и сведения"',
    'GhostBaseHistoryHubSection(title: "Подарки"',
    'GhostBaseHistoryHubSection(title: "Онлайн"',
    "presentationAnimation: .modalSheet",
):
    if proof not in text:
        raise SystemExit(f"[V11A verifier] profile proof missing: {proof}")
for forbidden in (
    'title: "GhostBase · Подарки"',
    'title: "GhostBase · Прикреплённый канал"',
    'title: "GhostBase · Присутствие"',
):
    if forbidden in text:
        raise SystemExit(f"[V11A verifier] old expanded profile UI remains: {forbidden}")
print("[V11A verifier] profile hub and personal channel baseline OK")
