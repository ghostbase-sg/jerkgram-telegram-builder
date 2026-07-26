#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
base = root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen"
sources = base / "Sources"
screen = sources / "PeerInfoScreen.swift"
header = sources / "PeerInfoHeaderNode.swift"
section = sources / "PeerInfoScreenItemSectionContainerNode.swift"
profile_items = sources / "PeerInfoProfileItems.swift"
build = base / "BUILD"

for path in [screen, header, section, profile_items, build]:
    if not path.exists():
        raise SystemExit(f"[V11E PROFILE] missing {path}")

# Canonical source applies this patch exactly once. Keep local re-runs safe.
if (
    "GhostBase v1.1E PROFILEBACKDROP3" in screen.read_text(encoding="utf-8")
    and "GhostBase v1.1E HEADERBUTTONS3" in header.read_text(encoding="utf-8")
    and "GhostBase v1.1E COLDSECTION3" in section.read_text(encoding="utf-8")
    and "GhostBase v1.1E PROFILEHUBNATIVE3 item" in profile_items.read_text(encoding="utf-8")
    and (sources / "GhostBaseProfileBackdropNode.swift").exists()
    and (sources / "GhostBaseColdGlassSectionView.swift").exists()
    and (sources / "GhostBaseProfileHubItem.swift").exists()
):
    print("[V11E] PROFILENATIVE3 already installed")
    raise SystemExit(0)

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"[V11E PROFILE] {label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)

def remove_if_present(text: str, old: str) -> str:
    return text.replace(old, "")

def remove_region(text: str, begin: str, end: str, preserve_end: bool = True) -> str:
    if begin not in text:
        return text
    s = text.index(begin)
    if end not in text[s:]:
        raise SystemExit(f"[V11E PROFILE] region end missing for {begin[:60]!r}")
    e = text.index(end, s)
    if not preserve_end:
        e += len(end)
    return text[:s] + text[e:]

