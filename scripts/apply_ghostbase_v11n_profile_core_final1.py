#!/usr/bin/env python3

import os
from pathlib import Path

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

P = (
    ROOT
    / "submodules/TelegramUI/Components/"
      "PeerInfo/PeerInfoScreen/Sources"
)

BG = P / "GhostBaseProfileFullscreenBackground.swift"
SEC = P / "PeerInfoScreenItemSectionContainerNode.swift"
REP = P / "GhostBaseProfileReportPaneNode.swift"

GIFTS = (
    ROOT
    / "submodules/TelegramUI/Components/"
      "PeerInfo/PeerInfoVisualMediaPaneNode/"
      "Sources/GiftsListView.swift"
)

for path in (BG, SEC, REP, GIFTS):
    if not path.is_file():
        raise RuntimeError(
            f"[V11N] missing: {path}"
        )


def replace_once(text, old, new, label):
    count = text.count(old)

    if count != 1:
        raise RuntimeError(
            f"[V11N] {label}: "
            f"expected 1 found {count}"
        )

    return text.replace(old, new, 1)


bg = BG.read_text(encoding="utf-8")
sec = SEC.read_text(encoding="utf-8")
rep = REP.read_text(encoding="utf-8")
gifts = GIFTS.read_text(encoding="utf-8")


if "GhostBase v1.1N PROFILECORE_FINAL1" in bg:
    print("[V11N] already materialized")
    raise SystemExit(0)


# ============================================================
# 1. PROFILE BACKGROUND
# ============================================================

bg = replace_once(
    bg,
    """import Foundation
import UIKit
""",
    """import Foundation
import UIKit
import AVFoundation
""",
    "AVFoundation import",
)


bg = replace_once(
    bg,
    """private struct GhostBaseAnimatedMediaSource {
    let identity: String
    let content: NativeVideoContent
}
""",
    """private struct GhostBaseAnimatedMediaSource {
    let identity: String
    let content: NativeVideoContent
    let resource: MediaResource
    let startTimestamp: Double?
    let useIndependentPlayer: Bool
}
""",
    "animated source descriptor",
)


bg = replace_once(
    bg,
    """    // Exactly one animated source is alive at most.
    // Telegram MediaBox owns the downloaded resource.
    private var videoNode: UniversalVideoNode?
    private var videoContent: NativeVideoContent?
    private var currentVideoIdentity: String?

    private let sourceDisposable = MetaDisposable()
""",
    """    // MARK: GhostBase v1.1N PROFILECORE_FINAL1
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

    private let sourceDisposable = MetaDisposable()
""",
    "animated renderer state",
)


bg = replace_once(
    bg,
    """        if let videoNode = self.videoNode {
            videoNode.frame = bounds
            videoNode.updateLayout(
                size: bounds.size,
                transition: .immediate
            )
        }

        self.blurView.frame = bounds
""",
    """        if let videoNode = self.videoNode {
            videoNode.frame = bounds
            videoNode.updateLayout(
                size: bounds.size,
                transition: .immediate
            )
        }

        if let independentVideoLayer =
            self.independentVideoLayer {

            independentVideoLayer.frame =
                bounds
        }

        self.blurView.frame = bounds
""",
    "independent player layout",
)


