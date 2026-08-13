#!/usr/bin/env python3

import os
from pathlib import Path


ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        "/root/gb_builder/work/swiftgram-src"
    )
)

P = (
    ROOT
    / "submodules/TelegramUI/Components/"
      "PeerInfo/PeerInfoScreen/Sources"
)

BG = P / "GhostBaseProfileFullscreenBackground.swift"
SEC = P / "PeerInfoScreenItemSectionContainerNode.swift"
REP = P / "GhostBaseProfileReportPaneNode.swift"
AVATAR = P / "PeerInfoAvatarTransformContainerNode.swift"

GIFTS = (
    ROOT
    / "submodules/TelegramUI/Components/"
      "PeerInfo/PeerInfoVisualMediaPaneNode/"
      "Sources/GiftsListView.swift"
)

COMP = (
    ROOT
    / "submodules/TelegramUI/Components"
)


def component_source(
    module: str,
    filename: str
) -> Path:
    direct = (
        COMP
        / module
        / "Sources"
        / filename
    )

    if direct.is_file():
        return direct

    for directory in COMP.rglob(module):
        if not directory.is_dir():
            continue

        candidate = (
            directory
            / "Sources"
            / filename
        )

        if candidate.is_file():
            return candidate

    return direct


GIFT_ITEM = component_source(
    "GiftItemComponent",
    "GiftItemComponent.swift"
)


for path in (
    BG,
    SEC,
    REP,
    AVATAR,
    GIFTS,
    GIFT_ITEM,
):
    if not path.is_file():
        raise RuntimeError(
            f"[V11O] missing: {path}"
        )


def replace_once(
    text: str,
    old: str,
    new: str,
    label: str,
) -> str:
    count = text.count(old)

    if count != 1:
        raise RuntimeError(
            f"[V11O] {label}: "
            f"expected 1 found {count}"
        )

    return text.replace(
        old,
        new,
        1
    )


bg = BG.read_text(encoding="utf-8")
sec = SEC.read_text(encoding="utf-8")
rep = REP.read_text(encoding="utf-8")
avatar = AVATAR.read_text(encoding="utf-8")
gifts = GIFTS.read_text(encoding="utf-8")
gift = GIFT_ITEM.read_text(encoding="utf-8")


if "GhostBase v1.1O VISUALRESET1" in bg:
    print("[V11O] already materialized")
    raise SystemExit(0)


# ============================================================
# 1. REMOVE V11N AVPLAYER EXPERIMENT
# ============================================================

bg = replace_once(
    bg,
    """import UIKit
import AVFoundation
""",
    """import UIKit
""",
    "remove AVFoundation import",
)


bg = replace_once(
    bg,
    """private struct GhostBaseAnimatedMediaSource {
    let identity: String
    let content: NativeVideoContent
    let resource: MediaResource
    let startTimestamp: Double?
    let useIndependentPlayer: Bool
}
""",
    """private struct GhostBaseAnimatedMediaSource {
    let identity: String
    let content: NativeVideoContent
}
""",
    "animated source descriptor",
)


bg = replace_once(
    bg,
    """    case premiumProfile
    case avatar
    case telegramTheme
""",
    """    case premiumProfile
    case avatar
    case placeholder
    case telegramTheme
""",
    "placeholder source kind",
)


bg = replace_once(
    bg,
    """    case premium(UIColor, UIColor, String)
    case avatar(EnginePeer, TelegramMediaImageRepresentation, String, GhostBaseAnimatedMediaSource?)
    case telegramTheme
""",
    """    case premium(UIColor, UIColor, String)
    case avatar(EnginePeer, TelegramMediaImageRepresentation, String, GhostBaseAnimatedMediaSource?)
    case placeholder(EnginePeer, UIColor, UIColor, String)
    case telegramTheme
""",
    "placeholder source enum",
)


# A peer without a photo now still owns a GhostBase scene.
bg = replace_once(
    bg,
    """        return !peer.profileImageRepresentations.isEmpty
    }
}
""",
    """        // Every resolved peer has a deliberate GhostBase scene.
        // Peers without a photo use Telegram's own placeholder palette.
        return true
    }
}
""",
    "placeholder stock cover blend",
)


