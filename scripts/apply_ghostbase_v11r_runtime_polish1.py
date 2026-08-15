#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src")).resolve()

PATHS = {
    "media": ROOT / "submodules/MediaPlayer/Sources/MediaPlayerNode.swift",
    "chunk": ROOT / "submodules/MediaPlayer/Sources/ChunkMediaPlayerV2.swift",
    "bg": ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift",
    "cover": ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoCoverComponent/Sources/PeerInfoCoverComponent.swift",
    "groups": ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoGroupsInCommonPaneNode.swift",
    "gift": ROOT / "submodules/TelegramUI/Components/Gifts/GiftViewScreen/Sources/GiftViewScreen.swift",
    "music_controller": ROOT / "submodules/TelegramUI/Sources/OverlayAudioPlayerControllerNode.swift",
    "music_controls": ROOT / "submodules/TelegramUI/Sources/OverlayAudioPlayerControlsNode.swift",
    "report": ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileReportPaneNode.swift",
    "quote": ROOT / "submodules/TextFormat/Sources/ChatInputContentConversion.swift",
    "settings": ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift",
    "root": ROOT / "submodules/TelegramUI/Sources/TelegramRootController.swift",
}

MARKERS = {
    "media": "GhostBase v1.1R SECONDARY_VIDEO_LIFECYCLE1",
    "chunk": "GhostBase v1.1R SECONDARY_VIDEO_RECOVERY1",
    "bg": "GhostBase v1.1R STATIC_AVATAR_DIRECT_RESOURCE1",
    "cover": "GhostBase v1.1R PREMIUM_PATTERN_RESTORE1",
    "groups": "GhostBase v1.1R COMMON_GROUPS_GLASS1",
    "gift": "GhostBase v1.1R GIFT_READABLE_GLASS1",
    "music_controller": "GhostBase v1.1R MUSIC_HEADER_GLASS2",
    "music_controls": "GhostBase v1.1R MUSIC_CONTROLS_GLASS2",
    "report": "GhostBase v1.1R HISTORY_CARDS1",
    "quote": "GhostBase v1.1R MULTILINE_QUOTE1",
    "settings": "GhostBase v1.1R RAM_SETTING1",
    "root": "GhostBase v1.1R RAM_OVERLAY1",
}

for name, path in PATHS.items():
    if not path.is_file():
        raise RuntimeError(f"[V11R] missing required source {name}: {path}")

sources = {name: path.read_text(encoding="utf-8") for name, path in PATHS.items()}
present = {name: marker in sources[name] for name, marker in MARKERS.items()}
if all(present.values()):
    print("[V11R] RUNTIME_POLISH1 already materialized")
    raise SystemExit(0)
if any(present.values()):
    partial = ", ".join(name for name, value in present.items() if value)
    raise RuntimeError(f"[V11R] partial materialization detected: {partial}")


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"[V11R] {label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def insert_before(text: str, token: str, addition: str, label: str) -> str:
    count = text.count(token)
    if count != 1:
        raise RuntimeError(f"[V11R] {label}: expected one token, found {count}")
    return text.replace(token, addition + token, 1)


