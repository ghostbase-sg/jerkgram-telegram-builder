#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

SOURCE_ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src")).resolve()
OFFICIAL_ROOT = Path(
    os.environ.get(
        "GHOSTBASE_OFFICIAL_ROOT",
        "/root/gb_builder/ports/ghostbase_12_9_2_port/telegram-ios-12.9.2-official",
    )
).resolve()

PEER_REL = Path("submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources")
PEER_SOURCE = SOURCE_ROOT / PEER_REL
PEER_OFFICIAL = OFFICIAL_ROOT / PEER_REL
SETTINGS = SOURCE_ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
GLASS_RUNTIME = SOURCE_ROOT / "submodules/Display/Source/GhostBaseGlass.swift"


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"[V11F PROFILE HEADER BLUR] {message}")


def require_file(path: Path) -> None:
    if not path.is_file():
        fail(f"missing required file: {path}")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def remove_region(text: str, begin: str, end: str, *, preserve_end: bool = True) -> str:
    if begin not in text:
        return text
    start = text.index(begin)
    end_pos = text.find(end, start)
    if end_pos < 0:
        fail(f"cleanup end anchor missing for {begin!r}")
    if not preserve_end:
        end_pos += len(end)
    return text[:start] + text[end_pos:]


def remove_exact_if_present(text: str, old: str, label: str) -> str:
    count = text.count(old)
    if count > 1:
        fail(f"{label}: expected at most one block, found {count}")
    if count == 1:
        return text.replace(old, "", 1)
    return text


for required in (
    PEER_OFFICIAL / "PeerInfoHeaderNode.swift",
    PEER_OFFICIAL / "PeerInfoScreen.swift",
    PEER_OFFICIAL / "PeerInfoScreenItemSectionContainerNode.swift",
    PEER_SOURCE / "PeerInfoProfileItems.swift",
    SETTINGS,
):
    require_file(required)

# ---------------------------------------------------------------------------
# 1. Restore the stock profile screen geometry and section container exactly.
#    PeerInfoHeaderNode is also restored first, then receives one isolated,
#    deterministic integration. This prevents PROFILEHUB/PROFILEBACKDROP code
#    from surviving merely because an earlier patcher happened to run first.
# ---------------------------------------------------------------------------
for filename in ("PeerInfoScreen.swift", "PeerInfoScreenItemSectionContainerNode.swift"):
    shutil.copyfile(PEER_OFFICIAL / filename, PEER_SOURCE / filename)

header_path = PEER_SOURCE / "PeerInfoHeaderNode.swift"
shutil.copyfile(PEER_OFFICIAL / "PeerInfoHeaderNode.swift", header_path)
header = header_path.read_text(encoding="utf-8")

header = replace_once(
    header,
    "import TelegramCore\n",
    "import TelegramCore\nimport Postbox\n",
    "PeerInfoHeaderNode Postbox import",
)