old_video_state = """    // MARK: GhostBase v1.1N PROFILECORE_FINAL1
    //
    // Settings keeps the already-correct Telegram UniversalVideo path.
    // Normal PeerInfo uses an independent AVPlayer over the SAME
    // completed MediaBox resource, avoiding ownership fights with
    // the native circular avatar UniversalVideoNode.
    private var videoNode: UniversalVideoNode?
    private var videoContent: NativeVideoContent?

    private var independentVideoPlayer: AVQueuePlayer?
    private var independentVideoLayer: AVPlayerLayer?
    private var independentVideoLooper: AVPlayerLooper?

    private let animatedResourceDisposable =
        MetaDisposable()

    private var currentVideoIdentity: String?
"""

new_video_state = """    // MARK: GhostBase v1.1O VISUALRESET1
    //
    // Native avatar and fullscreen backdrop share one Telegram profileVideo
    // playback identity. There is no second AVPlayer.
    //
    // Blur/tint intentionally remain the exact proven Build 97/V11K recipe.
    private var videoNode: UniversalVideoNode?
    private var videoContent: NativeVideoContent?
    private var currentVideoIdentity: String?
"""

bg = replace_once(
    bg,
    old_video_state,
    new_video_state,
    "video/blur state reset",
)


# ============================================================
# 2. TRUE FRACTIONAL BLUR
# ============================================================



bg = replace_once(
    bg,
    """        if let independentVideoLayer =
            self.independentVideoLayer {

            independentVideoLayer.frame =
                bounds
        }

        self.blurView.frame = bounds
""",
    """        self.blurView.frame = bounds
""",
    "remove independent video layout",
)


bg = replace_once(
    bg,
    """    override func didMoveToWindow() {
        super.didMoveToWindow()

        if let videoNode = self.videoNode {
            if self.window != nil {
                videoNode.canAttachContent = true
                videoNode.play()
            } else {
                videoNode.pause()
                videoNode.canAttachContent = false
            }
        }

        if let player =
            self.independentVideoPlayer {

            if self.window != nil {
                player.play()
            } else {
                player.pause()
            }
        }
    }
""",
    """    override func didMoveToWindow() {
        super.didMoveToWindow()

        if let videoNode = self.videoNode {
            if self.window != nil {
                videoNode.canAttachContent = true
                videoNode.play()
            } else {
                // The circular avatar may still own the same playback.
                // Detach only this presentation; never pause the shared id.
                videoNode.canAttachContent = false
            }
        }
    }
""",
    "shared video lifecycle",
)


resolve_anchor = """    private func resolveSource(
"""

placeholder_helpers = """    private func placeholderColors(
        peer: EnginePeer,
        presentationData: PresentationData
    ) -> (UIColor, UIColor, String) {
        let isDark =
            presentationData
                .theme
                .overallDarkAppearance

        // Custom Telegram name color, when present.
        if let nameColor = peer.nameColor,
           let colors =
                self.context
                    .peerNameColors
                    .get(
                        nameColor,
                        dark: isDark
                    ) {

            return (
                colors.main,
                colors.secondary
                    ?? colors.main,
                "nameColor:\\(String(describing: nameColor)):\\(isDark)"
            )
        }

        // Telegram legacy avatar-placeholder palette.
        let palette:
            [(UInt32, UInt32)] = [
                (0xff516a, 0xff885e),
                (0xffa85c, 0xffcd6a),
                (0x665fff, 0x82b1ff),
                (0x54cb68, 0xa0de7e),
                (0x4acccd, 0x00fcfd),
                (0x2a9ef1, 0x72d5fd),
                (0xd669ed, 0xe0a2f3)
            ]

        let rawId =
            peer.id.id
                ._internalGetInt64Value()

        let absoluteId: UInt64 =
            rawId == Int64.min
            ? UInt64(Int64.max)
            : UInt64(
                Swift.abs(rawId)
            )

        let index =
            Int(
                absoluteId
                % UInt64(
                    palette.count
                )
            )

        let pair =
            palette[index]

        return (
            UIColor(rgb: pair.0),
            UIColor(rgb: pair.1),
            "legacy:\\(index)"
        )
    }

    private static func colorLuminance(
        _ color: UIColor
    ) -> CGFloat {
        var red: CGFloat = 0.0
        var green: CGFloat = 0.0
        var blue: CGFloat = 0.0
        var alpha: CGFloat = 0.0

        guard color.getRed(
            &red,
            green: &green,
            blue: &blue,
            alpha: &alpha
        ) else {
            return 0.5
        }

        return
            red * 0.2126
            + green * 0.7152
            + blue * 0.0722
    }

"""


