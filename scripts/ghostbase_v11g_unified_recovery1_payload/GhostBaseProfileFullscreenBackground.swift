import Foundation
import UIKit
import Display
import Postbox
import TelegramCore
import AvatarNode
import AccountContext
import SwiftSignalKit
import TelegramPresentationData
import PhotoResources


// MARK: GhostBase v1.1G PROFILE_RUNTIME1
enum GhostBaseProfileGlassRuntime {
    static func loadSettings() -> GhostBaseProfileBlurSettings? {
        return GhostBaseProfileBlurSettings.loadEnabled()
    }

    static func shouldBlendStockCover(
        settings: GhostBaseProfileBlurSettings?,
        peer: EnginePeer?,
        cachedData: EngineCachedPeerData?,
        presentationData: PresentationData,
        isSettings: Bool
    ) -> Bool {
        guard let settings, !isSettings else {
            return false
        }
        if let cachedData = cachedData as? CachedUserData, cachedData.wallpaper != nil {
            return true
        }
        if let cachedData = cachedData as? CachedChannelData, cachedData.wallpaper != nil {
            return true
        }
        if presentationData.chatWallpaper != presentationData.theme.chat.defaultWallpaper {
            return true
        }
        if let peer {
            if let status = peer.emojiStatus, case .starGift = status.content {
                return false
            }
            if peer.effectiveProfileColor != nil {
                return false
            }
            if settings.avatarBlurInProfile, !peer.profileImageRepresentations.isEmpty {
                return true
            }
        }
        return false
    }
}

// MARK: GhostBase v1.1G PROFILEFULLSCREEN1
// The effect is owned by PeerInfoScreenNode and is optional by construction.
// With the main switch off this type is never instantiated, so there are no
// additional views, observers, signals, image work or palette work.
private final class GhostBaseProfileBackgroundCacheEntry: NSObject {
    let image: UIImage
    let tint: UIColor

    init(image: UIImage, tint: UIColor) {
        self.image = image
        self.tint = tint
    }
}

private enum GhostBaseProfileBackgroundSourceKind: Int {
    case personalWallpaper
    case globalWallpaper
    case premiumProfile
    case avatar
    case telegramTheme
}

private struct GhostBaseProfileBackgroundStateKey: Equatable {
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

final class GhostBaseProfileBackgroundView: UIView {
    private static let imageCache = NSCache<NSString, GhostBaseProfileBackgroundCacheEntry>()

    private let context: AccountContext
    private let settings: GhostBaseProfileBlurSettings

    // Exactly one reusable image view, one persistent visual-effect view and
    // one independent tint/dimming view. They are created once in init().
    private let imageView: UIImageView
    private let blurView: UIVisualEffectView
    private let tintView: UIView

    private let sourceDisposable = MetaDisposable()
    private var currentStateKey: GhostBaseProfileBackgroundStateKey?
    private var currentLoadKey: String?

    private(set) var usesCustomBackground = false
    var requestUpdate: (() -> Void)?

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
    ) -> GhostBaseProfileBackgroundSource {
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

        // 3) Premium profile color is a separate state source. It is never
        // mixed into the avatar cache or avatar-derived tint.
        if let peer {
            if let status = peer.emojiStatus,
               case let .starGift(_, _, _, _, _, innerColor, outerColor, _, _) = status.content {
                let main = UIColor(rgb: UInt32(bitPattern: innerColor))
                let secondary = UIColor(rgb: UInt32(bitPattern: outerColor))
                return .premium(
                    main,
                    secondary,
                    "gift:\(innerColor):\(outerColor)"
                )
            }
            if let profileColor = peer.effectiveProfileColor {
                let colors = self.context.peerNameColors.getProfile(
                    profileColor,
                    dark: presentationData.theme.overallDarkAppearance
                )
                return .premium(
                    colors.main,
                    colors.secondary ?? colors.main,
                    "profile:\(String(describing: profileColor)):\(presentationData.theme.overallDarkAppearance)"
                )
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
        source: GhostBaseProfileBackgroundSource,
        peer: EnginePeer?,
        presentationData: PresentationData
    ) -> GhostBaseProfileBackgroundStateKey {
        let peerId = peer?.id.toInt64()
        let themeIdentity = ObjectIdentifier(presentationData.theme)
        switch source {
        case let .wallpaper(wallpaper, kind):
            return GhostBaseProfileBackgroundStateKey(
                peerId: peerId,
                kind: kind,
                wallpaper: wallpaper,
                avatarResourceId: nil,
                premiumIdentity: nil,
                themeIdentity: themeIdentity
            )
        case let .premium(_, _, identity):
            return GhostBaseProfileBackgroundStateKey(
                peerId: peerId,
                kind: .premiumProfile,
                wallpaper: nil,
                avatarResourceId: nil,
                premiumIdentity: identity,
                themeIdentity: themeIdentity
            )
        case let .avatar(_, _, resourceId):
            return GhostBaseProfileBackgroundStateKey(
                peerId: peerId,
                kind: .avatar,
                wallpaper: nil,
                avatarResourceId: resourceId,
                premiumIdentity: nil,
                themeIdentity: themeIdentity
            )
        case .telegramTheme:
            return GhostBaseProfileBackgroundStateKey(
                peerId: peerId,
                kind: .telegramTheme,
                wallpaper: nil,
                avatarResourceId: nil,
                premiumIdentity: nil,
                themeIdentity: themeIdentity
            )
        }
    }

    private func apply(
        source: GhostBaseProfileBackgroundSource,
        stateKey: GhostBaseProfileBackgroundStateKey,
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
            effectStyle = reduced ? .systemUltraThinMaterialDark : .systemThinMaterialDark
        } else {
            effectStyle = reduced ? .systemUltraThinMaterialLight : .systemThinMaterialLight
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

            // Never generate wallpaper pixels from PeerInfoScreenNode layout.
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
                self.requestUpdate?()
            }))

