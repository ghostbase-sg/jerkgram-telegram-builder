#!/usr/bin/env python3

import os
from pathlib import Path


ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        "/root/gb_builder/work/swiftgram-src",
    )
)

PEER = (
    ROOT
    / "submodules/TelegramUI/Components/PeerInfo/"
      "PeerInfoScreen/Sources"
)

BG = PEER / "GhostBaseProfileFullscreenBackground.swift"
HDR = PEER / "PeerInfoHeaderNode.swift"
SEC = PEER / "PeerInfoScreenItemSectionContainerNode.swift"
PANE = PEER / "PeerInfoPaneContainerNode.swift"
SCR = PEER / "PeerInfoScreen.swift"
REP = PEER / "GhostBaseProfileReportPaneNode.swift"


for path in (
    BG,
    HDR,
    SEC,
    PANE,
    SCR,
    REP,
):
    if not path.is_file():
        raise SystemExit(
            f"[V11I FINAL] missing: {path}"
        )


def once(
    text: str,
    old: str,
    new: str,
    label: str,
) -> str:
    count = text.count(old)

    if count != 1:
        raise SystemExit(
            f"[V11I FINAL PREFLIGHT] "
            f"{label}: expected 1, found {count}"
        )

    return text.replace(
        old,
        new,
        1,
    )


bg = BG.read_text(encoding="utf-8")
hdr = HDR.read_text(encoding="utf-8")
sec = SEC.read_text(encoding="utf-8")
pane = PANE.read_text(encoding="utf-8")
scr = SCR.read_text(encoding="utf-8")
rep = REP.read_text(encoding="utf-8")


if "GhostBase v1.1I PROFILEFINAL1" in bg:
    print(
        "[V11I FINAL] already materialized"
    )
    raise SystemExit(0)


# ============================================================
# FULLSCREEN BACKGROUND
#
# One reusable image view.
# One persistent blur.
# One tint/dimming layer.
# ============================================================

bg = once(
    bg,
    '''    private static let imageCache = NSCache<NSString, GhostBaseProfileBackgroundCacheEntry>()
''',
    '''    // MARK: GhostBase v1.1I PROFILEFINAL1
    private static let imageCache: NSCache<NSString, GhostBaseProfileBackgroundCacheEntry> = {
        let cache = NSCache<NSString, GhostBaseProfileBackgroundCacheEntry>()
        cache.countLimit = 20
        return cache
    }()
''',
    "bounded background cache",
)


# ============================================================
# Correct source priority:
#
# personal wallpaper
# -> global wallpaper
# -> Premium/profile
# -> actual avatar pixels
# -> Telegram fallback
# ============================================================

bg = once(
    bg,
    '''        if let peer {
            // MARK: GhostBase v1.1H AVATARSOURCE1
            // If an avatar exists and avatar blur is enabled, the real image
            // is the visual source even when Telegram has a profile colour.
            if settings.avatarBlurInProfile,
               !peer.profileImageRepresentations.isEmpty {
                return true
            }
            if let status = peer.emojiStatus, case .starGift = status.content {
                return false
            }
            if peer.effectiveProfileColor != nil {
                return false
            }
        }
''',
    '''        if let peer {
            // Premium/profile decoration has priority over avatar fallback.
            if let status = peer.emojiStatus, case .starGift = status.content {
                return false
            }
            if peer.effectiveProfileColor != nil {
                return false
            }
            if settings.avatarBlurInProfile,
               !peer.profileImageRepresentations.isEmpty {
                return true
            }
        }
''',
    "stock-cover source priority",
)


source_old = '''        // 3) actual avatar image + blur
        // MARK: GhostBase v1.1H AVATARVISUAL1
        if self.settings.avatarBlurInProfile,
           let peer,
           let representation = peer.profileImageRepresentations.last {
            let resourceId = String(describing: representation.resource.id)
            return .avatar(peer, representation, resourceId)
        }

        // 4) Premium profile color is a separate state source. It is never
        // mixed into the avatar cache or avatar-derived tint.
        if let peer {
            if let status = peer.emojiStatus,
               case let .starGift(_, _, _, _, _, innerColor, outerColor, _, _) = status.content {
                let main = UIColor(rgb: UInt32(bitPattern: innerColor))
                let secondary = UIColor(rgb: UInt32(bitPattern: outerColor))
                return .premium(
                    main,
                    secondary,
                    "gift:\\(innerColor):\\(outerColor)"
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
                    "profile:\\(String(describing: profileColor)):\\(presentationData.theme.overallDarkAppearance)"
                )
            }
        }

'''

