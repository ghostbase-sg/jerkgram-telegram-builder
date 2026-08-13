#!/usr/bin/env python3

import os
from pathlib import Path

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

NODE = (
    ROOT
    / "submodules/TelegramUI/Sources/"
      "OverlayAudioPlayerControllerNode.swift"
)

if not NODE.is_file():
    raise RuntimeError(
        f"[V11M-B2] missing: {NODE}"
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
            f"[V11M-B2] {label}: "
            f"expected 1 found {count}"
        )

    return text.replace(
        old,
        new,
        1,
    )


text = NODE.read_text(
    encoding="utf-8"
)

if "GhostBase v1.1M MUSICPLAYERGLASS1" in text:
    print("[V11M-B2] already materialized")
    raise SystemExit(0)


text = replace_once(
    text,
    """import Foundation
import UIKit
""",
    """import Foundation
import UIKit
import Postbox
""",
    "Postbox import",
)


class_anchor = (
    "final class OverlayAudioPlayerControllerNode: "
    "ViewControllerTracingNode, ASGestureRecognizerDelegate {"
)


helper = r'''// MARK: GhostBase v1.1M MUSICPLAYERGLASS1
//
// Static profile-aware background for Saved Music.
//
// Important:
// - one fullscreen blur only;
// - no blur per track/cell;
// - MediaBox remains source/cache owner;
// - ordinary Telegram audio players remain untouched.
//
private final class GhostBaseMusicProfileBackdropView: UIView {
    private let context: AccountContext

    private let imageView =
        UIImageView()

    private let blurView =
        UIVisualEffectView(
            effect: nil
        )

    private let tintView =
        UIView()

    private let resourceDisposable =
        MetaDisposable()

    private var currentIdentity:
        String?

    init(
        context: AccountContext
    ) {
        self.context =
            context

        super.init(
            frame: .zero
        )

        self.isUserInteractionEnabled =
            false

        self.clipsToBounds =
            true

        self.imageView.contentMode =
            .scaleAspectFill

        self.imageView.clipsToBounds =
            true

        self.addSubview(
            self.imageView
        )

        self.blurView
            .isUserInteractionEnabled =
            false

        self.addSubview(
            self.blurView
        )

        self.tintView
            .isUserInteractionEnabled =
            false

        self.addSubview(
            self.tintView
        )
    }

    required init?(
        coder: NSCoder
    ) {
        preconditionFailure()
    }

    deinit {
        self.resourceDisposable
            .dispose()
    }

    override func layoutSubviews() {
        super.layoutSubviews()

        self.imageView.frame =
            self.bounds

        self.blurView.frame =
            self.bounds

        self.tintView.frame =
            self.bounds
    }

    func clear() {
        self.currentIdentity =
            nil

        self.resourceDisposable
            .set(nil)

        self.imageView.image =
            nil

        self.blurView.effect =
            nil

        self.tintView
            .backgroundColor =
            .clear

        self.backgroundColor =
            .clear

        self.isHidden =
            true
    }

    func update(
        peer: EnginePeer?,
        personalWallpaper:
            TelegramWallpaper?,
        presentationData:
            PresentationData
    ) {
        guard let settings =
            GhostBaseProfileBlurSettings
                .loadEnabled()
        else {
            self.clear()
            return
        }

        self.isHidden =
            false

        let isDark =
            presentationData
                .theme
                .overallDarkAppearance

        self.blurView.effect =
            UIBlurEffect(
                style:
                    isDark
                    ? .systemUltraThinMaterialDark
                    : .systemUltraThinMaterialLight
            )

        self.tintView.backgroundColor =
            UIColor(
                white:
                    isDark
                    ? 0.0
                    : 1.0,
                alpha:
                    settings.reducedBlur
                    ? 0.035
                    : 0.075
            )

        // Own Settings/profile must not inherit
        // an unrelated chat wallpaper.
        let canUseWallpaper =
            peer?.id
            != self.context
                .account
                .peerId

        if canUseWallpaper,
           let personalWallpaper {

            self.applyWallpaper(
                personalWallpaper,
                identity:
                    "personal:"
                    + String(
                        reflecting:
                            personalWallpaper
                    ),
                presentationData:
                    presentationData
            )

            return
        }

        if canUseWallpaper,
           presentationData
                .chatWallpaper
            != presentationData
                .theme
                .chat
                .defaultWallpaper {

            let wallpaper =
                presentationData
                    .chatWallpaper

            self.applyWallpaper(
                wallpaper,
                identity:
                    "global:"
                    + String(
                        reflecting:
                            wallpaper
                    ),
                presentationData:
                    presentationData
            )

            return
        }

        guard let peer else {
            self.applyFallback(
                presentationData:
                    presentationData
            )

            return
        }

        // Preference ON:
        // avatar -> Premium fallback.
        if settings.avatarBlurInProfile,
           let representation =
            peer
                .profileImageRepresentations
                .last {

            self.applyResource(
                representation.resource,
                identity:
                    "avatar:"
                    + String(
                        peer.id.toInt64()
                    )
                    + ":"
                    + String(
                        describing:
                            representation
                                .resource
                                .id
                    ),
                fallback:
                    presentationData
                        .theme
                        .list
                        .itemBlocksBackgroundColor
            )

            return
        }

        // Premium Star Gift profile colors.
        if let status =
            peer.emojiStatus,
           case let .starGift(
                _,
                _,
                _,
                _,
                _,
                innerColor,
                outerColor,
                _,
                _
           ) = status.content {

            self.applyGradient(
                colors: [
                    UIColor(
                        rgb:
                            UInt32(
                                bitPattern:
                                    innerColor
                            )
                    ),
                    UIColor(
                        rgb:
                            UInt32(
                                bitPattern:
                                    outerColor
                            )
                    )
                ],
                identity:
                    "gift:"
                    + String(innerColor)
                    + ":"
                    + String(outerColor)
            )

            return
        }

        // Premium/profile color.
        if let profileColor =
            peer.effectiveProfileColor {

            let colors =
                self.context
                    .peerNameColors
                    .getProfile(
                        profileColor,
                        dark:
                            presentationData
                                .theme
                                .overallDarkAppearance
                    )

            self.applyGradient(
                colors: [
                    colors.main,
                    colors.secondary
                        ?? colors.main
                ],
                identity:
                    "profile:"
                    + String(
                        describing:
                            profileColor
                    )
                    + ":"
                    + String(isDark)
            )

            return
        }

        // Preference OFF fallback:
        // Premium unavailable -> avatar.
        if let representation =
            peer
                .profileImageRepresentations
                .last {

            self.applyResource(
                representation.resource,
                identity:
                    "avatar:"
                    + String(
                        peer.id.toInt64()
                    )
                    + ":"
                    + String(
                        describing:
                            representation
                                .resource
                                .id
                    ),
                fallback:
                    presentationData
                        .theme
                        .list
                        .itemBlocksBackgroundColor
            )

            return
        }

        self.applyFallback(
            presentationData:
                presentationData
        )
    }

    private func applyFallback(
        presentationData:
            PresentationData
    ) {
        let identity =
            "theme:"
            + String(
                presentationData
                    .theme
                    .overallDarkAppearance
            )

        guard
            self.currentIdentity
            != identity
        else {
            return
        }

        self.currentIdentity =
            identity

        self.resourceDisposable
            .set(nil)

        self.imageView.image =
            nil

        self.backgroundColor =
            presentationData
                .theme
                .list
                .itemBlocksBackgroundColor
    }

    private func applyWallpaper(
        _ wallpaper:
            TelegramWallpaper,
        identity: String,
        presentationData:
            PresentationData
    ) {
        switch wallpaper {
        case let .image(
            representations,
            _
        ):
            if let representation =
                largestImageRepresentation(
                    representations
                ) {

                self.applyResource(
                    representation
                        .resource,
                    identity:
                        identity,
                    fallback:
                        presentationData
                            .theme
                            .list
                            .itemBlocksBackgroundColor
                )
            } else {
                self.applyGeneratedWallpaper(
                    wallpaper,
                    identity:
                        identity,
                    fallback:
                        presentationData
                            .theme
                            .list
                            .itemBlocksBackgroundColor
                )
            }

        case let .file(file):
            if wallpaper.isPattern {
                self.applyGeneratedWallpaper(
                    wallpaper,
                    identity:
                        identity,
                    fallback:
                        presentationData
                            .theme
                            .list
                            .itemBlocksBackgroundColor
                )
            } else {
                self.applyResource(
                    file.file.resource,
                    identity:
                        identity,
                    fallback:
                        presentationData
                            .theme
                            .list
                            .itemBlocksBackgroundColor
                )
            }

        default:
            self.applyGeneratedWallpaper(
                wallpaper,
                identity:
                    identity,
                fallback:
                    presentationData
                        .theme
                        .list
                        .itemBlocksBackgroundColor
            )
        }
    }

    private func applyGeneratedWallpaper(
        _ wallpaper:
            TelegramWallpaper,
        identity: String,
        fallback: UIColor
    ) {
        guard
            self.currentIdentity
            != identity
        else {
            return
        }

        self.currentIdentity =
            identity

        self.resourceDisposable
            .set(nil)

        let colors =
            Self.wallpaperColors(
                wallpaper
            )

        self.imageView.image =
            Self.generatedImage(
                colors:
                    colors.map {
                        UIColor(
                            argb: $0
                        )
                    },
                fallback:
                    fallback
            )

        self.backgroundColor =
            fallback
    }

    private func applyGradient(
        colors: [UIColor],
        identity: String
    ) {
        guard
            self.currentIdentity
            != identity
        else {
            return
        }

        self.currentIdentity =
            identity

        self.resourceDisposable
            .set(nil)

        self.imageView.image =
            Self.generatedImage(
                colors:
                    colors,
                fallback:
                    colors.first
                    ?? .black
            )

        self.backgroundColor =
            colors.first
            ?? .black
    }

    private func applyResource(
        _ resource:
            MediaResource,
        identity: String,
        fallback: UIColor
    ) {
        guard
            self.currentIdentity
            != identity
        else {
            return
        }

        self.currentIdentity =
            identity

        self.imageView.image =
            nil

        self.backgroundColor =
            fallback

        let mediaBox =
            self.context
                .account
                .postbox
                .mediaBox

        let fetchDisposable =
            mediaBox
                .fetchedResource(
                    resource,
                    parameters: nil
                )
                .start()

        let dataDisposable =
            (
                mediaBox
                    .resourceData(
                        resource
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

                    guard
                        let self,
                        self.currentIdentity
                            == identity
                    else {
                        return
                    }

                    guard let image =
                        UIImage(
                            contentsOfFile:
                                data.path
                        )
                    else {
                        return
                    }

                    self.imageView
                        .image =
                        image
                }
            )

        self.resourceDisposable
            .set(
                ActionDisposable {
                    fetchDisposable
                        .dispose()

                    dataDisposable
                        .dispose()
                }
            )
    }

    private static func wallpaperColors(
        _ wallpaper:
            TelegramWallpaper
    ) -> [UInt32] {
        switch wallpaper {
        case let .color(value):
            return [value]

        case let .gradient(value):
            return value.colors

        case let .image(
            _,
            settings
        ):
            return settings.colors

        case let .file(value):
            return value
                .settings
                .colors

        case .builtin,
             .emoticon:
            return []
        }
    }

    private static func generatedImage(
        colors: [UIColor],
        fallback: UIColor
    ) -> UIImage? {
        let resolved:
            [UIColor]

        if colors.isEmpty {
            resolved = [
                fallback,
                fallback
            ]
        } else if colors.count == 1 {
            resolved = [
                colors[0],
                colors[0]
            ]
        } else {
            resolved =
                colors
        }

        return generateImage(
            CGSize(
                width: 64.0,
                height: 64.0
            ),
            contextGenerator: {
                size,
                context in

                let colorSpace =
                    CGColorSpaceCreateDeviceRGB()

                var locations:
                    [CGFloat] =
                    resolved
                        .indices
                        .map {
                            index in

                            if resolved.count
                                <= 1 {

                                return 0.0
                            }

                            return CGFloat(
                                index
                            )
                            / CGFloat(
                                resolved.count
                                - 1
                            )
                        }

                guard let gradient =
                    CGGradient(
                        colorsSpace:
                            colorSpace,
                        colors:
                            resolved
                                .map {
                                    $0.cgColor
                                }
                                as CFArray,
                        locations:
                            &locations
                    )
                else {
                    context
                        .setFillColor(
                            fallback
                                .cgColor
                        )

                    context.fill(
                        CGRect(
                            origin:
                                .zero,
                            size:
                                size
                        )
                    )

                    return
                }

                context
                    .drawLinearGradient(
                        gradient,
                        start:
                            CGPoint(
                                x: 0.0,
                                y: 0.0
                            ),
                        end:
                            CGPoint(
                                x:
                                    size.width,
                                y:
                                    size.height
                            ),
                        options: [
                            .drawsBeforeStartLocation,
                            .drawsAfterEndLocation
                        ]
                    )
            },
            opaque: true,
            scale: 1.0
        )
    }
}

'''


