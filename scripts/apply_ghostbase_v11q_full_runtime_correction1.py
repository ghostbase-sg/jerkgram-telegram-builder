#!/usr/bin/env python3
import os
import atexit
from pathlib import Path

ROOT = Path(os.environ.get(
    'GHOSTBASE_SOURCE_ROOT',
    '/root/gb_builder/work/swiftgram-src'
))

PEER = (
    ROOT
    / 'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources'
)

LIST_SECTION = (
    ROOT
    / 'submodules/TelegramUI/Components/ListSectionComponent/Sources/ListSectionComponent.swift'
)

UNIVERSAL = (
    ROOT
    / 'submodules/AccountContext/Sources/UniversalVideoNode.swift'
)

UNIVERSAL_MANAGER = (
    ROOT
    / 'submodules/TelegramUniversalVideoContent/Sources/UniversalVideoContentManager.swift'
)

BG = (
    PEER
    / 'GhostBaseProfileFullscreenBackground.swift'
)

MEMBERS = (
    PEER
    / 'Panes/PeerInfoMembersPane.swift'
)

GROUPS = (
    PEER
    / 'Panes/PeerInfoGroupsInCommonPaneNode.swift'
)

GIFT = (
    ROOT
    / 'submodules/TelegramUI/Components/Gifts/GiftViewScreen/Sources/GiftViewScreen.swift'
)

GIFT_PAGER = (
    ROOT
    / 'submodules/TelegramUI/Components/Gifts/GiftViewScreen/Sources/GiftPagerComponent.swift'
)

REPORT = (
    PEER
    / 'GhostBaseProfileReportPaneNode.swift'
)

CORNERS = (
    ROOT
    / 'submodules/TelegramPresentationData/Sources/Resources/PresentationResourcesItemList.swift'
)

SECTION = (
    PEER
    / 'PeerInfoScreenItemSectionContainerNode.swift'
)

HEADER_SINGLE = (
    PEER
    / 'PeerInfoHeaderSingleLineTextFieldNode.swift'
)

HEADER_MULTI = (
    PEER
    / 'PeerInfoHeaderMultiLineTextFieldNode.swift'
)

MEDIA_NODE = (
    ROOT
    / 'submodules/MediaPlayer/Sources/MediaPlayerNode.swift'
)

CHUNK = (
    ROOT
    / 'submodules/MediaPlayer/Sources/ChunkMediaPlayerV2.swift'
)

NATIVE = (
    ROOT
    / 'submodules/TelegramUniversalVideoContent/Sources/NativeVideoContent.swift'
)

MUSIC = (
    ROOT
    / 'submodules/TelegramUI/Sources/OverlayAudioPlayerControllerNode.swift'
)

COVER = (
    ROOT
    / 'submodules/TelegramUI/Components/PeerInfo/PeerInfoCoverComponent/Sources/PeerInfoCoverComponent.swift'
)

HEADER = (
    PEER
    / 'PeerInfoHeaderNode.swift'
)

SCREEN = (
    PEER
    / 'PeerInfoScreen.swift'
)

TOUCHED = (
    LIST_SECTION,
    UNIVERSAL,
    UNIVERSAL_MANAGER,
    BG,
    MEMBERS,
    GIFT,
    REPORT,
)

REQUIRED = (
    *TOUCHED,
    GROUPS,
    GIFT_PAGER,
    CORNERS,
    SECTION,
    HEADER_SINGLE,
    HEADER_MULTI,
    MEDIA_NODE,
    CHUNK,
    NATIVE,
    MUSIC,
    COVER,
    HEADER,
    SCREEN,
)

for path in REQUIRED:
    if not path.is_file():
        raise RuntimeError(
            f'[V11Q] missing required source: {path}'
        )