helper = r'''
// MARK: GhostBase v1.1F PROFILEHEADERBLUR1
// The effect is owned by PeerInfoHeaderNode and is optional by construction.
// With the main switch off this type is never instantiated, so there are no
// additional views, observers, signals, image work or palette work.
private final class GhostBaseProfileHeaderBackgroundCacheEntry: NSObject {
    let image: UIImage
    let tint: UIColor

    init(image: UIImage, tint: UIColor) {
        self.image = image
        self.tint = tint
    }
}

private enum GhostBaseProfileHeaderBackgroundSourceKind: Int {
    case personalWallpaper
    case globalWallpaper
    case premiumProfile
    case avatar
    case telegramTheme
}

private struct GhostBaseProfileHeaderBackgroundStateKey: Equatable {
    let peerId: Int64?
    let kind: GhostBaseProfileHeaderBackgroundSourceKind
    let wallpaper: TelegramWallpaper?
    let avatarResourceId: String?
    let themeIdentity: ObjectIdentifier
}

private enum GhostBaseProfileHeaderBackgroundSource {
    case wallpaper(TelegramWallpaper, GhostBaseProfileHeaderBackgroundSourceKind)
    case premiumProfile
    case avatar(EnginePeer, TelegramMediaImageRepresentation, String)
    case telegramTheme
}

private final class GhostBaseProfileHeaderBackgroundView: UIView {
    private static let imageCache = NSCache<NSString, GhostBaseProfileHeaderBackgroundCacheEntry>()

    private let context: AccountContext
    private let settings: GhostBaseProfileBlurSettings

    // Exactly one reusable image view, one persistent visual-effect view and
    // one independent tint/dimming view. They are created once in init().
    private let imageView: UIImageView
    private let blurView: UIVisualEffectView
    private let tintView: UIView

    private let sourceDisposable = MetaDisposable()
    private var currentStateKey: GhostBaseProfileHeaderBackgroundStateKey?
    private var currentLoadKey: String?

    private(set) var usesCustomBackground = false
    private(set) var buttonTintColor: UIColor?
    var requestHeaderUpdate: (() -> Void)?

    init(context: AccountContext, settings: GhostBaseProfileBlurSettings) {
        self.context = context
        self.settings = settings

        self.imageView = UIImageView()
        self.imageView.contentMode = .scaleAspectFill
        self.imageView.clipsToBounds = true

        self.blurView = UIVisualEffectView(effect: nil)
        self.blurView.isUserInteractionEnabled = false

        self.tintView = UIView()
        self.tintView.isUserInteractionEnabled = false

        super.init(frame: .zero)

        self.clipsToBounds = true
        self.isUserInteractionEnabled = false
        self.addSubview(self.imageView)
        self.addSubview(self.blurView)
        self.addSubview(self.tintView)
    }

    required init?(coder: NSCoder) {
        preconditionFailure("init(coder:) has not been implemented")
    }

    deinit {
        self.sourceDisposable.dispose()
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        // Layout only updates frames. No image generation, color extraction,
        // UserDefaults access, source selection or signal creation occurs here.
        let bounds = self.bounds
        self.imageView.frame = bounds
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
        let stateKey = self.stateKey(
            source: source,
            peer: peer,
            presentationData: presentationData
        )
        guard self.currentStateKey != stateKey else {
            return
        }
        self.currentStateKey = stateKey
        self.apply(
            source: source,
            stateKey: stateKey,
            presentationData: presentationData
        )
    }

    private func resolveSource(
        peer: EnginePeer?,
        cachedData: EngineCachedPeerData?,
        presentationData: PresentationData,
        isSettings: Bool
    ) -> GhostBaseProfileHeaderBackgroundSource {
        // Required priority, kept explicit and verified in final materialized source:
        // 1) personal chat wallpaper
        if !isSettings {
            if let cachedData = cachedData as? CachedUserData, let wallpaper = cachedData.wallpaper {
                return .wallpaper(wallpaper, .personalWallpaper)
            }
            if let cachedData = cachedData as? CachedChannelData, let wallpaper = cachedData.wallpaper {
                return .wallpaper(wallpaper, .personalWallpaper)
            }
        }

        // 2) user-selected global wallpaper. The theme's own default wallpaper
        // is intentionally treated as the final Telegram fallback, not as a
        // custom global source that would permanently shadow Premium/avatar.
        if presentationData.chatWallpaper != presentationData.theme.chat.defaultWallpaper {
            return .wallpaper(presentationData.chatWallpaper, .globalWallpaper)
        }

        // 3) Premium profile color / unique gift cover remains a completely
        // separate stock PeerInfoCoverComponent state. It is never mixed into
        // the avatar cache or avatar-derived tint.
        if let peer {
            if let status = peer.emojiStatus, case .starGift = status.content {
                return .premiumProfile
            }
            if peer.effectiveProfileColor != nil {
                return .premiumProfile
            }
        }

        // 4) avatar-derived blurred background
        if self.settings.avatarBlurInProfile,
           let peer,
           let representation = peer.profileImageRepresentations.last {
            let resourceId = String(describing: representation.resource.id)
            return .avatar(peer, representation, resourceId)
        }

        // 5) untouched Telegram theme / stock cover
        return .telegramTheme
    }

    private func stateKey(
        source: GhostBaseProfileHeaderBackgroundSource,
        peer: EnginePeer?,
        presentationData: PresentationData
    ) -> GhostBaseProfileHeaderBackgroundStateKey {
        let peerId = peer?.id.toInt64()
        let themeIdentity = ObjectIdentifier(presentationData.theme)
        switch source {
        case let .wallpaper(wallpaper, kind):
            return GhostBaseProfileHeaderBackgroundStateKey(
                peerId: peerId,
                kind: kind,
                wallpaper: wallpaper,
                avatarResourceId: nil,
                themeIdentity: themeIdentity
            )
        case .premiumProfile:
            return GhostBaseProfileHeaderBackgroundStateKey(
                peerId: peerId,
                kind: .premiumProfile,
                wallpaper: nil,
                avatarResourceId: nil,
                themeIdentity: themeIdentity
            )
        case let .avatar(_, _, resourceId):
            return GhostBaseProfileHeaderBackgroundStateKey(
                peerId: peerId,
                kind: .avatar,
                wallpaper: nil,
                avatarResourceId: resourceId,
                themeIdentity: themeIdentity
            )
        case .telegramTheme:
            return GhostBaseProfileHeaderBackgroundStateKey(
                peerId: peerId,
                kind: .telegramTheme,
                wallpaper: nil,
                avatarResourceId: nil,
                themeIdentity: themeIdentity
            )
        }
    }

    private func apply(
        source: GhostBaseProfileHeaderBackgroundSource,
        stateKey: GhostBaseProfileHeaderBackgroundStateKey,
        presentationData: PresentationData
    ) {
        self.sourceDisposable.set(nil)
        self.currentLoadKey = nil

        let isDark = presentationData.theme.overallDarkAppearance
        let reduced = self.settings.reducedBlur
            || UIAccessibility.isReduceTransparencyEnabled
            || ProcessInfo.processInfo.isLowPowerModeEnabled
        let effectStyle: UIBlurEffect.Style
        if isDark {
            effectStyle = reduced ? .systemUltraThinMaterialDark : .systemMaterialDark
        } else {
            effectStyle = reduced ? .systemUltraThinMaterialLight : .systemMaterialLight
        }
        self.blurView.effect = UIBlurEffect(style: effectStyle)

        switch source {
        case let .wallpaper(wallpaper, kind):
            self.usesCustomBackground = true
            let fallback = presentationData.theme.list.itemBlocksBackgroundColor
            let metadataTint = Self.wallpaperTint(wallpaper, fallback: fallback)
            self.applyTint(metadataTint, fallback: fallback, isDark: isDark, reduced: reduced)
            self.backgroundColor = metadataTint

            let cacheKey = "wallpaper:\(kind.rawValue):\(String(reflecting: wallpaper))" as NSString
            if let cached = Self.imageCache.object(forKey: cacheKey) {
                self.imageView.image = cached.image
                self.applyTint(cached.tint, fallback: metadataTint, isDark: isDark, reduced: reduced)
                return
            }

            // Never generate wallpaper pixels from PeerInfoHeaderNode.update().
            // A metadata color is enough for the immediate fallback; any image
            // decode or generated gradient runs on the concurrent image path.
            self.imageView.image = nil
            let loadKey = cacheKey as String
            self.currentLoadKey = loadKey
            self.sourceDisposable.set((self.wallpaperEntrySignal(
                wallpaper: wallpaper,
                fallback: metadataTint
            )
            |> deliverOnMainQueue).start(next: { [weak self] entry in
                guard let self, self.currentLoadKey == loadKey, let entry else {
                    return
                }
                Self.imageCache.setObject(entry, forKey: cacheKey)
                self.imageView.image = entry.image
                self.applyTint(entry.tint, fallback: metadataTint, isDark: isDark, reduced: reduced)
                self.requestHeaderUpdate?()
            }))

        case .premiumProfile:
            // Stock PeerInfoCoverComponent remains visible and authoritative.
            self.usesCustomBackground = false
            self.imageView.image = nil
            self.tintView.backgroundColor = .clear
            self.backgroundColor = .clear
            self.buttonTintColor = nil

        case let .avatar(peer, representation, resourceId):
            self.usesCustomBackground = true
            let fallback = presentationData.theme.list.itemBlocksBackgroundColor
            self.backgroundColor = fallback
            self.applyTint(fallback, fallback: fallback, isDark: isDark, reduced: reduced)

            // The cache key is explicitly peer + avatar resource. A new avatar
            // cannot reuse the previous peer's processed image or tint.
            let cacheKey = "avatar:\(peer.id.toInt64()):\(resourceId)" as NSString
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
                fallback: fallback
            ) else {
                return
            }

            self.sourceDisposable.set((signal
            |> deliverOnMainQueue).start(next: { [weak self] entry in
                guard let self, self.currentLoadKey == loadKey, let entry else {
                    return
                }
                Self.imageCache.setObject(entry, forKey: cacheKey)
                self.imageView.image = entry.image
                self.applyTint(entry.tint, fallback: fallback, isDark: isDark, reduced: reduced)
                self.requestHeaderUpdate?()
            }))

        case .telegramTheme:
            self.usesCustomBackground = false
            self.imageView.image = nil
            self.tintView.backgroundColor = .clear
            self.backgroundColor = .clear
            self.buttonTintColor = nil
        }
    }

    private func applyTint(
        _ color: UIColor,
        fallback: UIColor,
        isDark: Bool,
        reduced: Bool
    ) {
        if self.settings.tintEnabled {
            self.tintView.backgroundColor = color.withAlphaComponent(reduced ? 0.28 : 0.18)
            self.buttonTintColor = color
        } else {
            // Tint-off is neutral dimming, not a universal accent color.
            self.tintView.backgroundColor = UIColor.black.withAlphaComponent(isDark ? 0.16 : 0.08)
            self.buttonTintColor = isDark ? UIColor(white: 0.12, alpha: 1.0) : fallback
        }
    }

    private func wallpaperEntrySignal(
        wallpaper: TelegramWallpaper,
        fallback: UIColor
    ) -> Signal<GhostBaseProfileHeaderBackgroundCacheEntry?, NoError> {
        switch wallpaper {
        case let .image(representations, _):
            guard let representation = largestImageRepresentation(representations) else {
                return .single(nil)
            }
            return self.resourceEntrySignal(
                resource: representation.resource,
                fallback: fallback
            )
        case let .file(file):
            if wallpaper.isPattern {
                return .single(nil)
            }
            return self.resourceEntrySignal(
                resource: file.file.resource,
                fallback: fallback
            )
        default:
            let colors = Self.wallpaperColors(wallpaper)
            let tint = Self.wallpaperTint(wallpaper, fallback: fallback)
            return deferred {
                guard let image = Self.generatedWallpaperImage(colors: colors, fallback: tint) else {
                    return .single(nil)
                }
                return .single(GhostBaseProfileHeaderBackgroundCacheEntry(image: image, tint: tint))
            }
            |> runOn(Queue.concurrentDefaultQueue())
        }
    }

    private func avatarEntrySignal(
        peer: EnginePeer,
        representation: TelegramMediaImageRepresentation,
        fallback: UIColor
    ) -> Signal<GhostBaseProfileHeaderBackgroundCacheEntry?, NoError>? {
        guard let signal = peerAvatarImage(
            account: self.context.account,
            peerReference: PeerReference(peer),
            authorOfMessage: nil,
            representation: representation,
            displayDimensions: CGSize(width: 360.0, height: 360.0),
            clipStyle: .none,
            blurred: true,
            inset: 0.0,
            emptyColor: nil,
            synchronousLoad: false
        ) else {
            return nil
        }
        return signal
        // Force tint sampling away from the main/layout path regardless of
        // which queue the Telegram avatar signal uses for delivery.
        |> deliverOn(Queue.concurrentDefaultQueue())
        |> map { versions -> GhostBaseProfileHeaderBackgroundCacheEntry? in
            guard let image = versions?.0 else {
                return nil
            }
            let tint = Self.sampledTint(from: image, fallback: fallback)
            return GhostBaseProfileHeaderBackgroundCacheEntry(image: image, tint: tint)
        }
    }

    private func resourceEntrySignal(
        resource: MediaResource,
        fallback: UIColor
    ) -> Signal<GhostBaseProfileHeaderBackgroundCacheEntry?, NoError> {
        let mediaBox = self.context.account.postbox.mediaBox
        return Signal { subscriber in
            let fetchDisposable = mediaBox.fetchedResource(resource, parameters: nil).start()
            let dataDisposable = (mediaBox.resourceData(resource)
            |> filter { $0.complete }
            |> take(1)
            |> mapToSignal { data -> Signal<GhostBaseProfileHeaderBackgroundCacheEntry?, NoError> in
                return deferred {
                    guard let image = UIImage(contentsOfFile: data.path) else {
                        return .single(nil)
                    }
                    let tint = Self.sampledTint(from: image, fallback: fallback)
                    return .single(GhostBaseProfileHeaderBackgroundCacheEntry(image: image, tint: tint))
                }
                |> runOn(Queue.concurrentDefaultQueue())
            }).start(next: { entry in
                subscriber.putNext(entry)
            }, completed: {
                subscriber.putCompletion()
            })
            return ActionDisposable {
                fetchDisposable.dispose()
                dataDisposable.dispose()
            }
        }
    }

    private static func wallpaperColors(_ wallpaper: TelegramWallpaper) -> [UInt32] {
        switch wallpaper {
        case let .color(value):
            return [value]
        case let .gradient(value):
            return value.colors
        case let .image(_, settings):
            return settings.colors
        case let .file(value):
            return value.settings.colors
        case .builtin:
            return []
        case .emoticon:
            return []
        }
    }

    private static func wallpaperTint(_ wallpaper: TelegramWallpaper, fallback: UIColor) -> UIColor {
        let colors = self.wallpaperColors(wallpaper)
        guard var result = colors.first.map({ UIColor(argb: $0) }) else {
            return fallback
        }
        if colors.count > 1 {
            for (index, value) in colors.dropFirst().enumerated() {
                let count = CGFloat(index + 2)
                result = result.mixedWith(UIColor(argb: value), alpha: 1.0 / count)
            }
        }
        return result
    }

    private static func generatedWallpaperImage(colors: [UInt32], fallback: UIColor) -> UIImage? {
        let resolvedColors: [UIColor]
        if colors.isEmpty {
            resolvedColors = [fallback, fallback]
        } else if colors.count == 1 {
            let color = UIColor(argb: colors[0])
            resolvedColors = [color, color]
        } else {
            resolvedColors = colors.map { UIColor(argb: $0) }
        }

        return generateImage(
            CGSize(width: 48.0, height: 48.0),
            contextGenerator: { size, context in
                let colorSpace = CGColorSpaceCreateDeviceRGB()
                var locations: [CGFloat] = resolvedColors.indices.map { index in
                    if resolvedColors.count <= 1 {
                        return 0.0
                    }
                    return CGFloat(index) / CGFloat(resolvedColors.count - 1)
                }
                guard let gradient = CGGradient(
                    colorsSpace: colorSpace,
                    colors: resolvedColors.map { $0.cgColor } as CFArray,
                    locations: &locations
                ) else {
                    context.setFillColor(fallback.cgColor)
                    context.fill(CGRect(origin: .zero, size: size))
                    return
                }
                context.drawLinearGradient(
                    gradient,
                    start: CGPoint(x: 0.0, y: 0.0),
                    end: CGPoint(x: size.width, y: size.height),
                    options: [.drawsBeforeStartLocation, .drawsAfterEndLocation]
                )
            },
            opaque: true,
            scale: 1.0
        )
    }

    private static func sampledTint(from image: UIImage, fallback: UIColor) -> UIColor {
        guard let cgImage = image.cgImage else {
            return fallback
        }
        var pixel = [UInt8](repeating: 0, count: 4)
        let rendered = pixel.withUnsafeMutableBytes { bytes -> Bool in
            guard let baseAddress = bytes.baseAddress,
                  let context = CGContext(
                    data: baseAddress,
                    width: 1,
                    height: 1,
                    bitsPerComponent: 8,
                    bytesPerRow: 4,
                    space: CGColorSpaceCreateDeviceRGB(),
                    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
                  ) else {
                return false
            }
            context.interpolationQuality = .medium
            context.draw(cgImage, in: CGRect(x: 0.0, y: 0.0, width: 1.0, height: 1.0))
            return true
        }
        guard rendered, pixel[3] > 8 else {
            return fallback
        }
        return UIColor(
            red: CGFloat(pixel[0]) / 255.0,
            green: CGFloat(pixel[1]) / 255.0,
            blue: CGFloat(pixel[2]) / 255.0,
            alpha: 1.0
        )
    }
}

'''
header = replace_once(
    header,
    "private let TitleNodeStateRegular = 0\nprivate let TitleNodeStateExpanded = 1\n\nfinal class PeerInfoHeaderNode: ASDisplayNode {",
    "private let TitleNodeStateRegular = 0\nprivate let TitleNodeStateExpanded = 1\n\n" + helper + "final class PeerInfoHeaderNode: ASDisplayNode {",
    "PeerInfoHeaderNode helper insertion",
)

