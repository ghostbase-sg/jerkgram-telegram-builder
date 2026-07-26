#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
options = root / "submodules/TelegramUI/Components/Gifts/GiftOptionsScreen/Sources/GiftOptionsScreen.swift"
item = root / "submodules/TelegramUI/Components/Gifts/GiftItemComponent/Sources/GiftItemComponent.swift"
for p in [options, item]:
    if not p.is_file(): raise SystemExit(f"[V11D GIFTS] missing {p}")

# Remove rejected screen-only alpha changes. The new work changes actual gift cells.
text = options.read_text(encoding="utf-8")
text = text.replace("            // MARK: GhostBase v1.1C GIFTSGLASS1 lightweight surfaces\n            self.topEdgeEffectView.update(content: GhostBaseGlassStyle.lightweightFillColor(theme.list.blocksBackgroundColor), blur: !GhostBaseGlassStyle.usesReducedEffects, alpha: 1.0, rect: topEdgeEffectFrame, edge: .top, edgeSize: topEdgeEffectFrame.height, transition: transition)\n", "            self.topEdgeEffectView.update(content: theme.list.blocksBackgroundColor, blur: true, alpha: 1.0, rect: topEdgeEffectFrame, edge: .top, edgeSize: topEdgeEffectFrame.height, transition: transition)\n")
text = text.replace("            self.bottomEdgeEffectView.update(content: GhostBaseGlassStyle.lightweightFillColor(theme.list.blocksBackgroundColor), blur: !GhostBaseGlassStyle.usesReducedEffects, alpha: 1.0, rect: bottomEdgeEffectFrame, edge: .bottom, edgeSize: bottomEdgeEffectFrame.height, transition: transition)\n", "            self.bottomEdgeEffectView.update(content: theme.list.blocksBackgroundColor, blur: true, alpha: 1.0, rect: bottomEdgeEffectFrame, edge: .bottom, edgeSize: bottomEdgeEffectFrame.height, transition: transition)\n")
text = text.replace("                self.backgroundColor = GhostBaseGlassStyle.lightweightFillColor(theme.list.blocksBackgroundColor)\n", "                self.backgroundColor = theme.list.blocksBackgroundColor\n")
if "GhostBase v1.1D GIFTCELLSGLASS2" not in text:
    marker = "import GlassBarButtonComponent\n"
    text = text.replace(marker, marker + "\n// MARK: GhostBase v1.1D GIFTCELLSGLASS2 actual cells use GiftItemComponent.Style.glass\n", 1)
options.write_text(text, encoding="utf-8")

text = item.read_text(encoding="utf-8")
if "GhostBase v1.1D GIFTCELLSGLASS2" not in text:
    # Border is lightweight; no blur per gift cell.
    anchor = "            self.backgroundLayer.cornerRadius = cornerRadius\n"
    insert = '''            self.backgroundLayer.cornerRadius = cornerRadius\n            // MARK: GhostBase v1.1D GIFTCELLSGLASS2 lightweight material, no per-cell blur\n            if case .glass = component.style, GhostBaseGlassStyle.isEnabled {\n                self.backgroundLayer.borderWidth = UIScreenPixel\n                self.backgroundLayer.borderColor = GhostBaseGlassStyle.borderColor(.white).cgColor\n                self.backgroundLayer.shadowColor = UIColor.black.cgColor\n                self.backgroundLayer.shadowOpacity = GhostBaseGlassStyle.usesReducedEffects ? 0.0 : 0.12\n                self.backgroundLayer.shadowRadius = 12.0\n                self.backgroundLayer.shadowOffset = CGSize(width: 0.0, height: 5.0)\n            } else {\n                self.backgroundLayer.borderWidth = 0.0\n                self.backgroundLayer.borderColor = nil\n                self.backgroundLayer.shadowOpacity = 0.0\n            }\n'''
    if anchor not in text: raise SystemExit("[V11D GIFTS] corner anchor missing")
    text = text.replace(anchor, insert, 1)

    old = '''            if let backgroundColor, let _ = secondBackgroundColor {\n                self.backgroundLayer.backgroundColor = backgroundColor.cgColor\n            } else {\n                if [.buttonIcon, .tableIcon].contains(component.mode) {\n                    \n                } else if case .upgradePreview = component.mode {\n                    self.backgroundLayer.backgroundColor = component.theme.list.itemModalBlocksBackgroundColor.cgColor\n                } else {\n                    self.backgroundLayer.backgroundColor = component.theme.list.itemBlocksBackgroundColor.cgColor\n                }\n            }\n'''
    new = '''            if case .glass = component.style, GhostBaseGlassStyle.isEnabled {\n                if let backgroundColor, let _ = secondBackgroundColor {\n                    self.backgroundLayer.backgroundColor = backgroundColor.withAlphaComponent(GhostBaseGlassStyle.usesReducedEffects ? 0.80 : 0.46).cgColor\n                } else if ![.buttonIcon, .tableIcon].contains(component.mode) {\n                    let tint = GhostBaseGlassStyle.activeTintColor(fallback: component.theme.list.itemAccentColor)\n                    self.backgroundLayer.backgroundColor = GhostBaseGlassStyle.lightweightTintColor(tint).cgColor\n                }\n            } else if let backgroundColor, let _ = secondBackgroundColor {\n                self.backgroundLayer.backgroundColor = backgroundColor.cgColor\n            } else {\n                if [.buttonIcon, .tableIcon].contains(component.mode) {\n                    \n                } else if case .upgradePreview = component.mode {\n                    self.backgroundLayer.backgroundColor = component.theme.list.itemModalBlocksBackgroundColor.cgColor\n                } else {\n                    self.backgroundLayer.backgroundColor = component.theme.list.itemBlocksBackgroundColor.cgColor\n                }\n            }\n'''
    if old not in text: raise SystemExit("[V11D GIFTS] actual cell background anchor missing")
    text = text.replace(old, new, 1)
    item.write_text(text, encoding="utf-8")
print("[V11D] GIFTCELLSGLASS2 actual gift surfaces installed")