required_v11p = (
    (CORNERS, 'GhostBase v1.1P GLOBAL_GLASS_CORNERS1'),
    (SECTION, 'GhostBase v1.1P SECTION_OWNER1'),
    (MEDIA_NODE, 'GhostBase v1.1P SECONDARY_RENDER_OUTPUT1'),
    (CHUNK, 'GhostBase v1.1P CHUNK_SECONDARY_RENDER_OUTPUT1'),
    (UNIVERSAL, 'GhostBase v1.1P UNIVERSAL_SECONDARY_OUTPUT1'),
    (NATIVE, 'UniversalVideoSecondaryOutputContentNode'),
    (BG, 'GhostBase v1.1P VIDEO_MIRROR1'),
    (HEADER_SINGLE, 'GhostBase v1.1P HEADER_FIELD_GLASS_OWNER1'),
    (HEADER_MULTI, 'GhostBase v1.1P HEADER_FIELD_GLASS_OWNER1'),
    (MUSIC, 'GhostBase v1.1P MUSIC_REAL_PROFILE_GLASS1'),
    (COVER, 'GhostBase v1.1P PREMIUM_COMPOSITE1'),
)

for path, marker in required_v11p:
    if marker not in path.read_text(encoding='utf-8'):
        raise RuntimeError(
            '[V11Q] V11P prerequisite missing: '
            f'{marker} in {path}'
        )

MARK = (
    '// MARK: GhostBase v1.1Q '
    'FULL_RUNTIME_CORRECTION1'
)

if MARK in LIST_SECTION.read_text(encoding='utf-8'):
    gates = (
        (UNIVERSAL, 'GhostBase v1.1Q SECONDARY_OUTPUT_REGISTRY1'),
        (UNIVERSAL_MANAGER, 'GhostBase v1.1Q SECONDARY_OUTPUT_REATTACH1'),
        (BG, 'GhostBase v1.1Q BUILD97_NEUTRAL_REOPEN1'),
        (MEMBERS, 'GhostBase v1.1Q MEMBERS_PANE_GLASS1'),
        (GIFT, 'GhostBase v1.1Q PROFILE_GIFT_READABILITY1'),
        (REPORT, 'GhostBase v1.1Q HISTORY_CLIP_HARDENING1'),
    )

    missing = [
        str(path)
        for path, marker in gates
        if marker not in path.read_text(encoding='utf-8')
    ]

    if missing:
        raise RuntimeError(
            '[V11Q] inconsistent partial materialization: '
            + ', '.join(missing)
        )

    print('[V11Q] already materialized')
    raise SystemExit(0)

_original = {path: path.read_bytes() for path in TOUCHED}
_committed = False


def rollback() -> None:
    if not _committed:
        for path, data in _original.items():
            path.write_bytes(data)


atexit.register(rollback)


def one(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f'[V11Q] {label}: expected one anchor, found {count}'
        )
    return text.replace(old, new, 1)


# ============================================================
# 1. MODERN COMPONENT GLASS
# Add Contact / new Settings surfaces
# ============================================================

list_section = LIST_SECTION.read_text(encoding='utf-8')

list_section = one(
    list_section,
    'public final class ListSectionContentView: UIView {\n',
    '''public final class ListSectionContentView: UIView {
    // MARK: GhostBase v1.1Q FULL_RUNTIME_CORRECTION1
    // MARK: GhostBase v1.1Q MODERN_GLASS_OWNER1
    private let ghostBaseDirectGlassBackgroundView = UIView()
    private var ghostBaseUsesDirectGlassBackground = false
''',
    'modern glass properties'
)

list_section = one(
    list_section,
    '''        super.init(frame: CGRect())
        
        self.layer.addSublayer(self.contentSeparatorContainerLayer)
''',
    '''        super.init(frame: CGRect())

        self.ghostBaseDirectGlassBackgroundView.isUserInteractionEnabled = false
        self.ghostBaseDirectGlassBackgroundView.clipsToBounds = true
        self.ghostBaseDirectGlassBackgroundView.isHidden = true
        self.addSubview(self.ghostBaseDirectGlassBackgroundView)
        
        self.layer.addSublayer(self.contentSeparatorContainerLayer)
''',
    'modern glass hierarchy'
)

