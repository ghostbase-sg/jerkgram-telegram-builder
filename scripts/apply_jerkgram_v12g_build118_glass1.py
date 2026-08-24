#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SCREEN = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources"
SECTION = SCREEN / "PeerInfoScreenItemSectionContainerNode.swift"
SINGLE = SCREEN / "PeerInfoHeaderSingleLineTextFieldNode.swift"
MULTI = SCREEN / "PeerInfoHeaderMultiLineTextFieldNode.swift"
CONTAINER = SCREEN / "PeerInfoPaneContainerNode.swift"
LIST = SCREEN / "Panes/PeerInfoListPaneNode.swift"
VISUAL = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoVisualMediaPaneNode/Sources/PeerInfoVisualMediaPaneNode.swift"
VISUAL_BUILD = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoVisualMediaPaneNode/BUILD"


def require(value, message):
    if not value:
        raise RuntimeError("[Build118 glass] " + message)


def replace_once(text, old, new, name):
    require(old in text, name + " anchor missing")
    return text.replace(old, new, 1)


def patch_simple_surfaces(text):
    text = text.replace("isDark ? 0.13 : 0.16", "isDark ? 0.26 : 0.18")
    text = text.replace("isDark\n                        ? 0.13\n                        : 0.16", "isDark\n                        ? 0.26\n                        : 0.18")
    text = text.replace("hasCorners\n                ? 26.0", "hasCorners\n                ? 16.0")
    require("0.26" in text and "0.18" in text, "report-card material not installed")
    return text


def patch_visual(text):
    text = replace_once(text, "    private let listBackgroundView: UIImageView\n", "    // MARK: Jerkgram v1.2G BUILD118_GLASS1\n    private let ghostBaseGlassEnabled: Bool\n    private let listBackgroundView: UIView\n", "visual property")
    old_init = "contentType: ContentType, captureProtected: Bool, initialFocusMessageIndex: EngineMessage.Index?) {"
    new_init = "contentType: ContentType, captureProtected: Bool, initialFocusMessageIndex: EngineMessage.Index?, ghostBaseGlassEnabled: Bool = false) {"
    text = replace_once(text, old_init, new_init, "visual init")
    visual_context_anchor = new_init + "\n        self.context = context\n"
    visual_context_replacement = new_init + "\n        self.context = context\n        self.ghostBaseGlassEnabled = ghostBaseGlassEnabled\n"
    text = replace_once(text, visual_context_anchor, visual_context_replacement, "visual flag init")
    old_background = '''        self.listBackgroundView = UIImageView()
        self.listBackgroundView.image = generateStretchableFilledCircleImage(diameter: 26.0 * 2.0, color: .white)?.withRenderingMode(.alwaysTemplate)
'''
    text = replace_once(text, old_background, "        self.listBackgroundView = UIView()\n        self.listBackgroundView.clipsToBounds = true\n", "visual background init")
    old_update = '''            self.listBackgroundView.isHidden = !isList
            self.listMaskView.isHidden = !isList
            if isList {
                self.listBackgroundView.tintColor = presentationData.theme.list.itemBlocksBackgroundColor
                self.listMaskView.tintColor = presentationData.theme.list.blocksBackgroundColor
                self.updateListBackground(transition: transition)
            }
'''
    new_update = '''            self.listBackgroundView.isHidden = !isList
            self.listMaskView.isHidden = true
            if isList {
                if self.ghostBaseGlassEnabled {
                    self.listBackgroundView.backgroundColor = UIColor(
                        white: presentationData.theme.overallDarkAppearance ? 0.0 : 1.0,
                        alpha: presentationData.theme.overallDarkAppearance ? 0.26 : 0.18
                    )
                    self.listBackgroundView.layer.cornerRadius = 16.0
                    self.listBackgroundView.layer.borderWidth = 0.5
                    self.listBackgroundView.layer.borderColor = presentationData.theme.list.itemPlainSeparatorColor
                        .withAlphaComponent(presentationData.theme.overallDarkAppearance ? 0.30 : 0.20).cgColor
                } else {
                    self.listBackgroundView.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor
                    self.listBackgroundView.layer.cornerRadius = 26.0
                    self.listBackgroundView.layer.borderWidth = 0.0
                    self.listBackgroundView.layer.borderColor = nil
                }
                self.updateListBackground(transition: transition)
            }
'''
    return replace_once(text, old_update, new_update, "visual update")