# ---------- Shared safe profile backdrop ----------
(sources / "GhostBaseProfileBackdropNode.swift").write_text(r'''import Foundation
import UIKit
import AsyncDisplayKit
import Display
import SwiftSignalKit
import AccountContext
import TelegramCore
import TelegramPresentationData
import WallpaperBackgroundNode
import AvatarNode

// MARK: GhostBase v1.1E PROFILEBACKDROP3
// A single passive backdrop below the stock PeerInfo hierarchy. It never owns
// controller frames, snapshots, gestures or transition completion.
final class GhostBaseProfileBackdropNode: ASDisplayNode {
    private let context: AccountContext
    private let peerId: EnginePeer.Id
    private let isSettings: Bool

    private let wallpaperNode: WallpaperBackgroundNode
    private let avatarNode: ASImageNode
    private let blurNode: ASDisplayNode
    private let dimNode: ASDisplayNode
    private let avatarDisposable = MetaDisposable()

    private var presentationData: PresentationData?
    private var currentData: PeerInfoScreenData?
    private var currentSourceKey: String?
    private var observers: [NSObjectProtocol] = []

    init(context: AccountContext, peerId: EnginePeer.Id, isSettings: Bool) {
        self.context = context
        self.peerId = peerId
        self.isSettings = isSettings
        self.wallpaperNode = createWallpaperBackgroundNode(context: context, forChatDisplay: false, useSharedAnimationPhase: false)
        self.avatarNode = ASImageNode()
        self.avatarNode.contentMode = .scaleAspectFill
        self.avatarNode.clipsToBounds = true
        self.blurNode = ASDisplayNode(viewBlock: {
            return UIVisualEffectView(effect: UIBlurEffect(style: .systemMaterialDark))
        })
        self.dimNode = ASDisplayNode()
        self.dimNode.isLayerBacked = true
        super.init()

        self.isUserInteractionEnabled = false
        self.addSubnode(self.wallpaperNode)
        self.addSubnode(self.avatarNode)
        self.addSubnode(self.blurNode)
        self.addSubnode(self.dimNode)

        let refresh: (Notification) -> Void = { [weak self] _ in
            self?.refreshMaterialOnly()
        }
        self.observers.append(NotificationCenter.default.addObserver(forName: .ghostBaseGlassDidChange, object: nil, queue: .main, using: refresh))
        self.observers.append(NotificationCenter.default.addObserver(forName: UIAccessibility.reduceTransparencyStatusDidChangeNotification, object: nil, queue: .main, using: refresh))
        self.observers.append(NotificationCenter.default.addObserver(forName: .NSProcessInfoPowerStateDidChange, object: nil, queue: .main, using: refresh))
    }

    deinit {
        self.avatarDisposable.dispose()
        for observer in self.observers {
            NotificationCenter.default.removeObserver(observer)
        }
    }

    func update(data: PeerInfoScreenData?, presentationData: PresentationData) {
        self.currentData = data
        self.presentationData = presentationData
        self.refreshSource()
    }

    func updateLayout(size: CGSize, transition: ContainedViewLayoutTransition) {
        transition.updateFrame(node: self.wallpaperNode, frame: CGRect(origin: .zero, size: size))
        self.wallpaperNode.updateLayout(size: size, displayMode: .aspectFill, transition: transition)
        transition.updateFrame(node: self.avatarNode, frame: CGRect(origin: .zero, size: size))
        transition.updateFrame(node: self.blurNode, frame: CGRect(origin: .zero, size: size))
        transition.updateFrame(node: self.dimNode, frame: CGRect(origin: .zero, size: size))
    }

    private func refreshMaterialOnly() {
        let enabled = GhostBaseGlassStyle.isEnabled
        self.isHidden = !enabled
        guard enabled else {
            return
        }
        let reduced = GhostBaseGlassStyle.usesReducedEffects
        self.blurNode.isHidden = reduced
        if let effectView = self.blurNode.view as? UIVisualEffectView {
            effectView.effect = reduced ? nil : UIBlurEffect(style: .systemMaterialDark)
        }
        self.dimNode.backgroundColor = UIColor.black.withAlphaComponent(reduced ? 0.68 : 0.30)
        if self.currentSourceKey == nil {
            self.refreshSource()
        }
    }

    private func refreshSource() {
        guard let presentationData = self.presentationData else {
            return
        }
        self.refreshMaterialOnly()
        guard GhostBaseGlassStyle.isEnabled else {
            self.avatarDisposable.set(nil)
            return
        }

        if self.isSettings {
            self.useWallpaper(presentationData.chatWallpaper, key: "global-settings")
            return
        }

        if let cached = self.currentData?.cachedData as? CachedUserData, let wallpaper = cached.wallpaper {
            self.useWallpaper(wallpaper, key: "peer-wallpaper-user")
            return
        }
        if let cached = self.currentData?.cachedData as? CachedChannelData, let wallpaper = cached.wallpaper {
            self.useWallpaper(wallpaper, key: "peer-wallpaper-channel")
            return
        }

        if let peer = self.currentData?.peer, let representation = peer.profileImageRepresentations.first,
           let signal = peerAvatarImage(
                account: self.context.account,
                peerReference: PeerReference(peer),
                authorOfMessage: nil,
                representation: representation,
                displayDimensions: CGSize(width: 180.0, height: 180.0),
                inset: 0.0,
                emptyColor: nil,
                synchronousLoad: false
           ) {
            let sourceKey = "avatar-\(peer.id.toInt64())-\(String(describing: representation.resource.id))"
            if self.currentSourceKey != sourceKey {
                self.currentSourceKey = sourceKey
                self.wallpaperNode.update(wallpaper: presentationData.chatWallpaper, animated: false)
                self.wallpaperNode.isHidden = false
                self.avatarNode.isHidden = true
                self.avatarDisposable.set((signal
                |> deliverOnMainQueue).start(next: { [weak self] versions in
                    guard let self, self.currentSourceKey == sourceKey, let image = versions?.0 else {
                        return
                    }
                    self.avatarNode.image = image
                    self.avatarNode.isHidden = false
                    self.wallpaperNode.isHidden = true
                    if let color = Self.averageColor(image) {
                        GhostBaseProfilePalette.setColor(color, peerId: self.peerId.toInt64())
                        GhostBaseProfilePalette.setColor(color, peerId: nil)
                    }
                }))
            }
            return
        }

        self.useWallpaper(presentationData.chatWallpaper, key: "global-fallback")
    }

    private func useWallpaper(_ wallpaper: TelegramWallpaper, key: String) {
        if self.currentSourceKey != key {
            self.currentSourceKey = key
            self.avatarDisposable.set(nil)
            self.avatarNode.image = nil
            self.avatarNode.isHidden = true
            self.wallpaperNode.isHidden = false
            self.wallpaperNode.update(wallpaper: wallpaper, animated: false)
        }
        if let color = Self.wallpaperColor(wallpaper) {
            GhostBaseProfilePalette.setColor(color, peerId: self.isSettings ? nil : self.peerId.toInt64())
            GhostBaseProfilePalette.setColor(color, peerId: nil)
        }
    }

    private static func wallpaperColor(_ wallpaper: TelegramWallpaper) -> UIColor? {
        let colors: [UInt32]
        switch wallpaper {
        case let .color(value):
            colors = [value]
        case let .gradient(value):
            colors = value.colors
        case let .image(_, settings):
            colors = settings.colors
        case let .file(value):
            colors = value.settings.colors
        case let .builtin(settings):
            colors = settings.colors
        case .emoticon:
            colors = []
        }
        guard !colors.isEmpty else {
            return nil
        }
        var red: CGFloat = 0.0
        var green: CGFloat = 0.0
        var blue: CGFloat = 0.0
        for value in colors {
            red += CGFloat((value >> 16) & 0xff) / 255.0
            green += CGFloat((value >> 8) & 0xff) / 255.0
            blue += CGFloat(value & 0xff) / 255.0
        }
        let count = CGFloat(colors.count)
        return UIColor(red: red / count, green: green / count, blue: blue / count, alpha: 1.0)
    }

    private static func averageColor(_ image: UIImage) -> UIColor? {
        guard let cgImage = image.cgImage else {
            return nil
        }
        var pixel = [UInt8](repeating: 0, count: 4)
        guard let context = CGContext(
            data: &pixel,
            width: 1,
            height: 1,
            bitsPerComponent: 8,
            bytesPerRow: 4,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else {
            return nil
        }
        context.interpolationQuality = .low
        context.draw(cgImage, in: CGRect(x: 0.0, y: 0.0, width: 1.0, height: 1.0))
        return UIColor(
            red: CGFloat(pixel[0]) / 255.0,
            green: CGFloat(pixel[1]) / 255.0,
            blue: CGFloat(pixel[2]) / 255.0,
            alpha: 1.0
        )
    }
}
''', encoding="utf-8")

