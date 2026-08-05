#!/usr/bin/env python3

import os
from pathlib import Path


ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        "/root/gb_builder/work/swiftgram-src",
    )
)

CORE = ROOT / "submodules/TelegramCore/Sources"
PEER = (
    ROOT
    / "submodules/TelegramUI/Components/PeerInfo/"
      "PeerInfoScreen/Sources"
)

ENGINE_MESSAGES = (
    CORE
    / "TelegramEngine/Messages/TelegramEngineMessages.swift"
)
TRANSCRIPTION = (
    CORE
    / "TelegramEngine/Messages/Transcription.swift"
)
ACCOUNT_STATE = (
    CORE
    / "State/AccountStateManagementUtils.swift"
)

BACKGROUND = PEER / "GhostBaseProfileFullscreenBackground.swift"
HEADER = PEER / "PeerInfoHeaderNode.swift"
SECTION = PEER / "PeerInfoScreenItemSectionContainerNode.swift"
PANE = PEER / "PeerInfoPaneContainerNode.swift"
PROFILE = PEER / "PeerInfoProfileItems.swift"

FILES = (
    ENGINE_MESSAGES,
    TRANSCRIPTION,
    ACCOUNT_STATE,
    BACKGROUND,
    HEADER,
    SECTION,
    PANE,
    PROFILE,
)

for path in FILES:
    if not path.is_file():
        raise SystemExit(f"[V11H] missing source: {path}")


def require_once(text: str, value: str, label: str) -> None:
    count = text.count(value)
    if count != 1:
        raise SystemExit(
            f"[V11H PREFLIGHT] {label}: expected 1, found {count}"
        )


def replace_once(
    text: str,
    old: str,
    new: str,
    label: str,
) -> str:
    if new in text and old not in text:
        print(f"[V11H] already materialized: {label}")
        return text

    require_once(text, old, label)
    return text.replace(old, new, 1)


MERGE_HELPER = r'''
// MARK: GhostBase v1.1H TRANSCRIPTIONACCUMULATOR1
private func ghostBaseMergeTranscriptionTextV11H(
    previous: String,
    incoming: String
) -> String {
    let previous = previous.trimmingCharacters(
        in: .whitespacesAndNewlines
    )
    let incoming = incoming.trimmingCharacters(
        in: .whitespacesAndNewlines
    )

    if previous.isEmpty {
        return incoming
    }
    if incoming.isEmpty {
        return previous
    }

    // Some transcription providers return the whole accumulated text on
    // every update, while others return only the next/revised fragment.
    if incoming.hasPrefix(previous) {
        return incoming
    }
    if previous.hasPrefix(incoming) {
        return previous
    }

    // Avoid duplicating a fragment when neighbouring chunks overlap.
    let maximumOverlap = min(previous.count, incoming.count)

    if maximumOverlap > 0 {
        for length in stride(
            from: maximumOverlap,
            through: 1,
            by: -1
        ) {
            let previousStart = previous.index(
                previous.endIndex,
                offsetBy: -length
            )
            let incomingEnd = incoming.index(
                incoming.startIndex,
                offsetBy: length
            )

            if previous[previousStart...] == incoming[..<incomingEnd] {
                let remainder = incoming[incomingEnd...]

                if remainder.isEmpty {
                    return previous
                }

                let needsSpace =
                    previous.last?.isWhitespace == false
                    && remainder.first?.isWhitespace == false

                return previous
                    + (needsSpace ? " " : "")
                    + remainder
            }
        }
    }

    return previous + " " + incoming
}

'''


# ============================================================
# PREFLIGHT
# Nothing is written until every important build-94 anchor
# has been confirmed.
# ============================================================

engine = ENGINE_MESSAGES.read_text(encoding="utf-8")
transcription = TRANSCRIPTION.read_text(encoding="utf-8")
account = ACCOUNT_STATE.read_text(encoding="utf-8")
background = BACKGROUND.read_text(encoding="utf-8")
header = HEADER.read_text(encoding="utf-8")
section = SECTION.read_text(encoding="utf-8")
pane = PANE.read_text(encoding="utf-8")
profile = PROFILE.read_text(encoding="utf-8")


local_old = '''                    var attributes = currentMessage.attributes.filter { !($0 is AudioTranscriptionMessageAttribute) }
                    
                    attributes.append(AudioTranscriptionMessageAttribute(id: 0, text: text, isPending: !isFinal, didRate: false, error: error))
'''

