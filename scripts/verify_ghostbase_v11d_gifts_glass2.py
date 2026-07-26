#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
item = (root / "submodules/TelegramUI/Components/Gifts/GiftItemComponent/Sources/GiftItemComponent.swift").read_text(encoding="utf-8")
options = (root / "submodules/TelegramUI/Components/Gifts/GiftOptionsScreen/Sources/GiftOptionsScreen.swift").read_text(encoding="utf-8")
for marker in ["GIFTCELLSGLASS2 lightweight material", "lightweightTintColor", "borderColor", "no per-cell blur"]:
    if marker not in item: raise SystemExit(f"[VERIFY V11D GIFTS] missing {marker}")
if "style: .glass" not in options: raise SystemExit("[VERIFY V11D GIFTS] GiftOptions no longer requests glass style")
if "GIFTSGLASS1 lightweight surfaces" in options: raise SystemExit("[VERIFY V11D GIFTS] rejected screen-only patch remains")
print("[VERIFY V11D GIFTS] OK")