if bg.count(resolve_anchor) != 1:
    raise RuntimeError(
        "[V11O] resolveSource anchor missing"
    )

bg = bg.replace(
    resolve_anchor,
    placeholder_helpers
    + resolve_anchor,
    1
)


# ============================================================
# 3. NO-AVATAR PLACEHOLDER SOURCE
# ============================================================

old_peer_end = """            if let representation =
                peer.profileImageRepresentations.last {

                let resourceId =
                    String(
                        describing:
                            representation.resource.id
                    )

                return .avatar(
                    peer,
                    representation,
                    resourceId,
                    self.animatedAvatarSource(
                        peer: peer,
                        item: avatarItem,
                        isSettings: isSettings
                    )
                )
            }
        }

        return .telegramTheme
"""

new_peer_end = """            if let representation =
                peer.profileImageRepresentations.last {

                let resourceId =
                    String(
                        describing:
                            representation.resource.id
                    )

                return .avatar(
                    peer,
                    representation,
                    resourceId,
                    self.animatedAvatarSource(
                        peer: peer,
                        item: avatarItem,
                        isSettings: isSettings
                    )
                )
            }

            // No photo at all: never reuse an old image buffer and never wait
            // for an avatar signal. Build the profile scene synchronously from
            // the same Telegram placeholder color family as the letter avatar.
            let placeholder =
                self.placeholderColors(
                    peer: peer,
                    presentationData:
                        presentationData
                )

            return .placeholder(
                peer,
                placeholder.0,
                placeholder.1,
                placeholder.2
            )
        }

        return .telegramTheme
"""

bg = replace_once(
    bg,
    old_peer_end,
    new_peer_end,
    "placeholder resolution",
)


# ============================================================
# 4. ONE TELEGRAM PROFILEVIDEO ID
# ============================================================

old_xor = """        // V11M:
        // Keep Telegram MediaBox resource identical,
        // but do not fight the native circular avatar
        // for one UniversalVideoManager identity.
        let ghostBasePlaybackId =
            videoId
            ^ 0x47424d4241434b44

        let content = NativeVideoContent(
            id: .profileVideo(
                ghostBasePlaybackId,
                nil
            ),
"""

new_xor = """        // V11O:
        // Native circle and fullscreen blur expose the SAME Telegram
        // UniversalVideoManager playback through two presentation nodes.
        let content = NativeVideoContent(
            id: .profileVideo(
                videoId,
                nil
            ),
"""

bg = replace_once(
    bg,
    old_xor,
    new_xor,
    "shared profileVideo id",
)


bg = replace_once(
    bg,
    """        return GhostBaseAnimatedMediaSource(
            identity: identity,
            content: content,
            resource:
                video.representation.resource,
            startTimestamp:
                video.representation.startTimestamp,
            useIndependentPlayer:
                !isSettings
        )
""",
    """        return GhostBaseAnimatedMediaSource(
            identity: identity,
            content: content
        )
""",
    "simple animated source",
)


# ============================================================
# 5. STATE KEY FOR PLACEHOLDER
# ============================================================

bg = replace_once(
    bg,
    """        case .telegramTheme:
            return GhostBaseProfileBackgroundStateKey(
""",
    """        case let .placeholder(
            _,
            _,
            _,
            identity
        ):
            return GhostBaseProfileBackgroundStateKey(
                peerId: peerId,
                kind: .placeholder,
                wallpaper: nil,
                avatarResourceId: nil,
                animatedIdentity: nil,
                premiumIdentity: identity,
                themeIdentity: themeIdentity
            )

        case .telegramTheme:
            return GhostBaseProfileBackgroundStateKey(
""",
    "placeholder state key",
)


# ============================================================
# 6. REPLACE ANIMATED RENDERER
# ============================================================

clear_start = bg.find(
    "    private func clearAnimatedMedia() {\n"
)

apply_animated_start = bg.find(
    "    private func applyAnimatedMedia(\n",
    clear_start
)

apply_start = bg.find(
    "    private func apply(\n",
    apply_animated_start
)

if (
    clear_start < 0
    or apply_animated_start < 0
    or apply_start < 0
):
    raise RuntimeError(
        "[V11O] animated renderer boundaries missing"
    )


