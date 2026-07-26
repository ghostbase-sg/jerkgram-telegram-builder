#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramUI/Components/Gifts/GiftOptionsScreen/Sources/GiftOptionsScreen.swift"
text = path.read_text(encoding="utf-8")

if "GhostBase v1.1C GIFTSGLASS1" in text:
    print("[V11C] GIFTSGLASS1 already installed")
    raise SystemExit(0)

old_top = "            self.topEdgeEffectView.update(content: theme.list.blocksBackgroundColor, blur: true, alpha: 1.0, rect: topEdgeEffectFrame, edge: .top, edgeSize: topEdgeEffectFrame.height, transition: transition)\n"
new_top = "            // MARK: GhostBase v1.1C GIFTSGLASS1 lightweight surfaces\n            self.topEdgeEffectView.update(content: GhostBaseGlassStyle.lightweightFillColor(theme.list.blocksBackgroundColor), blur: !GhostBaseGlassStyle.usesReducedEffects, alpha: 1.0, rect: topEdgeEffectFrame, edge: .top, edgeSize: topEdgeEffectFrame.height, transition: transition)\n"
if old_top not in text:
    raise SystemExit("[V11C GIFTSGLASS1] top edge anchor missing")
text = text.replace(old_top, new_top, 1)

old_bottom = "            self.bottomEdgeEffectView.update(content: theme.list.blocksBackgroundColor, blur: true, alpha: 1.0, rect: bottomEdgeEffectFrame, edge: .bottom, edgeSize: bottomEdgeEffectFrame.height, transition: transition)\n"
new_bottom = "            self.bottomEdgeEffectView.update(content: GhostBaseGlassStyle.lightweightFillColor(theme.list.blocksBackgroundColor), blur: !GhostBaseGlassStyle.usesReducedEffects, alpha: 1.0, rect: bottomEdgeEffectFrame, edge: .bottom, edgeSize: bottomEdgeEffectFrame.height, transition: transition)\n"
if old_bottom not in text:
    raise SystemExit("[V11C GIFTSGLASS1] bottom edge anchor missing")
text = text.replace(old_bottom, new_bottom, 1)

old_bg = "                self.backgroundColor = theme.list.blocksBackgroundColor\n"
new_bg = "                self.backgroundColor = GhostBaseGlassStyle.lightweightFillColor(theme.list.blocksBackgroundColor)\n"
if old_bg not in text:
    raise SystemExit("[V11C GIFTSGLASS1] background anchor missing")
text = text.replace(old_bg, new_bg, 1)

path.write_text(text, encoding="utf-8")
print("[V11C] GIFTSGLASS1 lightweight GiftOptions surfaces installed")