source_old = source_old.replace(
    "\\\\(",
    "\\(",
)

source_new = '''        // 3) Premium profile color / gift decoration.
        if let peer {
            if let status = peer.emojiStatus,
               case let .starGift(_, _, _, _, _, innerColor, outerColor, _, _) = status.content {
                let main = UIColor(rgb: UInt32(bitPattern: innerColor))
                let secondary = UIColor(rgb: UInt32(bitPattern: outerColor))
                return .premium(
                    main,
                    secondary,
                    "gift:\\(innerColor):\\(outerColor)"
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
                    "profile:\\(String(describing: profileColor)):\\(presentationData.theme.overallDarkAppearance)"
                )
            }
        }

        // 4) Avatar fallback uses the actual avatar pixels.
        if self.settings.avatarBlurInProfile,
           let peer,
           let representation = peer.profileImageRepresentations.last {
            let resourceId = String(describing: representation.resource.id)
            return .avatar(peer, representation, resourceId)
        }

'''

source_new = source_new.replace(
    "\\\\(",
    "\\(",
)

bg = once(
    bg,
    source_old,
    source_new,
    "background source priority",
)


# ============================================================
# Lighter persistent global material.
#
# V11H ThinMaterial was visually flattening the source.
# ============================================================

bg = once(
    bg,
    '''        let effectStyle: UIBlurEffect.Style
        if isDark {
            effectStyle = reduced ? .systemUltraThinMaterialDark : .systemThinMaterialDark
        } else {
            effectStyle = reduced ? .systemUltraThinMaterialLight : .systemThinMaterialLight
        }
        self.blurView.effect = UIBlurEffect(style: effectStyle)
''',
    '''        // Keep wallpaper/avatar structure visible instead of flattening
        // the scene into a dark material field.
        let effectStyle: UIBlurEffect.Style = isDark
            ? .systemUltraThinMaterialDark
            : .systemUltraThinMaterialLight
        self.blurView.effect = UIBlurEffect(style: effectStyle)
''',
    "global blur material",
)


# ============================================================
# Tint must grade the source, not replace it.
# ============================================================

bg = once(
    bg,
    '''    private func applyTint(
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
''',
    '''    private func applyTint(
        _ color: UIColor,
        fallback: UIColor,
        isDark: Bool,
        reduced: Bool
    ) {
        // The source image must remain visible. Tint only grades it lightly.
        if self.settings.tintEnabled {
            self.tintView.backgroundColor = color.withAlphaComponent(
                reduced
                    ? (isDark ? 0.030 : 0.020)
                    : (isDark ? 0.050 : 0.035)
            )
        } else {
            self.tintView.backgroundColor = UIColor.black.withAlphaComponent(
                reduced
                    ? (isDark ? 0.018 : 0.010)
                    : (isDark ? 0.030 : 0.016)
            )
        }
    }
''',
    "light source tint",
)


# ============================================================
# ACTION BUTTONS
#
# Restore Official Telegram 12.9.2 material.
# No custom geometry.
# No round buttons.
# No GhostBase material override.
# ============================================================

hdr = once(
    hdr,
    "        var regularContentButtonBackgroundColor: UIColor\n",
    "        let regularContentButtonBackgroundColor: UIColor\n",
    "stock content button declaration",
)

hdr = once(
    hdr,
    "        var regularHeaderButtonBackgroundColor: UIColor\n",
    "        let regularHeaderButtonBackgroundColor: UIColor\n",
    "stock header button declaration",
)

