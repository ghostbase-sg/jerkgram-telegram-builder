#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/ListItems/PeerInfoScreenLabeledValueItem.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_PROFILE_MORE_CUTOUT1"

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


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 profile more] " + message)


def patch_text(text: str) -> str:
    if MARKER in text:
        return text
    require(text.count(OLD) == 1, f"layout owner count is {text.count(OLD)}")
    return text.replace(OLD, NEW, 1)


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    TARGET.write_text(patch_text(text), encoding="utf-8")
    print("[Build124 profile more] GREEN")
    print("[Build124 profile more] collapsed bio reserves geometry for more without opaque glyph masking")


if __name__ == "__main__":
    main()
