#!/usr/bin/env python3
import os
from pathlib import Path

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

P = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources"

BG = P / "GhostBaseProfileFullscreenBackground.swift"
HDR = P / "PeerInfoHeaderNode.swift"
SEC = P / "PeerInfoScreenItemSectionContainerNode.swift"
PANE = P / "PeerInfoPaneContainerNode.swift"
SCR = P / "PeerInfoScreen.swift"
REP = P / "GhostBaseProfileReportPaneNode.swift"

SETTINGS = (
    ROOT
    / "submodules/SettingsUI/Sources/GhostBase/"
      "GhostBaseSettingsController.swift"
)

GLASS_CANDIDATES = [
    ROOT / "submodules/Display/Source/GhostBaseGlass.swift",
    ROOT / "submodules/Display/Sources/GhostBaseGlass.swift",
]

GLASS = next(
    (path for path in GLASS_CANDIDATES if path.is_file()),
    None
)

CALL_CONTROLLER = (
    ROOT
    / "submodules/TelegramCallsUI/Sources/"
      "CallControllerNodeV2.swift"
)

COMPONENTS_ROOT = (
    ROOT
    / "submodules/TelegramUI/Components"
)


def component_source(
    module_name: str,
    filename: str
) -> Path:
    direct = (
        COMPONENTS_ROOT
        / module_name
        / "Sources"
        / filename
    )

    if direct.is_file():
        return direct

    for module_dir in COMPONENTS_ROOT.rglob(
        module_name
    ):
        if not module_dir.is_dir():
            continue

        candidate = (
            module_dir
            / "Sources"
            / filename
        )

        if candidate.is_file():
            return candidate

    return direct


PRIVATE_CALL = component_source(
    "CallScreen",
    "PrivateCallScreen.swift"
)

COVER = component_source(
    "PeerInfoCoverComponent",
    "PeerInfoCoverComponent.swift"
)

GIFT = component_source(
    "GiftItemComponent",
    "GiftItemComponent.swift"
)

required = [
    BG,
    HDR,
    SEC,
    PANE,
    SCR,
    REP,
    SETTINGS,
    CALL_CONTROLLER,
    PRIVATE_CALL,
    COVER,
    GIFT,
]

if GLASS is None:
    raise RuntimeError(
        "[V11L] GhostBaseGlass.swift not found"
    )

required.append(GLASS)

for path in required:
    if not path.is_file():
        raise RuntimeError(
            f"[V11L] missing: {path}"
        )


def replace_once(
    text: str,
    old: str,
    new: str,
    label: str
) -> str:
    count = text.count(old)

    if count != 1:
        raise RuntimeError(
            f"[V11L] {label}: "
            f"expected 1 found {count}"
        )

    return text.replace(
        old,
        new,
        1
    )


def insert_after_once(
    text: str,
    anchor: str,
    addition: str,
    label: str
) -> str:
    count = text.count(anchor)

    if count != 1:
        raise RuntimeError(
            f"[V11L] {label}: "
            f"expected anchor once found {count}"
        )

    return text.replace(
        anchor,
        anchor + addition,
        1
    )


bg = BG.read_text(encoding="utf-8")
hdr = HDR.read_text(encoding="utf-8")
sec = SEC.read_text(encoding="utf-8")
pane = PANE.read_text(encoding="utf-8")
scr = SCR.read_text(encoding="utf-8")
rep = REP.read_text(encoding="utf-8")
settings = SETTINGS.read_text(encoding="utf-8")
glass = GLASS.read_text(encoding="utf-8")
cover = COVER.read_text(encoding="utf-8")
gift = GIFT.read_text(encoding="utf-8")
call = CALL_CONTROLLER.read_text(encoding="utf-8")
private_call = PRIVATE_CALL.read_text(encoding="utf-8")

if "GhostBase v1.1L PROFILESTATE1" in bg:
    print("[V11L] already materialized")
    raise SystemExit(0)


# ============================================================
# 1. SETTINGS / RUNTIME
# ============================================================

glass = replace_once(
    glass,
    '''    public static let avatarBlurKey = "GhostBase.ProfileBlur.Avatar"
    public static let tintKey = "GhostBase.ProfileBlur.Tint"
    public static let reducedKey = "GhostBase.ProfileBlur.Reduced"

    public let avatarBlurInProfile: Bool
    public let tintEnabled: Bool
    public let reducedBlur: Bool
''',
    '''    public static let avatarBlurKey = "GhostBase.ProfileBlur.Avatar"
    public static let animatedKey = "GhostBase.ProfileBlur.Animated"
    public static let tintKey = "GhostBase.ProfileBlur.Tint"
    public static let reducedKey = "GhostBase.ProfileBlur.Reduced"

    public let avatarBlurInProfile: Bool
    public let animatedBackgroundEnabled: Bool
    public let tintEnabled: Bool
    public let reducedBlur: Bool
''',
    "Glass animated setting fields"
)

glass = replace_once(
    glass,
    '''        return GhostBaseProfileBlurSettings(
            avatarBlurInProfile: defaults.object(forKey: self.avatarBlurKey) as? Bool ?? true,
            tintEnabled: defaults.object(forKey: self.tintKey) as? Bool ?? true,
            reducedBlur: defaults.object(forKey: self.reducedKey) as? Bool ?? false
        )
''',
    '''        return GhostBaseProfileBlurSettings(
            avatarBlurInProfile: defaults.object(forKey: self.avatarBlurKey) as? Bool ?? true,
            animatedBackgroundEnabled: defaults.object(forKey: self.animatedKey) as? Bool ?? true,
            tintEnabled: defaults.object(forKey: self.tintKey) as? Bool ?? true,
            reducedBlur: defaults.object(forKey: self.reducedKey) as? Bool ?? false
        )
''',
    "Glass animated setting load"
)

