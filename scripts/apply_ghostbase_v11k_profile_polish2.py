#!/usr/bin/env python3

import os
from pathlib import Path


ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        "/root/gb_builder/work/swiftgram-src",
    )
)

P = (
    ROOT
    / "submodules/TelegramUI/Components/PeerInfo/"
      "PeerInfoScreen/Sources"
)

BG = P / "GhostBaseProfileFullscreenBackground.swift"
HDR = P / "PeerInfoHeaderNode.swift"
SEC = P / "PeerInfoScreenItemSectionContainerNode.swift"
SCR = P / "PeerInfoScreen.swift"
REP = P / "GhostBaseProfileReportPaneNode.swift"
PANE = P / "PeerInfoPaneContainerNode.swift"

GROUPS = (
    P
    / "Panes/PeerInfoGroupsInCommonPaneNode.swift"
)

MEMBERS = (
    P
    / "Panes/PeerInfoMembersPane.swift"
)

GIFTS = (
    ROOT
    / "submodules/TelegramUI/Components/PeerInfo/"
      "PeerInfoVisualMediaPaneNode/Sources/"
      "PeerInfoGiftsPaneNode.swift"
)

SETTINGS = (
    ROOT
    / "submodules/SettingsUI/Sources/GhostBase/"
      "GhostBaseSettingsController.swift"
)

STAR = (
    ROOT
    / "submodules/TelegramCore/Sources/"
      "TelegramEngine/Payments/StarGifts.swift"
)


for path in (
    BG,
    HDR,
    SEC,
    SCR,
    REP,
    PANE,
    GROUPS,
    MEMBERS,
    GIFTS,
):
    if not path.is_file():
        raise RuntimeError(
            f"[V11K] missing: {path}"
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
            f"[V11K] {label}: "
            f"expected 1 found {count}"
        )

    return text.replace(
        old,
        new,
        1,
    )