new_animated_renderer = """    private func clearAnimatedMedia() {
        if let videoNode = self.videoNode {
            // Same id may still be displayed by the native avatar.
            // Never pause the global/shared playback from the backdrop.
            videoNode.canAttachContent = false
            videoNode.view.removeFromSuperview()
        }

        self.videoNode = nil
        self.videoContent = nil
        self.currentVideoIdentity = nil
    }

    private func applyAnimatedMedia(
        _ source: GhostBaseAnimatedMediaSource?
    ) {
        guard let source else {
            self.clearAnimatedMedia()
            return
        }

        if self.currentVideoIdentity
            == source.identity,
           self.videoNode != nil {

            return
        }

        self.clearAnimatedMedia()

        self.currentVideoIdentity =
            source.identity

        let mediaManager =
            self.context
                .sharedContext
                .mediaManager

        let videoNode =
            UniversalVideoNode(
                context:
                    self.context,
                postbox:
                    self.context
                        .account
                        .postbox,
                audioSession:
                    mediaManager
                        .audioSession,
                manager:
                    mediaManager
                        .universalVideoManager,
                decoration:
                    GalleryVideoDecoration(),
                content:
                    source.content,
                priority:
                    .embedded
            )

        videoNode.isUserInteractionEnabled =
            false

        self.insertSubview(
            videoNode.view,
            belowSubview:
                self.blurView
        )

        videoNode.frame =
            self.bounds

        videoNode.updateLayout(
            size:
                self.bounds.size,
            transition:
                .immediate
        )

        self.videoNode =
            videoNode

        self.videoContent =
            source.content

        if self.window != nil {
            videoNode.canAttachContent =
                true

            videoNode.play()
        }
    }

"""


bg = (
    bg[:clear_start]
    + new_animated_renderer
    + bg[apply_start:]
)


# ============================================================
# 7. BUILD 97 / V11K VISUAL RECIPE LOCK
#
# The actual blur/tint recipe in Build 97 and Build 100 is
# already identical. Do NOT invent a new fractional blur.
#
# The visual pipeline difference was the avatar presentation:
#
# Build 97:
#   360x360
#   synchronousLoad: false
#
# Build 100:
#   480x480
#   synchronousLoad: true
#
# Restore the proven Build 97 presentation feed while keeping
# the newer no-GhostBase-avatar-cache/state fixes.
# ============================================================

v11k_blur_recipe = """        let effectStyle: UIBlurEffect.Style = isDark
            ? .systemUltraThinMaterialDark
            : .systemUltraThinMaterialLight
        self.blurView.effect = UIBlurEffect(style: effectStyle)
"""

if v11k_blur_recipe not in bg:
    raise RuntimeError(
        "[V11O] Build 97/V11K blur recipe drifted"
    )

v11k_tint_recipe = """                reduced
                    ? (isDark ? 0.030 : 0.020)
                    : (isDark ? 0.050 : 0.035)
"""

if v11k_tint_recipe not in bg:
    raise RuntimeError(
        "[V11O] Build 97/V11K tint recipe drifted"
    )

v11k_neutral_tint_recipe = """                reduced
                    ? (isDark ? 0.018 : 0.010)
                    : (isDark ? 0.030 : 0.016)
"""

if v11k_neutral_tint_recipe not in bg:
    raise RuntimeError(
        "[V11O] Build 97/V11K neutral tint recipe drifted"
    )

avatar_feed_old = """                displayDimensions:
                    CGSize(
                        width: 480.0,
                        height: 480.0
                    ),
                clipStyle:
                    .none,
                blurred:
                    false,
                inset:
                    0.0,
                emptyColor:
                    nil,
                synchronousLoad:
                    true
"""

avatar_feed_new = """                displayDimensions:
                    CGSize(
                        width: 360.0,
                        height: 360.0
                    ),
                clipStyle:
                    .none,
                blurred:
                    false,
                inset:
                    0.0,
                emptyColor:
                    nil,
                synchronousLoad:
                    false
"""

bg = replace_once(
    bg,
    avatar_feed_old,
    avatar_feed_new,
    "Build97 avatar presentation feed",
)


# ============================================================
# 8. PLACEHOLDER APPLY
# ============================================================