# ---------- Safe Cold Glass: one passive material per section ----------
(sources / "GhostBaseColdGlassSectionView.swift").write_text(r'''import Foundation
import UIKit
import TelegramPresentationData
import Display

// MARK: GhostBase v1.1E COLDSECTION3
// One path, one clip, no lens, no transformed highlight, no innerColor.
final class GhostBaseColdGlassSectionView: UIView {
    private let effectView = UIVisualEffectView(effect: nil)
    private let tintView = UIView()
    private let borderLayer = CAShapeLayer()

    override init(frame: CGRect) {
        super.init(frame: frame)
        self.isUserInteractionEnabled = false
        self.addSubview(self.effectView)
        self.addSubview(self.tintView)
        self.layer.addSublayer(self.borderLayer)
    }

    required init?(coder: NSCoder) {
        preconditionFailure()
    }

    func update(size: CGSize, cornerRadius: CGFloat, presentationData: PresentationData) {
        self.frame.size = size
        self.layer.cornerCurve = .continuous
        self.layer.cornerRadius = cornerRadius
        self.layer.masksToBounds = true

        self.effectView.frame = CGRect(origin: .zero, size: size)
        self.tintView.frame = CGRect(origin: .zero, size: size)
        self.effectView.layer.cornerRadius = cornerRadius
        self.tintView.layer.cornerRadius = cornerRadius
        self.effectView.clipsToBounds = true
        self.tintView.clipsToBounds = true

        let path = UIBezierPath(roundedRect: CGRect(origin: .zero, size: size), cornerRadius: cornerRadius).cgPath
        self.borderLayer.path = path
        self.borderLayer.frame = CGRect(origin: .zero, size: size)
        self.borderLayer.fillColor = UIColor.clear.cgColor
        self.borderLayer.lineWidth = UIScreenPixel

        if GhostBaseGlassStyle.isEnabled {
            let reduced = GhostBaseGlassStyle.usesReducedEffects
            self.backgroundColor = .clear
            self.effectView.isHidden = reduced
            self.effectView.effect = reduced ? nil : UIBlurEffect(style: presentationData.theme.overallDarkAppearance ? .systemThinMaterialDark : .systemThinMaterialLight)
            let fallback = presentationData.theme.list.itemBlocksBackgroundColor
            let palette = GhostBaseProfilePalette.color(peerId: nil, fallback: fallback)
            self.tintView.backgroundColor = reduced ? fallback : palette.withAlphaComponent(presentationData.theme.overallDarkAppearance ? 0.24 : 0.16)
            self.borderLayer.strokeColor = presentationData.theme.overallDarkAppearance ? UIColor.white.withAlphaComponent(0.16).cgColor : UIColor.white.withAlphaComponent(0.34).cgColor
        } else {
            self.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor
            self.effectView.effect = nil
            self.effectView.isHidden = true
            self.tintView.backgroundColor = .clear
            self.borderLayer.strokeColor = UIColor.clear.cgColor
        }
    }
}
''', encoding="utf-8")