def function_span(
    text: str,
    signature: str,
):
    start = text.find(signature)

    if start < 0:
        raise RuntimeError(
            f"[V11K] function missing: "
            f"{signature}"
        )

    brace = text.find(
        "{",
        start,
    )

    if brace < 0:
        raise RuntimeError(
            f"[V11K] opening brace missing: "
            f"{signature}"
        )

    depth = 0
    in_string = False
    escaped = False

    for index in range(
        brace,
        len(text),
    ):
        char = text[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False

            continue

        if char == '"':
            in_string = True

        elif char == "{":
            depth += 1

        elif char == "}":
            depth -= 1

            if depth == 0:
                end = index + 1

                if (
                    end < len(text)
                    and text[end] == "\n"
                ):
                    end += 1

                return start, end

    raise RuntimeError(
        f"[V11K] unbalanced function: "
        f"{signature}"
    )


def apply_patch():
    bg = BG.read_text(
        encoding="utf-8"
    )

    hdr = HDR.read_text(
        encoding="utf-8"
    )

    sec = SEC.read_text(
        encoding="utf-8"
    )

    scr = SCR.read_text(
        encoding="utf-8"
    )

    rep = REP.read_text(
        encoding="utf-8"
    )

    pane = PANE.read_text(
        encoding="utf-8"
    )

    groups = GROUPS.read_text(
        encoding="utf-8"
    )

    members = MEMBERS.read_text(
        encoding="utf-8"
    )

    gifts = GIFTS.read_text(
        encoding="utf-8"
    )


    # ========================================================
    # BACKGROUND SOURCE / COVER
    # ========================================================

    start, end = function_span(
        bg,
        "    static func shouldBlendStockCover("
    )

    bg = (
        bg[:start]
        + '''    static func shouldBlendStockCover(
        settings: GhostBaseProfileBlurSettings?,
        peer: EnginePeer?,
        cachedData: EngineCachedPeerData?,
        presentationData: PresentationData,
        isSettings: Bool
    ) -> Bool {
        guard let settings else {
            return false
        }

        if !isSettings {
            if let cachedData = cachedData as? CachedUserData,
               cachedData.wallpaper != nil {
                return true
            }

            if let cachedData = cachedData as? CachedChannelData,
               cachedData.wallpaper != nil {
                return true
            }

            if presentationData.chatWallpaper
                != presentationData.theme.chat.defaultWallpaper {
                return true
            }
        }

        guard let peer else {
            return false
        }

        if settings.avatarBlurInProfile,
           !peer.profileImageRepresentations.isEmpty {
            return true
        }

        if let status = peer.emojiStatus,
           case .starGift = status.content {
            return true
        }

        if peer.effectiveProfileColor != nil {
            return true
        }

        return !peer.profileImageRepresentations.isEmpty
    }
'''
        + bg[end:]
    )


    # ========================================================
    # PERSISTENT SOURCE TONE
    # ========================================================

    bg = replace_once(
        bg,
        "cache.countLimit = 20",
        "cache.countLimit = 64",
        "image cache size",
    )


    cache_anchor = '''    private static let imageCache: NSCache<NSString, GhostBaseProfileBackgroundCacheEntry> = {
        let cache = NSCache<NSString, GhostBaseProfileBackgroundCacheEntry>()
        cache.countLimit = 64
        return cache
    }()
'''


    cache_extra = cache_anchor + '''
    // MARK: GhostBase v1.1K PROFILEPOLISH2
    //
    // Actual image resources remain owned/cached by Telegram MediaBox.
    // Only sampled tone is persisted by source identity.
    private static let persistentToneKey =
        "GhostBase.ProfileVisualTone.V11K"

    private static let persistentToneOrderKey =
        "GhostBase.ProfileVisualToneOrder.V11K"

    private static let persistentToneLock =
        NSLock()

    private static let maximumPersistentTones =
        96

    private static func persistentTint(
        identity: String
    ) -> UIColor? {
        self.persistentToneLock.lock()

        defer {
            self.persistentToneLock.unlock()
        }

        let defaults =
            UserDefaults.standard

        guard
            let values =
                defaults.object(
                    forKey:
                        self.persistentToneKey
                )
                as? [String: String],
            let encoded =
                values[identity]
        else {
            return nil
        }

        let parts =
            encoded.split(
                separator: ","
            )

        guard
            parts.count == 3,
            let red =
                Double(parts[0]),
            let green =
                Double(parts[1]),
            let blue =
                Double(parts[2])
        else {
            return nil
        }

        return UIColor(
            red: CGFloat(red),
            green: CGFloat(green),
            blue: CGFloat(blue),
            alpha: 1.0
        )
    }

    private static func storePersistentTint(
        _ color: UIColor,
        identity: String
    ) {
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
            return
        }

        self.persistentToneLock.lock()

        defer {
            self.persistentToneLock.unlock()
        }

        let defaults =
            UserDefaults.standard

        var values =
            defaults.object(
                forKey:
                    self.persistentToneKey
            )
            as? [String: String]
            ?? [:]

        var order =
            defaults.stringArray(
                forKey:
                    self.persistentToneOrderKey
            )
            ?? []

        values[identity] =
            "\\(Double(red)),\\(Double(green)),\\(Double(blue))"

        order.removeAll(
            where: {
                $0 == identity
            }
        )

        order.append(
            identity
        )

        while order.count
            > self.maximumPersistentTones {

            let removed =
                order.removeFirst()

            values.removeValue(
                forKey: removed
            )
        }

        defaults.set(
            values,
            forKey:
                self.persistentToneKey
        )

        defaults.set(
            order,
            forKey:
                self.persistentToneOrderKey
        )
    }
'''


    bg = replace_once(
        bg,
        cache_anchor,
        cache_extra,
        "persistent tone cache",
    )


    # ========================================================
    # SOURCE SELECTOR
    #
    # chat:
    # personal wallpaper
    # -> global custom wallpaper
    # -> avatar/Premium selector
    #
    # Settings:
    # avatar/Premium selector only
    # ========================================================

    start, end = function_span(
        bg,
        "    private func resolveSource("
    )


    resolve = '''    private func resolveSource(
        peer: EnginePeer?,
        cachedData: EngineCachedPeerData?,
        presentationData: PresentationData,
        isSettings: Bool
    ) -> GhostBaseProfileBackgroundSource {
        if !isSettings {
            if let cachedData = cachedData as? CachedUserData,
               let wallpaper = cachedData.wallpaper {

                return .wallpaper(
                    wallpaper,
                    .personalWallpaper
                )
            }

            if let cachedData = cachedData as? CachedChannelData,
               let wallpaper = cachedData.wallpaper {

                return .wallpaper(
                    wallpaper,
                    .personalWallpaper
                )
            }

            if presentationData.chatWallpaper
                != presentationData.theme.chat.defaultWallpaper {

                return .wallpaper(
                    presentationData.chatWallpaper,
                    .globalWallpaper
                )
            }
        }

        if let peer {
            // Existing toggle becomes a real source selector.
            //
            // ON:
            // avatar -> Premium
            //
            // OFF:
            // Premium -> avatar fallback

            if self.settings.avatarBlurInProfile,
               let representation =
                    peer.profileImageRepresentations.last {

                let resourceId =
                    String(
                        describing:
                            representation.resource.id
                    )

                return .avatar(
                    peer,
                    representation,
                    resourceId
                )
            }

            if let status = peer.emojiStatus,
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

                let main =
                    UIColor(
                        rgb:
                            UInt32(
                                bitPattern:
                                    innerColor
                            )
                    )

                let secondary =
                    UIColor(
                        rgb:
                            UInt32(
                                bitPattern:
                                    outerColor
                            )
                    )

                return .premium(
                    main,
                    secondary,
                    "gift:\\(innerColor):\\(outerColor)"
                )
            }

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

                return .premium(
                    colors.main,
                    colors.secondary
                        ?? colors.main,
                    "profile:\\(String(describing: profileColor)):\\(presentationData.theme.overallDarkAppearance)"
                )
            }

            if let representation =
                peer.profileImageRepresentations.last {

                let resourceId =
                    String(
                        describing:
                            representation.resource.id
                    )

                return .avatar(
                    peer,
                    representation,
                    resourceId
                )
            }
        }

        return .telegramTheme
    }
'''


    bg = (
        bg[:start]
        + resolve
        + bg[end:]
    )


    # ========================================================
    # PASS SOURCE IDENTITY INTO IMAGE/TONE PIPELINE
    # ========================================================

    bg = replace_once(
        bg,
        '''            self.sourceDisposable.set((self.wallpaperEntrySignal(
                wallpaper: wallpaper,
                fallback: metadataTint
            )
''',
        '''            self.sourceDisposable.set((self.wallpaperEntrySignal(
                wallpaper: wallpaper,
                fallback: metadataTint,
                identity: loadKey
            )
''',
        "wallpaper identity call",
    )


    bg = replace_once(
        bg,
        '''            guard let signal = self.avatarEntrySignal(
                peer: peer,
                representation: representation,
                fallback: fallback
            ) else {
''',
        '''            guard let signal = self.avatarEntrySignal(
                peer: peer,
                representation: representation,
                identity: loadKey,
                fallback: fallback
            ) else {
''',
        "avatar identity call",
    )


    start, end = function_span(
        bg,
        "    private func wallpaperEntrySignal("
    )


    wallpaper_signal = '''    private func wallpaperEntrySignal(
        wallpaper: TelegramWallpaper,
        fallback: UIColor,
        identity: String
    ) -> Signal<GhostBaseProfileBackgroundCacheEntry?, NoError> {
        switch wallpaper {
        case let .image(representations, _):
            guard let representation =
                largestImageRepresentation(
                    representations
                ) else {
                return .single(nil)
            }

            return self.resourceEntrySignal(
                resource:
                    representation.resource,
                identity:
                    identity,
                fallback:
                    fallback
            )

        case let .file(file):
            if wallpaper.isPattern {
                return .single(nil)
            }

            return self.resourceEntrySignal(
                resource:
                    file.file.resource,
                identity:
                    identity,
                fallback:
                    fallback
            )

        case let .file(file):
            if wallpaper.isPattern {
                return .single(nil)
            }

            return self.resourceEntrySignal(
                resource:
                    file.file.resource,
                identity:
                    identity,
                fallback:
                    fallback
            )

        default:
            let colors =
                Self.wallpaperColors(
                    wallpaper
                )

            let tint =
                Self.wallpaperTint(
                    wallpaper,
                    fallback: fallback
                )

            return deferred {
                guard let image =
                    Self.generatedWallpaperImage(
                        colors: colors,
                        fallback: tint
                    ) else {
                    return .single(nil)
                }

                return .single(
                    GhostBaseProfileBackgroundCacheEntry(
                        image: image,
                        tint: tint
                    )
                )
            }
            |> runOn(
                Queue.concurrentDefaultQueue()
            )
        }
    }
'''


    bg = (
        bg[:start]
        + wallpaper_signal
        + bg[end:]
    )


    start, end = function_span(
        bg,
        "    private func avatarEntrySignal("
    )


    avatar_signal = '''    private func avatarEntrySignal(
        peer: EnginePeer,
        representation: TelegramMediaImageRepresentation,
        identity: String,
        fallback: UIColor
    ) -> Signal<GhostBaseProfileBackgroundCacheEntry?, NoError>? {
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

            let tint: UIColor

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
                        fallback: fallback
                    )

                Self.storePersistentTint(
                    tint,
                    identity: identity
                )
            }

            return GhostBaseProfileBackgroundCacheEntry(
                image: image,
                tint: tint
            )
        }
    }
'''


    bg = (
        bg[:start]
        + avatar_signal
        + bg[end:]
    )


    start, end = function_span(
        bg,
        "    private func resourceEntrySignal("
    )


    resource_signal = '''    private func resourceEntrySignal(
        resource: MediaResource,
        identity: String,
        fallback: UIColor
    ) -> Signal<GhostBaseProfileBackgroundCacheEntry?, NoError> {
        let mediaBox =
            self.context.account.postbox.mediaBox

        return Signal {
            subscriber in

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
                    |> mapToSignal {
                        data
                        -> Signal<GhostBaseProfileBackgroundCacheEntry?, NoError>
                        in

                        return deferred {
                            guard let image =
                                UIImage(
                                    contentsOfFile:
                                        data.path
                                ) else {
                                return .single(nil)
                            }

                            let tint: UIColor

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

                            return .single(
                                GhostBaseProfileBackgroundCacheEntry(
                                    image: image,
                                    tint: tint
                                )
                            )
                        }
                        |> runOn(
                            Queue.concurrentDefaultQueue()
                        )
                    }
                )
                .start(
                    next: {
                        entry in

                        subscriber.putNext(
                            entry
                        )
                    },
                    completed: {
                        subscriber.putCompletion()
                    }
                )

            return ActionDisposable {
                fetchDisposable.dispose()
                dataDisposable.dispose()
            }
        }
    }
'''


    bg = (
        bg[:start]
        + resource_signal
        + bg[end:]
    )


    # ========================================================
    # SETTINGS / OWN PROFILE
    # ========================================================

    scr = replace_once(
        scr,
        '''        if !isSettings, let settings = GhostBaseProfileGlassRuntime.loadSettings() {
            self.ghostBaseProfileBackgroundView = GhostBaseProfileBackgroundView(
''',
        '''        if let settings = GhostBaseProfileGlassRuntime.loadSettings() {
            self.ghostBaseProfileBackgroundView = GhostBaseProfileBackgroundView(
''',
        "Settings background",
    )


    scr = replace_once(
        scr,
        '''        if !self.isSettings, let peer = data.peer, case .user = peer {
''',
        '''        if let peer = data.peer, case .user = peer {
''',
        "Settings history observation",
    )


    scr = replace_once(
        scr,
        '''            self.edgeEffectView.update(content: self.presentationData.theme.list.blocksBackgroundColor, rect: edgeEffectFrame, edge: .bottom, edgeSize: edgeEffectFrame.height, transition: ComponentTransition(transition))
''',
        '''            let edgeContent: UIColor =
                self.ghostBaseProfileBackgroundView != nil
                ? .clear
                : self.presentationData.theme.list.blocksBackgroundColor

            self.edgeEffectView.update(
                content: edgeContent,
                rect: edgeEffectFrame,
                edge: .bottom,
                edgeSize: edgeEffectFrame.height,
                transition:
                    ComponentTransition(
                        transition
                    )
            )
''',
        "Settings bottom edge",
    )


    # ========================================================
    # HEADER / BUTTONS / MUSIC
    # ========================================================

    hdr = replace_once(
        hdr,
        '''        self.ghostBaseProfileGlassSettings = isSettings ? nil : GhostBaseProfileGlassRuntime.loadSettings()
''',
        '''        self.ghostBaseProfileGlassSettings = GhostBaseProfileGlassRuntime.loadSettings()
''',
        "Settings header glass",
    )


    hdr = replace_once(
        hdr,
        "        let regularContentButtonBackgroundColor: UIColor\n",
        "        var regularContentButtonBackgroundColor: UIColor\n",
        "button background var",
    )


    hdr = replace_once(
        hdr,
        "        let regularHeaderButtonBackgroundColor: UIColor\n",
        "        var regularHeaderButtonBackgroundColor: UIColor\n",
        "header background var",
    )


    hdr = replace_once(
        hdr,
        '''        let regularContentButtonForegroundColor: UIColor = peer?.effectiveProfileColor != nil ? UIColor.white : presentationData.theme.list.itemAccentColor
''',
        '''        var regularContentButtonForegroundColor: UIColor = peer?.effectiveProfileColor != nil ? UIColor.white : presentationData.theme.list.itemAccentColor
''',
        "button foreground var",
    )


    hdr = replace_once(
        hdr,
        '''        self.contentButtonBackgroundColor = regularNavigationContentsSecondaryColor.mixedWith(regularContentButtonBackgroundColor, alpha: 0.5)
''',
        '''        if self.ghostBaseProfileGlassSettings != nil {
            // MARK: GhostBase v1.1K HEADERGLASS2
            //
            // Geometry, icons, labels and hit targets stay native.
            // Only the shared NavigationBackgroundNode material changes.
            if presentationData.theme.overallDarkAppearance {
                regularContentButtonBackgroundColor =
                    UIColor(
                        white: 0.0,
                        alpha: 0.16
                    )

                regularHeaderButtonBackgroundColor =
                    UIColor(
                        white: 0.0,
                        alpha: 0.12
                    )
            } else {
                regularContentButtonBackgroundColor =
                    UIColor(
                        white: 1.0,
                        alpha: 0.20
                    )

                regularHeaderButtonBackgroundColor =
                    UIColor(
                        white: 1.0,
                        alpha: 0.16
                    )
            }

            regularContentButtonForegroundColor =
                .white

            self.contentButtonBackgroundColor =
                regularContentButtonBackgroundColor
        } else {
            self.contentButtonBackgroundColor =
                regularNavigationContentsSecondaryColor
                    .mixedWith(
                        regularContentButtonBackgroundColor,
                        alpha: 0.5
                    )
        }
''',
        "header material",
    )


    hdr = replace_once(
        hdr,
        '''            backgroundCoverView.alpha = GhostBaseProfileGlassRuntime.shouldBlendStockCover(
                settings: self.ghostBaseProfileGlassSettings,
                peer: peer,
                cachedData: cachedData,
                presentationData: presentationData,
                isSettings: isSettings
            ) ? 0.18 : 1.0
''',
        '''            let ghostBaseBlendCover =
                GhostBaseProfileGlassRuntime
                    .shouldBlendStockCover(
                        settings:
                            self.ghostBaseProfileGlassSettings,
                        peer:
                            peer,
                        cachedData:
                            cachedData,
                        presentationData:
                            presentationData,
                        isSettings:
                            isSettings
                    )

            if ghostBaseBlendCover {
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
''',
        "stock cover alpha",
    )


    hdr = replace_once(
        hdr,
        '''            if hasBackground || self.isAvatarExpanded {
''',
        '''            if hasBackground || self.isAvatarExpanded || self.ghostBaseProfileGlassSettings != nil {
''',
        "music material condition",
    )


    hdr = replace_once(
        hdr,
        '''            let isOverlay = self.isAvatarExpanded || hasBackground
''',
        '''            let isOverlay = self.isAvatarExpanded || hasBackground || self.ghostBaseProfileGlassSettings != nil
''',
        "music overlay text",
    )


    # ========================================================
    # MAIN INFO CARD
    # ========================================================

    sec = replace_once(
        sec,
        '''        super.init()
        
        self.addSubnode(self.backgroundNode)
''',
        '''        super.init()

        self.backgroundColor = .clear
        self.itemContainerNode.backgroundColor = .clear
        
        self.addSubnode(self.backgroundNode)
''',
        "section clear parent",
    )


    sec = replace_once(
        sec,
        '''            self.backgroundNode.backgroundColor = UIColor(
                white: isDark ? 1.0 : 0.0,
                alpha: isDark ? 0.055 : 0.040
            )
''',
        '''            // MARK: GhostBase v1.1K READABILITY2
            //
            // Small neutral scrim improves text contrast over bright
            // wallpaper/avatar areas without another blur layer.
            self.backgroundNode.backgroundColor =
                UIColor(
                    white:
                        isDark
                            ? 0.0
                            : 1.0,
                    alpha:
                        isDark
                            ? 0.13
                            : 0.16
                )

            self.itemContainerNode.backgroundColor =
                .clear
''',
        "section readability",
    )


    sec = replace_once(
        sec,
        '''        if self.ghostBaseGlassEnabled {
            let radius: CGFloat = hasCorners ? 16.0 : 0.0
            self.backgroundNode.cornerRadius = radius
            self.backgroundNode.clipsToBounds = hasCorners
        }
''',
        '''        if self.ghostBaseGlassEnabled {
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
''',
        "section clipping",
    )


    # ========================================================
    # HISTORY
    # ========================================================

    rep = replace_once(
        rep,
        "    static let maximumEvents = 200\n",
        '''    static let maximumEvents = 200

    static func afterPendingWrites(
        _ action: @escaping () -> Void
    ) {
        self.queue.async(
            execute: action
        )
    }
''',
        "history queue hook",
    )


    rep = replace_once(
        rep,
        '''    private var reportText: String?
    private var didStartLoading = false
''',
        '''    private var reportText: String?
    private var didStartLoading = false
    private var wasVisible = false
''',
        "history visibility",
    )


    start, end = function_span(
        rep,
        "    private func startLoadingIfNeeded()"
    )


    loader = '''    private func startLoadingIfNeeded() {
        guard !self.didStartLoading else {
            return
        }

        self.didStartLoading = true

        let accountPeerId =
            self.accountPeerId

        let peerId =
            self.peerId

        let kind =
            self.kind

        let personalChannel =
            self.personalChannel

        let load: () -> Void = {
            [weak self] in

            let text =
                Self.loadReport(
                    accountPeerId:
                        accountPeerId,
                    peerId:
                        peerId,
                    kind:
                        kind,
                    personalChannel:
                        personalChannel
                )

            DispatchQueue.main.async {
                guard let self else {
                    return
                }

                self.reportText =
                    text

                self.updateTextLayout(
                    transition: .immediate
                )
            }
        }

        switch kind {
        case .profileHistory,
             .personalChannel:

            GhostBaseProfileReportStoreV11G
                .afterPendingWrites(
                    load
                )

        case .presence,
             .giftHistory:

            DispatchQueue.global(
                qos: .utility
            )
            .async(
                execute: load
            )
        }
    }
'''


    rep = (
        rep[:start]
        + loader
        + rep[end:]
    )


    rep = replace_once(
        rep,
        '''        if visibleHeight > 0.0 {
            self.startLoadingIfNeeded()
        }
''',
        '''        let isVisible =
            visibleHeight > 0.0

        if isVisible
            && !self.wasVisible {

            self.didStartLoading =
                false

            self.startLoadingIfNeeded()
        }

        self.wasVisible =
            isVisible
''',
        "history re-entry reload",
    )


    # ========================================================
    # PROPAGATE GLASS MODE TO GIFTS / GROUPS / MEMBERS
    # ========================================================

    pane = replace_once(
        pane,
        '''        switchToMediaTarget: PeerInfoSwitchToMediaTarget?,
        key: PeerInfoPaneKey,
''',
        '''        switchToMediaTarget: PeerInfoSwitchToMediaTarget?,
        ghostBaseGlassEnabled: Bool,
        key: PeerInfoPaneKey,
''',
        "pending pane glass arg",
    )


    pane = replace_once(
        pane,
        '''            let giftPaneNode = PeerInfoGiftsPaneNode(context: context, peerId: peerId, chatControllerInteraction: chatControllerInteraction, profileGiftsCollections: data.profileGiftsCollectionsContext!, profileGifts: data.profileGiftsContext!, canManage: canManage, canGift: canGift, initialGiftCollectionId: initialGiftCollectionId)
''',
        '''            let giftPaneNode = PeerInfoGiftsPaneNode(context: context, peerId: peerId, chatControllerInteraction: chatControllerInteraction, profileGiftsCollections: data.profileGiftsCollectionsContext!, profileGifts: data.profileGiftsContext!, canManage: canManage, canGift: canGift, initialGiftCollectionId: initialGiftCollectionId, ghostBaseGlassEnabled: ghostBaseGlassEnabled)
''',
        "gift pane propagation",
    )


    pane = replace_once(
        pane,
        '''        case .groupsInCommon:
            paneNode = PeerInfoGroupsInCommonPaneNode(context: context, peerId: peerId, chatControllerInteraction: chatControllerInteraction, openPeerContextAction: openPeerContextAction, groupsInCommonContext: data.groupsInCommon!)
''',
        '''        case .groupsInCommon:
            paneNode = PeerInfoGroupsInCommonPaneNode(context: context, peerId: peerId, chatControllerInteraction: chatControllerInteraction, openPeerContextAction: openPeerContextAction, groupsInCommonContext: data.groupsInCommon!, ghostBaseGlassEnabled: ghostBaseGlassEnabled)
''',
        "groups pane propagation",
    )


    pane = replace_once(
        pane,
        '''                paneNode = PeerInfoMembersPaneNode(context: context, peerId: peerId, membersContext: membersContext, addMemberAction: {
''',
        '''                paneNode = PeerInfoMembersPaneNode(context: context, peerId: peerId, membersContext: membersContext, ghostBaseGlassEnabled: ghostBaseGlassEnabled, addMemberAction: {
''',
        "members pane propagation",
    )


    pane = replace_once(
        pane,
        '''                    switchToMediaTarget: switchToMediaTarget,
                    key: key,
''',
        '''                    switchToMediaTarget: switchToMediaTarget,
                    ghostBaseGlassEnabled: self.ghostBaseGlassEnabled,
                    key: key,
''',
        "pending pane call propagation",
    )


    pane = replace_once(
        pane,
        '''            self.backgroundColor = backgroundColor.withAlphaComponent(
                isDark ? 0.20 : 0.30
            )
''',
        '''            self.backgroundColor =
                backgroundColor
                    .withAlphaComponent(
                        isDark
                            ? 0.08
                            : 0.12
                    )
''',
        "pane root transparency",
    )


    # ========================================================
    # COMMON GROUPS
    #
    # listMaskView is literally above ListView and was painted
    # with blocksBackgroundColor, covering names/avatars.
    # ========================================================

    groups = replace_once(
        groups,
        '''    private let listBackgroundView: UIImageView
    private let listMaskView: UIImageView
''',
        '''    private let ghostBaseGlassEnabled: Bool
    private let listBackgroundView: UIImageView
    private let listMaskView: UIImageView
''',
        "groups glass property",
    )


    groups = replace_once(
        groups,
        '''    init(context: AccountContext, peerId: EnginePeer.Id, chatControllerInteraction: ChatControllerInteraction, openPeerContextAction: @escaping (Bool, EnginePeer, ASDisplayNode, ContextGesture?) -> Void, groupsInCommonContext: GroupsInCommonContext) {
        self.context = context
''',
        '''    init(context: AccountContext, peerId: EnginePeer.Id, chatControllerInteraction: ChatControllerInteraction, openPeerContextAction: @escaping (Bool, EnginePeer, ASDisplayNode, ContextGesture?) -> Void, groupsInCommonContext: GroupsInCommonContext, ghostBaseGlassEnabled: Bool = false) {
        self.ghostBaseGlassEnabled = ghostBaseGlassEnabled
        self.context = context
''',
        "groups init",
    )


    groups = replace_once(
        groups,
        '''        self.listBackgroundView.tintColor = presentationData.theme.list.itemBlocksBackgroundColor
        self.listMaskView.tintColor = presentationData.theme.list.blocksBackgroundColor
''',
        '''        if self.ghostBaseGlassEnabled {
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
                            ? 0.12
                            : 0.16
                )

            self.listMaskView.tintColor =
                .clear
        } else {
            self.listBackgroundView.tintColor =
                presentationData
                    .theme
                    .list
                    .itemBlocksBackgroundColor

            self.listMaskView.tintColor =
                presentationData
                    .theme
                    .list
                    .blocksBackgroundColor
        }
''',
        "groups material",
    )


    # ========================================================
    # MEMBERS
    #
    # ContactsPeerItem is already systemStyle .glass and
    # hideBackground=true. The black overlay was the pane mask.
    # ========================================================

    members = replace_once(
        members,
        '''    private let listBackgroundView: UIImageView
    private let listMaskView: UIImageView
''',
        '''    private let ghostBaseGlassEnabled: Bool
    private let listBackgroundView: UIImageView
    private let listMaskView: UIImageView
''',
        "members glass property",
    )


    members = replace_once(
        members,
        '''    init(context: AccountContext, peerId: EnginePeer.Id, membersContext: PeerInfoMembersContext, addMemberAction: @escaping () -> Void, action: @escaping (PeerInfoMember, PeerMembersListAction) -> Void) {
        self.context = context
''',
        '''    init(context: AccountContext, peerId: EnginePeer.Id, membersContext: PeerInfoMembersContext, ghostBaseGlassEnabled: Bool = false, addMemberAction: @escaping () -> Void, action: @escaping (PeerInfoMember, PeerMembersListAction) -> Void) {
        self.ghostBaseGlassEnabled = ghostBaseGlassEnabled
        self.context = context
''',
        "members init",
    )


    members = replace_once(
        members,
        '''        self.listBackgroundView.tintColor = presentationData.theme.list.itemBlocksBackgroundColor
        self.listMaskView.tintColor = presentationData.theme.list.blocksBackgroundColor
''',
        '''        if self.ghostBaseGlassEnabled {
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
                            ? 0.12
                            : 0.16
                )

            self.listMaskView.tintColor =
                .clear
        } else {
            self.listBackgroundView.tintColor =
                presentationData
                    .theme
                    .list
                    .itemBlocksBackgroundColor

            self.listMaskView.tintColor =
                presentationData
                    .theme
                    .list
                    .blocksBackgroundColor
        }
''',
        "members material",
    )


    # ========================================================
    # GIFTS
    #
    # Remove the opaque pane-owned blocks background and the
    # bottom black edge. Gift cards/content remain native.
    # ========================================================

    gifts = replace_once(
        gifts,
        """    private let backgroundNode: ASDisplayNode
    private let scrollNode: ASScrollNode
""",
        """    private let ghostBaseGlassEnabled: Bool
    private let backgroundNode: ASDisplayNode
    private let scrollNode: ASScrollNode
""",
        "gifts glass property",
    )


    gifts = replace_once(
        gifts,
        """    public init(context: AccountContext, peerId: EnginePeer.Id, chatControllerInteraction: ChatControllerInteraction, profileGiftsCollections: ProfileGiftsCollectionsContext, profileGifts: ProfileGiftsContext, canManage: Bool, canGift: Bool, initialGiftCollectionId: Int64?) {
        self.context = context
""",
        """    public init(context: AccountContext, peerId: EnginePeer.Id, chatControllerInteraction: ChatControllerInteraction, profileGiftsCollections: ProfileGiftsCollectionsContext, profileGifts: ProfileGiftsContext, canManage: Bool, canGift: Bool, initialGiftCollectionId: Int64?, ghostBaseGlassEnabled: Bool = false) {
        self.ghostBaseGlassEnabled = ghostBaseGlassEnabled
        self.context = context
""",
        "gifts init",
    )


    gifts = replace_once(
        gifts,
        """        self.backgroundNode.backgroundColor = presentationData.theme.list.blocksBackgroundColor
""",
        """        if self.ghostBaseGlassEnabled {
            self.backgroundColor = .clear

            self.backgroundNode.backgroundColor =
                .clear

            self.scrollNode.backgroundColor =
                .clear

            self.scrollNode.view.backgroundColor =
                .clear

            self.giftsListView.backgroundColor =
                .clear
        } else {
            self.backgroundNode.backgroundColor =
                presentationData
                    .theme
                    .list
                    .blocksBackgroundColor
        }
""",
        "gifts root background",
    )


    gifts = replace_once(
        gifts,
        """            panelEdgeEffectView.update(content: presentationData.theme.list.blocksBackgroundColor, blur: false, rect: edgeEffectFrame, edge: .bottom, edgeSize: 40.0, transition: panelTransition)
""",
        """            let panelEdgeContent: UIColor =
                self.ghostBaseGlassEnabled
                ? .clear
                : presentationData
                    .theme
                    .list
                    .blocksBackgroundColor

            panelEdgeEffectView.update(
                content: panelEdgeContent,
                blur: false,
                rect: edgeEffectFrame,
                edge: .bottom,
                edgeSize: 40.0,
                transition: panelTransition
            )
""",
        "gifts bottom edge",
    )


    # ========================================================
    # SETTINGS LABEL
    # ========================================================

    if SETTINGS.is_file():
        settings_text = SETTINGS.read_text(
                encoding="utf-8"
            )

        settings_text = settings_text.replace(
                "Размытие аватара в профиле",
                "Предпочитать аватар как фон",
            )

        SETTINGS.write_text(
            settings_text,
            encoding="utf-8",
        )


    # ========================================================
    # NEW BEAR
    #
    # Bear ID is intentionally materialized by the existing
    # GIFTHISTORY2 canonical generator before this V11K pass.
    # Do not patch StarGifts.swift here: direct work-tree
    # application can run before GIFTHISTORY2 is materialized.
    # ========================================================

    # ========================================================
    # WRITE
    # ========================================================

    for path, text in (
        (BG, bg),
        (HDR, hdr),
        (SEC, sec),
        (SCR, scr),
        (REP, rep),
        (PANE, pane),
        (GROUPS, groups),
        (MEMBERS, members),
        (GIFTS, gifts),
    ):
        path.write_text(
            text,
            encoding="utf-8",
        )


    print("[V11K] applied")
    print("  source selector + persistent tone")
    print("  Settings/self profile background")
    print("  neutral glass buttons + music")
    print("  readable clipped info sections")
    print("  history write/read synchronization")
    print("  full-scene Gifts / Groups / Members")
    print("  bear 6046178578163303744 alias")


current = BG.read_text(
    encoding="utf-8"
)

if "GhostBase v1.1K PROFILEPOLISH2" in current:
    print(
        "[V11K] already materialized"
    )
else:
    apply_patch()
