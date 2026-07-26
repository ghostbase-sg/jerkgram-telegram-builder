#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
text = (root / "submodules/TelegramUI/Components/Gifts/GiftOptionsScreen/Sources/GiftOptionsScreen.swift").read_text(encoding="utf-8")
checks = {
    "marker": "GhostBase v1.1C GIFTSGLASS1" in text,
    "lightweight background": "GhostBaseGlassStyle.lightweightFillColor(theme.list.blocksBackgroundColor)" in text,
    "low-power edge fallback": text.count("blur: !GhostBaseGlassStyle.usesReducedEffects") == 2,
    "no gift-cell blur injection": "UIVisualEffectView" not in text,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("GIFTSGLASS1 VERIFY FAILED: " + ", ".join(failed))
print("GIFTSGLASS1 VERIFY OK")
