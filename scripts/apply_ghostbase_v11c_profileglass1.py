#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
base = root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen"
profile_items = base / "Sources/PeerInfoProfileItems.swift"
screen = base / "Sources/PeerInfoScreen.swift"
section = base / "Sources/PeerInfoScreenItemSectionContainerNode.swift"
build = base / "BUILD"
custom_item = base / "Sources/GhostBaseProfileHubItem.swift"

for path in [profile_items, screen, section, build]:
    if not path.exists():
        raise SystemExit(f"[V11C PROFILEGLASS1] missing required file: {path}")

item_source = r'''import Foundation
import UIKit
import Display
import AsyncDisplayKit
import AccountContext
import TelegramPresentationData

// MARK: GhostBase v1.1C PROFILEGLASS1 inline horizontal hub
final class GhostBaseProfileHubItem: PeerInfoScreenItem {
    let id: AnyHashable
    let title: String
    let isExpanded: Bool
    let selectedTab: Int
    let tabTitles: [String]
    let bodyText: String
    let toggle: () -> Void
    let selectTab: (Int) -> Void

    init(
        id: AnyHashable,
        title: String,
        isExpanded: Bool,
        selectedTab: Int,
        tabTitles: [String],
        bodyText: String,
        toggle: @escaping () -> Void,
        selectTab: @escaping (Int) -> Void
    ) {
        self.id = id
        self.title = title
        self.isExpanded = isExpanded
        self.selectedTab = selectedTab
        self.tabTitles = tabTitles
        self.bodyText = bodyText
        self.toggle = toggle
        self.selectTab = selectTab
    }

    func node() -> PeerInfoScreenItemNode {
        return GhostBaseProfileHubItemNode()
    }
}

private final class GhostBaseProfileHubView: UIView {
    private let headerButton = UIButton(type: .custom)
    private let titleLabel = UILabel()
    private let chevronView = UIImageView()
    private let tabsScrollView = UIScrollView()
    private let bodyLabel = UILabel()
    private var tabButtons: [UIButton] = []
    private var tabWidths: [CGFloat] = []
    private var toggleAction: (() -> Void)?
    private var selectTabAction: ((Int) -> Void)?
    private var expanded = false
    private var bodyHeight: CGFloat = 0.0

    override init(frame: CGRect) {
        super.init(frame: frame)

        self.clipsToBounds = true
        self.layer.cornerCurve = .continuous

        self.titleLabel.font = UIFont.systemFont(ofSize: 16.0, weight: .semibold)
        self.bodyLabel.font = UIFont.systemFont(ofSize: 14.0, weight: .regular)
        self.bodyLabel.numberOfLines = 0
        self.bodyLabel.lineBreakMode = .byWordWrapping

        self.chevronView.contentMode = .center

        self.tabsScrollView.showsHorizontalScrollIndicator = false
        self.tabsScrollView.alwaysBounceHorizontal = true
        self.tabsScrollView.delaysContentTouches = false

        self.headerButton.addTarget(self, action: #selector(self.headerPressed), for: .touchUpInside)

        self.addSubview(self.titleLabel)
        self.addSubview(self.chevronView)
        self.addSubview(self.headerButton)
        self.addSubview(self.tabsScrollView)
        self.addSubview(self.bodyLabel)
    }

    required init?(coder: NSCoder) {
        preconditionFailure()
    }

    @objc private func headerPressed() {
        self.toggleAction?()
    }

    @objc private func tabPressed(_ sender: UIButton) {
        self.selectTabAction?(sender.tag)
    }

    private func rebuildTabsIfNeeded(_ titles: [String]) {
        let currentTitles = self.tabButtons.compactMap { $0.title(for: .normal) }
        if currentTitles == titles {
            return
        }
        for button in self.tabButtons {
            button.removeFromSuperview()
        }
        self.tabButtons.removeAll()
        for (index, title) in titles.enumerated() {
            let button = UIButton(type: .custom)
            button.tag = index
            button.titleLabel?.font = UIFont.systemFont(ofSize: 13.0, weight: .semibold)
            button.setTitle(title, for: .normal)
            button.contentEdgeInsets = UIEdgeInsets(top: 7.0, left: 13.0, bottom: 7.0, right: 13.0)
            button.layer.cornerRadius = GhostBaseGlassStyle.compactCornerRadius
            button.layer.cornerCurve = .continuous
            button.addTarget(self, action: #selector(self.tabPressed(_:)), for: .touchUpInside)
            self.tabsScrollView.addSubview(button)
            self.tabButtons.append(button)
        }
    }

    func update(
        width: CGFloat,
        presentationData: PresentationData,
        item: GhostBaseProfileHubItem
    ) -> CGFloat {
        self.toggleAction = item.toggle
        self.selectTabAction = item.selectTab
        self.expanded = item.isExpanded
        self.titleLabel.text = item.title
        self.titleLabel.textColor = presentationData.theme.list.itemPrimaryTextColor
        self.bodyLabel.text = item.bodyText
        self.bodyLabel.textColor = presentationData.theme.list.itemSecondaryTextColor
        self.chevronView.tintColor = presentationData.theme.list.itemAccentColor
        self.chevronView.image = UIImage(systemName: item.isExpanded ? "chevron.up" : "chevron.down")

        self.backgroundColor = GhostBaseGlassStyle.coldFillColor(
            presentationData.theme.list.itemBlocksBackgroundColor
        )
        self.layer.borderWidth = UIScreenPixel
        self.layer.borderColor = GhostBaseGlassStyle.borderColor(
            presentationData.theme.list.itemPrimaryTextColor
        ).cgColor
        self.layer.cornerRadius = GhostBaseGlassStyle.cardCornerRadius

        self.rebuildTabsIfNeeded(item.tabTitles)
        self.tabWidths.removeAll(keepingCapacity: true)
        for (index, button) in self.tabButtons.enumerated() {
            let selected = index == item.selectedTab
            button.setTitleColor(
                selected ? presentationData.theme.list.itemAccentColor : presentationData.theme.list.itemSecondaryTextColor,
                for: .normal
            )
            button.backgroundColor = selected
                ? presentationData.theme.list.itemAccentColor.withAlphaComponent(GhostBaseGlassStyle.usesReducedEffects ? 0.13 : 0.18)
                : presentationData.theme.list.itemBlocksBackgroundColor.withAlphaComponent(0.28)
            let buttonSize = button.sizeThatFits(CGSize(width: 240.0, height: 36.0))
            self.tabWidths.append(max(68.0, ceil(buttonSize.width)))
        }

        if item.isExpanded {
            self.bodyHeight = ceil(self.bodyLabel.sizeThatFits(
                CGSize(width: max(1.0, width - 32.0), height: CGFloat.greatestFiniteMagnitude)
            ).height)
        } else {
            self.bodyHeight = 0.0
        }

        self.tabsScrollView.isHidden = !item.isExpanded
        self.bodyLabel.isHidden = !item.isExpanded
        self.setNeedsLayout()

        if item.isExpanded {
            return 58.0 + 44.0 + self.bodyHeight + 22.0
        } else {
            return 58.0
        }
    }

    override func layoutSubviews() {
        super.layoutSubviews()

        let width = self.bounds.width
        self.headerButton.frame = CGRect(x: 0.0, y: 0.0, width: width, height: 58.0)
        self.titleLabel.frame = CGRect(x: 16.0, y: 0.0, width: max(0.0, width - 58.0), height: 58.0)
        self.chevronView.frame = CGRect(x: max(0.0, width - 44.0), y: 7.0, width: 36.0, height: 44.0)

        guard self.expanded else {
            return
        }

        self.tabsScrollView.frame = CGRect(x: 12.0, y: 58.0, width: max(0.0, width - 24.0), height: 40.0)
        var x: CGFloat = 0.0
        for (index, button) in self.tabButtons.enumerated() {
            let buttonWidth = index < self.tabWidths.count ? self.tabWidths[index] : 76.0
            button.frame = CGRect(x: x, y: 2.0, width: buttonWidth, height: 34.0)
            x += buttonWidth + 8.0
        }
        self.tabsScrollView.contentSize = CGSize(width: max(0.0, x - 8.0), height: 40.0)
        self.bodyLabel.frame = CGRect(x: 16.0, y: 106.0, width: max(0.0, width - 32.0), height: self.bodyHeight)
    }
}

private final class GhostBaseProfileHubItemNode: PeerInfoScreenItemNode {
    private let contentView: GhostBaseProfileHubView
    private let contentNode: ASDisplayNode

    override init() {
        let contentView = GhostBaseProfileHubView()
        self.contentView = contentView
        self.contentNode = ASDisplayNode(viewBlock: {
            return contentView
        })
        super.init()
        self.addSubnode(self.contentNode)
    }

    override func update(
        context: AccountContext,
        width: CGFloat,
        safeInsets: UIEdgeInsets,
        presentationData: PresentationData,
        item: PeerInfoScreenItem,
        topItem: PeerInfoScreenItem?,
        bottomItem: PeerInfoScreenItem?,
        hasCorners: Bool,
        transition: ContainedViewLayoutTransition
    ) -> CGFloat {
        guard let item = item as? GhostBaseProfileHubItem else {
            return 0.0
        }
        let horizontalInset: CGFloat = 12.0
        let contentWidth = max(1.0, width - horizontalInset * 2.0)
        let contentHeight = self.contentView.update(
            width: contentWidth,
            presentationData: presentationData,
            item: item
        )
        transition.updateFrame(
            node: self.contentNode,
            frame: CGRect(x: horizontalInset, y: 4.0, width: contentWidth, height: contentHeight)
        )
        return contentHeight + 8.0
    }
}
'''
custom_item.write_text(item_source, encoding="utf-8")

