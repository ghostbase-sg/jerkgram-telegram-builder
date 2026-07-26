#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
settings = root / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
gift_item = root / "submodules/TelegramUI/Components/Gifts/GiftItemComponent/Sources/GiftItemComponent.swift"
gift_options = root / "submodules/TelegramUI/Components/Gifts/GiftOptionsScreen/Sources/GiftOptionsScreen.swift"
for path in (settings, gift_item, gift_options):
    if not path.exists():
        raise SystemExit(f"[V11E SETTINGS/GIFTS] missing {path}")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"[V11E SETTINGS/GIFTS] {label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)

text = settings.read_text(encoding="utf-8")
text = text.replace("// MARK: GhostBase v1.1D GLOBALGLASSTOGGLE2", "// MARK: GhostBase v1.1E GLOBALMATERIAL3")
old_info = "Единый визуальный слой профиля, настроек и подарков. Выключение полностью возвращает штатные поверхности Telegram. При Reduce Transparency и Low Power Mode эффекты автоматически облегчаются."
new_info = "Glass меняет только материал интерфейса. Данные, вкладки, логирование и высота секций не зависят от эффекта. При Reduce Transparency и Low Power Mode используются облегчённые поверхности."
if old_info in text:
    text = text.replace(old_info, new_info)
settings.write_text(text, encoding="utf-8")

text = gift_item.read_text(encoding="utf-8")
old_material = '''            // MARK: GhostBase v1.1D GIFTCELLSGLASS2 lightweight material, no per-cell blur
            if case .glass = component.style, GhostBaseGlassStyle.isEnabled {
                self.backgroundLayer.borderWidth = UIScreenPixel
                self.backgroundLayer.borderColor = GhostBaseGlassStyle.borderColor(.white).cgColor
                self.backgroundLayer.shadowColor = UIColor.black.cgColor
                self.backgroundLayer.shadowOpacity = GhostBaseGlassStyle.usesReducedEffects ? 0.0 : 0.12
                self.backgroundLayer.shadowRadius = 12.0
                self.backgroundLayer.shadowOffset = CGSize(width: 0.0, height: 5.0)
            } else {
                self.backgroundLayer.borderWidth = 0.0
                self.backgroundLayer.borderColor = nil
                self.backgroundLayer.shadowOpacity = 0.0
            }
'''
new_material = '''            // MARK: GhostBase v1.1E GIFTSURFACE3
            // Cells stay lightweight: no live blur, lens, transform or shadow per item.
            if case .glass = component.style, GhostBaseGlassStyle.isEnabled {
                self.backgroundLayer.borderWidth = UIScreenPixel
                self.backgroundLayer.borderColor = (component.theme.overallDarkAppearance ? UIColor.white.withAlphaComponent(0.14) : UIColor.white.withAlphaComponent(0.34)).cgColor
            } else {
                self.backgroundLayer.borderWidth = 0.0
                self.backgroundLayer.borderColor = nil
            }
            self.backgroundLayer.shadowOpacity = 0.0
            self.backgroundLayer.shadowRadius = 0.0
            self.backgroundLayer.shadowOffset = .zero
'''
if old_material in text:
    text = replace_once(text, old_material, new_material, "gift material")
elif "GhostBase v1.1E GIFTSURFACE3" not in text:
    raise SystemExit("[V11E SETTINGS/GIFTS] rejected gift material marker missing")

old_background = '''            if case .glass = component.style, GhostBaseGlassStyle.isEnabled {
                if let backgroundColor, let _ = secondBackgroundColor {
                    self.backgroundLayer.backgroundColor = backgroundColor.withAlphaComponent(GhostBaseGlassStyle.usesReducedEffects ? 0.80 : 0.46).cgColor
                } else if ![.buttonIcon, .tableIcon].contains(component.mode) {
                    let tint = GhostBaseGlassStyle.activeTintColor(fallback: component.theme.list.itemAccentColor)
                    self.backgroundLayer.backgroundColor = GhostBaseGlassStyle.lightweightTintColor(tint).cgColor
                }
            } else if let backgroundColor, let _ = secondBackgroundColor {
                self.backgroundLayer.backgroundColor = backgroundColor.cgColor
            } else {
                if [.buttonIcon, .tableIcon].contains(component.mode) {
                    
                } else if case .upgradePreview = component.mode {
                    self.backgroundLayer.backgroundColor = component.theme.list.itemModalBlocksBackgroundColor.cgColor
                } else {
                    self.backgroundLayer.backgroundColor = component.theme.list.itemBlocksBackgroundColor.cgColor
                }
            }
'''
new_background = '''            if case .glass = component.style, GhostBaseGlassStyle.isEnabled {
                if let backgroundColor, let _ = secondBackgroundColor {
                    self.backgroundLayer.backgroundColor = backgroundColor.withAlphaComponent(GhostBaseGlassStyle.usesReducedEffects ? 0.86 : 0.54).cgColor
                } else if ![.buttonIcon, .tableIcon].contains(component.mode) {
                    // Theme-derived neutral surface. Never inherit a stale peer tint.
                    let base = component.theme.list.itemBlocksBackgroundColor
                    self.backgroundLayer.backgroundColor = base.withAlphaComponent(GhostBaseGlassStyle.usesReducedEffects ? 0.92 : 0.58).cgColor
                }
            } else if let backgroundColor, let _ = secondBackgroundColor {
                self.backgroundLayer.backgroundColor = backgroundColor.cgColor
            } else {
                if [.buttonIcon, .tableIcon].contains(component.mode) {
                    
                } else if case .upgradePreview = component.mode {
                    self.backgroundLayer.backgroundColor = component.theme.list.itemModalBlocksBackgroundColor.cgColor
                } else {
                    self.backgroundLayer.backgroundColor = component.theme.list.itemBlocksBackgroundColor.cgColor
                }
            }
'''
if old_background in text:
    text = replace_once(text, old_background, new_background, "gift background")
elif "Theme-derived neutral surface" not in text:
    raise SystemExit("[V11E SETTINGS/GIFTS] gift background anchor missing")

gift_item.write_text(text, encoding="utf-8")

text = gift_options.read_text(encoding="utf-8")
text = text.replace("// MARK: GhostBase v1.1D GIFTCELLSGLASS2 actual cells use GiftItemComponent.Style.glass", "// MARK: GhostBase v1.1E GIFTSURFACE3 actual cells use lightweight style")
gift_options.write_text(text, encoding="utf-8")

print("[V11E] GLOBALMATERIAL3 + GIFTSURFACE3 installed: no disappearing data, no per-cell blur/shadow")
