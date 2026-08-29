#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
FILES = (
    ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderSingleLineTextFieldNode.swift",
    ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderMultiLineTextFieldNode.swift",
)
MARKER = "// MARK: Jerkgram v1.2N BUILD125_PROFILE_EDIT_GLASS_OWNER1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build125 profile edit] " + message)


def patch_text(text: str, label: str) -> str:
    if MARKER in text:
        return text
    owner = "// MARK: GhostBase v1.1P HEADER_FIELD_GLASS_OWNER1"
    require(text.count(owner) == 1, f"{label}: final field owner missing or ambiguous")
    start = text.index(owner)
    tail = text[start:]
    toggle = '''        let ghostBaseGlassEnabled =
            GhostBaseProfileBlurSettings
                .loadEnabled() != nil'''
    replacement_toggle = '''        // MARK: Jerkgram v1.2N BUILD125_PROFILE_EDIT_GLASS_OWNER1
        // Edit-profile fields must follow the visible profile Glass setting,
        // not a separate persisted flag which leaves the bio opaque.
        let ghostBaseGlassEnabled = GhostBaseGlassStyle.isEnabled'''
    if tail.count(toggle) == 1:
        tail = tail.replace(toggle, replacement_toggle, 1)
    elif tail.count("let ghostBaseGlassEnabled = GhostBaseGlassStyle.isEnabled") == 1:
        # Some Build124 materializations already migrated the toggle before
        # Build125 was installed. Continue from that real owner instead of
        # treating an equivalent state as a fatal historical-anchor mismatch.
        tail = tail.replace(
            "let ghostBaseGlassEnabled = GhostBaseGlassStyle.isEnabled",
            replacement_toggle,
            1,
        )
    else:
        require(False, f"{label}: profile Glass toggle owner missing")
    color = re.compile(
        r"            self\.backgroundNode\.backgroundColor =\n"
        r"                UIColor\(\n"
        r"                    white:\s*.*?\n"
        r"                    alpha:\s*.*?\n"
        r"                \)",
        re.DOTALL,
    )
    matches = color.findall(tail)
    if len(matches) == 1:
        tail = color.sub(
            '''            self.backgroundNode.isOpaque = false
            self.backgroundNode.backgroundColor =
                presentationData.theme.list.itemBlocksBackgroundColor.withAlphaComponent(
                    presentationData.theme.overallDarkAppearance ? 0.18 : 0.14
                )''',
            tail,
            count=1,
        )
    else:
        require(
            "self.backgroundNode.isOpaque = false" in tail
            and "itemBlocksBackgroundColor.withAlphaComponent" in tail
            and "? 0.18 : 0.14" in tail,
            f"{label}: translucent field color owner missing",
        )
    unused_is_dark = re.compile(
        r"\n\s*let isDark\s*=\s*presentationData\s*\.theme\s*\.overallDarkAppearance\s*\n"
    )
    tail, removed = unused_is_dark.subn("\n", tail, count=1)
    require(removed == 1, f"{label}: obsolete profile color temporary missing")
    return text[:start] + tail


def main() -> None:
    for path in FILES:
        path.write_text(patch_text(path.read_text(encoding="utf-8"), path.name), encoding="utf-8")
    print("[Build125 profile edit] GREEN")
    print("[Build125 profile edit] bio and name fields use the visible profile Glass switch and translucent theme card surface")


if __name__ == "__main__":
    main()