settings = replace_once(
    settings,
    '''    static let profileAvatarBlur = "GhostBase.ProfileBlur.Avatar"
    static let profileBlurTint = "GhostBase.ProfileBlur.Tint"
''',
    '''    static let profileAvatarBlur = "GhostBase.ProfileBlur.Avatar"
    static let profileAnimatedBackground = "GhostBase.ProfileBlur.Animated"
    static let profileBlurTint = "GhostBase.ProfileBlur.Tint"
''',
    "Settings animated key"
)

settings = replace_once(
    settings,
    '''    var profileAvatarBlur: Bool
    var profileBlurTint: Bool
''',
    '''    var profileAvatarBlur: Bool
    var profileAnimatedBackground: Bool
    var profileBlurTint: Bool
''',
    "Settings animated state"
)

settings = replace_once(
    settings,
    '''            profileAvatarBlur: ghostBaseBool(GhostBaseKey.profileAvatarBlur, defaultValue: true),
            profileBlurTint: ghostBaseBool(GhostBaseKey.profileBlurTint, defaultValue: true),
''',
    '''            profileAvatarBlur: ghostBaseBool(GhostBaseKey.profileAvatarBlur, defaultValue: true),
            profileAnimatedBackground: ghostBaseBool(GhostBaseKey.profileAnimatedBackground, defaultValue: true),
            profileBlurTint: ghostBaseBool(GhostBaseKey.profileBlurTint, defaultValue: true),
''',
    "Settings animated load"
)

settings = replace_once(
    settings,
    '''        UserDefaults.standard.set(self.profileAvatarBlur, forKey: GhostBaseKey.profileAvatarBlur)
        UserDefaults.standard.set(self.profileBlurTint, forKey: GhostBaseKey.profileBlurTint)
''',
    '''        UserDefaults.standard.set(self.profileAvatarBlur, forKey: GhostBaseKey.profileAvatarBlur)
        UserDefaults.standard.set(self.profileAnimatedBackground, forKey: GhostBaseKey.profileAnimatedBackground)
        UserDefaults.standard.set(self.profileBlurTint, forKey: GhostBaseKey.profileBlurTint)
''',
    "Settings animated save"
)

old_appearance_candidates = [
'''            .toggle(0, 2, GhostBaseKey.profileAvatarBlur, "Предпочитать аватар как фон", state.profileAvatarBlur),
            .toggle(0, 3, GhostBaseKey.profileBlurTint, "Цветовой tint", state.profileBlurTint),
            .toggle(0, 4, GhostBaseKey.profileBlurReduced, "Облегчённое размытие", state.profileBlurReduced),
            .info(0, "При выключенном главном тумблере профиль полностью использует штатный интерфейс Telegram."),
''',
'''            .toggle(0, 2, GhostBaseKey.profileAvatarBlur, "Размытие аватара в профиле", state.profileAvatarBlur),
            .toggle(0, 3, GhostBaseKey.profileBlurTint, "Цветовой tint", state.profileBlurTint),
            .toggle(0, 4, GhostBaseKey.profileBlurReduced, "Облегчённое размытие", state.profileBlurReduced),
            .info(0, "При выключенном главном тумблере профиль полностью использует штатный интерфейс Telegram."),
'''
]

new_appearance = '''            .toggle(0, 2, GhostBaseKey.profileAvatarBlur, "Предпочитать аватар как фон", state.profileAvatarBlur),
            .toggle(0, 3, GhostBaseKey.profileAnimatedBackground, "Анимированный фон", state.profileAnimatedBackground),
            .toggle(0, 4, GhostBaseKey.profileBlurTint, "Цветовой tint", state.profileBlurTint),
            .toggle(0, 5, GhostBaseKey.profileBlurReduced, "Облегчённое размытие", state.profileBlurReduced),
            .info(0, "Видеоаватар зацикливается и использует кэш Telegram. В режиме энергосбережения или облегчённого размытия используется статический кадр."),
            .info(0, "При выключенном главном тумблере профиль полностью использует штатный интерфейс Telegram."),
'''

matched = False

for old in old_appearance_candidates:
    if old in settings:
        settings = settings.replace(
            old,
            new_appearance,
            1
        )
        matched = True
        break

if not matched:
    raise RuntimeError(
        "[V11L] Settings appearance block not found"
    )

settings = replace_once(
    settings,
    '''            case GhostBaseKey.profileAvatarBlur:
                updated.profileAvatarBlur = value
            case GhostBaseKey.profileBlurTint:
''',
    '''            case GhostBaseKey.profileAvatarBlur:
                updated.profileAvatarBlur = value
            case GhostBaseKey.profileAnimatedBackground:
                updated.profileAnimatedBackground = value
            case GhostBaseKey.profileBlurTint:
''',
    "Settings animated action"
)


# ============================================================
# 2. PROFILE BACKGROUND STATE + ANIMATED VIDEO AVATAR
# ============================================================

bg = insert_after_once(
    bg,
    "import PhotoResources\n",
    '''import PeerInfoAvatarListNode
import UniversalMediaPlayer
import TelegramUniversalVideoContent
import GalleryUI
''',
    "Background animated imports"
)