# Replace the incorrect vertical PROFILEHUB2 item block with one inline item.
text = profile_items.read_text(encoding="utf-8")
if "GhostBase v1.1C PROFILEGLASS1 inline hub" not in text:
    start_marker = "    // MARK: GhostBase v1.1B PROFILEHUB2 inline rows\n"
    end_marker = "    var result: [(AnyHashable, [PeerInfoScreenItem])] = []\n"
    if start_marker not in text or end_marker not in text:
        raise SystemExit("[V11C PROFILEGLASS1] profile hub anchors missing")
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    replacement = r'''    // MARK: GhostBase v1.1C PROFILEGLASS1 inline hub
    if case let .user(user) = data.peer {
        let accountPeerId = context.account.peerId
        let targetPeerId = user.id
        let expanded = ghostBaseProfileHubIsExpanded(accountPeerId: accountPeerId, peerId: targetPeerId)
        let selectedTab = ghostBaseProfileHubSelectedTab(accountPeerId: accountPeerId, peerId: targetPeerId)
        let hiddenGiftCount = ghostBaseHiddenGiftHistoryEntries(accountPeerId: accountPeerId, peerId: targetPeerId).count

        let bodyText: String
        switch selectedTab {
        case .history:
            let gifts = ghostBaseGiftHistoryReport(accountPeerId: accountPeerId, peerId: targetPeerId)
            let presence = ghostBasePresenceHistoryReport(accountPeerId: accountPeerId, peerId: targetPeerId) ?? ""
            let channel = ghostBasePersonalChannelReport(accountPeerId: accountPeerId, targetPeerId: targetPeerId) ?? ""
            let report = [gifts, presence, channel].filter { !$0.isEmpty }.joined(separator: "\n")
            bodyText = ghostBaseProfileHubBody(report, empty: "Пока нет сохранённых изменений.")
        case .gifts:
            let hidden = ghostBaseHiddenGiftHistoryReport(accountPeerId: accountPeerId, peerId: targetPeerId)
            let all = ghostBaseGiftHistoryReport(accountPeerId: accountPeerId, peerId: targetPeerId)
            let report = hiddenGiftCount > 0 ? hidden + "\n\n" + all : all
            bodyText = ghostBaseProfileHubBody(report, empty: "Подарки пока не наблюдались.")
        case .online:
            let liveStatus = data.status?.text ?? "Текущий статус пока не получен"
            let timeline = ghostBasePresenceHistoryReport(accountPeerId: accountPeerId, peerId: targetPeerId) ?? ""
            let timelineBody = ghostBaseProfileHubBody(timeline, empty: "Сохранённых переходов пока нет.")
            bodyText = "Сейчас: \(liveStatus)\n\nИстория переходов\n\(timelineBody)"
        case .channel:
            let report = ghostBasePersonalChannelReport(accountPeerId: accountPeerId, targetPeerId: targetPeerId) ?? ""
            bodyText = ghostBaseProfileHubBody(report, empty: "Прикреплённый канал пока не наблюдался.")
        case .info:
            let username = user.addressName.map { "@\($0)" } ?? "не указан"
            bodyText = "Peer ID: \(user.id.toInt64())\nUsername: \(username)\nСкрытых подарков: \(hiddenGiftCount)"
        }

        items[.peerInfoTrailing]!.append(
            GhostBaseProfileHubItem(
                id: 9911200,
                title: "История и сведения",
                isExpanded: expanded,
                selectedTab: selectedTab.rawValue,
                tabTitles: GhostBaseProfileHubTab.allCases.map { $0.title },
                bodyText: bodyText,
                toggle: {
                    ghostBaseProfileHubSetExpanded(!expanded, accountPeerId: accountPeerId, peerId: targetPeerId)
                    interaction.requestLayout(true)
                },
                selectTab: { rawValue in
                    guard let tab = GhostBaseProfileHubTab(rawValue: rawValue) else {
                        return
                    }
                    ghostBaseProfileHubSetSelectedTab(tab, accountPeerId: accountPeerId, peerId: targetPeerId)
                    interaction.requestLayout(true)
                }
            )
        )
    }

'''
    text = text[:start] + replacement + text[end:]
    profile_items.write_text(text, encoding="utf-8")