text = replace_once(
    text,
    class_anchor,
    helper + class_anchor,
    "music backdrop helper",
)


text = replace_once(
    text,
    """    private var peer: EnginePeer?
""",
    """    private var peer: EnginePeer?
    private var ghostBaseWallpaper: TelegramWallpaper?
    private var ghostBaseBackdropView: GhostBaseMusicProfileBackdropView?
""",
    "music state",
)


text = replace_once(
    text,
    """        super.init()
        
        self.backgroundColor = nil
""",
    """        super.init()

        if let playlistLocation =
            self.playlistLocation
                as? PeerMessagesPlaylistLocation,
           case .savedMusic =
                playlistLocation,
           GhostBaseProfileBlurSettings
                .loadEnabled() != nil {

            let ghostBaseBackdropView =
                GhostBaseMusicProfileBackdropView(
                    context:
                        context
                )

            self.ghostBaseBackdropView =
                ghostBaseBackdropView

            self.view.insertSubview(
                ghostBaseBackdropView,
                at: 0
            )
        }
        
        self.backgroundColor = nil
""",
    "music backdrop init",
)


text = replace_once(
    text,
    """        let peer: Signal<EnginePeer?, NoError>
        if let playlistLocation = self.playlistLocation as? PeerMessagesPlaylistLocation, case let .savedMusic(savedMusicContext, _, _) = playlistLocation {
            peer = context.engine.data.get(TelegramEngine.EngineData.Item.Peer.Peer(id: savedMusicContext.peerId))
        } else {
            peer = .single(nil)
        }
        
        self.dataDisposable = combineLatest(
            queue: Queue.mainQueue(),
            context.engine.peers.savedMusicIds(),
            copyProtectionEnabled,
            peer
        ).start(next: { [weak self] savedIds, copyProtectionEnabled, peer in
""",
    """        let peer:
            Signal<
                EnginePeer?,
                NoError
            >

        let ghostBaseWallpaper:
            Signal<
                TelegramWallpaper?,
                NoError
            >

        if let playlistLocation =
            self.playlistLocation
                as? PeerMessagesPlaylistLocation,
           case let .savedMusic(
                savedMusicContext,
                _,
                _
           ) = playlistLocation {

            peer =
                context
                    .engine
                    .data
                    .get(
                        TelegramEngine
                            .EngineData
                            .Item
                            .Peer
                            .Peer(
                                id:
                                    savedMusicContext
                                        .peerId
                            )
                    )

            ghostBaseWallpaper =
                context
                    .account
                    .postbox
                    .peerView(
                        id:
                            savedMusicContext
                                .peerId
                    )
                |> map {
                    view
                    -> TelegramWallpaper?
                    in

                    if let cachedData =
                        view.cachedData
                            as? CachedUserData {

                        return cachedData
                            .wallpaper
                    } else if let cachedData =
                        view.cachedData
                            as? CachedChannelData {

                        return cachedData
                            .wallpaper
                    } else {
                        return nil
                    }
                }
        } else {
            peer =
                .single(nil)

            ghostBaseWallpaper =
                .single(nil)
        }

        let ghostBaseProfileData =
            combineLatest(
                peer,
                ghostBaseWallpaper
            )
        
        self.dataDisposable =
            combineLatest(
                queue:
                    Queue.mainQueue(),
                context
                    .engine
                    .peers
                    .savedMusicIds(),
                copyProtectionEnabled,
                ghostBaseProfileData
            )
            .start(
                next: {
                    [weak self]
                    savedIds,
                    copyProtectionEnabled,
                    ghostBaseProfileData in

                    let (
                        peer,
                        ghostBaseWallpaper
                    ) =
                        ghostBaseProfileData
""",
    "music peer/wallpaper signal",
)