bg = replace_once(
    bg,
    '''private struct GhostBaseProfileBackgroundStateKey: Equatable {
    let peerId: Int64?
    let kind: GhostBaseProfileBackgroundSourceKind
    let wallpaper: TelegramWallpaper?
    let avatarResourceId: String?
    let premiumIdentity: String?
    let themeIdentity: ObjectIdentifier
}

private enum GhostBaseProfileBackgroundSource {
    case wallpaper(TelegramWallpaper, GhostBaseProfileBackgroundSourceKind)
    case premium(UIColor, UIColor, String)
    case avatar(EnginePeer, TelegramMediaImageRepresentation, String)
    case telegramTheme
}
''',
    '''private struct GhostBaseProfileBackgroundStateKey: Equatable {
    let peerId: Int64?
    let kind: GhostBaseProfileBackgroundSourceKind
    let wallpaper: TelegramWallpaper?
    let avatarResourceId: String?
    let animatedIdentity: String?
    let premiumIdentity: String?
    let themeIdentity: ObjectIdentifier
}

// MARK: GhostBase v1.1L PROFILESTATE1
// Generic animated-media descriptor. Today it is fed by profile video;
// a future animated-wallpaper provider can feed the same renderer unchanged.
private struct GhostBaseAnimatedMediaSource {
    let identity: String
    let content: NativeVideoContent
}

private enum GhostBaseProfileBackgroundSource {
    case wallpaper(TelegramWallpaper, GhostBaseProfileBackgroundSourceKind)
    case premium(UIColor, UIColor, String)
    case avatar(EnginePeer, TelegramMediaImageRepresentation, String, GhostBaseAnimatedMediaSource?)
    case telegramTheme
}
''',
    "Background state/source types"
)

bg = replace_once(
    bg,
    '''    private let imageView: UIImageView
    private let blurView: UIVisualEffectView
    private let tintView: UIView

    private let sourceDisposable = MetaDisposable()
''',
    '''    private let imageView: UIImageView
    private let blurView: UIVisualEffectView
    private let tintView: UIView

    // Exactly one animated source is alive at most.
    // Telegram MediaBox owns the downloaded resource.
    private var videoNode: UniversalVideoNode?
    private var videoContent: NativeVideoContent?
    private var currentVideoIdentity: String?

    private let sourceDisposable = MetaDisposable()
''',
    "Background video properties"
)

bg = replace_once(
    bg,
    '''        self.imageView.frame = bounds
        self.blurView.frame = bounds
        self.tintView.frame = bounds
    }

    func update(
        peer: EnginePeer?,
        cachedData: EngineCachedPeerData?,
        presentationData: PresentationData,
        isSettings: Bool
    ) {
        let source = self.resolveSource(
            peer: peer,
            cachedData: cachedData,
            presentationData: presentationData,
            isSettings: isSettings
        )
''',
    '''        self.imageView.frame = bounds

        if let videoNode = self.videoNode {
            videoNode.frame = bounds
            videoNode.updateLayout(
                size: bounds.size,
                transition: .immediate
            )
        }

        self.blurView.frame = bounds
        self.tintView.frame = bounds
    }

    override func didMoveToWindow() {
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

    func update(
        peer: EnginePeer?,
        cachedData: EngineCachedPeerData?,
        presentationData: PresentationData,
        isSettings: Bool,
        avatarItem: PeerInfoAvatarListItem?
    ) {
        let source = self.resolveSource(
            peer: peer,
            cachedData: cachedData,
            presentationData: presentationData,
            isSettings: isSettings,
            avatarItem: avatarItem
        )
''',
    "Background layout/update signature"
)

bg = replace_once(
    bg,
    '''    private func resolveSource(
        peer: EnginePeer?,
        cachedData: EngineCachedPeerData?,
        presentationData: PresentationData,
        isSettings: Bool
    ) -> GhostBaseProfileBackgroundSource {
''',
    '''    private func resolveSource(
        peer: EnginePeer?,
        cachedData: EngineCachedPeerData?,
        presentationData: PresentationData,
        isSettings: Bool,
        avatarItem: PeerInfoAvatarListItem?
    ) -> GhostBaseProfileBackgroundSource {
''',
    "Background resolve signature"
)

old_avatar_return = '''                return .avatar(
                    peer,
                    representation,
                    resourceId
                )
'''

new_avatar_return = '''                return .avatar(
                    peer,
                    representation,
                    resourceId,
                    self.animatedAvatarSource(
                        peer: peer,
                        item: avatarItem
                    )
                )
'''

count = bg.count(old_avatar_return)

if count != 2:
    raise RuntimeError(
        f"[V11L] avatar return sites "
        f"expected 2 found {count}"
    )

bg = bg.replace(
    old_avatar_return,
    new_avatar_return
)

state_anchor = "    private func stateKey(\n"

