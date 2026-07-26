#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
base = root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen"
profile_items = base / "Sources/PeerInfoProfileItems.swift"
screen = base / "Sources/PeerInfoScreen.swift"
section = base / "Sources/PeerInfoScreenItemSectionContainerNode.swift"
header = base / "Sources/PeerInfoHeaderNode.swift"
build = base / "BUILD"
custom = base / "Sources/GhostBaseProfileHubItem.swift"
for p in [profile_items, screen, section, header, build]:
    if not p.is_file():
        raise SystemExit(f"[V11D PROFILE] missing {p}")

# New real Glass item, using Telegram's native GlassBackgroundView and TabSelectorComponent.
custom.write_text(r'''import Foundation
import UIKit
import Display
import AsyncDisplayKit
import AccountContext
import TelegramPresentationData
import ComponentFlow
import GlassBackgroundComponent
import TabSelectorComponent

// MARK: GhostBase v1.1D PROFILESELECTOR2 native glass selector
final class GhostBaseProfileHubItem: PeerInfoScreenItem {
    let id: AnyHashable
    let peerId: Int64
    let title: String
    let isExpanded: Bool
    let selectedTab: Int
    let tabTitles: [String]
    let bodyText: String
    let toggle: () -> Void
    let selectTab: (Int) -> Void

    init(id: AnyHashable, peerId: Int64, title: String, isExpanded: Bool, selectedTab: Int, tabTitles: [String], bodyText: String, toggle: @escaping () -> Void, selectTab: @escaping (Int) -> Void) {
        self.id = id
        self.peerId = peerId
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
    private let fallbackView = UIView()
    private let glassView = GlassBackgroundView()
    private let titleLabel = UILabel()
    private let chevronView = UIImageView()
    private let headerButton = UIButton(type: .custom)
    private let separator = UIView()
    private let bodyLabel = UILabel()
    private let tabSelector = ComponentView<Empty>()
    private var toggleAction: (() -> Void)?
    private var selectTabAction: ((Int) -> Void)?
    private var expanded = false
    private var selectorSize = CGSize()
    private var bodyHeight: CGFloat = 0.0

    override init(frame: CGRect) {
        super.init(frame: frame)
        self.clipsToBounds = false
        self.fallbackView.layer.cornerCurve = .continuous
        self.glassView.contentView.addSubview(self.titleLabel)
        self.glassView.contentView.addSubview(self.chevronView)
        self.glassView.contentView.addSubview(self.headerButton)
        self.glassView.contentView.addSubview(self.separator)
        self.glassView.contentView.addSubview(self.bodyLabel)
        self.insertSubview(self.fallbackView, at: 0)
        self.addSubview(self.glassView)
        self.titleLabel.font = UIFont.systemFont(ofSize: 17.0, weight: .semibold)
        self.bodyLabel.font = UIFont.systemFont(ofSize: 14.0, weight: .regular)
        self.bodyLabel.numberOfLines = 0
        self.bodyLabel.lineBreakMode = .byWordWrapping
        self.chevronView.contentMode = .center
        self.headerButton.addTarget(self, action: #selector(self.headerPressed), for: .touchUpInside)
    }

    required init?(coder: NSCoder) {
        preconditionFailure()
    }

    @objc private func headerPressed() {
        self.toggleAction?()
    }

    func update(width: CGFloat, context: AccountContext, presentationData: PresentationData, item: GhostBaseProfileHubItem) -> CGFloat {
        self.toggleAction = item.toggle
        self.selectTabAction = item.selectTab
        self.expanded = item.isExpanded
        let enabled = GhostBaseGlassStyle.isEnabled
        let isDark = presentationData.theme.overallDarkAppearance
        let tint = GhostBaseGlassStyle.tintColor(peerId: item.peerId, fallback: presentationData.theme.list.itemAccentColor)

        self.titleLabel.text = item.title
        self.titleLabel.textColor = enabled ? .white : presentationData.theme.list.itemPrimaryTextColor
        self.chevronView.image = UIImage(systemName: item.isExpanded ? "chevron.up" : "chevron.down")
        self.chevronView.tintColor = enabled ? UIColor.white.withAlphaComponent(0.92) : presentationData.theme.list.itemAccentColor
        self.bodyLabel.text = item.bodyText
        self.bodyLabel.textColor = enabled ? UIColor.white.withAlphaComponent(0.82) : presentationData.theme.list.itemSecondaryTextColor
        self.separator.backgroundColor = enabled ? UIColor.white.withAlphaComponent(0.12) : presentationData.theme.list.itemBlocksSeparatorColor

        if item.isExpanded {
            let selectorComponent = TabSelectorComponent(
                context: context,
                colors: TabSelectorComponent.Colors(
                    foreground: enabled ? .white : presentationData.theme.list.itemPrimaryTextColor,
                    selection: enabled ? UIColor.white.withAlphaComponent(0.20) : presentationData.theme.list.itemAccentColor.withAlphaComponent(0.18),
                    normal: enabled ? UIColor.white.withAlphaComponent(0.08) : presentationData.theme.list.itemBlocksBackgroundColor,
                    simple: false
                ),
                theme: presentationData.theme,
                style: enabled ? .glass : .legacy,
                customLayout: TabSelectorComponent.CustomLayout(font: UIFont.systemFont(ofSize: 14.0, weight: .semibold), spacing: 3.0, innerSpacing: 12.0, fillWidth: false, lineSelection: false, verticalInset: 0.0, allowScroll: true, height: 42.0),
                items: item.tabTitles.enumerated().map { index, title in
                    TabSelectorComponent.Item(id: index, title: title)
                },
                selectedId: item.selectedTab,
                setSelectedId: { [weak self] id in
                    guard let value = id.base as? Int else { return }
                    self?.selectTabAction?(value)
                }
            )
            self.selectorSize = self.tabSelector.update(
                transition: .immediate,
                component: AnyComponent(selectorComponent),
                environment: {},
                containerSize: CGSize(width: max(1.0, width - 24.0), height: 42.0)
            )
            if let selectorView = self.tabSelector.view, selectorView.superview == nil {
                self.glassView.contentView.addSubview(selectorView)
            }
            self.bodyHeight = ceil(self.bodyLabel.sizeThatFits(CGSize(width: max(1.0, width - 32.0), height: CGFloat.greatestFiniteMagnitude)).height)
        } else {
            self.selectorSize = .zero
            self.bodyHeight = 0.0
        }

        let totalHeight: CGFloat = item.isExpanded ? 58.0 + 48.0 + self.bodyHeight + 28.0 : 58.0
        self.fallbackView.isHidden = enabled
        self.fallbackView.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor
        self.fallbackView.layer.cornerRadius = 18.0
        self.glassView.isHidden = !enabled
        if enabled {
            self.glassView.update(
                size: CGSize(width: width, height: totalHeight),
                cornerRadius: 24.0,
                isDark: isDark,
                tintColor: GlassBackgroundView.TintColor(
                    kind: .custom(style: .default, color: tint.withAlphaComponent(GhostBaseGlassStyle.usesReducedEffects ? 0.72 : 0.26)),
                    innerColor: UIColor.white.withAlphaComponent(GhostBaseGlassStyle.usesReducedEffects ? 0.02 : 0.08),
                    innerInset: 2.0
                ),
                isInteractive: false,
                isVisible: true,
                transition: .immediate
            )
        }

        self.tabSelector.view?.isHidden = !item.isExpanded
        self.separator.isHidden = !item.isExpanded
        self.bodyLabel.isHidden = !item.isExpanded
        self.setNeedsLayout()
        return totalHeight
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        let size = self.bounds.size
        self.fallbackView.frame = self.bounds
        self.glassView.frame = self.bounds
        self.titleLabel.frame = CGRect(x: 18.0, y: 0.0, width: max(0.0, size.width - 70.0), height: 58.0)
        self.chevronView.frame = CGRect(x: max(0.0, size.width - 50.0), y: 7.0, width: 40.0, height: 44.0)
        self.headerButton.frame = CGRect(x: 0.0, y: 0.0, width: size.width, height: 58.0)
        guard self.expanded else { return }
        self.separator.frame = CGRect(x: 16.0, y: 57.0, width: max(0.0, size.width - 32.0), height: UIScreenPixel)
        if let selectorView = self.tabSelector.view {
            selectorView.frame = CGRect(x: 12.0, y: 64.0, width: max(0.0, size.width - 24.0), height: 42.0)
        }
        self.bodyLabel.frame = CGRect(x: 18.0, y: 114.0, width: max(0.0, size.width - 36.0), height: self.bodyHeight)
    }
}

private final class GhostBaseProfileHubItemNode: PeerInfoScreenItemNode {
    private let contentView: GhostBaseProfileHubView
    private let contentNode: ASDisplayNode

    override init() {
        let view = GhostBaseProfileHubView()
        self.contentView = view
        self.contentNode = ASDisplayNode(viewBlock: { view })
        super.init()
        self.addSubnode(self.contentNode)
    }

    override func update(context: AccountContext, width: CGFloat, safeInsets: UIEdgeInsets, presentationData: PresentationData, item: PeerInfoScreenItem, topItem: PeerInfoScreenItem?, bottomItem: PeerInfoScreenItem?, hasCorners: Bool, transition: ContainedViewLayoutTransition) -> CGFloat {
        guard let item = item as? GhostBaseProfileHubItem else { return 0.0 }
        let inset: CGFloat = 12.0
        let contentWidth = max(1.0, width - inset * 2.0)
        let height = self.contentView.update(width: contentWidth, context: context, presentationData: presentationData, item: item)
        transition.updateFrame(node: self.contentNode, frame: CGRect(x: inset, y: 4.0, width: contentWidth, height: height))
        return height + 8.0
    }
}
''', encoding="utf-8")