def balanced_region(text: str, start_token: str, open_char: str = "{", close_char: str = "}", start_at: int = 0, label: str = "region") -> tuple[int, int]:
    start = text.find(start_token, start_at)
    if start < 0:
        raise RuntimeError(f"[V11R] {label}: start token not found")
    brace = text.find(open_char, start + len(start_token))
    if brace < 0:
        raise RuntimeError(f"[V11R] {label}: opening delimiter not found")
    depth = 0
    in_string = False
    escaped = False
    for i in range(brace, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        elif ch == '"':
            in_string = True
            continue
        if ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
            if depth == 0:
                return start, i + 1
    raise RuntimeError(f"[V11R] {label}: closing delimiter not found")


# ---------------------------------------------------------------------------
# 1. Secondary video lifecycle / watchdog / decoding recovery.
# ---------------------------------------------------------------------------
media = sources["media"]
media = once(
    media,
    '''        if #available(iOS 13.0, *) {\n            layer.preventsCapture = self.captureProtected\n        }\n''',
    '''        // MARK: GhostBase v1.1R SECONDARY_VIDEO_LIFECYCLE1\n        // The primary Telegram renderer remains responsible for capture\n        // protection. Setting preventsCapture on the mirrored display layer\n        // can synchronously deadlock AVFoundation during scene resume.\n''',
    "secondary preventsCapture removal",
)
start = media.find("    private static func enqueueSecondaryCopies(")
end = media.find("\n    private func startPolling()", start)
if start < 0 or end < 0:
    raise RuntimeError("[V11R] secondary copy function boundaries missing")
media = media[:start] + '''    private static func enqueueSecondaryCopies(
        _ sampleBuffer: CMSampleBuffer,
        layers: [AVSampleBufferDisplayLayer]
    ) {
        for layer in layers {
            if layer.status == .failed {
                layer.flush()
            }
            if #available(iOS 14.0, *),
               layer.requiresFlushToResumeDecoding {
                layer.flush()
            }
            guard layer.isReadyForMoreMediaData else {
                continue
            }
            var copy: CMSampleBuffer?
            if CMSampleBufferCreateCopy(
                allocator: kCFAllocatorDefault,
                sampleBuffer: sampleBuffer,
                sampleBufferOut: &copy
            ) == noErr, let copy {
                layer.enqueue(copy)
            }
        }
    }
''' + media[end:]
sources["media"] = media

chunk = sources["chunk"]
chunk = once(
    chunk,
    "    private func updateInternalState() {\n",
    '''    // MARK: GhostBase v1.1R SECONDARY_VIDEO_RECOVERY1
    private func ghostBaseRecoverSecondaryVideoRenderers() {
        for layer in self.secondaryVideoRenderers.values {
            if layer.status == .failed {
                layer.flush()
            }
            if #available(iOS 14.0, *),
               layer.requiresFlushToResumeDecoding {
                layer.flush()
            }
        }
    }

    private func updateInternalState() {
        // ChunkMediaPlayerV2 already ticks on the main run loop. Repair only
        // secondary renderers that AVFoundation explicitly says need a flush.
        self.ghostBaseRecoverSecondaryVideoRenderers()
''',
    "ChunkMediaPlayerV2 recovery hook",
)
sources["chunk"] = chunk


# ---------------------------------------------------------------------------
# 2. Static avatar: direct Telegram MediaBox resource + fresh tint.
# ---------------------------------------------------------------------------
bg = sources["bg"]
start = bg.find("    private func avatarEntrySignal(")
end = bg.find("\n    private func resourceEntrySignal(", start)
if start < 0 or end < 0:
    raise RuntimeError("[V11R] avatarEntrySignal boundaries missing")
bg = bg[:start] + '''    // MARK: GhostBase v1.1R STATIC_AVATAR_DIRECT_RESOURCE1
    private func avatarEntrySignal(
        peer: EnginePeer,
        representation: TelegramMediaImageRepresentation,
        identity: String,
        fallback: UIColor
    ) -> Signal<GhostBaseProfileBackgroundCacheEntry?, NoError>? {
        // Wallpaper and animated-avatar sources already preserve a readable
        // silhouette. Static avatars now use the original Telegram MediaBox
        // resource too, instead of a 360x360 peerAvatarImage presentation.
        return self.resourceEntrySignal(
            resource: representation.resource,
            identity: identity,
            fallback: fallback,
            alwaysSampleTint: true
        )
    }
''' + bg[end:]
bg = once(
    bg,
    '''    private func resourceEntrySignal(
        resource: MediaResource,
        identity: String,
        fallback: UIColor
    ) -> Signal<GhostBaseProfileBackgroundCacheEntry?, NoError> {
''',
    '''    private func resourceEntrySignal(
        resource: MediaResource,
        identity: String,
        fallback: UIColor,
        alwaysSampleTint: Bool = false
    ) -> Signal<GhostBaseProfileBackgroundCacheEntry?, NoError> {
''',
    "resourceEntrySignal signature",
)
bg = once(
    bg,
    '''                            let tint: UIColor

                            if let persisted =
                                Self.persistentTint(
                                    identity:
                                        identity
                                ) {

                                tint = persisted
                            } else {
                                tint =
                                    Self.sampledTint(
                                        from: image,
                                        fallback:
                                            fallback
                                    )

                                Self.storePersistentTint(
                                    tint,
                                    identity:
                                        identity
                                )
                            }
''',
    '''                            let tint: UIColor

                            if alwaysSampleTint {
                                // A decoded static avatar is authoritative.
                                // Never let an old persisted tone turn reopen
                                // into a grey/flat plate.
                                tint = Self.sampledTint(
                                    from: image,
                                    fallback: fallback
                                )
                                Self.storePersistentTint(
                                    tint,
                                    identity: identity
                                )
                            } else if let persisted = Self.persistentTint(
                                identity: identity
                            ) {
                                tint = persisted
                            } else {
                                tint = Self.sampledTint(
                                    from: image,
                                    fallback: fallback
                                )
                                Self.storePersistentTint(
                                    tint,
                                    identity: identity
                                )
                            }
''',
    "fresh avatar tint",
)
sources["bg"] = bg


# ---------------------------------------------------------------------------
# 3. Premium decorations: keep native pattern opacity, grade only gradient.
# ---------------------------------------------------------------------------
cover = sources["cover"]
old = '''        // MARK: GhostBase v1.1P PREMIUM_COMPOSITE1
        public func setGhostBaseDecorationAlpha(_ alpha: CGFloat) {
            let alpha = max(0.0, min(1.0, alpha))
            let patternFraction =
                self.component?.patternTransitionFraction ?? 1.0
            let avatarGradientFraction =
                1.0 -
                (self.component?.avatarTransitionFraction ?? 0.0)

            self.avatarBackgroundPatternContentsLayer.opacity =
                Float(alpha)

            self.backgroundPatternContainer.alpha =
                patternFraction * alpha

            self.avatarBackgroundGradientLayer.opacity =
                Float(
                    avatarGradientFraction * alpha
                )
        }
'''
new = '''        // MARK: GhostBase v1.1R PREMIUM_PATTERN_RESTORE1
        public func setGhostBaseDecorationAlpha(_ alpha: CGFloat) {
            let alpha = max(0.0, min(1.0, alpha))
            let patternFraction =
                self.component?.patternTransitionFraction ?? 1.0
            let avatarGradientFraction =
                1.0 -
                (self.component?.avatarTransitionFraction ?? 0.0)

            // Premium pattern is native profile identity, not a heavy fill.
            // Keep it fully visible while GhostBase only attenuates gradient.
            self.avatarBackgroundPatternContentsLayer.opacity = 1.0
            self.backgroundPatternContainer.alpha = patternFraction

            self.avatarBackgroundGradientLayer.opacity =
                Float(avatarGradientFraction * alpha)
        }
'''
cover = once(cover, old, new, "Premium decoration method")
sources["cover"] = cover


# ---------------------------------------------------------------------------
# 4. Common Groups: same single pane-level material proven in Members.
# ---------------------------------------------------------------------------
groups = sources["groups"]
groups = once(
    groups,
    '''    private let listBackgroundView: UIImageView
    private let listMaskView: UIImageView
    private let listNode: ListView
''',
    '''    private let listBackgroundView: UIImageView
    private let listMaskView: UIImageView

    // MARK: GhostBase v1.1R COMMON_GROUPS_GLASS1
    private let ghostBaseGlassEffectView: UIVisualEffectView
    private let ghostBaseGlassTintView: UIView
    private var ghostBaseGlassIsDark: Bool?

    private let listNode: ListView
''',
    "Common Groups glass properties",
)
groups = once(
    groups,
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
    "Common Groups glass init",
)
groups = once(
    groups,
    '''        self.listNode.preloadPages = true
        self.view.addSubview(self.listBackgroundView)
        self.addSubnode(self.listNode)
        self.view.addSubview(self.listMaskView)
''',
    '''        self.listNode.preloadPages = true
        self.view.addSubview(self.listBackgroundView)
        self.view.addSubview(self.ghostBaseGlassEffectView)
        self.ghostBaseGlassEffectView.contentView.addSubview(self.ghostBaseGlassTintView)
        self.addSubnode(self.listNode)
        self.view.addSubview(self.listMaskView)
''',
    "Common Groups glass hierarchy",
)
old_start = groups.find("        if self.ghostBaseGlassEnabled {", groups.find("func update(size:"))
old_end = groups.find("\n\n        if isFirstLayout", old_start)
if old_start < 0 or old_end < 0:
    raise RuntimeError("[V11R] Common Groups update glass block boundaries missing")
groups = groups[:old_start] + '''        if self.ghostBaseGlassEnabled {
            let isDark = presentationData.theme.overallDarkAppearance

            self.backgroundColor = .clear
            self.listNode.backgroundColor = .clear

            if self.ghostBaseGlassIsDark != isDark {
                self.ghostBaseGlassIsDark = isDark
                self.ghostBaseGlassEffectView.effect = UIBlurEffect(
                    style: isDark
                        ? .systemUltraThinMaterialDark
                        : .systemUltraThinMaterialLight
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

            self.listBackgroundView.tintColor =
                presentationData.theme.list.itemBlocksBackgroundColor
            self.listMaskView.tintColor =
                presentationData.theme.list.blocksBackgroundColor
        }
''' + groups[old_end:]
groups = once(
    groups,
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
    "Common Groups glass frame",
)
sources["groups"] = groups


# ---------------------------------------------------------------------------
# 5. Opened Gift: readable translucent glass, not Build101 transparent / Official opaque.
# ---------------------------------------------------------------------------
gift = sources["gift"]
gift = once(
    gift,
    '''            // MARK: GhostBase v1.1Q PROFILE_GIFT_READABILITY1
            let ghostBaseSheetColor =
                environment
                    .theme
                    .actionSheet
                    .opaqueItemBackgroundColor
''',
    '''            // MARK: GhostBase v1.1R GIFT_READABLE_GLASS1
            let ghostBaseSheetColor =
                environment.theme.actionSheet.opaqueItemBackgroundColor
                    .withAlphaComponent(
                        environment.theme.overallDarkAppearance
                            ? 0.56
                            : 0.64
                    )
''',
    "Gift readable glass",
)
sources["gift"] = gift


# ---------------------------------------------------------------------------
# 6. Saved Music: glass real-profile controls + header surface.
# ---------------------------------------------------------------------------
controls = sources["music_controls"]
controls = once(
    controls,
    '''    private let backgroundNode: ASImageNode
''',
    '''    private let backgroundNode: ASImageNode

    // MARK: GhostBase v1.1R MUSIC_CONTROLS_GLASS2
    private let ghostBaseGlassEffectView: UIVisualEffectView
    private let ghostBaseGlassTintView: UIView
    private var ghostBaseGlassIsDark: Bool?

    var ghostBaseGlassBackgroundEnabled: Bool = false {
        didSet {
            if self.ghostBaseGlassBackgroundEnabled != oldValue {
                self.updateGhostBaseGlassBackground()
            }
        }
    }
''',
    "music controls glass properties",
)
controls = once(
    controls,
    '''        self.backgroundNode = ASImageNode()
        self.backgroundNode.isLayerBacked = true
''',
    '''        self.backgroundNode = ASImageNode()
        self.backgroundNode.isLayerBacked = true

        self.ghostBaseGlassEffectView = UIVisualEffectView(effect: nil)
        self.ghostBaseGlassEffectView.isUserInteractionEnabled = false
        self.ghostBaseGlassEffectView.isHidden = true
        self.ghostBaseGlassTintView = UIView()
        self.ghostBaseGlassTintView.isUserInteractionEnabled = false
        self.ghostBaseGlassIsDark = nil
''',
    "music controls glass init",
)
controls = once(
    controls,
    '''        self.addSubnode(self.backgroundNode)
''',
    '''        self.view.insertSubview(self.ghostBaseGlassEffectView, at: 0)
        self.ghostBaseGlassEffectView.contentView.addSubview(self.ghostBaseGlassTintView)
        self.addSubnode(self.backgroundNode)
''',
    "music controls glass hierarchy",
)
# Insert helper before updatePresentationData.
controls = insert_before(
    controls,
    "    func updatePresentationData(_ presentationData: PresentationData) {\n",
    '''    private func updateGhostBaseGlassBackground() {
        let isDark = self.presentationData.theme.overallDarkAppearance
        self.backgroundNode.isHidden = self.ghostBaseGlassBackgroundEnabled

        if self.ghostBaseGlassBackgroundEnabled {
            if self.ghostBaseGlassIsDark != isDark {
                self.ghostBaseGlassIsDark = isDark
                self.ghostBaseGlassEffectView.effect = UIBlurEffect(
                    style: isDark
                        ? .systemUltraThinMaterialDark
                        : .systemUltraThinMaterialLight
                )
            }
            self.ghostBaseGlassEffectView.isHidden = false
            self.ghostBaseGlassTintView.backgroundColor = UIColor(
                white: isDark ? 0.0 : 1.0,
                alpha: isDark ? 0.10 : 0.14
            )
        } else {
            self.ghostBaseGlassEffectView.isHidden = true
            self.ghostBaseGlassEffectView.effect = nil
            self.ghostBaseGlassTintView.backgroundColor = .clear
        }
    }

''',
    "music controls helper insertion",
)
controls = once(
    controls,
    '''        self.presentationData = presentationData
        
        self.playPauseButton.circleColor = presentationData.theme.list.controlSecondaryColor.withAlphaComponent(0.35)
''',
    '''        self.presentationData = presentationData
        self.updateGhostBaseGlassBackground()
        
        self.playPauseButton.circleColor = presentationData.theme.list.controlSecondaryColor.withAlphaComponent(0.35)
''',
    "music controls theme refresh",
)
controls = once(
    controls,
    '''        transition.updateFrame(node: self.backgroundNode, frame: CGRect(origin: CGPoint(x: 0.0, y: -8.0), size: CGSize(width: width, height: finalPanelHeight + 8.0)))
''',
    '''        let ghostBaseBackgroundFrame = CGRect(
            origin: CGPoint(x: 0.0, y: -8.0),
            size: CGSize(width: width, height: finalPanelHeight + 8.0)
        )
        transition.updateFrame(node: self.backgroundNode, frame: ghostBaseBackgroundFrame)
        transition.updateFrame(view: self.ghostBaseGlassEffectView, frame: ghostBaseBackgroundFrame)
        self.ghostBaseGlassEffectView.layer.cornerRadius = 28.0
        self.ghostBaseGlassEffectView.layer.maskedCorners = [
            .layerMinXMinYCorner,
            .layerMaxXMinYCorner
        ]
        self.ghostBaseGlassEffectView.layer.masksToBounds = true
        self.ghostBaseGlassTintView.frame = CGRect(
            origin: .zero,
            size: ghostBaseBackgroundFrame.size
        )
''',
    "music controls glass frame",
)
sources["music_controls"] = controls

controller = sources["music_controller"]
controller = once(
    controller,
    '''    private let title = ComponentView<Empty>()
''',
    '''    private let title = ComponentView<Empty>()

    // MARK: GhostBase v1.1R MUSIC_HEADER_GLASS2
    private var ghostBaseHeaderGlassView: UIVisualEffectView?
    private var ghostBaseHeaderGlassTintView: UIView?
''',
    "music header glass properties",
)
# Extend inactive and active branches via unique controlsNode assignments.
controller = once(
    controller,
    '''            self.controlsNode.hasPlainBackground =
                !self.historyNode.hasAnyMessages

            return
''',
    '''            self.controlsNode.hasPlainBackground =
                !self.historyNode.hasAnyMessages
            self.controlsNode.ghostBaseGlassBackgroundEnabled = false
            self.ghostBaseHeaderGlassView?.isHidden = true
            self.ghostBaseHeaderGlassView?.effect = nil
            self.ghostBaseHeaderGlassTintView?.backgroundColor = .clear

            return
''',
    "music inactive glass state",
)
controller = once(
    controller,
    '''        self.historyFrameTopMaskNode.alpha = 0.0
        self.controlsNode.hasPlainBackground = false
''',
    '''        self.historyFrameTopMaskNode.alpha = 0.0
        self.controlsNode.hasPlainBackground = false
        self.controlsNode.ghostBaseGlassBackgroundEnabled = true

        let headerGlassView: UIVisualEffectView
        let headerTintView: UIView
        if let current = self.ghostBaseHeaderGlassView,
           let currentTint = self.ghostBaseHeaderGlassTintView {
            headerGlassView = current
            headerTintView = currentTint
        } else {
            headerGlassView = UIVisualEffectView(effect: nil)
            headerGlassView.isUserInteractionEnabled = false
            headerGlassView.layer.cornerRadius = 22.0
            headerGlassView.layer.masksToBounds = true
            headerTintView = UIView()
            headerTintView.isUserInteractionEnabled = false
            headerGlassView.contentView.addSubview(headerTintView)
            self.historyFrameNode.view.insertSubview(headerGlassView, at: 0)
            self.ghostBaseHeaderGlassView = headerGlassView
            self.ghostBaseHeaderGlassTintView = headerTintView
        }
        headerGlassView.effect = UIBlurEffect(
            style: isDark
                ? .systemUltraThinMaterialDark
                : .systemUltraThinMaterialLight
        )
        headerGlassView.isHidden = false
        headerTintView.backgroundColor = UIColor(
            white: isDark ? 0.0 : 1.0,
            alpha: isDark ? 0.08 : 0.11
        )
''',
    "music active glass state",
)
# Header frame in savedMusic branch before controls panel layout.
controller = once(
    controller,
    '''            let headerInset: CGFloat = 16.0
            let headerButtonsSize = self.headerButtons.update(
''',
    '''            let headerInset: CGFloat = 16.0
            if let headerGlassView = self.ghostBaseHeaderGlassView {
                let headerGlassFrame = CGRect(
                    x: 12.0,
                    y: 8.0,
                    width: max(1.0, layout.size.width - 24.0),
                    height: 62.0
                )
                headerGlassView.frame = headerGlassFrame
                self.ghostBaseHeaderGlassTintView?.frame = CGRect(
                    origin: .zero,
                    size: headerGlassFrame.size
                )
            }
            let headerButtonsSize = self.headerButtons.update(
''',
    "music header glass frame",
)
sources["music_controller"] = controller


# ---------------------------------------------------------------------------
# 7. History: bounded storage/viewport unchanged; present report blocks as cards.
# ---------------------------------------------------------------------------
report = sources["report"]
# Some manually materialized Build102 audit trees contain a duplicated
# topMessageId.map( line even though the clean CI build does not. Normalize
# that harmless local replay artifact if present; do nothing on clean CI.
report = report.replace(
    "                            previous.topMessageId.map(\n"
    "                            previous.topMessageId.map(\n",
    "                            previous.topMessageId.map(\n",
    1,
)
class_token = "// MARK: GhostBase v1.1G NATIVEPANES1\nfinal class GhostBaseProfileReportPaneNode"
if class_token not in report:
    raise RuntimeError("[V11R] report pane class anchor missing")
card_class = '''// MARK: GhostBase v1.1R HISTORY_CARDS1
private final class GhostBaseProfileReportCardNode: ASDisplayNode {
    private let textNode = ImmediateTextNode()

    override init() {
        super.init()
        self.clipsToBounds = true
        self.layer.cornerRadius = 16.0
        self.textNode.displaysAsynchronously = false
        self.textNode.maximumNumberOfLines = 0
        self.addSubnode(self.textNode)
    }

    func update(
        text: String,
        presentationData: PresentationData,
        width: CGFloat
    ) -> CGSize {
        let isDark = presentationData.theme.overallDarkAppearance
        self.backgroundColor = UIColor(
            white: isDark ? 1.0 : 0.0,
            alpha: isDark ? 0.075 : 0.035
        )
        self.layer.borderWidth = 0.5
        self.layer.borderColor = presentationData.theme.list.itemPlainSeparatorColor
            .withAlphaComponent(isDark ? 0.30 : 0.20).cgColor

        let lines = text.components(separatedBy: "\\n")
        let attributed = NSMutableAttributedString(string: "")
        for (index, line) in lines.enumerated() {
            if index != 0 {
                attributed.append(NSAttributedString(string: "\\n"))
            }
            attributed.append(NSAttributedString(
                string: line,
                font: index == 0 ? Font.semibold(14.0) : Font.regular(14.0),
                textColor: index == 0
                    ? presentationData.theme.list.itemPrimaryTextColor
                    : presentationData.theme.list.itemSecondaryTextColor
            ))
        }
        self.textNode.attributedText = attributed
        let inset: CGFloat = 14.0
        let textSize = self.textNode.updateLayout(CGSize(
            width: max(1.0, width - inset * 2.0),
            height: .greatestFiniteMagnitude
        ))
        self.textNode.frame = CGRect(
            origin: CGPoint(x: inset, y: 12.0),
            size: textSize
        )
        return CGSize(width: width, height: textSize.height + 24.0)
    }
}

// MARK: GhostBase v1.1G NATIVEPANES1
final class GhostBaseProfileReportPaneNode'''
report = once(report, class_token, card_class, "history card class")
report = once(
    report,
    '''    private let scrollNode = ASScrollNode()
    private let textNode = ImmediateTextNode()
''',
    '''    private let scrollNode = ASScrollNode()
    private var cardNodes: [GhostBaseProfileReportCardNode] = []
    private var renderedReportSections: [String] = []
''',
    "history card properties",
)
report = once(
    report,
    '''        self.backgroundColor = .clear
        self.scrollNode.backgroundColor = .clear
        self.textNode.displaysAsynchronously = false

        // MARK: GhostBase v1.1L HISTORYMULTILINE1
        self.textNode.maximumNumberOfLines = 0

        self.addSubnode(self.scrollNode)
        self.scrollNode.addSubnode(self.textNode)
''',
    '''        self.backgroundColor = .clear
        self.scrollNode.backgroundColor = .clear

        self.addSubnode(self.scrollNode)
''',
    "history init presentation",
)
start = report.find("    private func updateTextLayout(transition: ContainedViewLayoutTransition) {")
end = report.find("\n    func update(\n", start)
if start < 0 or end < 0:
    raise RuntimeError("[V11R] history updateTextLayout boundaries missing")
report = report[:start] + '''    private static func reportSections(_ text: String) -> [String] {
        let sections = text
            .components(separatedBy: "\\n\\n")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
        return sections.isEmpty ? [text] : sections
    }

    private func updateTextLayout(transition: ContainedViewLayoutTransition) {
        guard let size = self.currentSize,
              let presentationData = self.currentPresentationData else {
            return
        }

        let text = self.reportText ?? "Загрузка…"
        let sections = Self.reportSections(text)

        if sections != self.renderedReportSections {
            for node in self.cardNodes {
                node.removeFromSupernode()
            }
            self.cardNodes.removeAll(keepingCapacity: true)
            self.renderedReportSections = sections
            for _ in sections {
                let node = GhostBaseProfileReportCardNode()
                self.cardNodes.append(node)
                self.scrollNode.addSubnode(node)
            }
        }

        let sideInset: CGFloat = 16.0
        let spacing: CGFloat = 10.0
        let cardWidth = max(1.0, size.width - sideInset * 2.0)
        var y: CGFloat = 16.0

        for index in 0 ..< min(sections.count, self.cardNodes.count) {
            let node = self.cardNodes[index]
            let cardSize = node.update(
                text: sections[index],
                presentationData: presentationData,
                width: cardWidth
            )
            transition.updateFrame(
                node: node,
                frame: CGRect(
                    origin: CGPoint(x: sideInset, y: y),
                    size: cardSize
                )
            )
            y += cardSize.height + spacing
        }

        let contentHeight = max(size.height + 1.0, y + 10.0)
        self.scrollNode.view.contentSize = CGSize(
            width: size.width,
            height: contentHeight
        )
    }
''' + report[end:]
sources["report"] = report


# ---------------------------------------------------------------------------
# 8. Multiline quote: consecutive quoted paragraphs -> one structured blockQuote.
# ---------------------------------------------------------------------------
quote = sources["quote"]
start = quote.find("    func appendParagraphs(in range: NSRange) {")
end = quote.find("\n    // Carve out the non-paragraph block regions", start)
if start < 0 or end < 0:
    raise RuntimeError("[V11R] quote appendParagraphs boundaries missing")
quote = quote[:start] + '''    // MARK: GhostBase v1.1R MULTILINE_QUOTE1
    func appendParagraphs(in range: NSRange) {
        guard range.length > 0 else { return }
        var paraRanges: [NSRange] = []
        var lineStart = range.location
        let end = range.location + range.length
        var i = range.location
        while i < end {
            if full.character(at: i) == 0x0A {
                paraRanges.append(NSRange(location: lineStart, length: i - lineStart))
                lineStart = i + 1
            }
            i += 1
        }
        paraRanges.append(NSRange(location: lineStart, length: end - lineStart))

        var pendingQuoteParagraphs: [ChatInputBlock] = []
        var pendingQuoteCollapsed = false

        func flushPendingQuote() {
            guard !pendingQuoteParagraphs.isEmpty else {
                return
            }
            blocks.append(.blockQuote(ChatInputBlockQuote(
                content: ChatInputContent(blocks: pendingQuoteParagraphs),
                collapsed: pendingQuoteCollapsed
            )))
            pendingQuoteParagraphs.removeAll(keepingCapacity: true)
        }

        for pr in paraRanges {
            var runs: [ChatInputRun] = []
            var isQuote = false
            var quoteCollapsed = false
            if pr.length > 0 {
                attributedText.enumerateAttributes(in: pr, options: []) { dict, r, _ in
                    var a = ChatInputInlineAttributes()
                    if dict[ChatTextInputAttributes.bold] != nil { a.bold = true }
                    if dict[ChatTextInputAttributes.italic] != nil { a.italic = true }
                    if dict[ChatTextInputAttributes.monospace] != nil { a.monospace = true }
                    if dict[ChatTextInputAttributes.strikethrough] != nil { a.strikethrough = true }
                    if dict[ChatTextInputAttributes.underline] != nil { a.underline = true }
                    if dict[ChatTextInputAttributes.spoiler] != nil { a.spoiler = true }
                    if let m = dict[ChatTextInputAttributes.textMention] as? ChatTextInputTextMentionAttribute {
                        a.entity = .mention(m.peerId)
                    } else if let d = dict[ChatTextInputAttributes.date] as? ChatTextInputTextDateAttribute {
                        a.entity = .date(d.date)
                    } else if let e = dict[ChatTextInputAttributes.customEmoji] as? ChatTextInputTextCustomEmojiAttribute {
                        a.entity = .customEmoji(fileId: e.fileId, file: e.file, enableAnimation: e.enableAnimation)
                    } else if let u = dict[ChatTextInputAttributes.textUrl] as? ChatTextInputTextUrlAttribute {
                        a.entity = .url(u.url)
                    }
                    if let q = dict[ChatTextInputAttributes.block] as? ChatTextInputTextQuoteAttribute,
                       case .quote = q.kind {
                        isQuote = true
                        quoteCollapsed = q.isCollapsed
                    }
                    runs.append(ChatInputRun(text: full.substring(with: r), attributes: a))
                }
            }

            let paragraph = ChatInputBlock.paragraph(
                ChatInputParagraph(style: .body, runs: runs)
            )

            if isQuote {
                if !pendingQuoteParagraphs.isEmpty && pendingQuoteCollapsed != quoteCollapsed {
                    flushPendingQuote()
                }
                if pendingQuoteParagraphs.isEmpty {
                    pendingQuoteCollapsed = quoteCollapsed
                }
                pendingQuoteParagraphs.append(paragraph)
            } else {
                flushPendingQuote()
                blocks.append(paragraph)
            }
        }
        flushPendingQuote()
    }
''' + quote[end:]
sources["quote"] = quote


# ---------------------------------------------------------------------------
# 9. RAM setting in canonical GhostBase Appearance page.
# ---------------------------------------------------------------------------
settings = sources["settings"]
settings = once(
    settings,
    '    static let messageSeconds = "GhostBase.Appearance.MessageSeconds"\n',
    '    // MARK: GhostBase v1.1R RAM_SETTING1\n'
    '    static let showRamUnderClock = "GhostBase.Appearance.ShowRamUnderClock"\n'
    '    static let messageSeconds = "GhostBase.Appearance.MessageSeconds"\n',
    "RAM settings key",
)
settings = once(
    settings,
    "    var messageSeconds: Bool\n",
    "    var showRamUnderClock: Bool\n    var messageSeconds: Bool\n",
    "RAM state property",
)
load_pattern = re.compile(
    r"(?P<indent>\s*)messageSeconds:\s*ghostBaseBool\(\s*GhostBaseKey\.messageSeconds,\s*defaultValue:\s*false\s*\),\n"
)
m = load_pattern.search(settings)
if not m:
    raise RuntimeError("[V11R] RAM state load anchor missing")
indent = m.group("indent")
settings = settings[:m.start()] + (
    f"{indent}showRamUnderClock: ghostBaseBool(\n"
    f"{indent}    GhostBaseKey.showRamUnderClock,\n"
    f"{indent}    defaultValue: false\n"
    f"{indent}),\n"
    + m.group(0)
) + settings[m.end():]
settings = once(
    settings,
    '''        UserDefaults.standard.set(
            self.messageSeconds,
            forKey: GhostBaseKey.messageSeconds
        )
''',
    '''        UserDefaults.standard.set(
            self.showRamUnderClock,
            forKey: GhostBaseKey.showRamUnderClock
        )
        UserDefaults.standard.set(
            self.messageSeconds,
            forKey: GhostBaseKey.messageSeconds
        )
''',
    "RAM settings save",
)
# Add toggle after hideOwnPhone on final Appearance page.
hide_toggle = re.compile(
    r'(?P<block>\s*\.toggle\(\s*1,\s*6,\s*GhostBaseKey\.hideOwnPhone,\s*"Скрывать мой номер",\s*state\.hideOwnPhone\s*\),\n)'
)
m = hide_toggle.search(settings)
if not m:
    raise RuntimeError("[V11R] RAM Appearance hideOwnPhone toggle anchor missing")
ram_toggle = '''            .toggle(
                1,
                7,
                GhostBaseKey.showRamUnderClock,
                "Показывать RAM под часами",
                state.showRamUnderClock
            ),
'''
settings = settings[:m.end()] + ram_toggle + settings[m.end():]
settings = insert_before(
    settings,
    "            case GhostBaseKey.messageSeconds:\n",
    '''            case GhostBaseKey.showRamUnderClock:
                updated.showRamUnderClock = value
                UserDefaults.standard.set(
                    value,
                    forKey: GhostBaseKey.showRamUnderClock
                )

''',
    "RAM switch case",
)
sources["settings"] = settings


# ---------------------------------------------------------------------------
# 10. Global RAM overlay under the status-bar clock.
# ---------------------------------------------------------------------------
root = sources["root"]
if "import Darwin\n" not in root:
    root = once(root, "import UIKit\n", "import UIKit\nimport Darwin\n", "Darwin import")
root = once(
    root,
    '''    private var applicationInFocusDisposable: Disposable?
    private var storyUploadEventsDisposable: Disposable?
''',
    '''    private var applicationInFocusDisposable: Disposable?
    private var storyUploadEventsDisposable: Disposable?

    // MARK: GhostBase v1.1R RAM_OVERLAY1
    private var ghostBaseRamLabel: UILabel?
    private var ghostBaseRamTimer: Foundation.Timer?
    private var ghostBaseRamDefaultsObserver: NSObjectProtocol?
    private var ghostBaseRamActiveObserver: NSObjectProtocol?
    private var ghostBaseRamInactiveObserver: NSObjectProtocol?
    private var ghostBaseRamLayout: ContainerViewLayout?
''',
    "RAM root properties",
)
# Insert setup before end of public init.
init_start, init_end = balanced_region(root, "    public init(context: AccountContext)", label="TelegramRootController init")
root = root[:init_end - 1] + '''
        self.ghostBaseSetupRamOverlay()
    ''' + root[init_end - 1:]
root = once(
    root,
    '''        self.applicationInFocusDisposable?.dispose()
        self.storyUploadEventsDisposable?.dispose()
    }
''',
    '''        self.applicationInFocusDisposable?.dispose()
        self.storyUploadEventsDisposable?.dispose()
        self.ghostBaseRamTimer?.invalidate()
        if let observer = self.ghostBaseRamDefaultsObserver {
            NotificationCenter.default.removeObserver(observer)
        }
        if let observer = self.ghostBaseRamActiveObserver {
            NotificationCenter.default.removeObserver(observer)
        }
        if let observer = self.ghostBaseRamInactiveObserver {
            NotificationCenter.default.removeObserver(observer)
        }
    }
''',
    "RAM root deinit",
)
root = insert_before(
    root,
    "    public func getContactsController() -> ViewController? {\n",
    '''    private static let ghostBaseRamEnabledKey =
        "GhostBase.Appearance.ShowRamUnderClock"

    private func ghostBaseSetupRamOverlay() {
        self.ghostBaseRamDefaultsObserver = NotificationCenter.default.addObserver(
            forName: UserDefaults.didChangeNotification,
            object: UserDefaults.standard,
            queue: .main,
            using: { [weak self] _ in
                self?.ghostBaseUpdateRamOverlayState()
            }
        )
        self.ghostBaseRamActiveObserver = NotificationCenter.default.addObserver(
            forName: UIApplication.didBecomeActiveNotification,
            object: nil,
            queue: .main,
            using: { [weak self] _ in
                self?.ghostBaseUpdateRamOverlayState()
            }
        )
        self.ghostBaseRamInactiveObserver = NotificationCenter.default.addObserver(
            forName: UIApplication.willResignActiveNotification,
            object: nil,
            queue: .main,
            using: { [weak self] _ in
                self?.ghostBaseUpdateRamOverlayState(forceInactive: true)
            }
        )
        self.ghostBaseUpdateRamOverlayState()
    }

    private func ghostBaseUpdateRamOverlayState(forceInactive: Bool = false) {
        let enabled = (
            UserDefaults.standard.object(
                forKey: Self.ghostBaseRamEnabledKey
            ) as? Bool
        ) ?? false
        let active = !forceInactive && UIApplication.shared.applicationState == .active

        guard enabled && active else {
            self.ghostBaseRamTimer?.invalidate()
            self.ghostBaseRamTimer = nil
            self.ghostBaseRamLabel?.removeFromSuperview()
            self.ghostBaseRamLabel = nil
            return
        }

        let label: UILabel
        if let current = self.ghostBaseRamLabel {
            label = current
        } else {
            label = UILabel()
            label.isUserInteractionEnabled = false
            label.backgroundColor = .clear
            label.font = UIFont.monospacedDigitSystemFont(
                ofSize: 8.5,
                weight: .semibold
            )
            label.textAlignment = .left
            label.adjustsFontSizeToFitWidth = false
            self.view.addSubview(label)
            self.ghostBaseRamLabel = label
        }

        label.textColor = self.presentationData.theme.overallDarkAppearance
            ? UIColor.white.withAlphaComponent(0.78)
            : UIColor.black.withAlphaComponent(0.68)

        if self.ghostBaseRamTimer == nil {
            let timer = Foundation.Timer(timeInterval: 1.0, repeats: true) { [weak self] _ in
                self?.ghostBaseUpdateRamValue()
            }
            RunLoop.main.add(timer, forMode: .common)
            self.ghostBaseRamTimer = timer
        }

        self.ghostBaseUpdateRamValue()
        self.ghostBaseLayoutRamLabel()
        self.view.bringSubviewToFront(label)
    }

    private func ghostBaseCurrentMemoryFootprint() -> UInt64? {
        var info = task_vm_info_data_t()
        var count = mach_msg_type_number_t(
            MemoryLayout<task_vm_info>.size / MemoryLayout<integer_t>.size
        )
        let result = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(
                to: integer_t.self,
                capacity: Int(count)
            ) {
                task_info(
                    mach_task_self_,
                    task_flavor_t(TASK_VM_INFO),
                    $0,
                    &count
                )
            }
        }
        guard result == KERN_SUCCESS else {
            return nil
        }
        return info.phys_footprint
    }

    private func ghostBaseUpdateRamValue() {
        guard let label = self.ghostBaseRamLabel else {
            return
        }
        if let bytes = self.ghostBaseCurrentMemoryFootprint() {
            let megabytes = Int((bytes + 524_288) / 1_048_576)
            label.text = "RAM \\(megabytes) MB"
        } else {
            label.text = "RAM —"
        }
    }

    private func ghostBaseLayoutRamLabel() {
        guard let label = self.ghostBaseRamLabel,
              let layout = self.ghostBaseRamLayout else {
            return
        }
        let statusHeight = max(
            layout.statusBarHeight ?? 0.0,
            layout.safeInsets.top
        )
        let height: CGFloat = 11.0
        let y: CGFloat
        if statusHeight >= 40.0 {
            y = max(0.0, statusHeight - height - 2.0)
        } else {
            y = statusHeight + 1.0
        }
        label.frame = CGRect(
            x: max(6.0, layout.safeInsets.left + 6.0),
            y: y,
            width: 76.0,
            height: height
        )
    }

''',
    "RAM root helpers",
)
root = once(
    root,
    '''        super.containerLayoutUpdated(layout, transition: transition)
    }
''',
    '''        super.containerLayoutUpdated(layout, transition: transition)
        self.ghostBaseRamLayout = layout
        self.ghostBaseUpdateRamOverlayState()
        self.ghostBaseLayoutRamLabel()
    }
''',
    "RAM root layout",
)
sources["root"] = root


# ---------------------------------------------------------------------------
# Semantic pre-write gates. These intentionally protect Build102 fixes.
# ---------------------------------------------------------------------------
checks = [
    ("secondary preventsCapture gone", "layer.preventsCapture = self.captureProtected" not in sources["media"][sources["media"].find("public func addSecondaryVideoLayer"):sources["media"].find("public func removeSecondaryVideoLayer")]),
    ("static avatar direct resource", "alwaysSampleTint: true" in sources["bg"] and "peerAvatarImage(" not in sources["bg"][sources["bg"].find("private func avatarEntrySignal"):sources["bg"].find("private func resourceEntrySignal")]),
    ("Premium pattern native", "avatarBackgroundPatternContentsLayer.opacity = 1.0" in sources["cover"]),
    ("Common Groups pane material", "ghostBaseGlassEffectView" in sources["groups"] and ".systemUltraThinMaterialDark" in sources["groups"]),
    ("Gift translucent", "? 0.56" in sources["gift"] and ": 0.64" in sources["gift"]),
    ("Music controls glass", "ghostBaseGlassBackgroundEnabled" in sources["music_controls"]),
    ("Music header glass", "ghostBaseHeaderGlassView" in sources["music_controller"]),
    ("History cards", "GhostBaseProfileReportCardNode" in sources["report"] and "renderedReportSections" in sources["report"]),
    ("Quote grouping", "pendingQuoteParagraphs" in sources["quote"]),
    ("RAM setting", "GhostBase.Appearance.ShowRamUnderClock" in sources["settings"] and "Показывать RAM под часами" in sources["settings"]),
    ("RAM footprint", "info.phys_footprint" in sources["root"] and "task_info(" in sources["root"]),
    ("Build102 no-avatar preserved", "BUILD97_NEUTRAL_REOPEN1" in sources["bg"]),
]
failed = [name for name, ok in checks if not ok]
if failed:
    raise RuntimeError("[V11R] semantic gate failed: " + ", ".join(failed))

# Atomic-ish write with backups and rollback on error.
backups: dict[Path, bytes] = {path: path.read_bytes() for path in PATHS.values()}
try:
    for name, path in PATHS.items():
        tmp = path.with_name(path.name + ".v11r.tmp")
        tmp.write_text(sources[name], encoding="utf-8")
        tmp.replace(path)
except Exception:
    for path, data in backups.items():
        try:
            path.write_bytes(data)
        except Exception:
            pass
    raise

print("[V11R] RUNTIME_POLISH1 materialized")
print("[V11R] video: secondary preventsCapture deadlock removed + renderer flush recovery")
print("[V11R] blur: static avatar now decodes original MediaBox resource + fresh tint")
print("[V11R] Premium pattern restored; Common Groups pane-level glass installed")
print("[V11R] Gift readable glass; saved-music controls/header glass")
print("[V11R] History cards + multiline quote grouping installed")
print("[V11R] RAM-under-clock toggle + process phys_footprint overlay installed")