helper = r'''    private func animatedAvatarSource(
        peer: EnginePeer,
        item: PeerInfoAvatarListItem?
    ) -> GhostBaseAnimatedMediaSource? {
        guard
            self.settings.animatedBackgroundEnabled,
            !self.settings.reducedBlur,
            !UIAccessibility.isReduceTransparencyEnabled,
            !ProcessInfo.processInfo.isLowPowerModeEnabled,
            let item,
            let peerReference = PeerReference(peer)
        else {
            return nil
        }

        let representations: [ImageRepresentationWithReference]
        let videoRepresentations: [VideoRepresentationWithReference]
        let immediateThumbnailData: Data?
        var videoId: Int64

        switch item {
        case .custom:
            return nil

        case let .topImage(
            topRepresentations,
            videoRepresentationsValue,
            immediateThumbnail
        ):
            representations = topRepresentations
            videoRepresentations = videoRepresentationsValue
            immediateThumbnailData = immediateThumbnail

            videoId =
                peer.id.id._internalGetInt64Value()

            if let resource =
                videoRepresentations
                    .first?
                    .representation
                    .resource
                    as? CloudPhotoSizeMediaResource {

                videoId =
                    videoId &+ resource.photoId
            }

        case let .image(
            reference,
            imageRepresentations,
            videoRepresentationsValue,
            immediateThumbnail,
            _,
            _
        ):
            representations = imageRepresentations
            videoRepresentations = videoRepresentationsValue
            immediateThumbnailData = immediateThumbnail

            if case let .cloud(
                imageId,
                _,
                _
            ) = reference {
                videoId = imageId
            } else {
                videoId =
                    peer.id.id._internalGetInt64Value()
            }
        }

        guard let video =
            videoRepresentations.last
        else {
            return nil
        }

        let videoFileReference =
            FileMediaReference.avatarList(
                peer: peerReference,
                media: TelegramMediaFile(
                    fileId: EngineMedia.Id(
                        namespace:
                            Namespaces.Media.LocalFile,
                        id: 0
                    ),
                    partialReference: nil,
                    resource:
                        video.representation.resource,
                    previewRepresentations:
                        representations.map {
                            $0.representation
                        },
                    videoThumbnails: [],
                    immediateThumbnailData:
                        immediateThumbnailData,
                    mimeType: "video/mp4",
                    size: nil,
                    attributes: [
                        .Animated,
                        .Video(
                            duration: 0,
                            size:
                                video
                                    .representation
                                    .dimensions,
                            flags: [],
                            preloadSize: nil,
                            coverTime: nil,
                            videoCodec: nil
                        )
                    ],
                    alternativeRepresentations: []
                )
            )

        let content = NativeVideoContent(
            id: .profileVideo(
                videoId,
                nil
            ),
            userLocation: .other,
            fileReference: videoFileReference,
            streamVideo:
                isMediaStreamable(
                    resource:
                        video.representation.resource
                )
                ? .conservative
                : .none,
            loopVideo: true,
            enableSound: false,
            fetchAutomatically: true,
            onlyFullSizeThumbnail: false,
            useLargeThumbnail: true,
            autoFetchFullSizeThumbnail: true,
            startTimestamp:
                video.representation.startTimestamp,
            continuePlayingWithoutSoundOnLostAudioSession:
                false,
            placeholderColor: .clear,
            captureProtected:
                peer.isCopyProtectionEnabled,
            storeAfterDownload: nil
        )

        let identity =
            "video:\(peer.id.toInt64()):\(String(describing: video.representation.resource.id)):\(video.representation.startTimestamp ?? 0.0)"

        return GhostBaseAnimatedMediaSource(
            identity: identity,
            content: content
        )
    }

'''

if bg.count(state_anchor) != 1:
    raise RuntimeError(
        "[V11L] stateKey anchor missing"
    )

bg = bg.replace(
    state_anchor,
    helper + state_anchor,
    1
)

bg = bg.replace(
    '''                avatarResourceId: nil,
                premiumIdentity: nil,
                themeIdentity: themeIdentity
''',
    '''                avatarResourceId: nil,
                animatedIdentity: nil,
                premiumIdentity: nil,
                themeIdentity: themeIdentity
'''
)

bg = bg.replace(
    '''                avatarResourceId: nil,
                premiumIdentity: identity,
                themeIdentity: themeIdentity
''',
    '''                avatarResourceId: nil,
                animatedIdentity: nil,
                premiumIdentity: identity,
                themeIdentity: themeIdentity
'''
)

bg = replace_once(
    bg,
    '''        case let .avatar(_, _, resourceId):
            return GhostBaseProfileBackgroundStateKey(
                peerId: peerId,
                kind: .avatar,
                wallpaper: nil,
                avatarResourceId: resourceId,
                premiumIdentity: nil,
                themeIdentity: themeIdentity
            )
''',
    '''        case let .avatar(
            _,
            _,
            resourceId,
            animatedSource
        ):
            return GhostBaseProfileBackgroundStateKey(
                peerId: peerId,
                kind: .avatar,
                wallpaper: nil,
                avatarResourceId: resourceId,
                animatedIdentity:
                    animatedSource?.identity,
                premiumIdentity: nil,
                themeIdentity: themeIdentity
            )
''',
    "Background avatar stateKey"
)

theme_pos = bg.find("case .telegramTheme:")

if (
    theme_pos >= 0
    and
    "animatedIdentity:"
        not in bg[
            theme_pos:
            theme_pos + 500
        ]
):
    raise RuntimeError(
        "[V11L] telegramTheme state key "
        "did not receive animatedIdentity"
    )

apply_anchor = "    private func apply(\n"

video_helpers = '''    private func clearAnimatedMedia() {
        guard let videoNode = self.videoNode else {
            self.videoContent = nil
            self.currentVideoIdentity = nil
            return
        }

        videoNode.pause()
        videoNode.canAttachContent = false
        videoNode.view.removeFromSuperview()

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

        if
            self.currentVideoIdentity
                == source.identity,
            self.videoNode != nil
        {
            return
        }

        self.clearAnimatedMedia()

        let mediaManager =
            self.context.sharedContext.mediaManager

        let videoNode = UniversalVideoNode(
            context: self.context,
            postbox:
                self.context.account.postbox,
            audioSession:
                mediaManager.audioSession,
            manager:
                mediaManager.universalVideoManager,
            decoration:
                GalleryVideoDecoration(),
            content: source.content,
            priority: .embedded
        )

        videoNode.isUserInteractionEnabled =
            false

        self.insertSubview(
            videoNode.view,
            belowSubview: self.blurView
        )

        videoNode.frame = self.bounds

        videoNode.updateLayout(
            size: self.bounds.size,
            transition: .immediate
        )

        self.videoNode = videoNode
        self.videoContent = source.content
        self.currentVideoIdentity =
            source.identity

        if self.window != nil {
            videoNode.canAttachContent = true
            videoNode.play()
        }
    }

'''

