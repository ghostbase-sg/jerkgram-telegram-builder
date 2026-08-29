#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/ListItems/PeerInfoScreenLabeledValueItem.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_PROFILE_MORE_CUTOUT1"
RUNTIME_MARKER = "// MARK: Jerkgram v1.2M BUILD124_PROFILE_MORE_NO_OVERLAY1"

OLD = '''        let textLayout = self.textNode.updateLayoutInfo(CGSize(width: width - sideInset * 2.0 - additionalSideInset, height: .greatestFiniteMagnitude))
        let textSize = textLayout.size
        
        let additionalTextSize = self.additionalTextNode.updateLayout(CGSize(width: width - sideInset * 2.0, height: .greatestFiniteMagnitude))
        
        var displayMore = false
        if !self.isExpanded {
            if textLayout.truncated || text.count < item.text.count {
                displayMore = true
            }
        }
        
        if case .multiLine = item.textBehavior, displayMore {
            self.expandBackgroundNode.isHidden = false
            self.expandNode.isHidden = false
            self.expandButonNode.isHidden = false
        } else {
            self.expandBackgroundNode.isHidden = true
            self.expandNode.isHidden = true
            self.expandButonNode.isHidden = true
        }'''

NEW = '''        // MARK: Jerkgram v1.2M BUILD124_PROFILE_MORE_CUTOUT1
        // Measure once without a stale cutout, then reserve real layout space
        // for Telegram's "more" control instead of painting over live glyphs.
        self.textNode.cutout = nil
        var textLayout = self.textNode.updateLayoutInfo(CGSize(width: width - sideInset * 2.0 - additionalSideInset, height: .greatestFiniteMagnitude))
        var textSize = textLayout.size
        
        let additionalTextSize = self.additionalTextNode.updateLayout(CGSize(width: width - sideInset * 2.0, height: .greatestFiniteMagnitude))
        
        var displayMore = false
        if !self.isExpanded {
            if textLayout.truncated || text.count < item.text.count {
                displayMore = true
            }
        }
        
        if case .multiLine = item.textBehavior, displayMore {
            self.textNode.cutout = TextNodeCutout(bottomRight: CGSize(
                width: expandSize.width + 22.0,
                height: expandSize.height + 4.0
            ))
            textLayout = self.textNode.updateLayoutInfo(CGSize(width: width - sideInset * 2.0 - additionalSideInset, height: .greatestFiniteMagnitude))
            textSize = textLayout.size
            self.expandBackgroundNode.isHidden = false
            self.expandNode.isHidden = false
            self.expandButonNode.isHidden = false
        } else {
            self.textNode.cutout = nil
            self.expandBackgroundNode.isHidden = true
            self.expandNode.isHidden = true
            self.expandButonNode.isHidden = true
        }'''

OLD_OVERLAY = '''        var expandBackgroundFrame = expandFrame
        expandBackgroundFrame.origin.x -= 50.0
        expandBackgroundFrame.size.width += 50.0
        self.expandBackgroundNode.frame = expandBackgroundFrame
        // MARK: Jerkgram v1.2L BUILD123_DESCRIPTION_EXPAND_GLASS1
        let expandSurfaceColor: UIColor
        if GhostBaseGlassStyle.isEnabled {
            expandSurfaceColor = UIColor(
                white: presentationData.theme.overallDarkAppearance ? 0.0 : 1.0,
                alpha: presentationData.theme.overallDarkAppearance ? 0.26 : 0.18
            )
        } else {
            expandSurfaceColor = presentationData.theme.list.itemBlocksBackgroundColor
        }
        self.expandBackgroundNode.image = generateExpandBackground(size: expandBackgroundFrame.size, color: expandSurfaceColor)
'''

NEW_OVERLAY = '''        // MARK: Jerkgram v1.2M BUILD124_PROFILE_MORE_NO_OVERLAY1
        // The text cutout above reserves the exact "more" footprint. Do not
        // paint Telegram's historical 50 pt cover over adjacent glyphs.
        self.expandBackgroundNode.isHidden = true
        self.expandBackgroundNode.image = nil
'''


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 profile more] " + message)


def patch_text(text: str) -> str:
    updated = text
    if MARKER not in updated:
        require(updated.count(OLD) == 1, f"layout owner count is {updated.count(OLD)}")
        updated = updated.replace(OLD, NEW, 1)
    if RUNTIME_MARKER not in updated:
        require(updated.count(OLD_OVERLAY) == 1, f"expand overlay owner count is {updated.count(OLD_OVERLAY)}")
        updated = updated.replace(OLD_OVERLAY, NEW_OVERLAY, 1)
    return updated


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    TARGET.write_text(patch_text(text), encoding="utf-8")
    print("[Build124 profile more] GREEN")
    print("[Build124 profile more] collapsed bio reserves geometry for more without opaque glyph masking")


if __name__ == "__main__":
    main()