placeholder_apply = """        case let .placeholder(
            peer,
            main,
            secondary,
            identity
        ):
            self.clearAnimatedMedia()
            self.sourceDisposable.set(nil)
            self.currentLoadKey = nil

            self.usesCustomBackground =
                true

            let cacheKey =
                "placeholder:\\(peer.id.toInt64()):\\(identity)"
                as NSString

            if let cached =
                Self.imageCache.object(
                    forKey: cacheKey
                ) {

                self.imageView.image =
                    cached.image
            } else {
                let image =
                    Self.generatedGradientImage(
                        colors: [
                            main,
                            secondary
                        ]
                    )

                if let image {
                    let entry =
                        GhostBaseProfileBackgroundCacheEntry(
                            image:
                                image,
                            tint:
                                main
                        )

                    Self.imageCache.setObject(
                        entry,
                        forKey:
                            cacheKey
                    )

                    self.imageView.image =
                        image
                } else {
                    self.imageView.image =
                        nil
                }
            }

            self.backgroundColor =
                main

            let luminance =
                max(
                    Self.colorLuminance(
                        main
                    ),
                    Self.colorLuminance(
                        secondary
                    )
                )

            // Keep Telegram's circular placeholder brighter than the scene.
            // Very bright yellow/green avatars receive a stronger dark scrim.
            let scrimAlpha =
                min(
                    isDark
                    ? 0.34
                    : 0.24,
                    max(
                        isDark
                        ? 0.16
                        : 0.09,
                        (
                            isDark
                            ? 0.12
                            : 0.06
                        )
                        + luminance
                        * (
                            isDark
                            ? 0.22
                            : 0.16
                        )
                    )
                )

            self.tintView
                .backgroundColor =
                UIColor.black
                    .withAlphaComponent(
                        scrimAlpha
                    )

"""


apply_blur_pos = bg.find(
    "        self.applyBlur(\n",
    bg.find(
        "    private func apply(\n"
    )
)

source_switch_pos = bg.find(
    "        switch source {\n",
    apply_blur_pos
)

telegram_apply_pos = bg.find(
    "        case .telegramTheme:\n",
    source_switch_pos
)

if (
    apply_blur_pos < 0
    or source_switch_pos < 0
    or telegram_apply_pos < 0
):
    raise RuntimeError(
        "[V11O] placeholder apply anchor missing"
    )

bg = (
    bg[:telegram_apply_pos]
    + placeholder_apply
    + bg[telegram_apply_pos:]
)


# ============================================================
# 9. BUILD 97 / V11K TINT PRESERVED
#
# No replacement here. Exact proven tint values stay materialized.
# ============================================================


# ============================================================
# 10. TRIANGLES:
#     REMOVE ROW MASKING, FIX ACTUAL TRANSLUCENT BACKING
# ============================================================

row_start = sec.find(
    "            // MARK: GhostBase v1.1N ROWCORNERS_FINAL1\n"
)

row_end = sec.find(
    "            if wasAdded {\n",
    row_start
)

if (
    row_start < 0
    or row_end < 0
):
    raise RuntimeError(
        "[V11O] V11N row corner block missing"
    )

sec = (
    sec[:row_start]
    + """            // MARK: GhostBase v1.1O CORNERSOURCE1
            //
            // One rounded section surface owns the card geometry.
            // Do not mask individual transparent rows.
"""
    + sec[row_end:]
)


sec = replace_once(
    sec,
    """        super.init()

        self.backgroundColor = .clear
        self.itemContainerNode.backgroundColor = .clear
""",
    """        super.init()

        // MARK: GhostBase v1.1O NONOPAQUECARD1
        //
        // This card is intentionally translucent. Its actual backing layers
        // must not stay opaque, otherwise rounded transparent corners can
        // reveal black wedges.
        self.layer.isOpaque = false
        self.backgroundNode.layer.isOpaque = false
        self.itemContainerNode.layer.isOpaque = false

        self.backgroundColor = .clear
        self.itemContainerNode.backgroundColor = .clear
""",
    "nonopaque section backing",
)


# ============================================================
# 11. HISTORY:
#     REPORT SCROLL MUST NOT COLLAPSE PROFILE HEADER/TABS
# ============================================================

rep = replace_once(
    rep,
    """    var tabBarOffset: CGFloat {
        return max(0.0, self.scrollNode.view.contentOffset.y)
    }
""",
    """    var tabBarOffset: CGFloat {
        // MARK: GhostBase v1.1O HISTORYSTATICHEADER1
        //
        // Text reports scroll only inside their clipped viewport.
        // They never drive PeerInfo header/tab collapsing.
        return 0.0
    }
""",
    "history static tab offset",
)