# Move old exposed ID/DC/registration card into the Сведения tab.
text = profile_items.read_text(encoding="utf-8")
start_metrics = "    // MARK: GhostBase v0.4A peer metrics card with toggles\n"
end_metrics = "\n\n    let bioContextAction:"
if start_metrics in text:
    s = text.index(start_metrics)
    e = text.index(end_metrics, s)
    text = text[:s] + "    // MARK: GhostBase v1.1D metrics moved into Сведения\n" + text[e:]

# Replace either Build 89 PROFILEHUB2 or rejected Build 90 PROFILEGLASS1 block.
markers = [
    "    // MARK: GhostBase v1.1D PROFILESELECTOR2 one native glass block\n",
    "    // MARK: GhostBase v1.1C PROFILEGLASS1 inline hub\n",
    "    // MARK: GhostBase v1.1B PROFILEHUB2 inline rows\n",
]
start = next((text.index(m) for m in markers if m in text), None)
end_marker = "    var result: [(AnyHashable, [PeerInfoScreenItem])] = []\n"
if start is None or end_marker not in text:
    raise SystemExit("[V11D PROFILE] profile hub anchors missing")
end = text.index(end_marker, start)
replacement = r'''    // MARK: GhostBase v1.1D PROFILESELECTOR2 one native glass block
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
            bodyText = ghostBaseProfileHubBody([gifts, presence, channel].filter { !$0.isEmpty }.joined(separator: "\n"), empty: "Пока нет сохранённых изменений.")
        case .gifts:
            let hidden = ghostBaseHiddenGiftHistoryReport(accountPeerId: accountPeerId, peerId: targetPeerId)
            let all = ghostBaseGiftHistoryReport(accountPeerId: accountPeerId, peerId: targetPeerId)
            bodyText = ghostBaseProfileHubBody(hiddenGiftCount > 0 ? hidden + "\n\n" + all : all, empty: "Подарки пока не наблюдались.")
        case .online:
            let live = data.status?.text ?? "Текущий статус пока не получен"
            let timeline = ghostBaseProfileHubBody(ghostBasePresenceHistoryReport(accountPeerId: accountPeerId, peerId: targetPeerId) ?? "", empty: "Сохранённых переходов пока нет.")
            bodyText = "Сейчас: \(live)\n\nИстория переходов\n\(timeline)"
        case .channel:
            bodyText = ghostBaseProfileHubBody(ghostBasePersonalChannelReport(accountPeerId: accountPeerId, targetPeerId: targetPeerId) ?? "", empty: "Прикреплённый канал пока не наблюдался.")
        case .info:
            let peerIdText = String(user.id.id._internalGetInt64Value())
            let username = user.addressName.map { "@\($0)" } ?? "не указан"
            var lines = ["Peer ID: \(peerIdText)", "Username: \(username)"]
            if let image = user.smallProfileImage, let resource = image.resource as? CloudPeerPhotoSizeMediaResource {
                lines.append("DC: \(resource.datacenterId)")
            }
            if let cachedData = data.cachedData as? CachedUserData, let registrationDate = cachedData.peerStatusSettings?.registrationDate {
                lines.append("Регистрация: \(registrationDate)")
            }
            lines.append("Скрытых подарков: \(hiddenGiftCount)")
            bodyText = lines.joined(separator: "\n")
        }

        items[.peerInfoTrailing]!.append(GhostBaseProfileHubItem(
            id: 9911200,
            peerId: targetPeerId.toInt64(),
            title: "История и сведения",
            isExpanded: expanded,
            selectedTab: selectedTab.rawValue,
            tabTitles: GhostBaseProfileHubTab.allCases.map { $0.title },
            bodyText: bodyText,
            toggle: {
                ghostBaseProfileHubSetExpanded(!expanded, accountPeerId: accountPeerId, peerId: targetPeerId)
                interaction.requestLayout(true)
            },
            selectTab: { raw in
                guard let tab = GhostBaseProfileHubTab(rawValue: raw) else { return }
                ghostBaseProfileHubSetSelectedTab(tab, accountPeerId: accountPeerId, peerId: targetPeerId)
                interaction.requestLayout(true)
            }
        ))
    }

'''
text = text[:start] + replacement + text[end:]
profile_items.write_text(text, encoding="utf-8")