# ---------- Exact official HorizontalTabsComponent hub ----------
(sources / "GhostBaseProfileHubItem.swift").write_text(r'''import Foundation
import UIKit
import Display
import AsyncDisplayKit
import AccountContext
import TelegramPresentationData
import ComponentFlow
import HorizontalTabsComponent

// MARK: GhostBase v1.1E PROFILEHUBNATIVE3
final class GhostBaseProfileHubItem: PeerInfoScreenItem {
    let id: AnyHashable
    let title: String
    let isExpanded: Bool
    let selectedTab: Int
    let tabTitles: [String]
    let bodyText: String
    let toggle: () -> Void
    let selectTab: (Int) -> Void

    init(id: AnyHashable, title: String, isExpanded: Bool, selectedTab: Int, tabTitles: [String], bodyText: String, toggle: @escaping () -> Void, selectTab: @escaping (Int) -> Void) {
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
    private let titleLabel = UILabel()
    private let chevronView = UIImageView()
    private let headerButton = UIButton(type: .custom)
    private let separator = UIView()
    private let bodyLabel = UILabel()
    private let tabs = ComponentView<Empty>()

    private var toggleAction: (() -> Void)?
    private var bodyHeight: CGFloat = 0.0
    private var expanded = false

    override init(frame: CGRect) {
        super.init(frame: frame)
        self.backgroundColor = .clear
        self.titleLabel.font = UIFont.systemFont(ofSize: 17.0, weight: .semibold)
        self.bodyLabel.font = UIFont.systemFont(ofSize: 14.0, weight: .regular)
        self.bodyLabel.numberOfLines = 0
        self.bodyLabel.lineBreakMode = .byWordWrapping
        self.chevronView.contentMode = .center
        self.headerButton.addTarget(self, action: #selector(self.headerPressed), for: .touchUpInside)
        self.addSubview(self.titleLabel)
        self.addSubview(self.chevronView)
        self.addSubview(self.headerButton)
        self.addSubview(self.separator)
        self.addSubview(self.bodyLabel)
    }

    required init?(coder: NSCoder) {
        preconditionFailure()
    }

    @objc private func headerPressed() {
        self.toggleAction?()
    }

    func update(width: CGFloat, context: AccountContext, presentationData: PresentationData, item: GhostBaseProfileHubItem) -> CGFloat {
        self.toggleAction = item.toggle
        self.expanded = item.isExpanded
        self.titleLabel.text = item.title
        self.titleLabel.textColor = presentationData.theme.list.itemPrimaryTextColor
        self.chevronView.image = UIImage(systemName: item.isExpanded ? "chevron.up" : "chevron.down")
        self.chevronView.tintColor = presentationData.theme.list.itemAccentColor
        self.separator.backgroundColor = presentationData.theme.list.itemBlocksSeparatorColor
        self.bodyLabel.text = item.bodyText
        self.bodyLabel.textColor = presentationData.theme.list.itemSecondaryTextColor

        if item.isExpanded {
            let tabs = item.tabTitles.enumerated().map { index, title -> HorizontalTabsComponent.Tab in
                return HorizontalTabsComponent.Tab(
                    id: AnyHashable(index),
                    content: .title(HorizontalTabsComponent.Tab.Title(text: title, entities: [], enableAnimations: false)),
                    badge: nil,
                    action: {
                        item.selectTab(index)
                    }
                )
            }
            let tabsSize = self.tabs.update(
                transition: .immediate,
                component: AnyComponent(HorizontalTabsComponent(
                    context: context,
                    theme: presentationData.theme,
                    tabs: tabs,
                    selectedTab: AnyHashable(item.selectedTab),
                    isEditing: false,
                    layout: .fit,
                    liftWhileSwitching: true
                )),
                environment: {},
                containerSize: CGSize(width: max(1.0, width - 24.0), height: 50.0)
            )
            if let tabsView = self.tabs.view, tabsView.superview == nil {
                self.addSubview(tabsView)
            }
            self.tabs.view?.frame = CGRect(x: 12.0, y: 64.0, width: max(1.0, width - 24.0), height: tabsSize.height)
            self.bodyHeight = ceil(self.bodyLabel.sizeThatFits(CGSize(width: max(1.0, width - 36.0), height: CGFloat.greatestFiniteMagnitude)).height)
        } else {
            self.bodyHeight = 0.0
        }

        self.tabs.view?.isHidden = !item.isExpanded
        self.separator.isHidden = !item.isExpanded
        self.bodyLabel.isHidden = !item.isExpanded
        self.setNeedsLayout()
        return item.isExpanded ? 58.0 + 56.0 + self.bodyHeight + 22.0 : 58.0
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        let size = self.bounds.size
        self.titleLabel.frame = CGRect(x: 16.0, y: 0.0, width: max(0.0, size.width - 66.0), height: 58.0)
        self.chevronView.frame = CGRect(x: max(0.0, size.width - 48.0), y: 7.0, width: 36.0, height: 44.0)
        self.headerButton.frame = CGRect(origin: .zero, size: CGSize(width: size.width, height: 58.0))
        guard self.expanded else {
            return
        }
        self.separator.frame = CGRect(x: 16.0, y: 57.0, width: max(0.0, size.width - 32.0), height: UIScreenPixel)
        self.bodyLabel.frame = CGRect(x: 18.0, y: 118.0, width: max(0.0, size.width - 36.0), height: self.bodyHeight)
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
        guard let item = item as? GhostBaseProfileHubItem else {
            return 0.0
        }
        let height = self.contentView.update(width: width, context: context, presentationData: presentationData, item: item)
        transition.updateFrame(node: self.contentNode, frame: CGRect(x: 0.0, y: 0.0, width: width, height: height))
        return height
    }
}
''', encoding="utf-8")