list_section = one(
    list_section,
    '''        if configuration.extendsItemHighlightToSection {
            let transition: ComponentTransition
            let backgroundColor: UIColor
            if itemId != nil {
                transition = .immediate
                backgroundColor = configuration.theme.list.itemHighlightedBackgroundColor
            } else {
                transition = .easeInOut(duration: 0.2)
                backgroundColor = configuration.isModal ? configuration.theme.list.itemModalBlocksBackgroundColor : configuration.theme.list.itemBlocksBackgroundColor
            }
            
            self.externalContentBackgroundView.updateColor(color: backgroundColor, transition: transition)
        } else {
''',
    '''        if configuration.extendsItemHighlightToSection {
            let transition: ComponentTransition
            let backgroundColor: UIColor

            if itemId != nil {
                transition = .immediate
                backgroundColor = configuration.theme.list.itemHighlightedBackgroundColor
            } else if self.ghostBaseUsesDirectGlassBackground {
                transition = .easeInOut(duration: 0.2)
                let isDark = configuration.theme.overallDarkAppearance
                backgroundColor = UIColor(
                    white: isDark ? 0.0 : 1.0,
                    alpha: isDark ? 0.13 : 0.16
                )
            } else {
                transition = .easeInOut(duration: 0.2)
                backgroundColor = configuration.isModal ? configuration.theme.list.itemModalBlocksBackgroundColor : configuration.theme.list.itemBlocksBackgroundColor
            }

            if self.ghostBaseUsesDirectGlassBackground {
                transition.setBackgroundColor(
                    view: self.ghostBaseDirectGlassBackgroundView,
                    color: backgroundColor
                )
            } else {
                self.externalContentBackgroundView.updateColor(
                    color: backgroundColor,
                    transition: transition
                )
            }
        } else {
''',
    'modern glass highlight owner'
)

list_section = one(
    list_section,
    '''    public func update(configuration: Configuration, width: CGFloat, leftInset: CGFloat, readyItems: [ReadyItem], transition: ComponentTransition) -> UpdateResult {
        self.configuration = configuration
        
        switch configuration.background {
''',
    '''    public func update(configuration: Configuration, width: CGFloat, leftInset: CGFloat, readyItems: [ReadyItem], transition: ComponentTransition) -> UpdateResult {
        self.configuration = configuration

        let ghostBaseDirectGlassBackground: Bool

        if GhostBaseGlassStyle.isEnabled {
            switch (configuration.style, configuration.background) {
            case (.glass, .all):
                ghostBaseDirectGlassBackground = true
            default:
                ghostBaseDirectGlassBackground = false
            }
        } else {
            ghostBaseDirectGlassBackground = false
        }

        self.ghostBaseUsesDirectGlassBackground = ghostBaseDirectGlassBackground
        
        switch configuration.background {
''',
    'modern glass enable gate'
)

list_section = one(
    list_section,
    '''        self.externalContentBackgroundView.updateColor(color: backgroundColor, transition: transition)
        
        let cornerRadius: CGFloat
''',
    '''        if ghostBaseDirectGlassBackground {
            let isDark = configuration.theme.overallDarkAppearance
            let directColor: UIColor

            if self.highlightedItemId != nil,
               configuration.extendsItemHighlightToSection {
                directColor = configuration.theme.list.itemHighlightedBackgroundColor
            } else {
                directColor = UIColor(
                    white: isDark ? 0.0 : 1.0,
                    alpha: isDark ? 0.13 : 0.16
                )
            }

            transition.setBackgroundColor(
                view: self.ghostBaseDirectGlassBackgroundView,
                color: directColor
            )
        } else {
            self.externalContentBackgroundView.updateColor(
                color: backgroundColor,
                transition: transition
            )
        }
        
        let cornerRadius: CGFloat
''',
    'modern glass material'
)

list_section = one(
    list_section,
    '''        if self.automaticallyLayoutExternalContentBackgroundView {
            transition.setFrame(view: self.externalContentBackgroundView, frame: backgroundFrame)
        }
        transition.setAlpha(view: self.externalContentBackgroundView, alpha: backgroundAlpha)
        transition.setCornerRadius(layer: self.layer, cornerRadius: contentCornerRadius)
''',
    '''        if self.automaticallyLayoutExternalContentBackgroundView {
            transition.setFrame(view: self.externalContentBackgroundView, frame: backgroundFrame)
        }

        if ghostBaseDirectGlassBackground {
            transition.setFrame(
                view: self.ghostBaseDirectGlassBackgroundView,
                frame: backgroundFrame
            )
            transition.setCornerRadius(
                layer: self.ghostBaseDirectGlassBackgroundView.layer,
                cornerRadius: cornerRadius
            )
            transition.setAlpha(
                view: self.ghostBaseDirectGlassBackgroundView,
                alpha: backgroundAlpha
            )
            self.ghostBaseDirectGlassBackgroundView.isHidden = backgroundAlpha <= 0.0
            transition.setAlpha(
                view: self.externalContentBackgroundView,
                alpha: 0.0
            )
        } else {
            self.ghostBaseDirectGlassBackgroundView.isHidden = true
            transition.setAlpha(
                view: self.ghostBaseDirectGlassBackgroundView,
                alpha: 0.0
            )
            transition.setAlpha(
                view: self.externalContentBackgroundView,
                alpha: backgroundAlpha
            )
        }

        transition.setCornerRadius(layer: self.layer, cornerRadius: contentCornerRadius)
''',
    'modern glass geometry'
)

