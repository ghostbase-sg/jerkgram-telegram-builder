#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SINGLE = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderSingleLineTextFieldNode.swift"
MULTI = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderMultiLineTextFieldNode.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_PROFILE_EDIT_SURFACE1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 profile edit glass] " + message)


OLD = "            self.backgroundNode.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor"
NEW = '''            // MARK: Jerkgram v1.2M BUILD124_PROFILE_EDIT_SURFACE1
            // The fullscreen profile scene owns the blur. Editing rows only add
            // a light readability tint; when Jerkgram Glass is off, preserve
            // Telegram's stock opaque block background exactly.
            self.backgroundNode.backgroundColor = GhostBaseGlassStyle.isEnabled
                ? presentationData.theme.list.itemBlocksBackgroundColor.withAlphaComponent(
                    presentationData.theme.overallDarkAppearance ? 0.26 : 0.18
                )
                : presentationData.theme.list.itemBlocksBackgroundColor'''


def patch_text(text: str, label: str) -> str:
    if MARKER in text:
        return text
    require("GhostBaseGlassStyle.isEnabled" in text, f"{label}: Build123 glass owner missing")
    require(text.count(OLD) == 1, f"{label}: opaque edit background owner count is {text.count(OLD)}")
    return text.replace(OLD, NEW, 1)


def main() -> None:
    for path, label in ((SINGLE, "single-line"), (MULTI, "multi-line")):
        text = path.read_text(encoding="utf-8")
        path.write_text(patch_text(text, label), encoding="utf-8")
    print("[Build124 profile edit glass] GREEN")
    print("[Build124 profile edit glass] edit rows are translucent with Glass on; stock Telegram remains with Glass off")


if __name__ == "__main__":
    main()