# ---------- Clean rejected Build 90/91 screen hierarchy ----------
text = screen.read_text(encoding="utf-8")
# Remove old rejected profile backdrop implementation.
text = remove_region(text, "    // MARK: GhostBase v1.1D PROFILEBACKDROP2\n", "    let headerNode: PeerInfoHeaderNode\n")
text = remove_region(text, "        self.ghostBaseBackdropWallpaperNode = createWallpaperBackgroundNode", "\n\n        var forumTopicThreadId: Int64?\n")
text = remove_region(text, "        self.addSubnode(self.ghostBaseBackdropWallpaperNode)\n", "        self.paneContainerNode.parentController = controller\n")
text = remove_if_present(text, "        for observer in self.ghostBaseGlassObservers { NotificationCenter.default.removeObserver(observer) }\n")
text = remove_if_present(text, "        self.ghostBaseUpdateBackdrop()\n")
text = remove_if_present(text, "        transition.updateFrame(node: self.ghostBaseBackdropWallpaperNode, frame: CGRect(origin: .zero, size: layout.size))\n        self.ghostBaseBackdropWallpaperNode.updateLayout(size: layout.size, displayMode: .aspectFill, transition: transition)\n        transition.updateFrame(node: self.ghostBaseBackdropAvatarNode, frame: CGRect(origin: .zero, size: layout.size))\n        transition.updateFrame(node: self.ghostBaseBackdropBlurNode, frame: CGRect(origin: .zero, size: layout.size))\n        transition.updateFrame(node: self.ghostBaseBackdropDimNode, frame: CGRect(origin: .zero, size: layout.size))\n\n")
text = remove_region(text, "    private func ghostBaseWallpaperTint(_ wallpaper: TelegramWallpaper) -> UIColor? {\n", "    private func updateBackgroundColor() {\n")
text = remove_if_present(text, "        if GhostBaseGlassStyle.isEnabled {\n            self.backgroundColor = .clear\n            return\n        }\n")

