#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
settings = (root / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift").read_text(encoding="utf-8")
gift = (root / "submodules/TelegramUI/Components/Gifts/GiftItemComponent/Sources/GiftItemComponent.swift").read_text(encoding="utf-8")
options = (root / "submodules/TelegramUI/Components/Gifts/GiftOptionsScreen/Sources/GiftOptionsScreen.swift").read_text(encoding="utf-8")
if "GhostBaseGlassStyle.setEnabled(value)" not in settings:
    raise SystemExit("[VERIFY V11E SETTINGS/GIFTS] global toggle missing")
if "Данные, вкладки, логирование и высота секций не зависят от эффекта" not in settings:
    raise SystemExit("[VERIFY V11E SETTINGS/GIFTS] material-only contract missing")
for value in ["GhostBase v1.1E GIFTSURFACE3", "no live blur, lens, transform or shadow per item", "shadowOpacity = 0.0"]:
    if value not in gift:
        raise SystemExit(f"[VERIFY V11E SETTINGS/GIFTS] gift surface missing {value}")
for forbidden in ["activeTintColor", "lightweightTintColor", "shadowRadius = 12.0", "systemPurple"]:
    if forbidden in gift:
        raise SystemExit(f"[VERIFY V11E SETTINGS/GIFTS] rejected gift effect remains {forbidden}")
if "style: .glass" not in options:
    raise SystemExit("[VERIFY V11E SETTINGS/GIFTS] actual GiftItemComponent glass route missing")
print("[VERIFY V11E SETTINGS/GIFTS3] OK")