        case let .premium(main, secondary, identity):
            self.usesCustomBackground = true
            self.backgroundColor = main
            self.applyTint(main, fallback: main, isDark: isDark, reduced: reduced)

            let cacheKey = "premium:\(identity)" as NSString
            if let cached = Self.imageCache.object(forKey: cacheKey) {
                self.imageView.image = cached.image
                self.applyTint(cached.tint, fallback: main, isDark: isDark, reduced: reduced)
                return
            }

            self.imageView.image = nil
            let loadKey = cacheKey as String
            self.currentLoadKey = loadKey
            self.sourceDisposable.set((deferred {
                guard let image = Self.generatedGradientImage(
                    colors: [main, secondary]
                ) else {
                    return .single(nil)
                }
                return .single(
                    GhostBaseProfileBackgroundCacheEntry(
                        image: image,
                        tint: main.mixedWith(secondary, alpha: 0.35)
                    )
                )
            }
            |> runOn(Queue.concurrentDefaultQueue())
            |> deliverOnMainQueue).start(next: { [weak self] entry in
                guard let self, self.currentLoadKey == loadKey, let entry else {
                    return
                }
                Self.imageCache.setObject(entry, forKey: cacheKey)
                self.imageView.image = entry.image
                self.applyTint(entry.tint, fallback: main, isDark: isDark, reduced: reduced)
                self.requestUpdate?()
            }))

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
                self.requestUpdate?()
            }))

        case .telegramTheme:
            self.usesCustomBackground = false
            self.imageView.image = nil
            self.tintView.backgroundColor = .clear
            self.backgroundColor = .clear
        }
    }

    private func applyTint(
        _ color: UIColor,
        fallback: UIColor,
        isDark: Bool,
        reduced: Bool
    ) {
        if self.settings.tintEnabled {
            self.tintView.backgroundColor = color.withAlphaComponent(reduced ? 0.10 : 0.12)
        } else {
            // Tint-off is neutral dimming, not a universal accent color.
            self.tintView.backgroundColor = UIColor.black.withAlphaComponent(isDark ? 0.10 : 0.06)
        }
    }

    private func wallpaperEntrySignal(
        wallpaper: TelegramWallpaper,
        fallback: UIColor
    ) -> Signal<GhostBaseProfileBackgroundCacheEntry?, NoError> {
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
                return .single(GhostBaseProfileBackgroundCacheEntry(image: image, tint: tint))
            }
            |> runOn(Queue.concurrentDefaultQueue())
        }
    }

    private func avatarEntrySignal(
        peer: EnginePeer,
        representation: TelegramMediaImageRepresentation,
        fallback: UIColor
    ) -> Signal<GhostBaseProfileBackgroundCacheEntry?, NoError>? {
        guard let signal = peerAvatarImage(
            account: self.context.account,
            peerReference: PeerReference(peer),
            authorOfMessage: nil,
            representation: representation,
            displayDimensions: CGSize(width: 360.0, height: 360.0),
            clipStyle: .none,
            blurred: false,
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
        |> map { versions -> GhostBaseProfileBackgroundCacheEntry? in
            guard let image = versions?.0 else {
                return nil
            }
            let tint = Self.sampledTint(from: image, fallback: fallback)
            return GhostBaseProfileBackgroundCacheEntry(image: image, tint: tint)
        }
    }

    private func resourceEntrySignal(
        resource: MediaResource,
        fallback: UIColor
    ) -> Signal<GhostBaseProfileBackgroundCacheEntry?, NoError> {
        let mediaBox = self.context.account.postbox.mediaBox
        return Signal { subscriber in
            let fetchDisposable = mediaBox.fetchedResource(resource, parameters: nil).start()
            let dataDisposable = (mediaBox.resourceData(resource)
            |> filter { $0.complete }
            |> take(1)
            |> mapToSignal { data -> Signal<GhostBaseProfileBackgroundCacheEntry?, NoError> in
                return deferred {
                    guard let image = UIImage(contentsOfFile: data.path) else {
                        return .single(nil)
                    }
                    let tint = Self.sampledTint(from: image, fallback: fallback)
                    return .single(GhostBaseProfileBackgroundCacheEntry(image: image, tint: tint))
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

    private static func generatedGradientImage(colors: [UIColor]) -> UIImage? {
        let resolved = colors.isEmpty ? [UIColor.black, UIColor.black] : colors
        return generateImage(
            CGSize(width: 64.0, height: 64.0),
            contextGenerator: { size, context in
                let colorSpace = CGColorSpaceCreateDeviceRGB()
                var locations: [CGFloat] = resolved.indices.map { index in
                    if resolved.count <= 1 {
                        return 0.0
                    }
                    return CGFloat(index) / CGFloat(resolved.count - 1)
                }
                guard let gradient = CGGradient(
                    colorsSpace: colorSpace,
                    colors: resolved.map { $0.cgColor } as CFArray,
                    locations: &locations
                ) else {
                    context.setFillColor(resolved[0].cgColor)
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