header = replace_once(
    header,
    "    let backgroundBannerView: UIView\n    let backgroundCover = ComponentView<Empty>()\n",
    "    let backgroundBannerView: UIView\n    // MARK: GhostBase v1.1F PROFILEHEADERBLUR1 optional ownership\n    private let ghostBaseProfileHeaderBackgroundView: GhostBaseProfileHeaderBackgroundView?\n    let backgroundCover = ComponentView<Empty>()\n",
    "PeerInfoHeaderNode optional property",
)

header = replace_once(
    header,
    "        self.backgroundBannerView = UIView()\n        self.backgroundBannerView.clipsToBounds = true\n",
    "        self.backgroundBannerView = UIView()\n        if let settings = GhostBaseProfileBlurSettings.loadEnabled() {\n            self.ghostBaseProfileHeaderBackgroundView = GhostBaseProfileHeaderBackgroundView(context: context, settings: settings)\n        } else {\n            self.ghostBaseProfileHeaderBackgroundView = nil\n        }\n        self.backgroundBannerView.clipsToBounds = true\n",
    "PeerInfoHeaderNode conditional construction",
)

header = replace_once(
    header,
    "        self.view.addSubview(self.backgroundBannerView)\n        self.titleNodeContainer.addSubnode(self.titleNode)\n",
    "        self.view.addSubview(self.backgroundBannerView)\n        if let ghostBaseProfileHeaderBackgroundView = self.ghostBaseProfileHeaderBackgroundView {\n            self.backgroundBannerView.insertSubview(ghostBaseProfileHeaderBackgroundView, at: 0)\n            ghostBaseProfileHeaderBackgroundView.requestHeaderUpdate = { [weak self] in\n                self?.requestUpdateLayout?(false)\n            }\n        }\n        self.titleNodeContainer.addSubnode(self.titleNode)\n",
    "PeerInfoHeaderNode hierarchy insertion",
)