LIST_SECTION.write_text(list_section, encoding='utf-8')


# ============================================================
# 2. ANIMATION
# Persistent secondary-output registry across holder handoffs
# ============================================================

uv = UNIVERSAL.read_text(encoding='utf-8')

uv = one(
    uv,
    '''public protocol UniversalVideoSecondaryOutputContentNode: AnyObject {
    func addSecondaryVideoLayer(_ layer: AVSampleBufferDisplayLayer)
    func removeSecondaryVideoLayer(_ layer: AVSampleBufferDisplayLayer)
}

''',
    '''public protocol UniversalVideoSecondaryOutputContentNode: AnyObject {
    func addSecondaryVideoLayer(_ layer: AVSampleBufferDisplayLayer)
    func removeSecondaryVideoLayer(_ layer: AVSampleBufferDisplayLayer)
}

// MARK: GhostBase v1.1Q SECONDARY_OUTPUT_REGISTRY1
public enum GhostBaseUniversalVideoSecondaryOutputRegistry {
    private final class WeakLayer {
        weak var value: AVSampleBufferDisplayLayer?

        init(_ value: AVSampleBufferDisplayLayer) {
            self.value = value
        }
    }

    private struct Key: Hashable {
        let manager: ObjectIdentifier
        let contentId: AnyHashable
    }

    private static var layers: [Key: [ObjectIdentifier: WeakLayer]] = [:]

    public static func register(
        manager: AnyObject,
        contentId: AnyHashable,
        layer: AVSampleBufferDisplayLayer
    ) {
        assert(Queue.mainQueue().isCurrent())
        let key = Key(manager: ObjectIdentifier(manager), contentId: contentId)
        var current = self.layers[key] ?? [:]
        current[ObjectIdentifier(layer)] = WeakLayer(layer)
        self.layers[key] = current
        self.compact(key: key)
    }

    public static func unregister(
        manager: AnyObject,
        contentId: AnyHashable,
        layer: AVSampleBufferDisplayLayer
    ) {
        assert(Queue.mainQueue().isCurrent())
        let key = Key(manager: ObjectIdentifier(manager), contentId: contentId)
        guard var current = self.layers[key] else {
            return
        }
        current.removeValue(forKey: ObjectIdentifier(layer))
        if current.isEmpty {
            self.layers.removeValue(forKey: key)
        } else {
            self.layers[key] = current
            self.compact(key: key)
        }
    }

    public static func attachRegisteredLayers(
        manager: AnyObject,
        contentId: AnyHashable,
        contentNode: AnyObject
    ) {
        assert(Queue.mainQueue().isCurrent())
        guard let outputNode = contentNode as? UniversalVideoSecondaryOutputContentNode else {
            return
        }
        let key = Key(manager: ObjectIdentifier(manager), contentId: contentId)
        guard let current = self.layers[key] else {
            return
        }
        for weakLayer in current.values {
            if let layer = weakLayer.value {
                outputNode.addSecondaryVideoLayer(layer)
            }
        }
        self.compact(key: key)
    }

    private static func compact(key: Key) {
        guard var current = self.layers[key] else {
            return
        }
        current = current.filter { $0.value.value != nil }
        if current.isEmpty {
            self.layers.removeValue(forKey: key)
        } else {
            self.layers[key] = current
        }
    }
}

''',
    'secondary registry declaration'
)