server_old = '''                        if let attribute = attributes[j] as? AudioTranscriptionMessageAttribute {
                            attributes[j] = AudioTranscriptionMessageAttribute(id: id, text: text, isPending: isPending, didRate: attribute.didRate, error: nil)
                            found = true
                            break loop
                        }
'''

request_success_old = '''                        updatedAttribute = AudioTranscriptionMessageAttribute(id: transcriptionId, text: text, isPending: isPending, didRate: false, error: nil)
'''

request_error_old = '''                case let .error(error):
                    updatedAttribute = AudioTranscriptionMessageAttribute(id: 0, text: "", isPending: false, didRate: false, error: error)
'''

blend_old = '''        if let peer {
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
'''

premium_start = '''        // 3) Premium profile color is a separate state source. It is never
        // mixed into the avatar cache or avatar-derived tint.
        if let peer {
'''

avatar_block = '''        // 4) avatar-derived blurred background
        if self.settings.avatarBlurInProfile,
           let peer,
           let representation = peer.profileImageRepresentations.last {
            let resourceId = String(describing: representation.resource.id)
            return .avatar(peer, representation, resourceId)
        }

'''

section_old = '''        if self.ghostBaseGlassEnabled {
            let alpha: CGFloat = presentationData.theme.overallDarkAppearance ? 0.36 : 0.56
            self.backgroundNode.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor.withAlphaComponent(alpha)
            self.topSeparatorNode.backgroundColor = presentationData.theme.list.itemBlocksSeparatorColor.withAlphaComponent(0.28)
            self.bottomSeparatorNode.backgroundColor = presentationData.theme.list.itemBlocksSeparatorColor.withAlphaComponent(0.28)
        } else {
'''

pane_old = '''        if self.ghostBaseGlassEnabled {
            self.backgroundColor = .clear
        } else {
            self.backgroundColor = backgroundColor
        }
'''

metrics_begin = (
    "    // MARK: GhostBase v1.1G PROFILEMETRICS1 "
    "native compact section\n"
)
metrics_end = "    let bioContextAction:"

if "MARK: GhostBase v1.1H RECOVERY1" not in engine:
    require_once(engine, local_old, "local transcription overwrite")

if "ghostBaseMergeTranscriptionTextV11H" not in account:
    require_once(account, server_old, "server transcription overwrite")

if "MARK: GhostBase v1.1H TRANSCRIPTIONREQUEST1" not in transcription:
    require_once(
        transcription,
        request_success_old,
        "request transcription success overwrite",
    )
    require_once(
        transcription,
        request_error_old,
        "request transcription destructive error",
    )

if "MARK: GhostBase v1.1H AVATARSOURCE1" not in background:
    require_once(
        background,
        blend_old,
        "stock-cover source decision",
    )
    require_once(
        background,
        premium_start,
        "Premium source block",
    )
    require_once(
        background,
        avatar_block,
        "avatar source block",
    )

if "MARK: GhostBase v1.1H ACTIONGLASS1" not in header:
    require_once(
        header,
        "        let regularContentButtonBackgroundColor: UIColor\n","content button declaration",
    )
    require_once(
        header,
        "        let regularHeaderButtonBackgroundColor: UIColor\n",
        "header button declaration",
    )
    require_once(
        header,
        "            ) ? 0.88 : 1.0\n",
        "stock cover alpha",
    )

if "MARK: GhostBase v1.1H SECTIONGLASS1" not in section:
    require_once(
        section,
        "    private let backgroundNode: ASDisplayNode\n",
        "section background property",
    )
    require_once(
        section,
        "        self.backgroundNode.isLayerBacked = true\n",
        "section layer-backed setup",
    )
    require_once(
        section,
        section_old,
        "old opaque section glass",
    )

if "MARK: GhostBase v1.1H NATIVEPANES1" not in pane:
    require_once(
        pane,
        pane_old,
        "transparent pane override",
    )

if "MARK: GhostBase v1.1H PROFILEMETRICS2" not in profile:
    start = profile.find(metrics_begin)
    end = profile.find(metrics_end, start)

    if start < 0 or end <= start:
        raise SystemExit(
            "[V11H PREFLIGHT] profile metrics span unavailable"
        )

    require_once(
        profile,
        '''    case personalChannel
    case peerInfo
    case ghostBaseMetrics
''',
        "profile section order",
    )

print("[V11H PREFLIGHT] all build-94 anchors OK")


# ============================================================
# 1. LOCAL / ON-DEVICE TRANSCRIPTION
# ============================================================