hdr = once(
    hdr,
    '''        // MARK: GhostBase v1.1H ACTIONGLASS1
        // Keep Telegram's native action-button geometry. Only its material
        // joins the same profile surface instead of becoming an opaque row.
        if self.ghostBaseProfileGlassSettings != nil && !isSettings {
            if presentationData.theme.overallDarkAppearance {
                regularContentButtonBackgroundColor = UIColor(
                    white: 0.0,
                    alpha: 0.16
                )
                regularHeaderButtonBackgroundColor = UIColor(
                    white: 0.0,
                    alpha: 0.12
                )
            } else {
                regularContentButtonBackgroundColor = UIColor(
                    white: 1.0,
                    alpha: 0.22
                )
                regularHeaderButtonBackgroundColor = UIColor(
                    white: 1.0,
                    alpha: 0.18
                )
            }
        }

''',
    "",
    "remove V11H action material",
)


# ============================================================
# SECTIONS
#
# Delete the V11H per-section UIVisualEffectView completely.
# This removes the known corner-mask/effect combination that
# can produce black wedges / triangles.
#
# The ONE fullscreen blur remains.
# Sections are only a lightweight Cold Glass overlay.
# ============================================================

sec = once(
    sec,
    '''    private let ghostBaseGlassEnabled: Bool
    private let backgroundNode: ASDisplayNode
    // MARK: GhostBase v1.1H SECTIONGLASS1
    private let ghostBaseGlassEffectView: UIVisualEffectView?
    private var ghostBaseGlassEffectIsDark: Bool?
''',
    '''    private let ghostBaseGlassEnabled: Bool
    private let backgroundNode: ASDisplayNode
    // MARK: GhostBase v1.1I SECTIONFINAL1
    // No per-section blur: the fullscreen background owns the single blur.
''',
    "section blur properties",
)

sec = once(
    sec,
    '''    init(ghostBaseGlassEnabled: Bool = false) {
        self.ghostBaseGlassEnabled = ghostBaseGlassEnabled
        if ghostBaseGlassEnabled {
            self.ghostBaseGlassEffectView = UIVisualEffectView(effect: nil)
        } else {
            self.ghostBaseGlassEffectView = nil
        }
        self.backgroundNode = ASDisplayNode()
        self.backgroundNode.isLayerBacked = !ghostBaseGlassEnabled
''',
    '''    init(ghostBaseGlassEnabled: Bool = false) {
        self.ghostBaseGlassEnabled = ghostBaseGlassEnabled
        self.backgroundNode = ASDisplayNode()
        self.backgroundNode.isLayerBacked = true
''',
    "section init",
)

sec = once(
    sec,
    '''        self.addSubnode(self.backgroundNode)
        if let ghostBaseGlassEffectView = self.ghostBaseGlassEffectView {
            ghostBaseGlassEffectView.isUserInteractionEnabled = false
            ghostBaseGlassEffectView.clipsToBounds = true
            self.backgroundNode.view.addSubview(
                ghostBaseGlassEffectView
            )
        }
        self.addSubnode(self.itemContainerNode)
''',
    '''        self.addSubnode(self.backgroundNode)
        self.addSubnode(self.itemContainerNode)
''',
    "section effect attachment",
)

sec = once(
    sec,
    '''        if self.ghostBaseGlassEnabled {
            let isDark = presentationData.theme.overallDarkAppearance

            if self.ghostBaseGlassEffectIsDark != isDark {
                self.ghostBaseGlassEffectIsDark = isDark
                self.ghostBaseGlassEffectView?.effect = UIBlurEffect(
                    style: isDark ? .dark : .light
                )
            }

            // Blur is the surface. Tint is deliberately very light; the old
            // itemBlocksBackgroundColor alpha was the source of the black
            // rectangles visible in build 94.
            self.backgroundNode.backgroundColor = UIColor(
                white: isDark ? 0.0 : 1.0,
                alpha: isDark ? 0.045 : 0.075
            )
            self.topSeparatorNode.backgroundColor = .clear
            self.bottomSeparatorNode.backgroundColor = .clear
        } else {
''',
    '''        if self.ghostBaseGlassEnabled {
            let isDark = presentationData.theme.overallDarkAppearance

            self.backgroundNode.backgroundColor = UIColor(
                white: isDark ? 1.0 : 0.0,
                alpha: isDark ? 0.055 : 0.040
            )

            self.topSeparatorNode.backgroundColor = .clear
            self.bottomSeparatorNode.backgroundColor = .clear
        } else {
''',
    "section Cold Glass surface",
)

