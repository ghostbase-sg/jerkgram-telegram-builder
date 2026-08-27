#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/ListItems/PeerInfoScreenLabeledValueItem.swift"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 profile more verify] " + message)


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    require("BUILD124_PROFILE_MORE_CUTOUT1" in text, "cutout owner missing")
    require("TextNodeCutout(bottomRight:" in text, "bottom-right cutout missing")
    require("width: expandSize.width + 22.0" in text, "more width reservation missing")
    require("height: expandSize.height + 4.0" in text, "more height reservation missing")
    require(text.count("self.textNode.cutout = nil") >= 2, "stale/expanded cutout reset missing")
    require("var textLayout = self.textNode.updateLayoutInfo" in text, "mutable initial text layout missing")
    require("textLayout = self.textNode.updateLayoutInfo" in text, "post-cutout relayout missing")
    require("var textSize = textLayout.size" in text and "textSize = textLayout.size" in text, "post-cutout text size refresh missing")
    print("[Build124 profile more verify] GREEN")
    print("[Build124 profile more verify] more control no longer relies on opaque overlap masking")


if __name__ == "__main__":
    main()