old_register = '''
    public func registerSecondaryVideoLayer(_ layer: AVSampleBufferDisplayLayer) -> Disposable? {
        assert(Queue.mainQueue().isCurrent())
        var didAttach = false
        let manager = self.manager
        let contentId = self.content.id
        manager.withUniversalVideoContent(id: contentId, { contentNode in
            if let contentNode = contentNode as? UniversalVideoSecondaryOutputContentNode {
                contentNode.addSecondaryVideoLayer(layer)
                didAttach = true
            }
        })
        guard didAttach else {
            return nil
        }
        return ActionDisposable {
            Queue.mainQueue().async {
                manager.withUniversalVideoContent(id: contentId, { contentNode in
                    (contentNode as? UniversalVideoSecondaryOutputContentNode)?.removeSecondaryVideoLayer(layer)
                })
                layer.flushAndRemoveImage()
            }
        }
    }
'''

new_register = '''
    public func registerSecondaryVideoLayer(_ layer: AVSampleBufferDisplayLayer) -> Disposable? {
        assert(Queue.mainQueue().isCurrent())

        let manager = self.manager
        let contentId = self.content.id

        GhostBaseUniversalVideoSecondaryOutputRegistry.register(
            manager: manager as AnyObject,
            contentId: contentId,
            layer: layer
        )

        manager.withUniversalVideoContent(id: contentId, { contentNode in
            if let contentNode {
                GhostBaseUniversalVideoSecondaryOutputRegistry.attachRegisteredLayers(
                    manager: manager as AnyObject,
                    contentId: contentId,
                    contentNode: contentNode
                )
            }
        })

        return ActionDisposable {
            Queue.mainQueue().async {
                GhostBaseUniversalVideoSecondaryOutputRegistry.unregister(
                    manager: manager as AnyObject,
                    contentId: contentId,
                    layer: layer
                )

                manager.withUniversalVideoContent(id: contentId, { contentNode in
                    (contentNode as? UniversalVideoSecondaryOutputContentNode)?.removeSecondaryVideoLayer(layer)
                })

                layer.flushAndRemoveImage()
            }
        }
    }
'''

register_start = uv.find(
    "    public func registerSecondaryVideoLayer("
)

register_end = uv.find(
    "    public func play() {",
    register_start
)

if register_start < 0:
    raise RuntimeError(
        "[V11Q] persistent registerSecondaryVideoLayer: "
        "method start not found"
    )

if register_end < 0:
    raise RuntimeError(
        "[V11Q] persistent registerSecondaryVideoLayer: "
        "play() boundary not found"
    )

actual_register = uv[
    register_start:
    register_end
]

for required in (
    "registerSecondaryVideoLayer",
    "UniversalVideoSecondaryOutputContentNode",
    "addSecondaryVideoLayer",
    "removeSecondaryVideoLayer",
    "ActionDisposable",
):
    count = actual_register.count(required)

    if count < 1:
        raise RuntimeError(
            "[V11Q] persistent registerSecondaryVideoLayer: "
            f"required token {required!r} missing"
        )

uv = (
    uv[:register_start]
    + new_register.strip("\n")
    + "\n\n"
    + uv[register_end:]
)

UNIVERSAL.write_text(uv, encoding='utf-8')

manager = UNIVERSAL_MANAGER.read_text(encoding='utf-8')

manager = one(
    manager,
    '''        let id = holder.addSubscriber(priority: priority, update: update)
        holder.update(forceUpdateId: id, initiatedCreation: initiatedCreation ? id : nil)
''',
    '''        // MARK: GhostBase v1.1Q SECONDARY_OUTPUT_REATTACH1
        GhostBaseUniversalVideoSecondaryOutputRegistry.attachRegisteredLayers(
            manager: self,
            contentId: holder.content.id,
            contentNode: holder.contentNode
        )

        let id = holder.addSubscriber(priority: priority, update: update)
        holder.update(forceUpdateId: id, initiatedCreation: initiatedCreation ? id : nil)
''',
    'manager secondary reattach'
)

UNIVERSAL_MANAGER.write_text(manager, encoding='utf-8')


# ============================================================
# 3. BUILD97 BLUR FIDELITY
# ============================================================

bg = BG.read_text(encoding='utf-8')