def patch_list(text):
    text = replace_once(text, "    private let listNode: ChatHistoryListNode\n", "    // MARK: Jerkgram v1.2G BUILD118_GLASS1\n    private let ghostBaseGlassEnabled: Bool\n    private let glassBackgroundView: UIView\n    private let listNode: ChatHistoryListNode\n", "list property")
    old_init = "chatLocationContextHolder: Atomic<ChatLocationContextHolder?>, tagMask: EngineMessage.Tags) {"
    new_init = "chatLocationContextHolder: Atomic<ChatLocationContextHolder?>, tagMask: EngineMessage.Tags, ghostBaseGlassEnabled: Bool = false) {"
    text = replace_once(text, old_init, new_init, "list init")
    text = replace_once(text, "        self.context = context\n", "        self.context = context\n        self.ghostBaseGlassEnabled = ghostBaseGlassEnabled\n        self.glassBackgroundView = UIView()\n        self.glassBackgroundView.clipsToBounds = true\n", "list flag init")
    text = replace_once(text, "        self.addSubnode(self.listNode)\n", "        self.view.addSubview(self.glassBackgroundView)\n        self.addSubnode(self.listNode)\n", "list hierarchy")
    marker = "        self.currentParams = (size, topInset, sideInset, bottomInset, deviceMetrics, visibleHeight, isScrollingLockedAtTop, expandProgress, navigationHeight, presentationData)\n"
    addition = '''        if self.ghostBaseGlassEnabled {
            let frame = CGRect(x: sideInset + 16.0, y: topInset, width: max(1.0, size.width - (sideInset + 16.0) * 2.0), height: max(1.0, size.height - topInset - bottomInset))
            transition.updateFrame(view: self.glassBackgroundView, frame: frame)
            self.glassBackgroundView.backgroundColor = UIColor(
                white: presentationData.theme.overallDarkAppearance ? 0.0 : 1.0,
                alpha: presentationData.theme.overallDarkAppearance ? 0.26 : 0.18
            )
            self.glassBackgroundView.layer.cornerRadius = 16.0
            self.glassBackgroundView.layer.borderWidth = 0.5
            self.glassBackgroundView.layer.borderColor = presentationData.theme.list.itemPlainSeparatorColor
                .withAlphaComponent(presentationData.theme.overallDarkAppearance ? 0.30 : 0.20).cgColor
            self.glassBackgroundView.isHidden = false
            self.listNode.backgroundColor = .clear
        } else {
            self.glassBackgroundView.isHidden = true
        }
'''
    return replace_once(text, marker, marker + addition, "list update")


def patch_container(text):
    text = text.replace("initialFocusMessageIndex: switchToMediaTarget?.kind == .photoVideo ? switchToMediaTarget?.messageIndex : nil)", "initialFocusMessageIndex: switchToMediaTarget?.kind == .photoVideo ? switchToMediaTarget?.messageIndex : nil, ghostBaseGlassEnabled: ghostBaseGlassEnabled)")
    text = text.replace("initialFocusMessageIndex: nil)", "initialFocusMessageIndex: nil, ghostBaseGlassEnabled: ghostBaseGlassEnabled)")
    text = replace_once(text, "tagMask: .webPage)", "tagMask: .webPage, ghostBaseGlassEnabled: ghostBaseGlassEnabled)", "links flag")
    require(text.count("ghostBaseGlassEnabled: ghostBaseGlassEnabled") >= 5, "not all panes receive flag")
    return text


def main():
    for path in (SECTION, SINGLE, MULTI, CONTAINER, LIST, VISUAL, VISUAL_BUILD):
        require(path.is_file(), "missing target: " + str(path))
    list_text = LIST.read_text()
    if "BUILD118_GLASS1" in list_text and "BUILD118_GLASS1" in VISUAL.read_text():
        print("[Build118 glass] reference glass already applied")
        return
    SECTION.write_text(patch_simple_surfaces(SECTION.read_text()), encoding="utf-8")
    SINGLE.write_text(patch_simple_surfaces(SINGLE.read_text()), encoding="utf-8")
    MULTI.write_text(patch_simple_surfaces(MULTI.read_text()), encoding="utf-8")
    CONTAINER.write_text(patch_container(CONTAINER.read_text()), encoding="utf-8")
    LIST.write_text(patch_list(LIST.read_text()), encoding="utf-8")
    VISUAL.write_text(patch_visual(VISUAL.read_text()), encoding="utf-8")
    build = VISUAL_BUILD.read_text()
    VISUAL_BUILD.write_text(build, encoding="utf-8")
    print("[Build118 glass] reference glass applied to profile sections and shared-media panes")


if __name__ == "__main__":
    main()