text = replace_once(
    text,
    """            self.controlsNode.forceCopyProtected.set(copyProtectionEnabled)
            self.peer = peer
            
            let transition: ContainedViewLayoutTransition = isFirstTime ? .immediate : .animated(duration: 0.5, curve: .spring)
""",
    """            self.controlsNode
                .forceCopyProtected
                .set(
                    copyProtectionEnabled
                )

            self.peer =
                peer

            self.ghostBaseWallpaper =
                ghostBaseWallpaper

            self.ghostBaseBackdropView?
                .update(
                    peer:
                        peer,
                    personalWallpaper:
                        ghostBaseWallpaper,
                    presentationData:
                        self.presentationData
                )

            self.updateGhostBaseMusicSurfaces()
            
            let transition: ContainedViewLayoutTransition = isFirstTime ? .immediate : .animated(duration: 0.5, curve: .spring)
""",
    "music source update",
)


anchor = (
    "    func updatePresentationData("
    "_ presentationData: PresentationData) {"
)


methods = r'''    private var isGhostBaseProfileMusicActive:
        Bool {

        guard
            GhostBaseProfileBlurSettings
                .loadEnabled()
            != nil
        else {
            return false
        }

        if let playlistLocation =
            self.playlistLocation
                as? PeerMessagesPlaylistLocation,
           case .savedMusic =
            playlistLocation {

            return true
        }

        return false
    }

    private func updateGhostBaseMusicSurfaces() {
        let active =
            self.isGhostBaseProfileMusicActive

        self.ghostBaseBackdropView?
            .isHidden =
            !active

        if active {
            let isDark =
                self.presentationData
                    .theme
                    .overallDarkAppearance

            // Keep the peer scene clearly visible.
            self.dimNode.backgroundColor =
                UIColor(
                    white: 0.0,
                    alpha: 0.10
                )

            // List itself already uses Telegram
            // systemStyle .glass.
            self.historyBackgroundContentNode
                .backgroundColor =
                .clear

            let glassColor =
                UIColor(
                    white:
                        isDark
                        ? 0.0
                        : 1.0,
                    alpha:
                        isDark
                        ? 0.14
                        : 0.18
                )

            self.historyFrameLeftOverlayNode
                .backgroundColor =
                glassColor

            self.historyFrameRightOverlayNode
                .backgroundColor =
                glassColor

            self.historyFrameTopOverlayNode
                .backgroundColor =
                glassColor

            // Official generated corners contain
            // an opaque theme-colored surface.
            self.historyFrameTopMaskNode
                .alpha =
                0.0

            self.controlsNode
                .hasPlainBackground =
                false
        } else {
            // Exact Official fallback.
            self.dimNode.backgroundColor =
                UIColor(
                    white: 0.0,
                    alpha: 0.5
                )

            self.historyBackgroundContentNode
                .backgroundColor =
                self.hasAnyHistoryMessages
                    == true
                ? self.presentationData
                    .theme
                    .list
                    .itemModalBlocksBackgroundColor
                : self.presentationData
                    .theme
                    .list
                    .modalPlainBackgroundColor

            self.historyFrameLeftOverlayNode
                .backgroundColor =
                self.hasAnyHistoryMessages
                    == true
                ? self.presentationData
                    .theme
                    .list
                    .modalBlocksBackgroundColor
                : self.presentationData
                    .theme
                    .list
                    .modalPlainBackgroundColor

            self.historyFrameRightOverlayNode
                .backgroundColor =
                self.hasAnyHistoryMessages
                    == true
                ? self.presentationData
                    .theme
                    .list
                    .modalBlocksBackgroundColor
                : self.presentationData
                    .theme
                    .list
                    .modalPlainBackgroundColor

            self.historyFrameTopOverlayNode
                .backgroundColor =
                self.hasAnyHistoryMessages
                    == true
                ? self.presentationData
                    .theme
                    .list
                    .modalBlocksBackgroundColor
                : self.presentationData
                    .theme
                    .list
                    .modalPlainBackgroundColor

            self.historyFrameTopMaskNode
                .alpha =
                1.0
        }
    }

'''


