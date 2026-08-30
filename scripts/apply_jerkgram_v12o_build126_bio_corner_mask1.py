#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenMultilineInputtem.swift"
MARKER = "// MARK: Jerkgram v1.2O BUILD126_PROFILE_BIO_CORNER_MASK1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build126 bio corner mask] " + message)


def patch_text(text: str) -> str:
    if MARKER in text:
        return text

    owner = '''        self.maskNode.image = hasCorners ? PresentationResourcesItemList.cornersImage(presentationData.theme, top: hasTopCorners, bottom: hasBottomCorners, glass: true) : nil
'''
    require(text.count(owner) == 1, f"profile bio corner-mask owner count is {text.count(owner)}")

    replacement = '''        // MARK: Jerkgram v1.2O BUILD126_PROFILE_BIO_CORNER_MASK1
        // The glass corner bitmap is composited over this translucent editor
        // and leaves visible triangular filler at its lower corners. Keep the
        // native bitmap for the non-glass setting; glass uses a real layer
        // corner mask instead.
        if GhostBaseGlassStyle.isEnabled {
            self.maskNode.image = nil
            self.cornerRadius = hasCorners ? 26.0 : 0.0
            self.clipsToBounds = hasCorners
            if hasTopCorners && hasBottomCorners {
                self.layer.maskedCorners = [
                    .layerMinXMinYCorner,
                    .layerMaxXMinYCorner,
                    .layerMinXMaxYCorner,
                    .layerMaxXMaxYCorner
                ]
            } else if hasTopCorners {
                self.layer.maskedCorners = [
                    .layerMinXMinYCorner,
                    .layerMaxXMinYCorner
                ]
            } else if hasBottomCorners {
                self.layer.maskedCorners = [
                    .layerMinXMaxYCorner,
                    .layerMaxXMaxYCorner
                ]
            } else {
                self.layer.maskedCorners = []
            }
        } else {
            self.maskNode.image = hasCorners ? PresentationResourcesItemList.cornersImage(presentationData.theme, top: hasTopCorners, bottom: hasBottomCorners, glass: true) : nil
            self.cornerRadius = 0.0
            self.clipsToBounds = true
            self.layer.maskedCorners = []
        }
'''
    return text.replace(owner, replacement, 1)


def main() -> None:
    require(TARGET.is_file(), f"missing profile bio owner: {TARGET}")
    TARGET.write_text(patch_text(TARGET.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build126 bio corner mask] GREEN")


if __name__ == "__main__":
    main()