# Install one cached wallpaper backdrop behind the whole PeerInfo screen.
text = screen.read_text(encoding="utf-8")
if "GhostBase v1.1C PROFILEGLASS1 wallpaper backdrop" not in text:
    import_anchor = "import Display\n"
    if import_anchor not in text:
        raise SystemExit("[V11C PROFILEGLASS1] Display import anchor missing")
    text = text.replace(import_anchor, import_anchor + "import WallpaperBackgroundNode\n", 1)

    property_anchor = "    let edgeEffectView: EdgeEffectView\n"
    if property_anchor not in text:
        raise SystemExit("[V11C PROFILEGLASS1] property anchor missing")
    text = text.replace(
        property_anchor,
        property_anchor
        + "    // MARK: GhostBase v1.1C PROFILEGLASS1 wallpaper backdrop\n"
        + "    let ghostBaseGlassWallpaperNode: WallpaperBackgroundNode?\n"
        + "    let ghostBaseGlassOverlayNode: ASDisplayNode?\n",
        1,
    )

    init_anchor = "        self.edgeEffectView = EdgeEffectView()\n"
    if init_anchor not in text:
        raise SystemExit("[V11C PROFILEGLASS1] init anchor missing")
    init_block = r'''

        if GhostBaseGlassStyle.isEnabled {
            self.ghostBaseGlassWallpaperNode = createWallpaperBackgroundNode(
                context: context,
                forChatDisplay: false,
                useSharedAnimationPhase: false
            )
            let overlayNode = ASDisplayNode()
            overlayNode.isLayerBacked = true
            self.ghostBaseGlassOverlayNode = overlayNode
        } else {
            self.ghostBaseGlassWallpaperNode = nil
            self.ghostBaseGlassOverlayNode = nil
        }
'''
    text = text.replace(init_anchor, init_anchor + init_block, 1)

    super_anchor = "        super.init()\n        \n        self.paneContainerNode.parentController = controller\n"
    if super_anchor not in text:
        raise SystemExit("[V11C PROFILEGLASS1] super anchor missing")
    super_block = r'''        super.init()

        if let wallpaperNode = self.ghostBaseGlassWallpaperNode {
            wallpaperNode.update(wallpaper: self.presentationData.chatWallpaper, animated: false)
            self.addSubnode(wallpaperNode)
        }
        if let overlayNode = self.ghostBaseGlassOverlayNode {
            overlayNode.backgroundColor = self.presentationData.theme.list.blocksBackgroundColor.withAlphaComponent(
                GhostBaseGlassStyle.backdropOverlayAlpha
            )
            self.addSubnode(overlayNode)
        }
        
        self.paneContainerNode.parentController = controller
'''
    text = text.replace(super_anchor, super_block, 1)

    bg_anchor = "        self.backgroundColor = self.presentationData.theme.list.blocksBackgroundColor\n"
    if bg_anchor not in text:
        raise SystemExit("[V11C PROFILEGLASS1] initial background anchor missing")
    text = text.replace(
        bg_anchor,
        "        self.backgroundColor = GhostBaseGlassStyle.isEnabled ? .clear : self.presentationData.theme.list.blocksBackgroundColor\n",
        1,
    )

    presentation_anchor = "        self.presentationData = presentationData\n        \n        self.updateBackgroundColor()\n"
    if presentation_anchor not in text:
        raise SystemExit("[V11C PROFILEGLASS1] presentation update anchor missing")
    presentation_block = r'''        self.presentationData = presentationData

        if let wallpaperNode = self.ghostBaseGlassWallpaperNode {
            wallpaperNode.update(wallpaper: presentationData.chatWallpaper, animated: false)
        }
        if let overlayNode = self.ghostBaseGlassOverlayNode {
            overlayNode.backgroundColor = presentationData.theme.list.blocksBackgroundColor.withAlphaComponent(
                GhostBaseGlassStyle.backdropOverlayAlpha
            )
        }
        
        self.updateBackgroundColor()
'''
    text = text.replace(presentation_anchor, presentation_block, 1)

    layout_anchor = "        transition.updateFrame(node: self.scrollNode, frame: CGRect(origin: CGPoint(), size: layout.size))\n"
    if layout_anchor not in text:
        raise SystemExit("[V11C PROFILEGLASS1] layout anchor missing")
    layout_block = r'''        if let wallpaperNode = self.ghostBaseGlassWallpaperNode {
            transition.updateFrame(node: wallpaperNode, frame: CGRect(origin: CGPoint(), size: layout.size))
            wallpaperNode.updateLayout(size: layout.size, displayMode: .aspectFill, transition: transition)
        }
        if let overlayNode = self.ghostBaseGlassOverlayNode {
            transition.updateFrame(node: overlayNode, frame: CGRect(origin: CGPoint(), size: layout.size))
        }

'''
    text = text.replace(layout_anchor, layout_block + layout_anchor, 1)

    old_bg_func = '''    private func updateBackgroundColor() {
        let color: UIColor
        if self.paneContainerNode.currentPaneKey == .gifts {
            color = self.presentationData.theme.list.blocksBackgroundColor
        } else {
            color = self.presentationData.theme.list.blocksBackgroundColor.mixedWith(self.presentationData.theme.list.plainBackgroundColor, alpha: self.effectiveAreaExpansionFraction)
        }
        self.backgroundColor = color
    }
'''
    new_bg_func = '''    private func updateBackgroundColor() {
        if GhostBaseGlassStyle.isEnabled {
            self.backgroundColor = .clear
            return
        }
        let color: UIColor
        if self.paneContainerNode.currentPaneKey == .gifts {
            color = self.presentationData.theme.list.blocksBackgroundColor
        } else {
            color = self.presentationData.theme.list.blocksBackgroundColor.mixedWith(self.presentationData.theme.list.plainBackgroundColor, alpha: self.effectiveAreaExpansionFraction)
        }
        self.backgroundColor = color
    }
'''
    if old_bg_func not in text:
        raise SystemExit("[V11C PROFILEGLASS1] updateBackgroundColor anchor missing")
    text = text.replace(old_bg_func, new_bg_func, 1)
    screen.write_text(text, encoding="utf-8")

# Lightweight Cold Glass section surfaces. No blur per row.
text = section.read_text(encoding="utf-8")
old = "        self.backgroundNode.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor\n"
new = "        self.backgroundNode.backgroundColor = GhostBaseGlassStyle.coldFillColor(presentationData.theme.list.itemBlocksBackgroundColor)\n"
if new not in text:
    if old not in text:
        raise SystemExit("[V11C PROFILEGLASS1] section background anchor missing")
    text = text.replace(old, new, 1)
    section.write_text(text, encoding="utf-8")

# Wallpaper dependency for the profile component.
text = build.read_text(encoding="utf-8")
dep = '        "//submodules/WallpaperBackgroundNode",\n'
if dep not in text:
    anchor = '        "//submodules/Display",\n'
    if anchor not in text:
        raise SystemExit("[V11C PROFILEGLASS1] BUILD Display dependency anchor missing")
    text = text.replace(anchor, anchor + dep, 1)
    build.write_text(text, encoding="utf-8")

print("[V11C] PROFILEGLASS1 + PRESENCELIVE1 installed")