# Install the passive node without touching transition containers.
prop_anchor = "    let edgeEffectView: EdgeEffectView\n"
if "GhostBase v1.1E PROFILEBACKDROP3" not in text:
    text = replace_once(text, prop_anchor, prop_anchor + "    // MARK: GhostBase v1.1E PROFILEBACKDROP3\n    let ghostBaseProfileBackdropNode: GhostBaseProfileBackdropNode\n", "screen property")
    init_anchor = "        self.edgeEffectView = EdgeEffectView()\n"
    text = replace_once(text, init_anchor, init_anchor + "        self.ghostBaseProfileBackdropNode = GhostBaseProfileBackdropNode(context: context, peerId: peerId, isSettings: isSettings)\n", "screen init")
    add_anchor = "        self.addSubnode(self.scrollNode)\n"
    text = replace_once(text, add_anchor, "        self.addSubnode(self.ghostBaseProfileBackdropNode)\n" + add_anchor, "screen z-order")
    data_anchor = "        self.data = data\n"
    text = replace_once(text, data_anchor, data_anchor + "        self.ghostBaseProfileBackdropNode.update(data: data, presentationData: self.presentationData)\n", "screen data")
    presentation_anchor = "        self.presentationData = presentationData\n"
    text = replace_once(text, presentation_anchor, presentation_anchor + "        self.ghostBaseProfileBackdropNode.update(data: self.data, presentationData: presentationData)\n", "screen presentation")
    layout_anchor = "        transition.updateFrame(node: self.scrollNode, frame: CGRect(origin: CGPoint(), size: layout.size))\n"
    text = replace_once(text, layout_anchor, "        transition.updateFrame(node: self.ghostBaseProfileBackdropNode, frame: CGRect(origin: .zero, size: layout.size))\n        self.ghostBaseProfileBackdropNode.updateLayout(size: layout.size, transition: transition)\n\n" + layout_anchor, "screen layout")
    bg_anchor = "    private func updateBackgroundColor() {\n"
    text = replace_once(text, bg_anchor, bg_anchor + "        if GhostBaseGlassStyle.isEnabled {\n            self.backgroundColor = .clear\n            return\n        }\n", "screen background")