# Clean rejected Build 90 backdrop first, then install wallpaper -> avatar -> global priority with real blur.
text = screen.read_text(encoding="utf-8")
# Remove rejected properties and blocks when present.
def remove_region(value: str, begin: str, finish: str, *, keep_finish: bool = True) -> str:
    if begin not in value:
        return value
    region_start = value.index(begin)
    region_end = value.index(finish, region_start)
    if not keep_finish:
        region_end += len(finish)
    return value[:region_start] + value[region_end:]

text = text.replace(
    "    // MARK: GhostBase v1.1C PROFILEGLASS1 wallpaper backdrop\n"
    "    let ghostBaseGlassWallpaperNode: WallpaperBackgroundNode?\n"
    "    let ghostBaseGlassOverlayNode: ASDisplayNode?\n",
    ""
)
text = remove_region(
    text,
    "\n        if GhostBaseGlassStyle.isEnabled {\n            self.ghostBaseGlassWallpaperNode = createWallpaperBackgroundNode(",
    "\n        var forumTopicThreadId: Int64?\n"
)
text = remove_region(
    text,
    "        if let wallpaperNode = self.ghostBaseGlassWallpaperNode {\n            wallpaperNode.update(wallpaper: self.presentationData.chatWallpaper, animated: false)",
    "        self.paneContainerNode.parentController = controller\n"
)
text = text.replace(
    "        self.backgroundColor = GhostBaseGlassStyle.isEnabled ? .clear : self.presentationData.theme.list.blocksBackgroundColor\n",
    "        self.backgroundColor = self.presentationData.theme.list.blocksBackgroundColor\n"
)
text = remove_region(
    text,
    "        if let wallpaperNode = self.ghostBaseGlassWallpaperNode {\n            wallpaperNode.update(wallpaper: presentationData.chatWallpaper, animated: false)",
    "        self.updateBackgroundColor()\n"
)
text = remove_region(
    text,
    "        if let wallpaperNode = self.ghostBaseGlassWallpaperNode {\n            transition.updateFrame(node: wallpaperNode, frame: CGRect(origin: CGPoint(), size: layout.size))",
    "        transition.updateFrame(node: self.scrollNode, frame: CGRect(origin: CGPoint(), size: layout.size))\n"
)
text = text.replace(
    "    private func updateBackgroundColor() {\n"
    "        if GhostBaseGlassStyle.isEnabled {\n"
    "            self.backgroundColor = .clear\n"
    "            return\n"
    "        }\n"
    "        let color: UIColor\n",
    "    private func updateBackgroundColor() {\n        let color: UIColor\n"
)