if bg.count(apply_anchor) != 1:
    raise RuntimeError(
        "[V11L] apply anchor missing"
    )

bg = bg.replace(
    apply_anchor,
    video_helpers + apply_anchor,
    1
)

bg = replace_once(
    bg,
    '''        case let .wallpaper(wallpaper, kind):
            self.usesCustomBackground = true
''',
    '''        case let .wallpaper(wallpaper, kind):
            self.clearAnimatedMedia()
            self.usesCustomBackground = true
''',
    "wallpaper clear video"
)

bg = replace_once(
    bg,
    '''        case let .premium(main, secondary, identity):
            self.usesCustomBackground = true
''',
    '''        case let .premium(main, secondary, identity):
            self.clearAnimatedMedia()
            self.usesCustomBackground = true
''',
    "premium clear video"
)

bg = replace_once(
    bg,
    '''        case .telegramTheme:
            self.usesCustomBackground = false
''',
    '''        case .telegramTheme:
            self.clearAnimatedMedia()
            self.usesCustomBackground = false
''',
    "theme clear video"
)

old_avatar_apply = '''        case let .avatar(peer, representation, resourceId):
            self.usesCustomBackground = true
            let fallback = presentationData.theme.list.itemBlocksBackgroundColor
            self.backgroundColor = fallback
            self.applyTint(fallback, fallback: fallback, isDark: isDark, reduced: reduced)

            // The cache key is explicitly peer + avatar resource. A new avatar
            // cannot reuse the previous peer's processed image or tint.
            let cacheKey = "avatar:\\(peer.id.toInt64()):\\(resourceId)" as NSString
            if let cached = Self.imageCache.object(forKey: cacheKey) {
                self.imageView.image = cached.image
                self.applyTint(cached.tint, fallback: fallback, isDark: isDark, reduced: reduced)
                return
            }

            self.imageView.image = nil
            let loadKey = cacheKey as String
            self.currentLoadKey = loadKey
            guard let signal = self.avatarEntrySignal(
                peer: peer,
                representation: representation,
                identity: loadKey,
                fallback: fallback
            ) else {
                return
            }
'''

new_avatar_apply = '''        case let .avatar(
            peer,
            representation,
            resourceId,
            animatedSource
        ):
            self.usesCustomBackground = true

            let fallback =
                presentationData
                    .theme
                    .list
                    .itemBlocksBackgroundColor

            let cacheKey =
                "avatar:\\(peer.id.toInt64()):\\(resourceId)"
                as NSString

            let loadKey =
                cacheKey as String

            let immediateTint =
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

            self.applyAnimatedMedia(
                animatedSource
            )

            if let cached =
                Self.imageCache.object(
                    forKey: cacheKey
                ) {

                self.imageView.image =
                    cached.image

                self.applyTint(
                    cached.tint,
                    fallback: immediateTint,
                    isDark: isDark,
                    reduced: reduced
                )

                return
            }

            self.imageView.image = nil
            self.currentLoadKey = loadKey

            guard let signal =
                self.avatarEntrySignal(
                    peer: peer,
                    representation:
                        representation,
                    identity: loadKey,
                    fallback:
                        immediateTint
                )
            else {
                return
            }
'''

bg = replace_once(
    bg,
    old_avatar_apply,
    new_avatar_apply,
    "avatar apply persistent/video"
)

bg = replace_once(
    bg,
    '''                synchronousLoad:
                    false
''',
    '''                synchronousLoad:
                    true
''',
    "avatar synchronous MediaBox load"
)


# ============================================================
# 3. PASS CURRENT AVATAR VIDEO ITEM TO FULLSCREEN RENDERER
# ============================================================

scr = replace_once(
    scr,
    '''                presentationData: self.presentationData,
                isSettings: self.isSettings
            )
''',
    '''                presentationData: self.presentationData,
                isSettings: self.isSettings,
                avatarItem:
                    self.headerNode
                        .avatarListNode
                        .item
            )
''',
    "PeerInfoScreen background avatar item"
)

hdr = replace_once(
    hdr,
    '''            strongSelf.editingContentNode.avatarNode.update(peer: peer, threadData: strongSelf.threadData, chatLocation: chatLocation, item: strongSelf.avatarListNode.item, updatingAvatar: state.updatingAvatar, uploadProgress: state.avatarUploadProgress, theme: presentationData.theme, avatarSize: avatarSize, isEditing: state.isEditing)
        }
''',
    '''            strongSelf.editingContentNode.avatarNode.update(peer: peer, threadData: strongSelf.threadData, chatLocation: chatLocation, item: strongSelf.avatarListNode.item, updatingAvatar: state.updatingAvatar, uploadProgress: state.avatarUploadProgress, theme: presentationData.theme, avatarSize: avatarSize, isEditing: state.isEditing)

            // A video representation can arrive after the first layout.
            // Refresh once the avatar list updates.
            strongSelf.requestUpdateLayout?(false)
        }
''',
    "Header avatar item refresh"
)


# ============================================================
# 4. PREMIUM PATTERN
# ============================================================

cover_anchor = '''        func update(component: PeerInfoCoverComponent, availableSize: CGSize, state: EmptyComponentState, environment: Environment<Empty>, transition: ComponentTransition) -> CGSize {
'''

cover_method = '''        // MARK: GhostBase v1.1L PREMIUM_PATTERN1
        // Hide only Telegram's stock color fill. Native Premium pattern
        // layers remain at their original opacity.
        public func setGhostBaseBackgroundFillAlpha(
            _ alpha: CGFloat
        ) {
            self.backgroundView.alpha = alpha
            self.backgroundGradientLayer.opacity =
                Float(alpha)
        }

'''