sec = once(
    sec,
    '''        if let ghostBaseGlassEffectView = self.ghostBaseGlassEffectView {
            ghostBaseGlassEffectView.frame = CGRect(
                origin: .zero,
                size: backgroundFrame.size
            )

            let radius: CGFloat = hasCorners ? 16.0 : 0.0
            self.backgroundNode.cornerRadius = radius
            self.backgroundNode.clipsToBounds = hasCorners
            ghostBaseGlassEffectView.layer.cornerRadius = radius
            ghostBaseGlassEffectView.layer.masksToBounds = hasCorners
        }
''',
    '''        if self.ghostBaseGlassEnabled {
            let radius: CGFloat = hasCorners ? 16.0 : 0.0
            self.backgroundNode.cornerRadius = radius
            self.backgroundNode.clipsToBounds = hasCorners
        }
''',
    "remove section effect masks",
)


# ============================================================
# PANES
#
# History / Presence / Gifts / Media / Files / Links / Voice
# keep their native pane ownership and geometry.
#
# But the pane container no longer becomes an opaque wall that
# hides the fullscreen visual source.
#
# Not .clear: readability is retained with a neutral material.
# ============================================================

pane = once(
    pane,
    '''        // MARK: GhostBase v1.1H NATIVEPANES1
        // Preserve Telegram's own pane/list background and geometry.
        // Glass belongs to the profile surfaces, not to every pane cell.
        self.backgroundColor = backgroundColor
''',
    '''        // MARK: GhostBase v1.1I FULLPANEFINAL1
        // Preserve native pane ownership/geometry, but do not cover the
        // fullscreen wallpaper/avatar source with an opaque Telegram block.
        if self.ghostBaseGlassEnabled {
            let isDark = presentationData.theme.overallDarkAppearance

            self.backgroundColor = backgroundColor.withAlphaComponent(
                isDark ? 0.20 : 0.30
            )
        } else {
            self.backgroundColor = backgroundColor
        }
''',
    "full-pane material",
)


scr = once(
    scr,
    '''            self.backgroundColor = .clear
            self.scrollNode.backgroundColor = .clear
            self.scrollNode.view.backgroundColor = .clear
            self.paneContainerNode.backgroundColor = .clear
''',
    '''            self.backgroundColor = .clear
            self.scrollNode.backgroundColor = .clear
            self.scrollNode.view.backgroundColor = .clear
            // PeerInfoPaneContainerNode owns its translucent glass material.
''',
    "remove global pane clear override",
)


# ============================================================
# PROFILE HISTORY
#
# Keep existing persisted schema so no migration destroys old
# observations.
#
# Turn snapshots back into meaningful old -> new changes.
# Preserve old PROFILEINTEL2.
# ============================================================

profile_start = rep.find(
    "    static func profileReport("
    "accountPeerId: Int64, peerId: Int64"
    ") -> String? {"
)

profile_end = rep.find(
    "    static func personalChannelReport(",
    profile_start,
)

if profile_start < 0 or profile_end < 0:
    raise SystemExit(
        "[V11I FINAL PREFLIGHT] "
        "profileReport boundaries missing"
    )