if "GhostBase v1.1D PROFILEBACKDROP2" not in text:
    if "import WallpaperBackgroundNode\n" not in text:
        text = text.replace("import Display\n", "import Display\nimport WallpaperBackgroundNode\n", 1)
    prop = "    let edgeEffectView: EdgeEffectView\n"
    props = '''    let edgeEffectView: EdgeEffectView\n    // MARK: GhostBase v1.1D PROFILEBACKDROP2\n    let ghostBaseBackdropWallpaperNode: WallpaperBackgroundNode\n    let ghostBaseBackdropAvatarNode: ASImageNode\n    let ghostBaseBackdropBlurNode: ASDisplayNode\n    let ghostBaseBackdropDimNode: ASDisplayNode\n    private var ghostBaseGlassObservers: [NSObjectProtocol] = []\n    private var ghostBaseBackdropUsesPersonalWallpaper = false\n'''
    if prop not in text: raise SystemExit("[V11D PROFILE] property anchor missing")
    text = text.replace(prop, props, 1)

    init_anchor = "        self.edgeEffectView = EdgeEffectView()\n"
    init_insert = '''        self.edgeEffectView = EdgeEffectView()\n        self.ghostBaseBackdropWallpaperNode = createWallpaperBackgroundNode(context: context, forChatDisplay: false, useSharedAnimationPhase: false)\n        self.ghostBaseBackdropAvatarNode = ASImageNode()\n        self.ghostBaseBackdropAvatarNode.contentMode = .scaleAspectFill\n        self.ghostBaseBackdropAvatarNode.clipsToBounds = true\n        self.ghostBaseBackdropBlurNode = ASDisplayNode(viewBlock: {\n            return UIVisualEffectView(effect: UIBlurEffect(style: .systemMaterialDark))\n        })\n        self.ghostBaseBackdropDimNode = ASDisplayNode()\n        self.ghostBaseBackdropDimNode.isLayerBacked = true\n'''
    if init_anchor not in text: raise SystemExit("[V11D PROFILE] init anchor missing")
    text = text.replace(init_anchor, init_insert, 1)

    super_anchor = "        super.init()\n"
    super_insert = '''        super.init()

        self.addSubnode(self.ghostBaseBackdropWallpaperNode)
        self.addSubnode(self.ghostBaseBackdropAvatarNode)
        self.addSubnode(self.ghostBaseBackdropBlurNode)
        self.addSubnode(self.ghostBaseBackdropDimNode)
        let ghostBaseRefreshGlass: (Notification) -> Void = { [weak self] _ in
            guard let self else { return }
            self.ghostBaseUpdateBackdrop()
            if let (layout, navigationHeight) = self.validLayout {
                self.containerLayoutUpdated(layout: layout, navigationHeight: navigationHeight, transition: .immediate)
            }
        }
        self.ghostBaseGlassObservers.append(NotificationCenter.default.addObserver(forName: .ghostBaseGlassDidChange, object: nil, queue: .main, using: ghostBaseRefreshGlass))
        self.ghostBaseGlassObservers.append(NotificationCenter.default.addObserver(forName: .ghostBaseGlassTintDidChange, object: nil, queue: .main, using: ghostBaseRefreshGlass))
        self.ghostBaseGlassObservers.append(NotificationCenter.default.addObserver(forName: UIAccessibility.reduceTransparencyStatusDidChangeNotification, object: nil, queue: .main, using: ghostBaseRefreshGlass))
        self.ghostBaseGlassObservers.append(NotificationCenter.default.addObserver(forName: .NSProcessInfoPowerStateDidChange, object: nil, queue: .main, using: ghostBaseRefreshGlass))
'''
    if super_anchor not in text: raise SystemExit("[V11D PROFILE] super anchor missing")
    text = text.replace(super_anchor, super_insert, 1)

    deinit_anchor = "    deinit {\n        self.dataDisposable?.dispose()\n"
    deinit_insert = "    deinit {\n        for observer in self.ghostBaseGlassObservers { NotificationCenter.default.removeObserver(observer) }\n        self.dataDisposable?.dispose()\n"
    if deinit_anchor not in text: raise SystemExit("[V11D PROFILE] deinit anchor missing")
    text = text.replace(deinit_anchor, deinit_insert, 1)

    data_anchor = "        self.data = data\n"
    if data_anchor not in text: raise SystemExit("[V11D PROFILE] data anchor missing")
    text = text.replace(data_anchor, data_anchor + "        self.ghostBaseUpdateBackdrop()\n", 1)

    presentation_anchor = "        self.presentationData = presentationData\n"
    presentation_insert = "        self.presentationData = presentationData\n        self.ghostBaseUpdateBackdrop()\n"
    if presentation_anchor not in text: raise SystemExit("[V11D PROFILE] presentation anchor missing")
    text = text.replace(presentation_anchor, presentation_insert, 1)

    layout_anchor = "        transition.updateFrame(node: self.scrollNode, frame: CGRect(origin: CGPoint(), size: layout.size))\n"
    layout_insert = '''        transition.updateFrame(node: self.ghostBaseBackdropWallpaperNode, frame: CGRect(origin: .zero, size: layout.size))\n        self.ghostBaseBackdropWallpaperNode.updateLayout(size: layout.size, displayMode: .aspectFill, transition: transition)\n        transition.updateFrame(node: self.ghostBaseBackdropAvatarNode, frame: CGRect(origin: .zero, size: layout.size))\n        transition.updateFrame(node: self.ghostBaseBackdropBlurNode, frame: CGRect(origin: .zero, size: layout.size))\n        transition.updateFrame(node: self.ghostBaseBackdropDimNode, frame: CGRect(origin: .zero, size: layout.size))\n\n        transition.updateFrame(node: self.scrollNode, frame: CGRect(origin: CGPoint(), size: layout.size))\n'''
    if layout_anchor not in text: raise SystemExit("[V11D PROFILE] layout anchor missing")
    text = text.replace(layout_anchor, layout_insert, 1)

    method_anchor = "    private func updateBackgroundColor() {\n"
    helper = r'''    private func ghostBaseWallpaperTint(_ wallpaper: TelegramWallpaper) -> UIColor? {
        let colors: [UInt32]
        switch wallpaper {
        case let .color(value): colors = [value]
        case let .gradient(value): colors = value.colors
        case let .image(_, settings): colors = settings.colors
        case let .file(value): colors = value.settings.colors
        case let .builtin(settings): colors = settings.colors
        case .emoticon: colors = []
        }
        guard !colors.isEmpty else { return nil }
        var red: CGFloat = 0.0, green: CGFloat = 0.0, blue: CGFloat = 0.0
        for value in colors {
            red += CGFloat((value >> 16) & 0xff) / 255.0
            green += CGFloat((value >> 8) & 0xff) / 255.0
            blue += CGFloat(value & 0xff) / 255.0
        }
        let count = CGFloat(colors.count)
        return UIColor(red: red / count, green: green / count, blue: blue / count, alpha: 1.0)
    }

    private func ghostBaseAverageColor(_ image: UIImage) -> UIColor? {
        guard let cgImage = image.cgImage else { return nil }
        var pixel = [UInt8](repeating: 0, count: 4)
        guard let context = CGContext(data: &pixel, width: 1, height: 1, bitsPerComponent: 8, bytesPerRow: 4, space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { return nil }
        context.interpolationQuality = .medium
        context.draw(cgImage, in: CGRect(x: 0.0, y: 0.0, width: 1.0, height: 1.0))
        return UIColor(red: CGFloat(pixel[0]) / 255.0, green: CGFloat(pixel[1]) / 255.0, blue: CGFloat(pixel[2]) / 255.0, alpha: 1.0)
    }

    private func ghostBaseCaptureAvatarBackdrop() {
        guard GhostBaseGlassStyle.isEnabled, !self.ghostBaseBackdropUsesPersonalWallpaper else { return }
        let sourceView = self.headerNode.avatarListNode.avatarContainerNode.avatarNode.contentNode.view
        guard sourceView.bounds.width > 2.0, sourceView.bounds.height > 2.0 else { return }
        let renderer = UIGraphicsImageRenderer(bounds: sourceView.bounds)
        let image = renderer.image { _ in
            sourceView.drawHierarchy(in: sourceView.bounds, afterScreenUpdates: true)
        }
        self.ghostBaseBackdropAvatarNode.image = image
        self.ghostBaseBackdropAvatarNode.isHidden = false
        self.ghostBaseBackdropWallpaperNode.isHidden = true
        if let tint = self.ghostBaseAverageColor(image) {
            GhostBaseGlassStyle.setActiveTintColor(tint, peerId: self.peerId.toInt64())
        }
    }

    private func ghostBaseUpdateBackdrop() {
        let enabled = GhostBaseGlassStyle.isEnabled
        self.ghostBaseBackdropWallpaperNode.isHidden = !enabled
        self.ghostBaseBackdropAvatarNode.isHidden = true
        self.ghostBaseBackdropBlurNode.isHidden = !enabled || GhostBaseGlassStyle.usesReducedEffects
        self.ghostBaseBackdropDimNode.isHidden = !enabled
        self.ghostBaseBackdropDimNode.backgroundColor = UIColor.black.withAlphaComponent(GhostBaseGlassStyle.usesReducedEffects ? 0.66 : 0.30)
        guard enabled else {
            self.backgroundColor = self.presentationData.theme.list.blocksBackgroundColor
            return
        }

        if !self.isSettings, let cached = self.data?.cachedData as? CachedUserData, let wallpaper = cached.wallpaper {
            self.ghostBaseBackdropUsesPersonalWallpaper = true
            self.ghostBaseBackdropWallpaperNode.isHidden = false
            self.ghostBaseBackdropAvatarNode.isHidden = true
            self.ghostBaseBackdropWallpaperNode.update(wallpaper: wallpaper, animated: false)
            if let tint = self.ghostBaseWallpaperTint(wallpaper) {
                GhostBaseGlassStyle.setActiveTintColor(tint, peerId: self.peerId.toInt64())
            }
        } else if !self.isSettings {
            self.ghostBaseBackdropUsesPersonalWallpaper = false
            self.ghostBaseBackdropWallpaperNode.update(wallpaper: self.presentationData.chatWallpaper, animated: false)
            Queue.mainQueue().after(0.05) { [weak self] in self?.ghostBaseCaptureAvatarBackdrop() }
        } else {
            self.ghostBaseBackdropUsesPersonalWallpaper = false
            self.ghostBaseBackdropWallpaperNode.isHidden = false
            self.ghostBaseBackdropWallpaperNode.update(wallpaper: self.presentationData.chatWallpaper, animated: false)
            if let tint = self.ghostBaseWallpaperTint(self.presentationData.chatWallpaper) {
                GhostBaseGlassStyle.setActiveTintColor(tint, peerId: nil)
            }
        }
        self.backgroundColor = .clear
    }

'''
    if method_anchor not in text: raise SystemExit("[V11D PROFILE] background method anchor missing")
    text = text.replace(method_anchor, helper + method_anchor, 1)

    old_bg = '''    private func updateBackgroundColor() {\n        let color: UIColor\n        if self.paneContainerNode.currentPaneKey == .gifts {\n            color = self.presentationData.theme.list.blocksBackgroundColor\n        } else {\n            color = self.presentationData.theme.list.blocksBackgroundColor.mixedWith(self.presentationData.theme.list.plainBackgroundColor, alpha: self.effectiveAreaExpansionFraction)\n        }\n        self.backgroundColor = color\n    }\n'''
    new_bg = '''    private func updateBackgroundColor() {\n        if GhostBaseGlassStyle.isEnabled {\n            self.backgroundColor = .clear\n            return\n        }\n        let color: UIColor\n        if self.paneContainerNode.currentPaneKey == .gifts {\n            color = self.presentationData.theme.list.blocksBackgroundColor\n        } else {\n            color = self.presentationData.theme.list.blocksBackgroundColor.mixedWith(self.presentationData.theme.list.plainBackgroundColor, alpha: self.effectiveAreaExpansionFraction)\n        }\n        self.backgroundColor = color\n    }\n'''
    if old_bg not in text: raise SystemExit("[V11D PROFILE] background function exact anchor missing")
    text = text.replace(old_bg, new_bg, 1)

