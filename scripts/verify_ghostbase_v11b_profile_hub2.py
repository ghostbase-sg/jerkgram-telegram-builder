#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/ports/ghostbase_12_9_2_port/telegram-ios-12.9.2-official"))
p = root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"
text = p.read_text(encoding="utf-8")
required = ["GhostBase v1.1B PROFILEHUB2", "PROFILEHUB2 inline rows", "GhostBaseProfileHubTab", "interaction.requestLayout(true)", "ghostBaseHiddenGiftHistoryReport"]
forbidden = ["GhostBaseHistoryHubController", "presentationAnimation: .modalSheet", "navigationPresentation = .modal"]
missing = [x for x in required if x not in text]
remain = [x for x in forbidden if x in text]
if missing: raise SystemExit("[VERIFY PROFILEHUB2] missing: " + ", ".join(missing))
if remain: raise SystemExit("[VERIFY PROFILEHUB2] modal residue: " + ", ".join(remain))
print("[VERIFY PROFILEHUB2] OK")