bg = replace_once(
    bg,
    """    override func didMoveToWindow() {
        super.didMoveToWindow()

        guard let videoNode = self.videoNode else {
            return
        }

        if self.window != nil {
            videoNode.canAttachContent = true
            videoNode.play()
        } else {
            videoNode.pause()
            videoNode.canAttachContent = false
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
    "animated lifecycle",
)


bg = bg.replace(
    """                    self.animatedAvatarSource(
                        peer: peer,
                        item: avatarItem
                    )
""",
    """                    self.animatedAvatarSource(
                        peer: peer,
                        item: avatarItem,
                        isSettings: isSettings
                    )
""",
)

if bg.count(
    "isSettings: isSettings"
) < 2:
    raise RuntimeError(
        "[V11N] animated source call sites "
        "were not updated"
    )


bg = replace_once(
    bg,
    """    private func animatedAvatarSource(
        peer: EnginePeer,
        item: PeerInfoAvatarListItem?
    ) -> GhostBaseAnimatedMediaSource? {
""",
    """    private func animatedAvatarSource(
        peer: EnginePeer,
        item: PeerInfoAvatarListItem?,
        isSettings: Bool
    ) -> GhostBaseAnimatedMediaSource? {
""",
    "animated source signature",
)


bg = replace_once(
    bg,
    """        return GhostBaseAnimatedMediaSource(
            identity: identity,
            content: content
        )
""",
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
    "animated source return",
)


clear_start = bg.find(
    "    private func clearAnimatedMedia() {\n"
)

clear_end = bg.find(
    "    private func applyAnimatedMedia(",
    clear_start
)

if clear_start < 0 or clear_end <= clear_start:
    raise RuntimeError(
        "[V11N] animated clear boundaries missing"
    )

new_clear = """    private func clearAnimatedMedia() {
        self.animatedResourceDisposable.set(nil)

        if let videoNode = self.videoNode {
            videoNode.pause()
            videoNode.canAttachContent = false
            videoNode.view.removeFromSuperview()
        }

        self.videoNode = nil
        self.videoContent = nil

        if let player =
            self.independentVideoPlayer {

            player.pause()
            player.removeAllItems()
        }

        self.independentVideoLayer?
            .removeFromSuperlayer()

        self.independentVideoLooper =
            nil

        self.independentVideoPlayer =
            nil

        self.independentVideoLayer =
            nil

        self.currentVideoIdentity =
            nil
    }

"""

bg = (
    bg[:clear_start]
    + new_clear
    + bg[clear_end:]
)


apply_start = bg.find(
    "    private func applyAnimatedMedia(\n"
)

apply_end = bg.find(
    "    private func apply(\n",
    apply_start
)

if apply_start < 0 or apply_end <= apply_start:
    raise RuntimeError(
        "[V11N] animated apply boundaries missing"
    )

new_apply = """    private func applyAnimatedMedia(
        _ source: GhostBaseAnimatedMediaSource?
    ) {
        guard let source else {
            self.clearAnimatedMedia()
            return
        }

        if self.currentVideoIdentity
            == source.identity {

            if source.useIndependentPlayer {
                if self.independentVideoPlayer != nil {
                    return
                }
            } else if self.videoNode != nil {
                return
            }
        }

        self.clearAnimatedMedia()

        self.currentVideoIdentity =
            source.identity

        // Settings path is already correct in Build 99.
        // Preserve it verbatim.
        if !source.useIndependentPlayer {
            let mediaManager =
                self.context.sharedContext.mediaManager

            let videoNode =
                UniversalVideoNode(
                    context:
                        self.context,
                    postbox:
                        self.context.account.postbox,
                    audioSession:
                        mediaManager.audioSession,
                    manager:
                        mediaManager.universalVideoManager,
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

            return
        }

        // Normal PeerInfo:
        // never register a second UniversalVideo consumer.
        //
        // Reuse the downloaded Telegram MediaBox file directly.
        let mediaBox =
            self.context
                .account
                .postbox
                .mediaBox

        let fetchDisposable =
            mediaBox
                .fetchedResource(
                    source.resource,
                    parameters: nil
                )
                .start()

        let identity =
            source.identity

        let dataDisposable =
            (
                mediaBox.resourceData(
                    source.resource
                )
                |> filter {
                    $0.complete
                }
                |> take(1)
                |> deliverOnMainQueue
            )
            .start(
                next: {
                    [weak self]
                    data in

                    guard let self,
                          self.currentVideoIdentity
                            == identity
                    else {
                        return
                    }

                    let url =
                        URL(
                            fileURLWithPath:
                                data.path
                        )

                    let item =
                        AVPlayerItem(
                            url: url
                        )

                    let player =
                        AVQueuePlayer()

                    player.isMuted =
                        true

                    player.automaticallyWaitsToMinimizeStalling =
                        false

                    let looper =
                        AVPlayerLooper(
                            player:
                                player,
                            templateItem:
                                item
                        )

                    let layer =
                        AVPlayerLayer(
                            player:
                                player
                        )

                    layer.videoGravity =
                        .resizeAspectFill

                    layer.frame =
                        self.bounds

                    self.layer.insertSublayer(
                        layer,
                        below:
                            self.blurView.layer
                    )

                    self.independentVideoPlayer =
                        player

                    self.independentVideoLayer =
                        layer

                    self.independentVideoLooper =
                        looper

                    let play = {
                        guard
                            self.window != nil,
                            self.currentVideoIdentity
                                == identity
                        else {
                            return
                        }

                        player.playImmediately(
                            atRate: 1.0
                        )
                    }

                    if let startTimestamp =
                        source.startTimestamp,
                       startTimestamp > 0.0 {

                        player.seek(
                            to:
                                CMTime(
                                    seconds:
                                        startTimestamp,
                                    preferredTimescale:
                                        600
                                ),
                            toleranceBefore:
                                .zero,
                            toleranceAfter:
                                .zero,
                            completionHandler: {
                                _ in

                                play()
                            }
                        )
                    } else {
                        play()
                    }
                }
            )

        self.animatedResourceDisposable.set(
            ActionDisposable {
                fetchDisposable.dispose()
                dataDisposable.dispose()
            }
        )
    }

"""

bg = (
    bg[:apply_start]
    + new_apply
    + bg[apply_end:]
)


# ============================================================
# 2. AVATAR IMAGE:
#    RETURN TO TELEGRAM PIPELINE, NO GHOSTBASE AVATAR CACHE
# ============================================================

avatar_start = bg.find(
    "    private func avatarEntrySignal(\n"
)

avatar_end = bg.find(
    "    private func resourceEntrySignal(\n",
    avatar_start
)

if avatar_start < 0 or avatar_end <= avatar_start:
    raise RuntimeError(
        "[V11N] avatar signal boundaries missing"
    )

new_avatar = """    private func avatarEntrySignal(
        peer: EnginePeer,
        representation:
            TelegramMediaImageRepresentation,
        identity: String,
        fallback: UIColor
    ) -> Signal<
        GhostBaseProfileBackgroundCacheEntry?,
        NoError
    >? {
        // MARK: GhostBase v1.1N AVATARPIPELINE_FINAL1
        //
        // Telegram owns decoding/caching.
        // GhostBase never permanently caches a possibly
        // intermediate avatar UIImage.
        guard let signal =
            peerAvatarImage(
                account:
                    self.context.account,
                peerReference:
                    PeerReference(peer),
                authorOfMessage:
                    nil,
                representation:
                    representation,
                displayDimensions:
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
            )
        else {
            return nil
        }

        return signal
        |> deliverOn(
            Queue.concurrentDefaultQueue()
        )
        |> map {
            versions
            -> GhostBaseProfileBackgroundCacheEntry?
            in

            guard let image =
                versions?.0
            else {
                return nil
            }

            // Always refresh the persisted tone from
            // the actual decoded avatar. This repairs
            // any stale tone from earlier builds.
            let tint =
                Self.sampledTint(
                    from:
                        image,
                    fallback:
                        fallback
                )

            Self.storePersistentTint(
                tint,
                identity:
                    identity
            )

            return GhostBaseProfileBackgroundCacheEntry(
                image:
                    image,
                tint:
                    tint
            )
        }
    }

"""

bg = (
    bg[:avatar_start]
    + new_avatar
    + bg[avatar_end:]
)


avatar_case_start = bg.find(
    "        case let .avatar(\n",
    bg.find("    private func apply(\n")
)

telegram_case = bg.find(
    "        case .telegramTheme:",
    avatar_case_start
)

if avatar_case_start < 0 or telegram_case <= avatar_case_start:
    raise RuntimeError(
        "[V11N] avatar apply case missing"
    )

avatar_case = bg[
    avatar_case_start:
    telegram_case
]

cache_hit_start = avatar_case.find(
    """            if let cached =
                Self.imageCache.object(
                    forKey: cacheKey
                ) {
"""
)

cache_hit_end_token = """                return
            }

"""

if cache_hit_start >= 0:
    cache_hit_end = avatar_case.find(
        cache_hit_end_token,
        cache_hit_start
    )

    if cache_hit_end < 0:
        raise RuntimeError(
            "[V11N] avatar cache-hit block malformed"
        )

    cache_hit_end += len(
        cache_hit_end_token
    )

    avatar_case = (
        avatar_case[:cache_hit_start]
        + avatar_case[cache_hit_end:]
    )


avatar_case = avatar_case.replace(
    """                Self.imageCache.setObject(entry, forKey: cacheKey)
                self.imageView.image = entry.image
""",
    """                self.imageView.image = entry.image
""",
    1
)

if "Self.imageCache.setObject" in avatar_case:
    raise RuntimeError(
        "[V11N] avatar image cache write survived"
    )

bg = (
    bg[:avatar_case_start]
    + avatar_case
    + bg[telegram_case:]
)


# ============================================================
# 3. TRIANGLES:
#    REMOVE SECTION MASK, CLIP REAL CARD ROWS THEMSELVES
# ============================================================

sec = sec.replace(
    """    private let ghostBaseSectionMaskLayer =
        CAShapeLayer()
""",
    ""
)


frame_anchor = """            itemTransition.updateFrame(node: itemNode, frame: itemFrame)
"""

row_clip = """            itemTransition.updateFrame(node: itemNode, frame: itemFrame)

            // MARK: GhostBase v1.1N ROWCORNERS_FINAL1
            //
            // Do not mask the whole section.
            // Header/comment regions are not card backgrounds.
            // Clip only the actual first/last card rows.
            if self.ghostBaseGlassEnabled
                && hasCorners
                && !(item is PeerInfoScreenHeaderItem)
                && !(item is PeerInfoScreenCommentItem) {

                var corners:
                    CACornerMask = []

                if topItem == nil {
                    corners.insert(
                        .layerMinXMinYCorner
                    )
                    corners.insert(
                        .layerMaxXMinYCorner
                    )
                }

                if bottomItem == nil {
                    corners.insert(
                        .layerMinXMaxYCorner
                    )
                    corners.insert(
                        .layerMaxXMaxYCorner
                    )
                }

                if !corners.isEmpty {
                    itemNode.layer.cornerRadius =
                        16.0

                    itemNode.layer.maskedCorners =
                        corners

                    itemNode.layer.masksToBounds =
                        true
                } else {
                    itemNode.layer.cornerRadius =
                        0.0

                    itemNode.layer.maskedCorners =
                        []

                    itemNode.layer.masksToBounds =
                        false
                }
            } else {
                itemNode.layer.cornerRadius =
                    0.0

                itemNode.layer.maskedCorners =
                    []

                itemNode.layer.masksToBounds =
                    false
            }
"""

sec = replace_once(
    sec,
    frame_anchor,
    row_clip,
    "row clipping",
)


mask_start = sec.find(
    """            // MARK: GhostBase v1.1M SECTIONMASKFINAL1
"""
)

mask_end_anchor = """        transition.updateFrame(node: self.topSeparatorNode,"""

mask_end = sec.find(
    mask_end_anchor,
    mask_start
)

if mask_start < 0 or mask_end <= mask_start:
    raise RuntimeError(
        "[V11N] old section-wide mask block missing"
    )

replacement = """            // MARK: GhostBase v1.1N SECTIONMASK_REMOVED1
            //
            // Whole-section clipping caused the persistent
            // black wedges. Real row nodes now own corners.
            self.itemContainerNode.cornerRadius =
                0.0

            self.itemContainerNode.layer.mask =
                nil

            self.layer.mask =
                nil
        } else {
            self.itemContainerNode.layer.mask =
                nil

            self.layer.mask =
                nil
        }

"""

sec = (
    sec[:mask_start]
    + replacement
    + sec[mask_end:]
)


# ============================================================
# 4. HISTORY:
#    REAL VIEWPORT BELOW HEADER/TABS
# ============================================================

rep = replace_once(
    rep,
    """        self.currentSize = size
        self.currentPresentationData = presentationData

        transition.updateFrame(
            node: self.scrollNode,
            frame: CGRect(origin: .zero, size: size)
        )
        self.scrollNode.view.contentInset = UIEdgeInsets(
            top: topInset,
            left: 0.0,
            bottom: bottomInset,
            right: 0.0
        )
        self.scrollNode.view.scrollIndicatorInsets = self.scrollNode.view.contentInset
""",
    """        // MARK: GhostBase v1.1N HISTORYVIEWPORT_FINAL1
        //
        // The report scroll view no longer exists underneath
        // the profile header/tab bar. Offset clamping alone
        // cannot prevent content from being rendered there.
        let viewportTop =
            max(
                0.0,
                topInset
            )

        let viewportSize =
            CGSize(
                width:
                    size.width,
                height:
                    max(
                        0.0,
                        size.height
                        - viewportTop
                    )
            )

        self.currentSize =
            viewportSize

        self.currentPresentationData =
            presentationData

        transition.updateFrame(
            node:
                self.scrollNode,
            frame:
                CGRect(
                    origin:
                        CGPoint(
                            x: 0.0,
                            y: viewportTop
                        ),
                    size:
                        viewportSize
                )
        )

        self.scrollNode.view.clipsToBounds =
            true

        self.scrollNode.view.contentInset =
            UIEdgeInsets(
                top:
                    0.0,
                left:
                    0.0,
                bottom:
                    bottomInset,
                right:
                    0.0
            )

        self.scrollNode.view.scrollIndicatorInsets =
            self.scrollNode.view.contentInset
""",
    "history physical viewport",
)


# ============================================================
# 5. GIFTS:
#    STRONGER READABILITY SCRIM
# ============================================================

old_gift_alpha = """                alpha:
                    isDark
                    ? 0.16
                    : 0.20
"""

new_gift_alpha = """                // MARK: GhostBase v1.1N GIFTCONTRAST1
                //
                // Gift artwork and sender avatars can be almost white,
                // so this needs substantially more contrast than the
                // profile action-button masks.
                alpha:
                    isDark
                    ? 0.34
                    : 0.30
"""

if gifts.count(old_gift_alpha) != 1:
    raise RuntimeError(
        "[V11N] Gifts shared-glass alpha: "
        f"expected 1 found "
        f"{gifts.count(old_gift_alpha)}"
    )

gifts = gifts.replace(
    old_gift_alpha,
    new_gift_alpha,
    1
)


# ============================================================
# WRITE ONLY AFTER ALL ANCHORS PASSED
# ============================================================

for path, text in (
    (BG, bg),
    (SEC, sec),
    (REP, rep),
    (GIFTS, gifts),
):
    path.write_text(
        text,
        encoding="utf-8"
    )


print("[V11N] applied")
print("  avatar source restored to Telegram decoder")
print("  no GhostBase avatar UIImage cache")
print("  Settings video path preserved")
print("  normal PeerInfo background uses independent AVPlayer")
print("  whole-section triangle mask removed")
print("  first/last real card rows own rounded clipping")
print("  History has a physical viewport below header/tabs")
print("  Gifts material darkened for readability")