rep = replace_once(
    rep,
    """        self.tabBarOffsetUpdated?(
            .immediate
        )
""",
    """        // Report scrolling deliberately does not move PeerInfo tabs.
""",
    "history no tab callback",
)


# ============================================================
# 12. GIFTS:
#     REMOVE SHARED MASKED BLUR, USE STABLE READABLE SCRIM
# ============================================================

gift_props = """    // MARK: GhostBase v1.1M GIFTSGLASS1
    //
    // One reusable material node for the whole grid.
    // Visible GiftItem frames form its mask.
    private var ghostBaseGlassNode:
        NavigationBackgroundNode?

    private let ghostBaseGlassMaskLayer =
        CAShapeLayer()

"""

gifts = replace_once(
    gifts,
    gift_props,
    "",
    "gift shared blur properties",
)


method_start = gifts.find(
    "    private func updateGhostBaseGlass(\n"
)

method_end = gifts.find(
    "    @discardableResult\n"
    "    private func updateScrolling",
    method_start
)

if (
    method_start < 0
    or method_end < 0
):
    raise RuntimeError(
        "[V11O] Gifts shared blur method boundaries missing"
    )

gifts = (
    gifts[:method_start]
    + gifts[method_end:]
)


gifts = replace_once(
    gifts,
    """        self.updateGhostBaseGlass(
            presentationData:
                params.presentationData
        )

""",
    "",
    "gift shared blur update call",
)


gift = replace_once(
    gift,
    """                    case .ghostBase:
                        // MARK: GhostBase v1.1M GIFTCARDMASK1
                        //
                        // One shared NavigationBackgroundNode
                        // in GiftsListView owns the real blur.
                        self.backgroundLayer.backgroundColor =
                            UIColor.clear.cgColor
""",
    """                    case .ghostBase:
                        // MARK: GhostBase v1.1O GIFTCARDSCRIM1
                        //
                        // No per-card blur and no shared masked blur.
                        // A stable translucent scrim keeps text readable
                        // over bright gifts and white sender avatars.
                        let isDark =
                            component
                                .theme
                                .overallDarkAppearance

                        self.backgroundLayer
                            .backgroundColor =
                            UIColor(
                                white:
                                    isDark
                                    ? 0.0
                                    : 1.0,
                                alpha:
                                    isDark
                                    ? 0.42
                                    : 0.34
                            )
                            .cgColor
""",
    "gift direct readable scrim",
)


# ============================================================
# 13. KEEP A2 NO-PAUSE, UPDATE ITS STALE COMMENT
# ============================================================

avatar = avatar.replace(
    """            // V11L created a second fullscreen video source.
            // Telegram's native profile transition normally pauses
            // the circular avatar whenever fraction > 0.
            //
            // With GhostBase animated background enabled, keep the
            // native avatar decoder alive as well. V11M-A already
            // gives the fullscreen backdrop a separate playback id,
            // so both consumers can coexist on the same MediaBox file.
""",
    """            // V11O:
            // Fullscreen background and circular avatar share the same
            // Telegram profileVideo playback id. While GhostBase animation
            // is enabled this node must not pause that shared playback.
"""
)


# ============================================================
# WRITE ONLY AFTER ALL ANCHORS PASSED
# ============================================================

for path, text in (
    (BG, bg),
    (SEC, sec),
    (REP, rep),
    (AVATAR, avatar),
    (GIFTS, gifts),
    (GIFT_ITEM, gift),
):
    path.write_text(
        text,
        encoding="utf-8"
    )


print("[V11O] applied")
print("  exact Build 97/V11K blur recipe preserved")
print("  exact Build 97/V11K tint recipe preserved")
print("  Build 97 360px async avatar presentation restored")
print("  GhostBase avatar UIImage cache remains disabled")
print("  no-photo Telegram placeholder color scene")
print("  placeholder scene darkened adaptively")
print("  one shared Telegram profileVideo playback id")
print("  V11N AVPlayer experiment removed")
print("  actual translucent section backing made non-opaque")
print("  experimental row corner masks removed")
print("  History no longer drives header/tabs")
print("  Gifts use stable 0.42/0.34 readable scrim")