if "MARK: GhostBase v1.1H RECOVERY1" not in engine:
    require_once(
        engine,
        "import TelegramApi\n",
        "TelegramEngineMessages import anchor",
    )

    engine = engine.replace(
        "import TelegramApi\n",
        "import TelegramApi\n"
        + MERGE_HELPER
        + "// MARK: GhostBase v1.1H RECOVERY1\n",
        1,
    )

    local_new = '''                    let previousAttribute = currentMessage.attributes.first(
                        where: { $0 is AudioTranscriptionMessageAttribute }
                    ) as? AudioTranscriptionMessageAttribute

                    let accumulatedText = ghostBaseMergeTranscriptionTextV11H(
                        previous: previousAttribute?.text ?? "",
                        incoming: text
                    )

                    var attributes = currentMessage.attributes.filter {
                        !($0 is AudioTranscriptionMessageAttribute)
                    }

                    // A failure in a later chunk must not erase chunks that
                    // were already recognised.
                    let effectiveError: AudioTranscriptionMessageAttribute.TranscriptionError?
                    if accumulatedText.isEmpty {
                        effectiveError = error
                    } else {
                        effectiveError = nil
                    }

                    attributes.append(
                        AudioTranscriptionMessageAttribute(
                            id: previousAttribute?.id ?? 0,
                            text: accumulatedText,
                            isPending: !isFinal,
                            didRate: previousAttribute?.didRate ?? false,
                            error: effectiveError
                        )
                    )
'''

    engine = engine.replace(local_old, local_new, 1)


# ============================================================
# 2. SERVER updateTranscribedAudio
# ============================================================

if "ghostBaseMergeTranscriptionTextV11H" not in account:
    require_once(
        account,
        "import EncryptionProvider\n",
        "AccountState import anchor",
    )

    account = account.replace(
        "import EncryptionProvider\n",
        "import EncryptionProvider\n" + MERGE_HELPER,
        1,
    )

    server_new = '''                        if let attribute = attributes[j] as? AudioTranscriptionMessageAttribute {
                            let accumulatedText = ghostBaseMergeTranscriptionTextV11H(previous: attribute.text,
                                incoming: text
                            )
                            attributes[j] = AudioTranscriptionMessageAttribute(
                                id: id,
                                text: accumulatedText,
                                isPending: isPending,
                                didRate: attribute.didRate,
                                error: nil
                            )
                            found = true
                            break loop
                        }
'''

    account = account.replace(server_old, server_new, 1)


# ============================================================
# 3. INITIAL TRANSCRIPTION REQUEST
# Success is merged with existing partial text.
# Error preserves already recognised text.
# ============================================================

if "MARK: GhostBase v1.1H TRANSCRIPTIONREQUEST1" not in transcription:
    require_once(
        transcription,
        "import MtProtoKit\n",
        "Transcription import anchor",
    )

    transcription = transcription.replace(
        "import MtProtoKit\n",
        "import MtProtoKit\n"
        + MERGE_HELPER
        + "// MARK: GhostBase v1.1H TRANSCRIPTIONREQUEST1\n",
        1,
    )

    old_decl = '''                let updatedAttribute: AudioTranscriptionMessageAttribute
                switch result {
'''

    new_decl = '''                let previousAttribute = transaction
                    .getMessage(messageId)?
                    .attributes
                    .first(where: {
                        $0 is AudioTranscriptionMessageAttribute
                    }) as? AudioTranscriptionMessageAttribute

                let updatedAttribute: AudioTranscriptionMessageAttribute
                switch result {
'''

    require_once(
        transcription,
        old_decl,
        "previous transcription attribute anchor",
    )

    transcription = transcription.replace(
        old_decl,
        new_decl,
        1,
    )

    request_success_new = '''                        let accumulatedText = ghostBaseMergeTranscriptionTextV11H(
                            previous: previousAttribute?.text ?? "",
                            incoming: text
                        )
                        updatedAttribute = AudioTranscriptionMessageAttribute(
                            id: transcriptionId,
                            text: accumulatedText,
                            isPending: isPending,
                            didRate: previousAttribute?.didRate ?? false,
                            error: nil
                        )
'''

    transcription = transcription.replace(
        request_success_old,
        request_success_new,
        1,
    )

    request_error_new = '''                case let .error(error):
                    if let previousAttribute,
                       !previousAttribute.text.isEmpty {
                        updatedAttribute = AudioTranscriptionMessageAttribute(
                            id: previousAttribute.id,
                            text: previousAttribute.text,
                            isPending: false,
                            didRate: previousAttribute.didRate,
                            error: nil
                        )
                    } else {
                        updatedAttribute = AudioTranscriptionMessageAttribute(
                            id: 0,
                            text: "",
                            isPending: false,
                            didRate: false,
                            error: error
                        )
                    }
'''

    transcription = transcription.replace(
        request_error_old,
        request_error_new,
        1,
    )