if cover.count(cover_anchor) != 1:
    raise RuntimeError(
        "[V11L] cover update anchor missing"
    )

cover = cover.replace(
    cover_anchor,
    cover_method + cover_anchor,
    1
)

old_cover_alpha = '''            if ghostBaseBlendCover {
                backgroundCoverView.alpha =
                    self.ghostBaseProfileGlassSettings?
                        .avatarBlurInProfile
                        == true
                    ? 0.08
                    : 0.16
            } else {
                backgroundCoverView.alpha =
                    1.0
            }
'''

new_cover_alpha = '''            backgroundCoverView.alpha = 1.0

            backgroundCoverView
                .setGhostBaseBackgroundFillAlpha(
                    ghostBaseBlendCover
                        ? 0.0
                        : 1.0
                )
'''

hdr = replace_once(
    hdr,
    old_cover_alpha,
    new_cover_alpha,
    "Header preserve premium pattern"
)


# ============================================================
# 5. UNIFIED MATERIAL + TRIANGLE MASK
# ============================================================

old_pane_glass = '''        if self.ghostBaseGlassEnabled {
            let isDark = presentationData.theme.overallDarkAppearance

            self.backgroundColor =
                backgroundColor
                    .withAlphaComponent(
                        isDark
                            ? 0.08
                            : 0.12
                    )
        } else {
            self.backgroundColor = backgroundColor
        }
'''

new_pane_glass = '''        if self.ghostBaseGlassEnabled {
            // MARK: GhostBase v1.1L UNIFIEDMATERIAL1
            // Fullscreen scene owns tone. Pane roots stay transparent,
            // removing the hard horizontal color bands.
            self.backgroundColor = .clear
        } else {
            self.backgroundColor = backgroundColor
        }
'''

pane = replace_once(
    pane,
    old_pane_glass,
    new_pane_glass,
    "Pane root clear"
)

sec = replace_once(
    sec,
    '''    private let itemContainerNode: ASDisplayNode
''',
    '''    private let itemContainerNode: ASDisplayNode
    private let ghostBaseItemMaskLayer =
        CAShapeLayer()
''',
    "Section mask property"
)

old_section_clip = '''        if self.ghostBaseGlassEnabled {
            let radius: CGFloat =
                hasCorners ? 16.0 : 0.0

            self.backgroundNode.cornerRadius =
                radius

            self.backgroundNode.clipsToBounds =
                hasCorners

            self.itemContainerNode.cornerRadius =
                radius

            self.itemContainerNode.clipsToBounds =
                hasCorners
        }
'''

new_section_clip = '''        if self.ghostBaseGlassEnabled {
            let radius: CGFloat =
                hasCorners ? 16.0 : 0.0

            self.backgroundNode.cornerRadius =
                radius

            self.backgroundNode.clipsToBounds =
                hasCorners

            // MARK: GhostBase v1.1L SECTIONMASK1
            //
            // V11K rounded the whole container although the actual
            // card starts at contentWithBackgroundOffset. The
            // mismatched geometry exposed square native surfaces
            // as black triangular corners.
            self.itemContainerNode.cornerRadius =
                0.0

            self.itemContainerNode.clipsToBounds =
                false

            if hasCorners {
                let maskPath = UIBezierPath()

                if backgroundFrame.minY > 0.0 {
                    maskPath.append(
                        UIBezierPath(
                            rect: CGRect(
                                x: 0.0,
                                y: 0.0,
                                width: width,
                                height:
                                    backgroundFrame.minY
                            )
                        )
                    )
                }

                maskPath.append(
                    UIBezierPath(
                        roundedRect:
                            backgroundFrame,
                        cornerRadius:
                            radius
                    )
                )

                if backgroundFrame.maxY
                    < contentHeight {

                    maskPath.append(
                        UIBezierPath(
                            rect: CGRect(
                                x: 0.0,
                                y:
                                    backgroundFrame
                                        .maxY,
                                width: width,
                                height:
                                    contentHeight
                                    - backgroundFrame
                                        .maxY
                            )
                        )
                    )
                }

                self.ghostBaseItemMaskLayer.frame =
                    CGRect(
                        origin: .zero,
                        size: CGSize(
                            width: width,
                            height: contentHeight
                        )
                    )

                self.ghostBaseItemMaskLayer.path =
                    maskPath.cgPath

                self.itemContainerNode.layer.mask =
                    self.ghostBaseItemMaskLayer
            } else {
                self.itemContainerNode.layer.mask =
                    nil
            }
        } else {
            self.itemContainerNode.layer.mask =
                nil
        }
'''

sec = replace_once(
    sec,
    old_section_clip,
    new_section_clip,
    "Section precise mask"
)


# ============================================================
# 6. HISTORY + OWN PHONE HEADER
# ============================================================

rep = replace_once(
    rep,
    '''        self.textNode.displaysAsynchronously = false

        self.addSubnode(self.scrollNode)
''',
    '''        self.textNode.displaysAsynchronously = false

        // MARK: GhostBase v1.1L HISTORYMULTILINE1
        self.textNode.maximumNumberOfLines = 0

        self.addSubnode(self.scrollNode)
''',
    "History multiline"
)

hdr = replace_once(
    hdr,
    '                var subtitle = formatPhoneNumber(context: self.context, number: user.phone ?? "")\n',
    r"""                // MARK: GhostBase v1.1L HIDEPHONEHEADER1
                let hideOwnPhone =
                    (
                        UserDefaults.standard
                            .object(
                                forKey:
                                    "GhostBase.Appearance.HideOwnPhone"
                            )
                        as? Bool
                    )
                    ?? false

                var subtitle =
                    hideOwnPhone
                    ? ""
                    : formatPhoneNumber(
                        context: self.context,
                        number: user.phone ?? ""
                    )
""",
    "Settings header phone subtitle"
)