old_avatar_tint = '''            let immediateTint =
                Self.persistentTint(
                    identity: loadKey
                )
                ?? fallback

            self.backgroundColor =
                immediateTint

            self.applyTint(
                immediateTint,
                fallback: fallback,
                isDark: isDark,
                reduced: reduced
            )
'''

new_avatar_tint = '''            // MARK: GhostBase v1.1Q BUILD97_NEUTRAL_REOPEN1
            let immediateTint =
                fallback

            self.backgroundColor =
                fallback

            self.applyTint(
                fallback,
                fallback:
                    fallback,
                isDark:
                    isDark,
                reduced:
                    reduced
            )
'''

bg = one(
    bg,
    old_avatar_tint,
    new_avatar_tint,
    'Build97 neutral avatar fallback'
)

BG.write_text(bg, encoding='utf-8')


# ============================================================
# 4. MEMBERS
# ============================================================

members = MEMBERS.read_text(encoding='utf-8')

members = one(
    members,
    '''    private let ghostBaseGlassEnabled: Bool
    private let listBackgroundView: UIImageView
    private let listMaskView: UIImageView
''',
    '''    private let ghostBaseGlassEnabled: Bool
    private let listBackgroundView: UIImageView
    private let listMaskView: UIImageView

    // MARK: GhostBase v1.1Q MEMBERS_PANE_GLASS1
    private let ghostBaseGlassEffectView: UIVisualEffectView
    private let ghostBaseGlassTintView: UIView
    private var ghostBaseGlassIsDark: Bool?
''',
    'members glass properties'
)

members = one(
    members,
    '''        self.listBackgroundView = UIImageView()
        self.listBackgroundView.image = generateStretchableFilledCircleImage(diameter: 26.0 * 2.0, color: .white)?.withRenderingMode(.alwaysTemplate)
        self.listMaskView = UIImageView()
''',
    '''        self.listBackgroundView = UIImageView()
        self.listBackgroundView.image = generateStretchableFilledCircleImage(diameter: 26.0 * 2.0, color: .white)?.withRenderingMode(.alwaysTemplate)

        self.ghostBaseGlassEffectView = UIVisualEffectView(effect: nil)
        self.ghostBaseGlassEffectView.isUserInteractionEnabled = false
        self.ghostBaseGlassEffectView.isHidden = !ghostBaseGlassEnabled

        self.ghostBaseGlassTintView = UIView()
        self.ghostBaseGlassTintView.isUserInteractionEnabled = false
        self.ghostBaseGlassIsDark = nil

        self.listMaskView = UIImageView()
''',
    'members glass init'
)

members = one(
    members,
    '''        self.listNode.preloadPages = true
        self.view.addSubview(self.listBackgroundView)
        self.addSubnode(self.listNode)
''',
    '''        self.listNode.preloadPages = true
        self.view.addSubview(self.listBackgroundView)
        self.view.addSubview(self.ghostBaseGlassEffectView)
        self.ghostBaseGlassEffectView.contentView.addSubview(self.ghostBaseGlassTintView)
        self.addSubnode(self.listNode)
''',
    'members glass hierarchy'
)

old_members_on = '''        if self.ghostBaseGlassEnabled {
            let isDark =
                presentationData
                    .theme
                    .overallDarkAppearance

            self.backgroundColor =
                .clear

            self.listNode.backgroundColor =
                .clear

            self.listBackgroundView.tintColor =
                UIColor(
                    white:
                        isDark
                            ? 0.0
                            : 1.0,
                    alpha:
                        isDark
                            ? 0.045
                            : 0.075
                )

            self.listMaskView.tintColor =
                .clear
        } else {
'''

new_members_on = '''        if self.ghostBaseGlassEnabled {
            let isDark = presentationData.theme.overallDarkAppearance

            self.backgroundColor = .clear
            self.listNode.backgroundColor = .clear

            if self.ghostBaseGlassIsDark != isDark {
                self.ghostBaseGlassIsDark = isDark
                self.ghostBaseGlassEffectView.effect = UIBlurEffect(
                    style: isDark ? .systemUltraThinMaterialDark : .systemUltraThinMaterialLight
                )
            }

            self.ghostBaseGlassEffectView.isHidden = false
            self.ghostBaseGlassTintView.backgroundColor = UIColor(
                white: isDark ? 0.0 : 1.0,
                alpha: isDark ? 0.055 : 0.075
            )

            self.listBackgroundView.isHidden = true
            self.listMaskView.isHidden = true
        } else {
            self.ghostBaseGlassEffectView.isHidden = true
            self.ghostBaseGlassEffectView.effect = nil
            self.ghostBaseGlassTintView.backgroundColor = .clear
            self.listBackgroundView.isHidden = false
            self.listMaskView.isHidden = false
'''