# ============================================================
# 4. PROFILE SOURCE PRIORITY
#
# personal wallpaper
# -> global wallpaper
# -> actual avatar image + blur
# -> Premium/profile colour fallback
# -> Telegram theme
# Palette is not allowed to replace the actual avatar image.
# ============================================================

if "MARK: GhostBase v1.1H AVATARSOURCE1" not in background:
    blend_new = '''        if let peer {
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
'''

    background = background.replace(
        blend_old,
        blend_new,
        1,
    )

    premium_pos = background.find(premium_start)
    avatar_pos = background.find(avatar_block)

    if premium_pos < 0 or avatar_pos < 0 or avatar_pos <= premium_pos:
        raise SystemExit(
            "[V11H] unexpected Premium/avatar source ordering"
        )

    avatar_end = avatar_pos + len(avatar_block)

    background = (
        background[:premium_pos]
        + '''        // 3) actual avatar image + blur
        // MARK: GhostBase v1.1H AVATARVISUAL1
        if self.settings.avatarBlurInProfile,
           let peer,
           let representation = peer.profileImageRepresentations.last {
            let resourceId = String(describing: representation.resource.id)
            return .avatar(peer, representation, resourceId)
        }

'''
        + background[premium_pos:avatar_pos]
        .replace(
            "// 3) Premium profile color",
            "// 4) Premium profile color",
            1,
        )
        + background[avatar_end:]
    )

    background = background.replace(
        "        // 5) untouched Telegram theme / stock cover",
        "        // 5) untouched Telegram theme / stock cover",
        1,
    )


# ============================================================
# 5. NATIVE HEADER REMAINS ALIVE, BUT IT MUST NOT COVER
# THE REAL WALLPAPER / AVATAR WITH AN OPAQUE STOCK SURFACE.
# ============================================================

if "MARK: GhostBase v1.1H ACTIONGLASS1" not in header:
    header = header.replace(
        "        let regularContentButtonBackgroundColor: UIColor\n",
        "        var regularContentButtonBackgroundColor: UIColor\n",
        1,
    )

    header = header.replace(
        "        let regularHeaderButtonBackgroundColor: UIColor\n",
        "        var regularHeaderButtonBackgroundColor: UIColor\n",
        1,
    )

    action_anchor = '''        self.contentButtonBackgroundColor = regularNavigationContentsSecondaryColor.mixedWith(regularContentButtonBackgroundColor, alpha: 0.5)
'''

    action_new = '''        // MARK: GhostBase v1.1H ACTIONGLASS1
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

        self.contentButtonBackgroundColor = regularNavigationContentsSecondaryColor.mixedWith(regularContentButtonBackgroundColor, alpha: 0.5)
'''

    require_once(
        header,
        action_anchor,"action button assignment",
    )

    header = header.replace(
        action_anchor,
        action_new,
        1,
    )

    # 0.88 was visually almost the whole stock cover. Keep the native cover
    # component alive for status/gift decoration, but let the actual source
    # below it remain visible.
    header = header.replace(
        "            ) ? 0.88 : 1.0\n",
        "            ) ? 0.18 : 1.0\n",
        1,
    )


# ============================================================
# 6. WHITEGRAM-LIKE SECTION MATERIAL
#
# One blur per section surface, not per cell.
# No 0.36 black cards, no opaque corner wedges.
# ============================================================

