#!/usr/bin/env python3

import os
from pathlib import Path


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenMultilineInputtem.swift"
MARKER = "// MARK: Jerkgram v1.2Q BUILD128_PROFILE_BIO_CORNER_OWNER1"
BUILD126_MARKER = "// MARK: Jerkgram v1.2O BUILD126_PROFILE_BIO_CORNER_MASK1"
FRAME_OWNER = "        transition.updateFrame(node: self.maskNode, frame:"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build128 bio corner owner] " + message)


def patch_text(text: str) -> str:
    if MARKER in text:
        return text

    require(text.count(BUILD126_MARKER) == 1, "Build126 outer corner patch missing or ambiguous")
    start = text.index(BUILD126_MARKER)
    frame = text.find(FRAME_OWNER, start)
    require(frame != -1, "mask-frame owner missing after Build126 patch")

    replacement = '''// MARK: Jerkgram v1.2Q BUILD128_PROFILE_BIO_CORNER_OWNER1
        // `cornersImage(..., glass: true)` is an opaque corner raster. Over a
        // translucent bio editor its filler remains visible as lower-corner
        // triangles. The section container already owns the rounded clipping,
        // so glass must not draw a second corner layer here.
        if GhostBaseGlassStyle.isEnabled {
            self.maskNode.image = nil
        } else {
            self.maskNode.image = hasCorners ? PresentationResourcesItemList.cornersImage(presentationData.theme, top: hasTopCorners, bottom: hasBottomCorners, glass: true) : nil
        }
'''
    return text[:start] + replacement + text[frame:]


def main() -> None:
    require(TARGET.is_file(), f"missing profile bio owner: {TARGET}")
    TARGET.write_text(patch_text(TARGET.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build128 bio corner owner] GREEN")


if __name__ == "__main__":
    main()