screen.write_text(text, encoding="utf-8")

# One real Cold Glass view per large section, never per row.
text = section.read_text(encoding="utf-8")
if "GhostBase v1.1D SECTIONGLASS2" not in text:
    if "import ComponentFlow\n" not in text:
        text = text.replace("import Display\n", "import Display\nimport ComponentFlow\nimport GlassBackgroundComponent\n", 1)
    text = text.replace("    private let backgroundNode: ASDisplayNode\n", "    // MARK: GhostBase v1.1D SECTIONGLASS2 one material per section\n    private let backgroundNode: ASDisplayNode\n", 1)
    text = text.replace("        self.backgroundNode = ASDisplayNode()\n        self.backgroundNode.isLayerBacked = true\n", "        self.backgroundNode = ASDisplayNode(viewBlock: { GlassBackgroundView() })\n", 1)
    old = "        self.backgroundNode.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor\n"
    new = '''        if let glassView = self.backgroundNode.view as? GlassBackgroundView, GhostBaseGlassStyle.isEnabled {
            glassView.isHidden = false
            self.backgroundNode.backgroundColor = .clear
        } else {
            (self.backgroundNode.view as? GlassBackgroundView)?.isHidden = true
            self.backgroundNode.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor
        }
'''
    # Accept rejected v11c line too.
    text = text.replace("        self.backgroundNode.backgroundColor = GhostBaseGlassStyle.coldFillColor(presentationData.theme.list.itemBlocksBackgroundColor)\n", old)
    if old not in text: raise SystemExit("[V11D PROFILE] section color anchor missing")
    text = text.replace(old, new, 1)

    frame_anchor = "        transition.updateFrame(node: self.backgroundNode, frame: CGRect(origin: CGPoint(x: 0.0, y: contentWithBackgroundOffset), size: CGSize(width: width, height: max(0.0, contentWithBackgroundHeight - contentWithBackgroundOffset))))\n"
    frame_insert = frame_anchor + '''        // MARK: GhostBase v1.1D SECTIONGLASS2 exact final material size
        if let glassView = self.backgroundNode.view as? GlassBackgroundView, GhostBaseGlassStyle.isEnabled {
            let materialHeight = max(1.0, contentWithBackgroundHeight - contentWithBackgroundOffset)
            let tint = GhostBaseGlassStyle.activeTintColor(fallback: presentationData.theme.list.itemAccentColor)
            glassView.update(size: CGSize(width: width, height: materialHeight), cornerRadius: hasCorners ? 22.0 : 0.0, isDark: presentationData.theme.overallDarkAppearance, tintColor: GlassBackgroundView.TintColor(kind: .custom(style: .default, color: tint.withAlphaComponent(GhostBaseGlassStyle.usesReducedEffects ? 0.78 : 0.22)), innerColor: UIColor.white.withAlphaComponent(0.05), innerInset: 2.0), isInteractive: false, isVisible: true, transition: ComponentTransition(transition))
        }
'''
    if frame_anchor not in text: raise SystemExit("[V11D PROFILE] section final frame anchor missing")
    text = text.replace(frame_anchor, frame_insert, 1)
    section.write_text(text, encoding="utf-8")