header = replace_once(
    header,
    "        let themeUpdated = self.presentationData?.theme !== presentationData.theme\n        self.presentationData = presentationData\n",
    "        let themeUpdated = self.presentationData?.theme !== presentationData.theme\n        self.presentationData = presentationData\n\n        if let ghostBaseProfileHeaderBackgroundView = self.ghostBaseProfileHeaderBackgroundView {\n            ghostBaseProfileHeaderBackgroundView.update(\n                peer: peer,\n                cachedData: screenData?.cachedData ?? cachedData,\n                presentationData: presentationData,\n                isSettings: isSettings\n            )\n        }\n",
    "PeerInfoHeaderNode source update",
)

for old, new, label in (
    (
        "        let regularNavigationContentsAccentColor: UIColor = peer?.effectiveProfileColor != nil ? .white : presentationData.theme.list.itemAccentColor\n",
        "        var regularNavigationContentsAccentColor: UIColor = peer?.effectiveProfileColor != nil ? .white : presentationData.theme.list.itemAccentColor\n",
        "regular accent mutability",
    ),
    (
        "        let regularNavigationContentsPrimaryColor: UIColor = peer?.effectiveProfileColor != nil ? .white : presentationData.theme.list.itemPrimaryTextColor\n",
        "        var regularNavigationContentsPrimaryColor: UIColor = peer?.effectiveProfileColor != nil ? .white : presentationData.theme.list.itemPrimaryTextColor\n",
        "regular primary mutability",
    ),
    (
        "        let regularContentButtonForegroundColor: UIColor = peer?.effectiveProfileColor != nil ? UIColor.white : presentationData.theme.list.itemAccentColor\n",
        "        var regularContentButtonForegroundColor: UIColor = peer?.effectiveProfileColor != nil ? UIColor.white : presentationData.theme.list.itemAccentColor\n",
        "regular foreground mutability",
    ),
    (
        "        let regularContentButtonBackgroundColor: UIColor\n",
        "        var regularContentButtonBackgroundColor: UIColor\n",
        "regular content button background mutability",
    ),
    (
        "        let regularHeaderButtonBackgroundColor: UIColor\n",
        "        var regularHeaderButtonBackgroundColor: UIColor\n",
        "regular header button background mutability",
    ),
    (
        "        let regularNavigationContentsSecondaryColor: UIColor\n",
        "        var regularNavigationContentsSecondaryColor: UIColor\n",
        "regular secondary mutability",
    ),
):
    header = replace_once(header, old, new, label)

