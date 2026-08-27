#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
PANE = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoListPaneNode.swift"
GROUPS = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoGroupsInCommonPaneNode.swift"
DESCRIPTION = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/ListItems/PeerInfoScreenLabeledValueItem.swift"
PHONE = ROOT / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryControllerNode.swift"
PROFILE_ITEMS = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"
HEADER = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderNode.swift"
SINGLE = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderSingleLineTextFieldNode.swift"
MULTI = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderMultiLineTextFieldNode.swift"
MARKER = "// MARK: Jerkgram v1.2L BUILD123_LINKS_INTRINSIC_GLASS1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build123 profile UI] " + message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    require(text.count(old) == 1, f"{label}: expected one anchor, found {text.count(old)}")
    return text.replace(old, new, 1)


def patch_links() -> None:
    text = PANE.read_text(encoding="utf-8")
    if MARKER in text:
        return
    old = '''        if self.ghostBaseGlassEnabled {
            let frame = CGRect(x: sideInset + 16.0, y: topInset, width: max(1.0, size.width - (sideInset + 16.0) * 2.0), height: max(1.0, size.height - topInset - bottomInset))
            transition.updateFrame(view: self.glassBackgroundView, frame: frame)'''
    new = '''        // MARK: Jerkgram v1.2L BUILD123_LINKS_INTRINSIC_GLASS1
        // Links already owns a luminance-aware row surface. Never place its
        // variable-height results inside a viewport-height plate.
        if self.ghostBaseGlassEnabled && !self.jerkgramLinksReadabilityEnabled {
            let frame = CGRect(x: sideInset + 16.0, y: topInset, width: max(1.0, size.width - (sideInset + 16.0) * 2.0), height: max(1.0, size.height - topInset - bottomInset))
            transition.updateFrame(view: self.glassBackgroundView, frame: frame)'''
    text = replace_once(text, old, new, "Links outer plate")
    old_else = '''        } else {
            self.glassBackgroundView.isHidden = true
        }

        // MARK: Jerkgram v1.2D BUILD115_LINKS_READABILITY_OWNER1'''
    new_else = '''        } else {
            self.glassBackgroundView.isHidden = true
            transition.updateFrame(view: self.glassBackgroundView, frame: self.jerkgramLinksReadabilityEnabled ? .zero : self.glassBackgroundView.frame)
        }

        // MARK: Jerkgram v1.2D BUILD115_LINKS_READABILITY_OWNER1'''
    text = replace_once(text, old_else, new_else, "Links hidden plate")
    PANE.write_text(text, encoding="utf-8")


def patch_groups() -> None:
    text = GROUPS.read_text(encoding="utf-8")
    if "BUILD123_COMMON_GROUPS_SURFACE1" in text:
        return
    old = '''            // MARK: Jerkgram v1.2B BUILD113_COMMON_GROUPS_OWNER1
            // The fullscreen profile scene owns blur/tone. Common Groups must
            // not stack a second material/tint plate over it.
            self.backgroundColor = .clear
            self.view.backgroundColor = .clear
            self.listNode.backgroundColor = .clear
            self.listNode.view.backgroundColor = .clear

            self.ghostBaseGlassEffectView.effect = nil
            self.ghostBaseGlassEffectView.backgroundColor = .clear
            self.ghostBaseGlassEffectView.contentView.backgroundColor = .clear
            self.ghostBaseGlassEffectView.isHidden = true
            self.ghostBaseGlassTintView.backgroundColor = .clear

            self.listBackgroundView.isHidden = true
            self.listBackgroundView.alpha = 0.0
            self.listMaskView.isHidden = true
            self.listMaskView.alpha = 0.0

            self.listBackgroundView.isHidden = true
            self.listBackgroundView.alpha = 0.0
            self.listMaskView.isHidden = true
            self.listMaskView.alpha = 0.0'''
    new = '''            // MARK: Jerkgram v1.2L BUILD123_COMMON_GROUPS_SURFACE1
            // One neutral readability surface, matching neighboring cards;
            // the fullscreen profile remains the only blur owner.
            self.ghostBaseGlassEffectView.effect = nil
            self.ghostBaseGlassEffectView.backgroundColor = .clear
            self.ghostBaseGlassEffectView.contentView.backgroundColor = .clear
            self.ghostBaseGlassEffectView.isHidden = false
            self.ghostBaseGlassTintView.backgroundColor = UIColor(
                white: isDark ? 0.0 : 1.0,
                alpha: isDark ? 0.26 : 0.18
            )
            self.listBackgroundView.isHidden = true
            self.listBackgroundView.alpha = 0.0
            self.listMaskView.isHidden = true
            self.listMaskView.alpha = 0.0'''
    text = replace_once(text, old, new, "Common Groups transparent owner")
    GROUPS.write_text(text, encoding="utf-8")