profile_report = r'''    static func profileReport(accountPeerId: Int64, peerId: Int64) -> String? {
        let defaults = UserDefaults.standard

        let key = self.profileKey(
            accountPeerId: accountPeerId,
            peerId: peerId
        )

        var sections: [String] = []

        if let data = defaults.data(forKey: key),
           let history = try? JSONDecoder().decode(
            GhostBaseObservedProfileHistoryV11G.self,
            from: data
           ) {
            let formatter = DateFormatter()
            formatter.locale = Locale(
                identifier: "ru_RU"
            )
            formatter.dateFormat = "dd.MM.yyyy HH:mm"

            func value(_ value: String?) -> String {
                guard let value, !value.isEmpty else {
                    return "—"
                }
                return value
            }

            var blocks: [String] = []
            var changeCount = 0

            if history.events.count >= 2 {
                for index in stride(
                    from: history.events.count - 1,
                    through: 1,
                    by: -1
                ) {
                    let previous = history.events[index - 1]
                    let current = history.events[index]

                    var changes: [String] = []

                    if previous.displayName != current.displayName {
                        changes.append(
                            "Имя: \(value(previous.displayName)) → \(value(current.displayName))"
                        )
                    }

                    if previous.username != current.username {
                        changes.append(
                            "Username: \(value(previous.username)) → \(value(current.username))"
                        )
                    }

                    if previous.about != current.about {
                        changes.append(
                            "BIO: \(value(previous.about)) → \(value(current.about))"
                        )
                    }

                    if previous.avatarResourceId != current.avatarResourceId {
                        let description: String

                        if previous.avatarResourceId == nil {
                            description = "Аватар: установлен"
                        } else if current.avatarResourceId == nil {
                            description = "Аватар: удалён"
                        } else {
                            description = "Аватар: изменён"
                        }

                        changes.append(
                            description
                        )
                    }

                    if previous.emojiStatus != current.emojiStatus {
                        changes.append(
                            "Emoji-status: \(previous.emojiStatus) → \(current.emojiStatus)"
                        )
                    }

                    guard !changes.isEmpty else {
                        continue
                    }

                    changeCount += changes.count

                    let date = formatter.string(
                        from: Date(
                            timeIntervalSince1970:
                                TimeInterval(
                                    current.observedAt
                                )
                        )
                    )

                    blocks.append(
                        (
                            [date]
                            + changes.map {
                                "• \($0)"
                            }
                        )
                        .joined(
                            separator: "\n"
                        )
                    )
                }
            }

            var lines: [String] = []

            lines.append(
                "История изменений профиля"
            )

            lines.append(
                "Зафиксировано изменений: \(changeCount)"
            )

            if let first = history.events.first {
                lines.append(
                    "Первое наблюдение: "
                    + formatter.string(
                        from: Date(
                            timeIntervalSince1970:
                                TimeInterval(
                                    first.observedAt
                                )
                        )
                    )
                )
            }

            if blocks.isEmpty {
                lines.append(
                    "Изменений после первого наблюдения пока нет."
                )
            } else {
                lines.append("")
                lines.append(
                    blocks.joined(
                        separator: "\n\n"
                    )
                )
            }

            sections.append(
                lines.joined(
                    separator: "\n"
                )
            )
        }

        // Preserve the old detailed logger instead of replacing
        // all historical information with a counter.
        let oldBase =
            "GhostBase.ProfileIntel2."
            + "\(accountPeerId)."
            + "\(peerId)."

        if let oldHistory = defaults.string(
            forKey: oldBase + "History"
        ),
           !oldHistory.isEmpty {

            sections.append(
                "Старый журнал PROFILEINTEL2\n"
                + oldHistory
            )
        }

        return sections.isEmpty
            ? nil
            : sections.joined(
                separator: "\n\n"
            )
    }

'''


rep = (
    rep[:profile_start]
    + profile_report
    + rep[profile_end:]
)


# ============================================================
# PERSONAL CHANNEL HISTORY
#
# Same idea: actual transitions, not just event count.
# ============================================================

personal_start = rep.find(
    "    static func personalChannelReport("
)

personal_end = rep.find(
    "\n}\n\nfunc ghostBaseRecordObservedProfileV11G",
    personal_start,
)

if personal_start < 0 or personal_end < 0:
    raise SystemExit(
        "[V11I FINAL PREFLIGHT] "
        "personalChannelReport boundaries missing"
    )