header = replace_once(
    header,
    "        self.contentButtonBackgroundColor = regularNavigationContentsSecondaryColor.mixedWith(regularContentButtonBackgroundColor, alpha: 0.5)\n",
    r'''        // MARK: GhostBase v1.1F PROFILEHEADERBLUR1 palette application
        // Only the stock color variables are adjusted. Button nodes, labels,
        // badges, avatar/video avatar and transition geometry stay untouched.
        if let background = self.ghostBaseProfileHeaderBackgroundView,
           background.usesCustomBackground {
            let base = background.buttonTintColor ?? presentationData.theme.list.itemBlocksBackgroundColor
            regularNavigationContentsAccentColor = .white
            regularNavigationContentsPrimaryColor = .white
            regularNavigationContentsSecondaryColor = UIColor(white: 1.0, alpha: 0.72)
            regularContentButtonBackgroundColor = base.withAlphaComponent(0.30)
            regularHeaderButtonBackgroundColor = base.withAlphaComponent(0.24)
            regularContentButtonForegroundColor = .white
        }
        self.contentButtonBackgroundColor = regularNavigationContentsSecondaryColor.mixedWith(regularContentButtonBackgroundColor, alpha: 0.5)
''',
    "PeerInfoHeaderNode palette application",
)

# Use the same exact frame as the stock PeerInfoCoverComponent. The custom view
# never changes controller/header geometry and is always behind the stock cover.
cover_if = "        if let backgroundCoverView = self.backgroundCover.view as? PeerInfoCoverComponent.View {\n"
header = replace_once(
    header,
    cover_if,
    cover_if + "            backgroundCoverView.alpha = self.ghostBaseProfileHeaderBackgroundView?.usesCustomBackground == true ? 0.0 : 1.0\n",
    "PeerInfoHeaderNode stock cover visibility",
)

cover_end_anchor = "        if let profileGiftsContext, let peer {\n"
custom_frame_block = r'''        if let ghostBaseProfileHeaderBackgroundView = self.ghostBaseProfileHeaderBackgroundView {
            let frame = CGRect(
                origin: CGPoint(x: -bannerInset, y: bannerFrame.height - backgroundCoverSize.height),
                size: backgroundCoverSize
            )
            if additive {
                transition.updateFrameAdditive(view: ghostBaseProfileHeaderBackgroundView, frame: frame)
            } else {
                transition.updateFrame(view: ghostBaseProfileHeaderBackgroundView, frame: frame)
            }
        }

'''
header = replace_once(
    header,
    cover_end_anchor,
    custom_frame_block + cover_end_anchor,
    "PeerInfoHeaderNode custom background frame",
)

header_path.write_text(header, encoding="utf-8")

# ---------------------------------------------------------------------------
# 2. Remove every known PROFILEHUB/card path and synchronous personal-channel
#    history work from infoItems(), while preserving unrelated GhostBase rows.
# ---------------------------------------------------------------------------
profile_items_path = PEER_SOURCE / "PeerInfoProfileItems.swift"
profile_items = profile_items_path.read_text(encoding="utf-8")