if "import WallpaperBackgroundNode\n" not in text:
    text = text.replace("import Display\n", "import Display\nimport WallpaperBackgroundNode\n", 1)
screen.write_text(text, encoding="utf-8")

# ---------- Preserve stock header content and tint only native square buttons ----------
text = header.read_text(encoding="utf-8")
text = remove_region(text, "        // MARK: GhostBase v1.1D HEADERGLASS2", "        do {\n")
text = remove_if_present(text, "            // PROFILEBACKDROP2 replaces the stock premium cover with the active chat wallpaper/avatar backdrop.\n            backgroundCoverView.alpha = GhostBaseGlassStyle.isEnabled ? 0.0 : 1.0\n")
text = text.replace("        let contentButtonBackgroundColor: UIColor\n        let contentButtonForegroundColor: UIColor\n", "        var contentButtonBackgroundColor: UIColor\n        var contentButtonForegroundColor: UIColor\n")
if "GhostBase v1.1E HEADERBUTTONS3" not in text:
    anchor = "        do {\n            self.currentCredibilityIcon = credibilityIcon\n"
    block = '''        // MARK: GhostBase v1.1E HEADERBUTTONS3
        // The stock button nodes, icon layout, labels and badges are untouched.
        if GhostBaseGlassStyle.isEnabled, !state.isEditing, !self.isAvatarExpanded, let peer {
            let palette = GhostBaseProfilePalette.color(peerId: peer.id.toInt64(), fallback: presentationData.theme.list.itemBlocksBackgroundColor)
            contentButtonBackgroundColor = palette.withAlphaComponent(GhostBaseGlassStyle.usesReducedEffects ? 0.72 : 0.30)
            contentButtonForegroundColor = .white
        }

'''
    text = replace_once(text, anchor, block + anchor, "header tint")
    cover_anchor = "        if let backgroundCoverView = self.backgroundCover.view as? PeerInfoCoverComponent.View {\n"
    text = replace_once(text, cover_anchor, cover_anchor + "            backgroundCoverView.alpha = GhostBaseGlassStyle.isEnabled ? 0.0 : 1.0\n", "header cover")
header.write_text(text, encoding="utf-8")

# ---------- Replace rejected section lens with one safe Cold Glass material ----------
text = section.read_text(encoding="utf-8")
text = remove_if_present(text, "import ComponentFlow\n")
text = remove_if_present(text, "import GlassBackgroundComponent\n")
text = remove_if_present(text, "    // MARK: GhostBase v1.1D SECTIONGLASS2 one material per section\n")
text = text.replace("        self.backgroundNode = ASDisplayNode(viewBlock: { GlassBackgroundView() })\n", "        self.backgroundNode = ASDisplayNode(viewBlock: { GhostBaseColdGlassSectionView() })\n")
text = remove_region(text, "        if let glassView = self.backgroundNode.view as? GlassBackgroundView, GhostBaseGlassStyle.isEnabled {\n", "        self.topSeparatorNode.backgroundColor", preserve_end=True)
# Previous removal leaves the anchor itself, restore clean line.
if "        self.backgroundNode.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor\n" in text:
    text = text.replace("        self.backgroundNode.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor\n", "")