members = one(
    members,
    old_members_on,
    new_members_on,
    'members real pane glass'
)

members = one(
    members,
    '''        transition.updateFrame(view: self.listBackgroundView, frame: listBackgroundFrame)
        transition.updateFrame(view: self.listMaskView, frame: listMaskFrame)
''',
    '''        transition.updateFrame(view: self.listBackgroundView, frame: listBackgroundFrame)
        transition.updateFrame(view: self.listMaskView, frame: listMaskFrame)
        transition.updateFrame(view: self.ghostBaseGlassEffectView, frame: listBackgroundFrame)

        self.ghostBaseGlassEffectView.layer.cornerRadius = 26.0
        self.ghostBaseGlassEffectView.layer.masksToBounds = true
        self.ghostBaseGlassTintView.frame = CGRect(origin: .zero, size: listBackgroundFrame.size)
''',
    'members glass frame'
)

MEMBERS.write_text(members, encoding='utf-8')


# ============================================================
# 5. OPENED GIFT
# ============================================================

gift = GIFT.read_text(encoding='utf-8')

old_gift_material = '''            // MARK: GhostBase v1.1M PROFILEGIFTGLASS1
            let ghostBaseProfileGift:
                Bool

            if
                case .profileGift =
                    context.component.subject,
                GhostBaseProfileBlurSettings
                    .loadEnabled() != nil
            {
                ghostBaseProfileGift =
                    true
            } else {
                ghostBaseProfileGift =
                    false
            }

            let ghostBaseSheetColor:
                UIColor

            if ghostBaseProfileGift {
                ghostBaseSheetColor =
                    UIColor(
                        white:
                            environment
                                .theme
                                .overallDarkAppearance
                            ? 0.0
                            : 1.0,
                        alpha:
                            environment
                                .theme
                                .overallDarkAppearance
                            ? 0.56
                            : 0.64
                    )
            } else {
                ghostBaseSheetColor =
                    environment
                        .theme
                        .actionSheet
                        .opaqueItemBackgroundColor
            }
'''

new_gift_material = '''            // MARK: GhostBase v1.1Q PROFILE_GIFT_READABILITY1
            let ghostBaseSheetColor =
                environment
                    .theme
                    .actionSheet
                    .opaqueItemBackgroundColor
'''

gift = one(
    gift,
    old_gift_material,
    new_gift_material,
    'opened gift official sheet'
)

GIFT.write_text(gift, encoding='utf-8')


# ============================================================
# 6. HISTORY
# ============================================================

report = REPORT.read_text(encoding='utf-8')

report = one(
    report,
    '''        self.scrollNode.view.clipsToBounds =
            true

        self.scrollNode.view.contentInset =
''',
    '''        // MARK: GhostBase v1.1Q HISTORY_CLIP_HARDENING1
        self.clipsToBounds =
            true

        self.scrollNode.clipsToBounds =
            true

        self.scrollNode.view.clipsToBounds =
            true

        self.scrollNode.view.contentInset =
''',
    'history node-level clipping'
)

REPORT.write_text(report, encoding='utf-8')

_committed = True

print('[V11Q] FULL_RUNTIME_CORRECTION1 materialized')
print('[V11Q] modern .glass owner: Add Contact/new Settings rounded surface')
print('[V11Q] animation: persistent one-timeline secondary output across holder handoffs')
print('[V11Q] blur: Build97 neutral cache-miss + exact final-image reopen cache preserved')
print('[V11Q] Members: single pane-level UltraThinMaterial, old black image surfaces hidden')
print('[V11Q] opened Gift: Official opaque sheet readability restored')
print('[V11Q] history: physical viewport clipping hardened; V11N/V11O bounded logic preserved')