personal_report = r'''    static func personalChannelReport(
        accountPeerId: Int64,
        peerId: Int64
    ) -> String? {
        let key = self.personalChannelKey(
            accountPeerId: accountPeerId,
            peerId: peerId
        )

        guard let data = UserDefaults.standard.data(
            forKey: key
        ),
        let history = try? JSONDecoder().decode(
            GhostBasePersonalChannelHistoryV11G.self,
            from: data
        ) else {
            return nil
        }

        let formatter = DateFormatter()
        formatter.locale = Locale(
            identifier: "ru_RU"
        )
        formatter.dateFormat = "dd.MM.yyyy HH:mm"

        func value(_ value: String?) -> String {
            guard let value, !value.isEmpty else {
                return "—"
            }
            return value
        }

        var blocks: [String] = []
        var changeCount = 0

        if history.events.count >= 2 {
            for index in stride(
                from: history.events.count - 1,
                through: 1,
                by: -1
            ) {
                let previous = history.events[index - 1]
                let current = history.events[index]

                var changes: [String] = []

                if previous.channelPeerId != current.channelPeerId {
                    if current.channelPeerId == nil {
                        changes.append(
                            "Личный канал: откреплён"
                        )
                    } else if previous.channelPeerId == nil {
                        changes.append(
                            "Личный канал: прикреплён"
                        )
                    } else {
                        changes.append(
                            "Канал ID: "
                            + (
                                previous.channelPeerId.map(
                                    String.init
                                )
                                ?? "—"
                            )
                            + " → "
                            + (
                                current.channelPeerId.map(
                                    String.init
                                )
                                ?? "—"
                            )
                        )
                    }
                }

                if previous.title != current.title {
                    changes.append(
                        "Название: "
                        + value(previous.title)
                        + " → "
                        + value(current.title)
                    )
                }

                if previous.username != current.username {
                    changes.append(
                        "Username: "
                        + value(previous.username)
                        + " → "
                        + value(current.username)
                    )
                }

                if previous.link != current.link {
                    changes.append(
                        "Ссылка: "
                        + value(previous.link)
                        + " → "
                        + value(current.link)
                    )
                }

                if previous.subscriberCount
                    != current.subscriberCount {

                    changes.append(
                        "Подписчики: "
                        + (
                            previous.subscriberCount.map(
                                String.init
                            )
                            ?? "—"
                        )
                        + " → "
                        + (
                            current.subscriberCount.map(
                                String.init
                            )
                            ?? "—"
                        )
                    )
                }

                if previous.topMessageId
                    != current.topMessageId {

                    changes.append(
                        "Последний message ID: "
                        + (
                            previous.topMessageId.map(
                            previous.topMessageId.map(
                                String.init
                            )
                            ?? "—"
                        )
                        + " → "
                        + (
                            current.topMessageId.map(
                                String.init
                            )
                            ?? "—"
                        )
                    )
                }

                guard !changes.isEmpty else {
                    continue
                }

                changeCount += changes.count

                let date = formatter.string(
                    from: Date(
                        timeIntervalSince1970:
                            TimeInterval(
                                current.observedAt
                            )
                    )
                )

                blocks.append(
                    (
                        [date]
                        + changes.map {
                            "• \($0)"
                        }
                    )
                    .joined(
                        separator: "\n"
                    )
                )
            }
        }

        var lines: [String] = [
            "История личного канала",
            "Зафиксировано изменений: \(changeCount)"
        ]

        if blocks.isEmpty {
            lines.append(
                "Изменений после первого наблюдения пока нет."
            )
        } else {
            lines.append("")
            lines.append(
                blocks.joined(
                    separator: "\n\n"
                )
            )
        }

        return lines.joined(
            separator: "\n"
        )
    }
'''


rep = (
    rep[:personal_start]
    + personal_report
    + rep[personal_end:]
)


# ============================================================
# WRITE
# ============================================================

for path, text in (
    (BG, bg),
    (HDR, hdr),
    (SEC, sec),
    (PANE, pane),
    (SCR, scr),
    (REP, rep),
):
    path.write_text(
        text,
        encoding="utf-8",
    )


print("[V11I FINAL] patched:")
print(f"  {BG}")
print(f"  {HDR}")
print(f"  {SEC}")
print(f"  {PANE}")
print(f"  {SCR}")
print(f"  {REP}")

print()
print("[V11I FINAL] stock buttons preserved")
print("[V11I FINAL] per-section blur removed")
print("[V11I FINAL] fullscreen pane continuity enabled")
print("[V11I FINAL] detailed history restored")
print("[V11I FINAL] old PROFILEINTEL2 preserved")
print("[V11I FINAL] done")