text = replace_once(
    text,
    anchor,
    methods + anchor,
    "music surface helpers",
)


old_presentation = """    func updatePresentationData(_ presentationData: PresentationData) {
        self.presentationData = presentationData
        
        self.historyBackgroundContentNode.backgroundColor = self.hasAnyHistoryMessages == true ? self.presentationData.theme.list.itemModalBlocksBackgroundColor : self.presentationData.theme.list.modalPlainBackgroundColor
        self.historyFrameLeftOverlayNode.backgroundColor = self.hasAnyHistoryMessages == true ? self.presentationData.theme.list.modalBlocksBackgroundColor : self.presentationData.theme.list.modalPlainBackgroundColor
        self.historyFrameRightOverlayNode.backgroundColor = self.hasAnyHistoryMessages == true ? self.presentationData.theme.list.modalBlocksBackgroundColor : self.presentationData.theme.list.modalPlainBackgroundColor
        self.historyFrameTopOverlayNode.backgroundColor = self.hasAnyHistoryMessages == true ? self.presentationData.theme.list.modalBlocksBackgroundColor : self.presentationData.theme.list.modalPlainBackgroundColor
        self.historyFrameTopMaskNode.image = generateCornersImage(theme: self.presentationData.theme)
        
        self.collapseNode.setImage(generateCollapseIcon(theme: self.presentationData.theme), for: [])
        
        self.controlsNode.updatePresentationData(self.presentationData)
    }
"""