profile_items = remove_region(
    profile_items,
    "// MARK: GhostBase v1.0ZG PROFILEINTEL3 personal channel storage",
    "enum InfoSection: Int, CaseIterable {",
    preserve_end=True,
)
profile_items = profile_items.replace("    case ghostbase\n", "")
profile_items = remove_region(
    profile_items,
    "// MARK: GhostBase v1.1B PROFILEHUB2 inline expandable profile block",
    "func infoItems(",
    preserve_end=True,
)

for marker in (
    "        // MARK: GhostBase v1.0ZG PROFILEINTEL3 observe personal channel\n",
    "        // MARK: GhostBase v1.1A PERSONALCHANNEL2 confirmed observation\n",
):
    profile_items = remove_region(
        profile_items,
        marker,
        "        if let cachedUserData = data.cachedData as? CachedUserData, cachedUserData.flags.contains(.unofficialSecurityRisk) {",
        preserve_end=True,
    )

metrics_marker = "    // MARK: GhostBase v0.4A peer metrics card with toggles\n"
if metrics_marker in profile_items:
    profile_items = remove_region(
        profile_items,
        metrics_marker,
        "    let bioContextAction:",
        preserve_end=True,
    )

trailing_markers = (
    "    // MARK: GhostBase v1.0ZG PROFILEINTEL3 history action\n",
    "    // MARK: GhostBase v1.0ZG GIFTHISTORY1 profile action\n",
    "    // MARK: GhostBase v1.0ZH PROFILEUI1 integrated profile cards\n",
    "    // MARK: GhostBase v1.1B PROFILEHUB2 inline rows\n",
    "    // MARK: GhostBase v1.1C PROFILEGLASS1 inline hub\n",
    "    // MARK: GhostBase v1.1D PROFILESELECTOR2 one native glass block\n",
    "    // MARK: GhostBase v1.1E PROFILEHUBNATIVE3 item\n",
    "    // MARK: GhostBase v1.1F PROFILEHUB4 item\n",
)
positions = [profile_items.index(marker) for marker in trailing_markers if marker in profile_items]
if positions:
    start = min(positions)
    result_anchor = "    var result: [(AnyHashable, [PeerInfoScreenItem])] = []\n"
    end = profile_items.find(result_anchor, start)
    if end < 0:
        fail("PeerInfoProfileItems trailing legacy block has no result anchor")
    profile_items = profile_items[:start] + profile_items[end:]

profile_items_path.write_text(profile_items, encoding="utf-8")

for legacy_file in (
    "GhostBaseProfileHubItem.swift",
    "GhostBaseProfileBackdropNode.swift",
    "GhostBaseColdGlassSectionView.swift",
):
    path = PEER_SOURCE / legacy_file
    if path.exists():
        path.unlink()

# ---------------------------------------------------------------------------
# 3. Replace the process-global palette/observer runtime with a tiny settings
#    snapshot. Existing non-profile Glass callers keep their old public API.
# ---------------------------------------------------------------------------
GLASS_RUNTIME.parent.mkdir(parents=True, exist_ok=True)
GLASS_RUNTIME.write_text(r'''import Foundation
import UIKit

// MARK: GhostBase v1.1F PROFILEBLURSETTINGS1
public enum GhostBaseGlassStyle {
    public static let enabledKey = "GhostBase.Glass.Enabled"

    public static var isEnabled: Bool {
        if let value = UserDefaults.standard.object(forKey: self.enabledKey) as? Bool {
            return value
        }
        return true
    }

    public static var usesReducedEffects: Bool {
        return UIAccessibility.isReduceTransparencyEnabled || ProcessInfo.processInfo.isLowPowerModeEnabled
    }

    public static func setEnabled(_ value: Bool) {
        UserDefaults.standard.set(value, forKey: self.enabledKey)
    }

    // Pure compatibility tokens for the existing lightweight settings/gifts
    // surfaces. They hold no peer palette, observers or persisted tint state.
    public static var backdropOverlayAlpha: CGFloat {
        return self.usesReducedEffects ? 0.78 : 0.52
    }

    public static var coldSurfaceAlpha: CGFloat {
        return self.usesReducedEffects ? 0.92 : 0.70
    }

    public static var lightweightSurfaceAlpha: CGFloat {
        return self.usesReducedEffects ? 0.96 : 0.82
    }

    public static var borderAlpha: CGFloat {
        return self.usesReducedEffects ? 0.08 : 0.20
    }

    public static let compactCornerRadius: CGFloat = 13.0
    public static let cardCornerRadius: CGFloat = 18.0

    public static func coldFillColor(_ base: UIColor) -> UIColor {
        guard self.isEnabled else {
            return base
        }
        return base.withAlphaComponent(self.coldSurfaceAlpha)
    }

    public static func lightweightFillColor(_ base: UIColor) -> UIColor {
        guard self.isEnabled else {
            return base
        }
        return base.withAlphaComponent(self.lightweightSurfaceAlpha)
    }

    public static func lightweightTintColor(_ base: UIColor) -> UIColor {
        guard self.isEnabled else {
            return base
        }
        return base.withAlphaComponent(self.usesReducedEffects ? 0.94 : 0.18)
    }

    public static func borderColor(_ base: UIColor) -> UIColor {
        guard self.isEnabled else {
            return .clear
        }
        return base.withAlphaComponent(self.borderAlpha)
    }

    public static func activeTintColor(fallback: UIColor) -> UIColor {
        // Never inherit a process-global or previous-peer tint.
        return fallback
    }
}

public struct GhostBaseProfileBlurSettings: Equatable {
    public static let avatarBlurKey = "GhostBase.ProfileBlur.Avatar"
    public static let tintKey = "GhostBase.ProfileBlur.Tint"
    public static let reducedKey = "GhostBase.ProfileBlur.Reduced"

    public let avatarBlurInProfile: Bool
    public let tintEnabled: Bool
    public let reducedBlur: Bool

    // Reads the master key first. Child settings are not read and no profile
    // object is created when the effect is disabled.
    public static func loadEnabled() -> GhostBaseProfileBlurSettings? {
        guard GhostBaseGlassStyle.isEnabled else {
            return nil
        }
        let defaults = UserDefaults.standard
        return GhostBaseProfileBlurSettings(
            avatarBlurInProfile: defaults.object(forKey: self.avatarBlurKey) as? Bool ?? true,
            tintEnabled: defaults.object(forKey: self.tintKey) as? Bool ?? true,
            reducedBlur: defaults.object(forKey: self.reducedKey) as? Bool ?? false
        )
    }
}
''', encoding="utf-8")