text = remove_region(text, "        // MARK: GhostBase v1.1D SECTIONGLASS2 exact final material size\n", "        transition.updateFrame(node: self.topSeparatorNode", preserve_end=True)
frame_anchor = "        transition.updateFrame(node: self.backgroundNode, frame: CGRect(origin: CGPoint(x: 0.0, y: contentWithBackgroundOffset), size: CGSize(width: width, height: max(0.0, contentWithBackgroundHeight - contentWithBackgroundOffset))))\n"
if "GhostBase v1.1E COLDSECTION3" not in text:
    material = '''        // MARK: GhostBase v1.1E COLDSECTION3
        if let materialView = self.backgroundNode.view as? GhostBaseColdGlassSectionView {
            materialView.update(
                size: CGSize(width: width, height: max(0.0, contentWithBackgroundHeight - contentWithBackgroundOffset)),
                cornerRadius: hasCorners ? 16.0 : 0.0,
                presentationData: presentationData
            )
        }
'''
    text = replace_once(text, frame_anchor, frame_anchor + material, "section material")
section.write_text(text, encoding="utf-8")

# ---------- Replace all old profile hub rows/cards with one native selector item ----------
text = profile_items.read_text(encoding="utf-8")
metrics_begin = "    // MARK: GhostBase v0.4A peer metrics card with toggles\n"
if metrics_begin in text:
    text = remove_region(text, metrics_begin, "\n\n    let bioContextAction:")
    text = text.replace("    let bioContextAction:", "\n\n    let bioContextAction:", 1)

hub_markers = [
    "    // MARK: GhostBase v1.1D PROFILESELECTOR2 one native glass block\n",
    "    // MARK: GhostBase v1.1C PROFILEGLASS1 inline hub\n",
    "    // MARK: GhostBase v1.1B PROFILEHUB2 inline rows\n",
]
start_positions = [text.index(m) for m in hub_markers if m in text]
if start_positions:
    start = min(start_positions)
    end_marker = "    var result: [(AnyHashable, [PeerInfoScreenItem])] = []\n"
    if end_marker not in text[start:]:
        raise SystemExit("[V11E PROFILE] hub end marker missing")
    end = text.index(end_marker, start)
    text = text[:start] + text[end:]

if "GhostBase v1.1E PROFILEHUBNATIVE3 item" not in text:
    result_anchor = "    var result: [(AnyHashable, [PeerInfoScreenItem])] = []\n"
    block = r'''    // MARK: GhostBase v1.1E PROFILEHUBNATIVE3 item
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
            let username = user.addressName.map { "@\($0)" } ?? "не указан"
            var lines = ["Peer ID: \(user.id.toInt64())", "Username: \(username)"]
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
                guard let tab = GhostBaseProfileHubTab(rawValue: raw) else {
                    return
                }
                ghostBaseProfileHubSetSelectedTab(tab, accountPeerId: accountPeerId, peerId: targetPeerId)
                interaction.requestLayout(true)
            }
        ))
    }

'''
    info_start = text.index("func infoItems(")
    editing_start = text.index("func editingItems(", info_start)
    result_pos = text.index(result_anchor, info_start, editing_start)
    text = text[:result_pos] + block + text[result_pos:]
profile_items.write_text(text, encoding="utf-8")

# Exact official component and wallpaper dependencies.
build_text = build.read_text(encoding="utf-8")
for dep, anchor in [
    ('        "//submodules/WallpaperBackgroundNode",\n', '        "//submodules/Display",\n'),
    ('        "//submodules/TelegramUI/Components/HorizontalTabsComponent",\n', '        "//submodules/TelegramUI/Components/TabSelectorComponent",\n'),
]:
    if dep not in build_text:
        if anchor not in build_text:
            raise SystemExit(f"[V11E PROFILE] BUILD anchor missing for {dep.strip()}")
        build_text = build_text.replace(anchor, anchor + dep, 1)
build.write_text(build_text, encoding="utf-8")

print("[V11E] PROFILEBACKDROP3 + COLDSECTION3 + exact HorizontalTabsComponent hub installed")