hdr = replace_once(
    hdr,
    '                    subtitle = "\\(subtitle) • @\\(mainUsername)"\n',
    r"""                    subtitle =
                        hideOwnPhone
                        ? "@\(mainUsername)"
                        : "\(subtitle) • @\(mainUsername)"
""",
    "Settings header phone username composition"
)


# ============================================================
# 7. GIFTS LIGHTER GLASS
# ============================================================

old_gift_bg = '''                } else if case .upgradePreview = component.mode {
                    self.backgroundLayer.backgroundColor = component.theme.list.itemModalBlocksBackgroundColor.cgColor
                } else {
                    self.backgroundLayer.backgroundColor = component.theme.list.itemBlocksBackgroundColor.cgColor
                }
'''

new_gift_bg = '''                } else if case .upgradePreview = component.mode {
                    self.backgroundLayer.backgroundColor = component.theme.list.itemModalBlocksBackgroundColor.cgColor
                } else {
                    switch component.style {
                    case .glass:
                        // MARK: GhostBase v1.1L GIFTGLASS1
                        //
                        // Fullscreen scene already owns blur.
                        // Gift cards use only a light translucent material.
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
                                    ? 0.16
                                    : 0.20
                            )
                            .cgColor

                    case .legacy:
                        self.backgroundLayer
                            .backgroundColor =
                            component
                                .theme
                                .list
                                .itemBlocksBackgroundColor
                                .cgColor
                    }
                }
'''

gift = replace_once(
    gift,
    old_gift_bg,
    new_gift_bg,
    "Gift glass surface"
)


# ============================================================
# 8. NORMAL 1:1 CALL BACKDROP
#
# Safe current source exposes EnginePeer + static avatar UIImage.
# No profile-video representation is exposed here, so this pass
# deliberately does NOT fake animated call video.
# ============================================================

private_call = replace_once(
    private_call,
    '    private let pipView: PrivateCallPictureInPictureView\n',
    r"""    // MARK: GhostBase v1.1L CALLBACKDROP1
    public var ghostBaseBackdropEnabled:
        Bool = false

    private let pipView: PrivateCallPictureInPictureView
""",
    "Private call backdrop flag"
)

private_call = replace_once(
    private_call,
    '''        let backgroundAlpha = self.isAnimatedOutToGroupCall ? 0.0 : 1.0
''',
    '''        let backgroundAlpha =
            (
                self.isAnimatedOutToGroupCall
                || self.ghostBaseBackdropEnabled
            )
            ? 0.0
            : 1.0

        let ghostBaseNativeAuxAlpha:
            CGFloat =
            self.ghostBaseBackdropEnabled
            ? 0.0
            : 1.0

        genericAlphaTransition.setAlpha(
            layer:
                self.backgroundLayer
                    .blurredLayer,
            alpha:
                ghostBaseNativeAuxAlpha
        )

        genericAlphaTransition.setAlpha(
            layer:
                self.blobBackgroundLayer,
            alpha:
                ghostBaseNativeAuxAlpha
        )
''',
    "Private call native bg alpha"
)

call = insert_after_once(
    call,
    "import LibYuvBinding\n",
    '''
// MARK: GhostBase v1.1L CALLBACKDROP1
private final class GhostBaseCallBackdropView:
    UIView {

    private let imageView =
        UIImageView()

    private let gradientLayer =
        CAGradientLayer()

    private let blurView =
        UIVisualEffectView(effect: nil)

    private let tintView =
        UIView()

    override init(frame: CGRect) {
        super.init(frame: frame)

        self.isUserInteractionEnabled =
            false

        self.clipsToBounds = true

        self.imageView.contentMode =
            .scaleAspectFill

        self.imageView.clipsToBounds =
            true

        self.layer.addSublayer(
            self.gradientLayer
        )

        self.addSubview(
            self.imageView
        )

        self.addSubview(
            self.blurView
        )

        self.addSubview(
            self.tintView
        )
    }

    required init?(coder: NSCoder) {
        preconditionFailure()
    }

    override func layoutSubviews() {
        super.layoutSubviews()

        self.gradientLayer.frame =
            self.bounds

        self.imageView.frame =
            self.bounds

        self.blurView.frame =
            self.bounds

        self.tintView.frame =
            self.bounds
    }

    func update(
        peer: EnginePeer,
        avatarImage: UIImage?,
        context: AccountContext,
        presentationData:
            PresentationData
    ) -> Bool {
        guard let settings =
            GhostBaseProfileBlurSettings
                .loadEnabled()
        else {
            self.isHidden = true
            return false
        }

        let isDark =
            presentationData
                .theme
                .overallDarkAppearance

        let reduced =
            settings.reducedBlur
            || UIAccessibility
                .isReduceTransparencyEnabled
            || ProcessInfo
                .processInfo
                .isLowPowerModeEnabled

        self.blurView.effect =
            UIBlurEffect(
                style:
                    isDark
                    ? .systemUltraThinMaterialDark
                    : .systemUltraThinMaterialLight
            )

        var colors:
            (UIColor, UIColor)?

        if !settings.avatarBlurInProfile {
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

                colors = (
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
                )
            } else if let profileColor =
                peer.effectiveProfileColor {

                let profileColors =
                    context
                        .peerNameColors
                        .getProfile(
                            profileColor,
                            dark: isDark
                        )

                colors = (
                    profileColors.main,
                    profileColors.secondary
                        ?? profileColors.main
                )
            }
        }

        if let colors {
            self.gradientLayer.isHidden =
                false

            self.gradientLayer.colors = [
                colors.0.cgColor,
                colors.1.cgColor
            ]

            self.gradientLayer.startPoint =
                CGPoint(
                    x: 0.15,
                    y: 0.0
                )

            self.gradientLayer.endPoint =
                CGPoint(
                    x: 0.85,
                    y: 1.0
                )

            self.imageView.image = nil

            self.backgroundColor =
                colors.0

            self.tintView.backgroundColor =
                settings.tintEnabled
                ? colors.0
                    .withAlphaComponent(
                        reduced
                        ? 0.03
                        : 0.05
                    )
                : UIColor.black
                    .withAlphaComponent(
                        reduced
                        ? 0.02
                        : 0.03
                    )
        } else if let avatarImage {
            self.gradientLayer.isHidden =
                true

            self.imageView.image =
                avatarImage

            self.backgroundColor =
                .black

            self.tintView.backgroundColor =
                settings.tintEnabled
                ? UIColor.black
                    .withAlphaComponent(
                        reduced
                        ? 0.03
                        : 0.06
                    )
                : UIColor.black
                    .withAlphaComponent(
                        reduced
                        ? 0.02
                        : 0.04
                    )
        } else {
            self.isHidden = true
            return false
        }

        self.isHidden = false
        return true
    }
}
''',
    "Call backdrop class"
)