# ---------------------------------------------------------------------------
# 4. Add the four Whitegram-equivalent controls to the existing Appearance page.
# ---------------------------------------------------------------------------
settings = SETTINGS.read_text(encoding="utf-8")
if "GhostBase v1.1F PROFILEBLURSETTINGS1" not in settings:
    settings = replace_once(
        settings,
        '    static let glassEnabled = "GhostBase.Glass.Enabled"\n',
        '    // MARK: GhostBase v1.1F PROFILEBLURSETTINGS1\n'
        '    static let glassEnabled = "GhostBase.Glass.Enabled"\n'
        '    static let profileAvatarBlur = "GhostBase.ProfileBlur.Avatar"\n'
        '    static let profileBlurTint = "GhostBase.ProfileBlur.Tint"\n'
        '    static let profileBlurReduced = "GhostBase.ProfileBlur.Reduced"\n',
        "settings keys",
    )
    settings = replace_once(
        settings,
        "    var glassEnabled: Bool\n    var messageSeconds: Bool\n",
        "    var glassEnabled: Bool\n    var profileAvatarBlur: Bool\n    var profileBlurTint: Bool\n    var profileBlurReduced: Bool\n    var messageSeconds: Bool\n",
        "settings state properties",
    )
    settings = replace_once(
        settings,
        "            glassEnabled: ghostBaseBool(\n                GhostBaseKey.glassEnabled,\n                defaultValue: true\n            ),\n            messageSeconds: ghostBaseBool(\n",
        "            glassEnabled: ghostBaseBool(\n                GhostBaseKey.glassEnabled,\n                defaultValue: true\n            ),\n            profileAvatarBlur: ghostBaseBool(\n                GhostBaseKey.profileAvatarBlur,\n                defaultValue: true\n            ),\n            profileBlurTint: ghostBaseBool(\n                GhostBaseKey.profileBlurTint,\n                defaultValue: true\n            ),\n            profileBlurReduced: ghostBaseBool(\n                GhostBaseKey.profileBlurReduced,\n                defaultValue: false\n            ),\n            messageSeconds: ghostBaseBool(\n",
        "settings load",
    )
    settings = replace_once(
        settings,
        "        UserDefaults.standard.set(\n            self.glassEnabled,\n            forKey: GhostBaseKey.glassEnabled\n        )\n        UserDefaults.standard.set(\n            self.messageSeconds,\n",
        "        UserDefaults.standard.set(\n            self.glassEnabled,\n            forKey: GhostBaseKey.glassEnabled\n        )\n        UserDefaults.standard.set(self.profileAvatarBlur, forKey: GhostBaseKey.profileAvatarBlur)\n        UserDefaults.standard.set(self.profileBlurTint, forKey: GhostBaseKey.profileBlurTint)\n        UserDefaults.standard.set(self.profileBlurReduced, forKey: GhostBaseKey.profileBlurReduced)\n        UserDefaults.standard.set(\n            self.messageSeconds,\n",
        "settings save",
    )

    appearance_start = settings.find("    if page == .appearance {\n")
    appearance_end = settings.find("\n    if page == .about {\n", appearance_start)
    if appearance_start < 0 or appearance_end < 0:
        fail("appearance page region missing")
    appearance = r'''    if page == .appearance {
        return [
            .header(0, "Фон профиля"),
            .toggle(
                0,
                1,
                GhostBaseKey.glassEnabled,
                "Эффект фона профиля",
                state.glassEnabled
            ),
            .toggle(
                0,
                2,
                GhostBaseKey.profileAvatarBlur,
                "Размывать аватар в профиле",
                state.profileAvatarBlur
            ),
            .toggle(
                0,
                3,
                GhostBaseKey.profileBlurTint,
                "Цветовой tint",
                state.profileBlurTint
            ),
            .toggle(
                0,
                4,
                GhostBaseKey.profileBlurReduced,
                "Облегчённое размытие",
                state.profileBlurReduced
            ),
            .info(
                0,
                "Выключенный главный эффект не создаёт дополнительные profile views, observers или image/palette pipeline. Новые значения применяются при следующем открытии профиля."
            ),
            .header(1, "Прочее"),
            .toggle(
                1,
                1,
                GhostBaseKey.messageSeconds,
                "Показывать секунды в сообщениях",
                state.messageSeconds
            ),
            .toggle(
                1,
                2,
                GhostBaseKey.hideOwnPhone,
                "Скрывать мой номер",
                state.hideOwnPhone
            ),
            .info(
                1,
                "Номер скрывается только локально в интерфейсе GhostBase. Экран изменения профиля и смены номера остаётся доступен."
            )
        ]
    }
'''
    settings = settings[:appearance_start] + appearance + settings[appearance_end:]

    settings = replace_once(
        settings,
        "            case GhostBaseKey.glassEnabled:\n                // MARK: GhostBase v1.1F SETTINGS4 isolated toggle\n                updated.glassEnabled = value\n                UserDefaults.standard.set(value, forKey: GhostBaseKey.glassEnabled)\n\n            case GhostBaseKey.messageSeconds:\n",
        "            case GhostBaseKey.glassEnabled:\n                updated.glassEnabled = value\n                UserDefaults.standard.set(value, forKey: GhostBaseKey.glassEnabled)\n\n            case GhostBaseKey.profileAvatarBlur:\n                updated.profileAvatarBlur = value\n                UserDefaults.standard.set(value, forKey: GhostBaseKey.profileAvatarBlur)\n\n            case GhostBaseKey.profileBlurTint:\n                updated.profileBlurTint = value\n                UserDefaults.standard.set(value, forKey: GhostBaseKey.profileBlurTint)\n\n            case GhostBaseKey.profileBlurReduced:\n                updated.profileBlurReduced = value\n                UserDefaults.standard.set(value, forKey: GhostBaseKey.profileBlurReduced)\n\n            case GhostBaseKey.messageSeconds:\n",
        "settings update switch",
    )

