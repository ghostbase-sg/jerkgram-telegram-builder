#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SINGLE = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderSingleLineTextFieldNode.swift"
MULTI = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderMultiLineTextFieldNode.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_PROFILE_EDIT_SURFACE1"
RUNTIME_MARKER = "// MARK: Jerkgram v1.2M BUILD124_PROFILE_EDIT_RUNTIME_SURFACE1"


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

RUNTIME_OLD = '''            self.backgroundNode.backgroundColor =
                UIColor(
                    white:
                        isDark
                        ? 0.0
                        : 1.0,
                    alpha:
                        isDark
                        ? 0.26
                        : 0.18
                )'''

RUNTIME_NEW = '''            // MARK: Jerkgram v1.2M BUILD124_PROFILE_EDIT_RUNTIME_SURFACE1
            // This is the actual final visual owner. Keep it visibly lighter
            // than the legacy card so the profile backdrop remains readable.
            self.backgroundNode.backgroundColor =
                UIColor(
                    white:
                        isDark
                        ? 0.0
                        : 1.0,
                    alpha:
                        isDark
                        ? 0.12
                        : 0.10
                )'''


def patch_text(text: str, label: str) -> str:
    updated = text
    if MARKER not in updated:
        require("GhostBaseGlassStyle.isEnabled" in updated, f"{label}: Build123 glass owner missing")
        require(updated.count(OLD) == 1, f"{label}: opaque edit background owner count is {updated.count(OLD)}")
        updated = updated.replace(OLD, NEW, 1)

    if RUNTIME_MARKER not in updated:
        owner_marker = "// MARK: GhostBase v1.1P HEADER_FIELD_GLASS_OWNER1"
        require(owner_marker in updated, f"{label}: final header field visual owner missing")
        owner_start = updated.index(owner_marker)
        owner = updated[owner_start:]
        require(owner.count(RUNTIME_OLD) == 1, f"{label}: final opaque field surface owner count is {owner.count(RUNTIME_OLD)}")
        owner = owner.replace(RUNTIME_OLD, RUNTIME_NEW, 1)
        updated = updated[:owner_start] + owner
    return updated


def main() -> None:
    for path, label in ((SINGLE, "single-line"), (MULTI, "multi-line")):
        text = path.read_text(encoding="utf-8")
        path.write_text(patch_text(text, label), encoding="utf-8")
    print("[Build124 profile edit glass] GREEN")
    print("[Build124 profile edit glass] edit rows are translucent with Glass on; stock Telegram remains with Glass off")


if __name__ == "__main__":
    main()