new_presentation = """    func updatePresentationData(_ presentationData: PresentationData) {
        self.presentationData = presentationData

        self.historyFrameTopMaskNode.image =
            generateCornersImage(
                theme:
                    self.presentationData
                        .theme
            )

        self.ghostBaseBackdropView?
            .update(
                peer:
                    self.peer,
                personalWallpaper:
                    self.ghostBaseWallpaper,
                presentationData:
                    presentationData
            )

        self.updateGhostBaseMusicSurfaces()
        
        self.collapseNode.setImage(generateCollapseIcon(theme: self.presentationData.theme), for: [])
        
        self.controlsNode.updatePresentationData(self.presentationData)
    }
"""


text = replace_once(
    text,
    old_presentation,
    new_presentation,
    "presentation surfaces",
)


text = replace_once(
    text,
    """        self.controlsNode.hasPlainBackground = !self.historyNode.hasAnyMessages
""",
    """        if self.isGhostBaseProfileMusicActive {
            self.controlsNode.hasPlainBackground =
                false
        } else {
            self.controlsNode.hasPlainBackground =
                !self.historyNode
                    .hasAnyMessages
        }
""",
    "controls glass",
)


text = replace_once(
    text,
    """        transition.updateFrame(node: self.dimNode, frame: CGRect(origin: CGPoint(), size: layout.size))
        transition.updateFrameAsPositionAndBounds(node: self.containerContainingNode, frame: CGRect(origin: CGPoint(), size: layout.size))
""",
    """        transition.updateFrame(node: self.dimNode, frame: CGRect(origin: CGPoint(), size: layout.size))

        self.ghostBaseBackdropView?
            .frame =
            CGRect(
                origin: .zero,
                size: layout.size
            )

        self.updateGhostBaseMusicSurfaces()

        transition.updateFrameAsPositionAndBounds(node: self.containerContainingNode, frame: CGRect(origin: CGPoint(), size: layout.size))
""",
    "music backdrop layout",
)


NODE.write_text(
    text,
    encoding="utf-8",
)

print("[V11M-B2] applied")
print("  Saved Music gets peer-aware GhostBase scene")
print("  personal/global wallpaper -> avatar/Premium")
print("  own profile skips chat wallpaper")
print("  MediaBox complete resources only")
print("  player history/frame surfaces are translucent")
print("  ordinary audio players remain Official")