if "MARK: GhostBase v1.1H SECTIONGLASS1" not in section:
    section = section.replace(
        "    private let backgroundNode: ASDisplayNode\n",
        '''    private let backgroundNode: ASDisplayNode
    // MARK: GhostBase v1.1H SECTIONGLASS1
    private let ghostBaseGlassEffectView: UIVisualEffectView?
    private var ghostBaseGlassEffectIsDark: Bool?
''',
        1,
    )

    init_old = '''        self.ghostBaseGlassEnabled = ghostBaseGlassEnabled
        self.backgroundNode = ASDisplayNode()
        self.backgroundNode.isLayerBacked = true
'''

    init_new = '''        self.ghostBaseGlassEnabled = ghostBaseGlassEnabled
        if ghostBaseGlassEnabled {
            self.ghostBaseGlassEffectView = UIVisualEffectView(effect: nil)
        } else {
            self.ghostBaseGlassEffectView = nil
        }
        self.backgroundNode = ASDisplayNode()
        self.backgroundNode.isLayerBacked = !ghostBaseGlassEnabled
'''

    require_once(
        section,
        init_old,
        "section init",
    )

    section = section.replace(
        init_old,
        init_new,
        1,
    )

    add_old = '''        self.addSubnode(self.backgroundNode)
        self.addSubnode(self.itemContainerNode)
'''

    add_new = '''        self.addSubnode(self.backgroundNode)
        if let ghostBaseGlassEffectView = self.ghostBaseGlassEffectView {
            ghostBaseGlassEffectView.isUserInteractionEnabled = false
            ghostBaseGlassEffectView.clipsToBounds = true
            self.backgroundNode.view.addSubview(
                ghostBaseGlassEffectView
            )
        }
        self.addSubnode(self.itemContainerNode)
'''

    require_once(
        section,
        add_old,
        "section effect attachment",
    )

    section = section.replace(
        add_old,
        add_new,
        1,
    )

    section_new = '''        if self.ghostBaseGlassEnabled {
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
'''

    section = section.replace(
        section_old,
        section_new,
        1,
    )

    frame_old = '''        transition.updateFrame(node: self.backgroundNode, frame: CGRect(origin: CGPoint(x: 0.0, y: contentWithBackgroundOffset), size: CGSize(width: width, height: max(0.0, contentWithBackgroundHeight - contentWithBackgroundOffset))))
'''

    frame_new = '''        let backgroundFrame = CGRect(
            origin: CGPoint(
                x: 0.0,
                y: contentWithBackgroundOffset
            ),
            size: CGSize(
                width: width,
                height: max(
                    0.0,contentWithBackgroundHeight
                        - contentWithBackgroundOffset
                )
            )
        )
        transition.updateFrame(
            node: self.backgroundNode,
            frame: backgroundFrame
        )

        if let ghostBaseGlassEffectView = self.ghostBaseGlassEffectView {
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
'''

    require_once(
        section,
        frame_old,
        "section background frame",
    )

    section = section.replace(
        frame_old,
        frame_new,
        1,
    )


# ============================================================
# 7. MEMBERS / MEDIA / GIFTS PANES STAY TELEGRAM-NATIVE
#
# Build 94 made the pane itself transparent, which let unrelated
# profile material bleed through participants and other native panes.
# ============================================================

if "MARK: GhostBase v1.1H NATIVEPANES1" not in pane:
    pane_new = '''        // MARK: GhostBase v1.1H NATIVEPANES1
        // Preserve Telegram's own pane/list background and geometry.
        // Glass belongs to the profile surfaces, not to every pane cell.
        self.backgroundColor = backgroundColor
'''

    pane = pane.replace(
        pane_old,
        pane_new,
        1,
    )


# ============================================================
# 8. ID / DC / REGISTRATION
#
# No separate "Сведения" section.
# Put them back into native peerInfo at the top and restore copy.
# Personal Channel remains its native PeerInfoScreenPersonalChannelItem.
# ============================================================