# Remove the dead PROFILEHUB/Profile Metrics controls themselves. They no
# longer drive any materialized profile UI and must not remain as misleading
# settings after the old architecture is removed.
for block, label in (
    (
        '    static let profileEnabled = "GhostBase.Profile.Enabled"\n'
        '    static let showIds = "GhostBase.Profile.ShowIds"\n'
        '    static let showDCs = "GhostBase.Profile.ShowDCs"\n'
        '    static let showRegistration = "GhostBase.Profile.ShowRegistration"\n\n',
        "legacy profile keys",
    ),
    (
        '    var profileEnabled: Bool\n'
        '    var showIds: Bool\n'
        '    var showDCs: Bool\n'
        '    var showRegistration: Bool\n\n',
        "legacy profile state",
    ),
    (
        '            profileEnabled: ghostBaseBool(GhostBaseKey.profileEnabled, defaultValue: true),\n'
        '            showIds: ghostBaseBool(GhostBaseKey.showIds, defaultValue: true),\n'
        '            showDCs: ghostBaseBool(GhostBaseKey.showDCs, defaultValue: true),\n'
        '            showRegistration: ghostBaseBool(GhostBaseKey.showRegistration, defaultValue: true),\n',
        "legacy profile state load",
    ),
    (
        '        UserDefaults.standard.set(self.profileEnabled, forKey: GhostBaseKey.profileEnabled)\n'
        '        UserDefaults.standard.set(self.showIds, forKey: GhostBaseKey.showIds)\n'
        '        UserDefaults.standard.set(self.showDCs, forKey: GhostBaseKey.showDCs)\n'
        '        UserDefaults.standard.set(self.showRegistration, forKey: GhostBaseKey.showRegistration)\n\n',
        "legacy profile state save",
    ),
    (
        '            .toggle(0, 1, GhostBaseKey.profileEnabled, "Карточка профиля", state.profileEnabled),\n'
        '            .toggle(0, 2, GhostBaseKey.showIds, "Показывать ID", state.showIds),\n'
        '            .toggle(0, 3, GhostBaseKey.showDCs, "Показывать DC", state.showDCs),\n'
        '            .toggle(0, 4, GhostBaseKey.showRegistration, "Дата регистрации", state.showRegistration),\n',
        "legacy home profile toggles",
    ),
    (
        '    entries.append(.header(profile, "Profile Metrics"))\n'
        '    entries.append(.toggle(profile, 1, GhostBaseKey.profileEnabled, "Enable Profile Card", state.profileEnabled))\n'
        '    entries.append(.toggle(profile, 2, GhostBaseKey.showIds, "Show IDs", state.showIds))\n'
        '    entries.append(.toggle(profile, 3, GhostBaseKey.showDCs, "Show DCs", state.showDCs))\n'
        '    entries.append(.toggle(profile, 4, GhostBaseKey.showRegistration, "Show Registration Date", state.showRegistration))\n\n',
        "legacy fallback profile section",
    ),
    (
        '            if !next.showIds && !next.showDCs && !next.showRegistration {\n'
        '                next.profileEnabled = false\n'
        '            } else if next.showIds || next.showDCs || next.showRegistration {\n'
        '                if !current.showIds && !current.showDCs && !current.showRegistration {\n'
        '                    next.profileEnabled = true\n'
        '                }\n'
        '            }\n\n',
        "legacy profile state coupling",
    ),
):
    settings = remove_exact_if_present(settings, block, label)

settings = remove_region(
    settings,
    "            case GhostBaseKey.profileEnabled:\n",
    "            case GhostBaseKey.saveDeleted:\n",
    preserve_end=True,
)

# Renumber the remaining home controls after removing the dead profile card.
settings = settings.replace(
    '            .toggle(0, 5, GhostBaseKey.localStarsEnabled, "Локальный баланс Stars", state.localStarsEnabled),\n'
    '            .input(0, 6, GhostBaseKey.localStarsAmount, "Баланс Stars", state.localStarsAmount),\n',
    '            .toggle(0, 1, GhostBaseKey.localStarsEnabled, "Локальный баланс Stars", state.localStarsEnabled),\n'
    '            .input(0, 2, GhostBaseKey.localStarsAmount, "Баланс Stars", state.localStarsAmount),\n',
    1,
)
settings = settings.replace(
    "Profile Metrics affects the profile card after reopening a profile. ",
    "Profile Blur settings apply when a profile is opened. ",
)

settings = re.sub(r"Version: v1\.1[^\n]*", "Version: v1.1F-profile-header", settings)
settings = settings.replace("Base: Official Telegram 12.8", "Base: Official Telegram 12.9.2")
settings = settings.replace("Base: Official Telegram 12.7", "Base: Official Telegram 12.9.2")
SETTINGS.write_text(settings, encoding="utf-8")

print("[V11F] PROFILEHEADERBLUR1 applied")
print(f"[V11F] source={SOURCE_ROOT}")
print(f"[V11F] official={OFFICIAL_ROOT}")