call = replace_once(
    call,
    '''    private let containerView: UIView
    private let callScreen: PrivateCallScreen
''',
    '''    private let containerView: UIView
    private let ghostBaseBackdropView:
        GhostBaseCallBackdropView
    private let callScreen: PrivateCallScreen
''',
    "Call backdrop property"
)

call = replace_once(
    call,
    '''        self.containerView = UIView()
        self.containerView.clipsToBounds = true
        self.callScreen = PrivateCallScreen()
''',
    '''        self.containerView = UIView()
        self.containerView.clipsToBounds = true

        self.ghostBaseBackdropView =
            GhostBaseCallBackdropView(
                frame: .zero
            )

        self.callScreen = PrivateCallScreen()
''',
    "Call backdrop init"
)

call = replace_once(
    call,
    '''        self.view.addSubview(self.containerView)
        self.containerView.addSubview(self.callScreen)
''',
    '''        self.view.addSubview(self.containerView)

        self.containerView.addSubview(
            self.ghostBaseBackdropView
        )

        self.containerView.addSubview(
            self.callScreen
        )
''',
    "Call backdrop hierarchy"
)

call_anchor = '''    func updatePeer(accountPeer: EnginePeer, peer: EnginePeer, hasOther: Bool) {
'''

call_helper = '''    private func updateGhostBaseBackdrop(
        peer: EnginePeer,
        avatarImage: UIImage?
    ) {
        let enabled =
            self.ghostBaseBackdropView
                .update(
                    peer: peer,
                    avatarImage:
                        avatarImage,
                    context:
                        self.call.context,
                    presentationData:
                        self.presentationData
                )

        self.callScreen
            .ghostBaseBackdropEnabled =
            enabled
    }

'''

if call.count(call_anchor) != 1:
    raise RuntimeError(
        "[V11L] call updatePeer anchor missing"
    )

call = call.replace(
    call_anchor,
    call_helper + call_anchor,
    1
)

call = replace_once(
    call,
    '''                    if let image {
                        callScreenState.avatarImage = image
                        self.callScreenState = callScreenState
                        self.update(transition: .immediate)
                    }
''',
    '''                    if let image {
                        callScreenState.avatarImage =
                            image

                        self.callScreenState =
                            callScreenState

                        self.updateGhostBaseBackdrop(
                            peer: peer,
                            avatarImage: image
                        )

                        self.update(
                            transition: .immediate
                        )
                    }
''',
    "Call backdrop image arrival"
)

call = replace_once(
    call,
    '        self.currentPeer = peer\n',
    r"""        self.currentPeer = peer

        self.updateGhostBaseBackdrop(
            peer: peer,
            avatarImage:
                callScreenState.avatarImage
        )
""",
    "Call backdrop update peer"
)

call = replace_once(
    call,
    '''        transition.updateFrame(view: self.callScreen, frame: CGRect(origin: CGPoint(), size: layout.size))
''',
    '''        transition.updateFrame(
            view:
                self.ghostBaseBackdropView,
            frame:
                CGRect(
                    origin: CGPoint(),
                    size: layout.size
                )
        )

        transition.updateFrame(view: self.callScreen, frame: CGRect(origin: CGPoint(), size: layout.size))
''',
    "Call backdrop layout"
)


# ============================================================
# WRITE ONLY AFTER ALL ANCHORS PASSED
# ============================================================

for path, text in [
    (BG, bg),
    (HDR, hdr),
    (SEC, sec),
    (PANE, pane),
    (SCR, scr),
    (REP, rep),
    (SETTINGS, settings),
    (GLASS, glass),
    (COVER, cover),
    (GIFT, gift),
    (CALL_CONTROLLER, call),
    (PRIVATE_CALL, private_call),
]:
    path.write_text(
        text,
        encoding="utf-8"
    )

print("[V11L] applied")
print("  persistent per-source avatar fallback / synchronous cache hit")
print("  animated video-avatar profile backdrop with loop + MediaBox reuse")
print("  Premium emoji-pattern preserved at full opacity")
print("  pane tone bands removed + section geometry mask fixed")
print("  profile history multiline output enabled")
print("  own phone hidden in Settings header")
print("  Gifts glass surface lightened")
print("  1:1 call static avatar/Premium backdrop enabled")