if "MARK: GhostBase v1.1H PROFILEMETRICS2" not in profile:
    profile = profile.replace(
        '''    case personalChannel
    case peerInfo
    case ghostBaseMetrics
''',
        '''    case peerInfo
    case personalChannel
    case ghostBaseMetrics
''',
        1,
    )

    start = profile.find(metrics_begin)
    end = profile.find(metrics_end, start)

    metrics_new = '''    // MARK: GhostBase v1.1H PROFILEMETRICS2
    // These are normal Telegram labeled-value rows again. They belong to
    // peerInfo, not to a second standalone "Сведения" card.
    if ghostBaseMetricsSettings.enabled, let peer = data.peer {
        var itemId = 990000
        var metricItems: [PeerInfoScreenItem] = []

        if ghostBaseMetricsSettings.showIds {
            let idText: String
            if case let .channel(channel) = peer {
                idText = "-100" + String(
                    channel.id.id._internalGetInt64Value()
                )
            } else {
                idText = String(
                    peer.id.id._internalGetInt64Value()
                )
            }

            metricItems.append(
                PeerInfoScreenLabeledValueItem(
                    id: itemId,
                    label: "Telegram ID",
                    text: idText,
                    textColor: .primary,
                    action: { _, _ in
                        UIPasteboard.general.string = idText
                    },
                    longTapAction: { _ in
                        UIPasteboard.general.string = idText
                    },
                    requestLayout: { _ in
                        interaction.requestLayout(false)
                    }
                )
            )
            itemId += 1
        }

        if ghostBaseMetricsSettings.showDCs,
           let representation = peer.smallProfileImage,
           let resource = representation.resource
                as? CloudPeerPhotoSizeMediaResource {
            let dcText = String(resource.datacenterId)

            metricItems.append(PeerInfoScreenLabeledValueItem(
                    id: itemId,
                    label: "DC",
                    text: dcText,
                    textColor: .primary,
                    action: { _, _ in
                        UIPasteboard.general.string = dcText
                    },
                    longTapAction: { _ in
                        UIPasteboard.general.string = dcText
                    },
                    requestLayout: { _ in
                        interaction.requestLayout(false)
                    }
                )
            )
            itemId += 1
        }

        if ghostBaseMetricsSettings.showRegistration,
           let cachedData = data.cachedData as? CachedUserData,
           let registrationDate =
                cachedData.peerStatusSettings?.registrationDate {
            let components = registrationDate.components(
                separatedBy: "."
            )

            if components.count == 2,
               let monthValue = Int32(components[0]),
               let yearValue = Int32(components[1]) {
                let dateText = stringForMonth(
                    strings: presentationData.strings,
                    month: monthValue - 1,
                    ofYear: yearValue - 1900
                )

                metricItems.append(
                    PeerInfoScreenLabeledValueItem(
                        id: itemId,
                        label: "Дата регистрации",
                        text: dateText,
                        textColor: .primary,
                        action: { _, _ in
                            UIPasteboard.general.string = dateText
                        },
                        longTapAction: { _ in
                            UIPasteboard.general.string = dateText
                        },
                        requestLayout: { _ in
                            interaction.requestLayout(false)
                        }
                    )
                )
            }
        }

        if !metricItems.isEmpty {
            items[.peerInfo]!.append(
                contentsOf: metricItems
            )
        }
    }

'''

    profile = (
        profile[:start]
        + metrics_new
        + profile[end:]
    )


# ============================================================
# FINAL MATERIALIZED-SOURCE ASSERTIONS
# ============================================================

assert 'text: "", isPending: false, didRate: false, error: error' \
    not in transcription

assert "previous: attribute.text" in account
assert "previousAttribute?.text ?? \"\"" in engine

avatar_position = background.find(
    "// 3) actual avatar image + blur"
)
premium_position = background.find(
    "// 4) Premium profile color"
)

if (
    avatar_position < 0
    or premium_position < 0
    or avatar_position >= premium_position
):
    raise SystemExit(
        "[V11H] avatar/Premium priority final assertion failed"
    )

if "0.36 : 0.56" in section:
    raise SystemExit(
        "[V11H] old opaque section glass survived"
    )

if '''if self.ghostBaseGlassEnabled {
            self.backgroundColor = .clear''' in pane:
    raise SystemExit(
        "[V11H] transparent pane override survived"
    )

if 'text: "Сведения"' in profile:
    raise SystemExit(
        "[V11H] standalone Сведения header survived"
    )

if "items[.peerInfo]!.append" not in profile:
    raise SystemExit(
        "[V11H] peerInfo metrics integration missing"
    )


# ============================================================
# WRITE ONLY AFTER THE ENTIRE TRANSFORMATION SUCCEEDED
# ============================================================

outputs = {
    ENGINE_MESSAGES: engine,
    TRANSCRIPTION: transcription,
    ACCOUNT_STATE: account,
    BACKGROUND: background,
    HEADER: header,
    SECTION: section,
    PANE: pane,
    PROFILE: profile,
}

for path, value in outputs.items():
    path.write_text(value, encoding="utf-8")

print("[V11H] RECOVERY1 applied")
print("[V11H] long transcription now accumulates")
print("[V11H] final transcription errors preserve recognised text")
print("[V11H] actual avatar image precedes Premium colour fallback")
print("[V11H] stock cover no longer hides avatar/wallpaper")
print("[V11H] native action geometry preserved with glass material")
print("[V11H] opaque profile cards replaced by section blur")
print("[V11H] native members/media/gifts pane background restored")
print("[V11H] Telegram ID/DC/registration returned to peerInfo")
print("[V11H] metric rows are copyable")
print("[V11H] Personal Channel/Gifts native wiring left intact")