# Tint existing native blurred profile action buttons from the active backdrop source.
text = header.read_text(encoding="utf-8")
if "GhostBase v1.1D HEADERGLASS2" not in text:
    text = text.replace("        let contentButtonBackgroundColor: UIColor\n        let contentButtonForegroundColor: UIColor\n", "        var contentButtonBackgroundColor: UIColor\n        var contentButtonForegroundColor: UIColor\n", 1)
    anchor = "        do {\n            self.currentCredibilityIcon = credibilityIcon\n"
    insert = '''        // MARK: GhostBase v1.1D HEADERGLASS2 tint native blurred buttons from active backdrop\n        if GhostBaseGlassStyle.isEnabled, let peer {\n            let tint = GhostBaseGlassStyle.tintColor(peerId: peer.id.toInt64(), fallback: presentationData.theme.list.itemAccentColor)\n            contentButtonBackgroundColor = tint.withAlphaComponent(GhostBaseGlassStyle.usesReducedEffects ? 0.72 : 0.28)\n            contentButtonForegroundColor = .white\n        }\n\n'''
    if anchor not in text: raise SystemExit("[V11D PROFILE] header tint anchor missing")
    text = text.replace(anchor, insert + anchor, 1)

    cover_anchor = "        if let backgroundCoverView = self.backgroundCover.view as? PeerInfoCoverComponent.View {\n"
    cover_insert = cover_anchor + "            // PROFILEBACKDROP2 replaces the stock premium cover with the active chat wallpaper/avatar backdrop.\n            backgroundCoverView.alpha = GhostBaseGlassStyle.isEnabled ? 0.0 : 1.0\n"
    if cover_anchor not in text: raise SystemExit("[V11D PROFILE] header premium cover anchor missing")
    text = text.replace(cover_anchor, cover_insert, 1)
    header.write_text(text, encoding="utf-8")

# Required backdrop dependency; native Glass/Tab deps already exist in Official 12.9.2.
text = build.read_text(encoding="utf-8")
dep = '        "//submodules/WallpaperBackgroundNode",\n'
if dep not in text:
    anchor = '        "//submodules/Display",\n'
    if anchor not in text: raise SystemExit("[V11D PROFILE] BUILD anchor missing")
    text = text.replace(anchor, anchor + dep, 1)
build.write_text(text, encoding="utf-8")
print("[V11D] PROFILEBACKDROP2 + PROFILESELECTOR2 + SECTIONGLASS2 installed")
