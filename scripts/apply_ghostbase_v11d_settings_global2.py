#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
text = path.read_text(encoding="utf-8")
if "GhostBase v1.1D GLOBALGLASSTOGGLE2" in text:
    print("[V11D] GLOBALGLASSTOGGLE2 already installed")
    raise SystemExit(0)
if 'static let glassEnabled = "GhostBase.Glass.Enabled"' not in text:
    raise SystemExit("[V11D SETTINGS] v1.1C Glass toggle missing")
old = '''            case GhostBaseKey.glassEnabled:\n                updated.glassEnabled = value\n                UserDefaults.standard.set(\n                    value,\n                    forKey: GhostBaseKey.glassEnabled\n                )\n\n'''
new = '''            case GhostBaseKey.glassEnabled:\n                // MARK: GhostBase v1.1D GLOBALGLASSTOGGLE2\n                updated.glassEnabled = value\n                GhostBaseGlassStyle.setEnabled(value)\n\n'''
if old not in text:
    raise SystemExit("[V11D SETTINGS] toggle action anchor missing")
text = text.replace(old, new, 1)
text = text.replace("Единая система Glass. При Reduce Transparency и Low Power Mode эффекты автоматически облегчаются.", "Единый визуальный слой профиля, настроек и подарков. Выключение полностью возвращает штатные поверхности Telegram. При Reduce Transparency и Low Power Mode эффекты автоматически облегчаются.", 1)
path.write_text(text, encoding="utf-8")
print("[V11D] GLOBALGLASSTOGGLE2 installed")
