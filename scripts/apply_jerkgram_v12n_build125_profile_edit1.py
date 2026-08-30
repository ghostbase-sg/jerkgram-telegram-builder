#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
FILES = (
    ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderSingleLineTextFieldNode.swift",
    ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderMultiLineTextFieldNode.swift",
)
BIO = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenMultilineInputtem.swift"
ITEM_RENDERER = ROOT / "submodules/ItemListUI/Sources/Items/ItemListMultilineInputItem.swift"
MARKER = "// MARK: Jerkgram v1.2N BUILD125_PROFILE_EDIT_GLASS_OWNER1"
BIO_MARKER = "// MARK: Jerkgram v1.2N BUILD125_PROFILE_BIO_GLASS_OWNER1"
ITEM_MARKER = "// MARK: Jerkgram v1.2N BUILD125_PROFILE_BIO_BACKGROUND_API1"


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
            '''            // Keep this node as a tint only. `itemBlocksBackgroundColor`
            // is an opaque list surface on Telegram 12.9.2 even after alpha is
            // applied, which is why the bio still looked like a solid black card.
            self.backgroundNode.isOpaque = false
            self.backgroundNode.backgroundColor = presentationData.theme.overallDarkAppearance
                ? UIColor.white.withAlphaComponent(0.055)
                : UIColor.black.withAlphaComponent(0.045)''',
            tail,
            count=1,
        )
    else:
        require(
            "self.backgroundNode.isOpaque = false" in tail
            and "UIColor.white.withAlphaComponent(0.055)" in tail
            and "UIColor.black.withAlphaComponent(0.045)" in tail,
            f"{label}: translucent field color owner missing",
        )
    # The Build124 owner declared this solely for its old black/white color
    # expression. Build125 now uses the presentation theme directly, so Swift
    # 6 correctly rejects the stale declaration as unused.
    unused_is_dark = re.compile(
        r"\n\s*let isDark\s*=\s*presentationData\s*\.theme\s*\.overallDarkAppearance\s*\n"
    )
    tail, removed = unused_is_dark.subn("\n", tail, count=1)
    require(removed == 1, f"{label}: obsolete profile color temporary missing")
    return text[:start] + tail


def patch_bio_input(text: str) -> str:
    if BIO_MARKER in text:
        return text
    owner = "systemStyle: .glass, text: item.text"
    require(text.count(owner) == 1, f"bio input owner count is {text.count(owner)}")
    replacement = '''systemStyle: .glass,
            // MARK: Jerkgram v1.2N BUILD125_PROFILE_BIO_GLASS_OWNER1
            // `systemStyle` only controls corners/insets. Supply an explicit
            // tint for this one profile-bio field so the generic `.blocks`
            // renderer cannot replace it with Telegram's opaque list card.
            backgroundColor: GhostBaseGlassStyle.isEnabled
                ? (presentationData.theme.overallDarkAppearance
                    ? UIColor.white.withAlphaComponent(0.055)
                    : UIColor.black.withAlphaComponent(0.045))
                : nil,
            text: item.text'''
    return text.replace(owner, replacement, 1)


def patch_bio_source(text: str) -> str:
    text = patch_bio_input(text)
    if "import TelegramUIPreferences" not in text:
        require("import TelegramPresentationData" in text, "bio input preference import anchor missing")
        text = text.replace("import TelegramPresentationData", "import TelegramPresentationData\nimport TelegramUIPreferences", 1)
    return text


def patch_item_renderer(text: str) -> str:
    if ITEM_MARKER in text:
        return text
    require("let systemStyle: ItemListSystemStyle" in text, "multiline item style field missing")
    require("let text: String" in text, "multiline item text field missing")
    require("systemStyle: ItemListSystemStyle = .legacy, text: String" in text, "multiline item initializer owner missing")
    require("self.systemStyle = systemStyle" in text, "multiline item initializer assignment missing")
    old_background = "itemBackgroundColor = item.presentationData.theme.list.itemBlocksBackgroundColor"
    require(text.count(old_background) == 1, f"multiline blocks background owner count is {text.count(old_background)}")
    text = text.replace(
        "let systemStyle: ItemListSystemStyle\n    let text: String",
        "let systemStyle: ItemListSystemStyle\n    // MARK: Jerkgram v1.2N BUILD125_PROFILE_BIO_BACKGROUND_API1\n    // Optional per-item override. Generic callers retain Telegram's stock cards.\n    let backgroundColor: UIColor?\n    let text: String",
        1,
    )
    text = text.replace(
        "systemStyle: ItemListSystemStyle = .legacy, text: String",
        "systemStyle: ItemListSystemStyle = .legacy, backgroundColor: UIColor? = nil, text: String",
        1,
    )
    text = text.replace("self.systemStyle = systemStyle", "self.systemStyle = systemStyle\n        self.backgroundColor = backgroundColor", 1)
    text = text.replace(
        old_background,
        "itemBackgroundColor = item.backgroundColor ?? item.presentationData.theme.list.itemBlocksBackgroundColor",
        1,
    )
    return text


def main() -> None:
    for path in FILES:
        path.write_text(patch_text(path.read_text(encoding="utf-8"), path.name), encoding="utf-8")
    BIO.write_text(patch_bio_source(BIO.read_text(encoding="utf-8")), encoding="utf-8")
    ITEM_RENDERER.write_text(patch_item_renderer(ITEM_RENDERER.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build125 profile edit] GREEN")
    print("[Build125 profile edit] header fields and the actual bio_edit renderer use the visible profile Glass switch")


if __name__ == "__main__":
    main()