def patch_description() -> None:
    text = DESCRIPTION.read_text(encoding="utf-8")
    if "BUILD123_DESCRIPTION_EXPAND_GLASS1" in text:
        return
    old = "        self.expandBackgroundNode.image = generateExpandBackground(size: expandBackgroundFrame.size, color: presentationData.theme.list.itemBlocksBackgroundColor)"
    new = '''        // MARK: Jerkgram v1.2L BUILD123_DESCRIPTION_EXPAND_GLASS1
        let expandSurfaceColor: UIColor
        if GhostBaseGlassStyle.isEnabled {
            expandSurfaceColor = UIColor(
                white: presentationData.theme.overallDarkAppearance ? 0.0 : 1.0,
                alpha: presentationData.theme.overallDarkAppearance ? 0.26 : 0.18
            )
        } else {
            expandSurfaceColor = presentationData.theme.list.itemBlocksBackgroundColor
        }
        self.expandBackgroundNode.image = generateExpandBackground(size: expandBackgroundFrame.size, color: expandSurfaceColor)'''
    text = replace_once(text, old, new, "description expansion background")
    DESCRIPTION.write_text(text, encoding="utf-8")


def patch_editing() -> None:
    for path in (SINGLE, MULTI):
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            "let ghostBaseGlassEnabled =\n            GhostBaseProfileBlurSettings\n                .loadEnabled() != nil",
            "let ghostBaseGlassEnabled = GhostBaseGlassStyle.isEnabled"
        )
        path.write_text(text, encoding="utf-8")
    text = HEADER.read_text(encoding="utf-8")
    if "BUILD123_PROFILE_EDIT_GLASS_OWNER1" not in text:
        old = "        self.editingEdgeEffectView.update(content: presentationData.theme.list.blocksBackgroundColor, blur: true, rect: editingEdgeEffectFrame, edge: .top, edgeSize: editingEdgeEffectHeight, transition: ComponentTransition(transition))"
        new = '''        // MARK: Jerkgram v1.2L BUILD123_PROFILE_EDIT_GLASS_OWNER1
        let editingEdgeColor: UIColor
        if GhostBaseGlassStyle.isEnabled {
            editingEdgeColor = UIColor(
                white: presentationData.theme.overallDarkAppearance ? 0.0 : 1.0,
                alpha: presentationData.theme.overallDarkAppearance ? 0.26 : 0.18
            )
        } else {
            editingEdgeColor = presentationData.theme.list.blocksBackgroundColor
        }
        self.editingEdgeEffectView.update(content: editingEdgeColor, blur: true, rect: editingEdgeEffectFrame, edge: .top, edgeSize: editingEdgeEffectHeight, transition: ComponentTransition(transition))'''
        text = replace_once(text, old, new, "editing edge")
        HEADER.write_text(text, encoding="utf-8")


def patch_login() -> None:
    text = PHONE.read_text(encoding="utf-8")
    if "BUILD123_SAFE_LOGIN_ALL_ACCOUNTS1" not in text:
        old = '''        self.ghostBaseSafeLoginNode.isHidden = true
        self.ghostBaseSafeLoginInfoNode.isHidden = true'''
        new = '''        // MARK: Jerkgram v1.2L BUILD123_SAFE_LOGIN_ALL_ACCOUNTS1
        // Available for both first authorization and add-account flows.
        self.ghostBaseSafeLoginNode.isHidden = false
        self.ghostBaseSafeLoginInfoNode.isHidden = false'''
        text = replace_once(text, old, new, "Safe Login visibility")
        PHONE.write_text(text, encoding="utf-8")


def remove_invite_probe() -> None:
    text = PROFILE_ITEMS.read_text(encoding="utf-8")
    marker = "    // MARK: GhostBase v1.0ZG PRIVATELINK1 cached exported invite"
    if marker not in text:
        return
    start = text.index(marker)
    end = text.index("    var result: [(AnyHashable, [PeerInfoScreenItem])] = []", start)
    text = text[:start] + "    // MARK: Jerkgram v1.2L BUILD123_REMOVE_PRIVATE_LINK_PROBE1\n\n" + text[end:]
    PROFILE_ITEMS.write_text(text, encoding="utf-8")


def main() -> None:
    patch_links()
    patch_groups()
    patch_description()
    patch_editing()
    patch_login()
    remove_invite_probe()
    print("[Build123 profile UI] GREEN")


if __name__ == "__main__":
    main()
