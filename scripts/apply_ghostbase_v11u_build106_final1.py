#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src",
)).resolve()

PATHS = {
    "bg": ROOT / (
        "submodules/TelegramUI/Components/PeerInfo/"
        "PeerInfoScreen/Sources/"
        "GhostBaseProfileFullscreenBackground.swift"
    ),
    "peer_item": ROOT / (
        "submodules/ItemListPeerItem/Sources/"
        "ItemListPeerItem.swift"
    ),
    "music_controller": ROOT / (
        "submodules/TelegramUI/Sources/"
        "OverlayAudioPlayerControllerNode.swift"
    ),
    "music_controls": ROOT / (
        "submodules/TelegramUI/Sources/"
        "OverlayAudioPlayerControlsNode.swift"
    ),
    "chat_text": ROOT / (
        "submodules/ChatPresentationInterfaceState/Sources/"
        "ChatTextFormat.swift"
    ),
    "enqueue": ROOT / (
        "submodules/TelegramCore/Sources/PendingMessages/"
        "EnqueueMessage.swift"
    ),
    "gift_options": ROOT / (
        "submodules/TelegramUI/Components/Gifts/"
        "GiftOptionsScreen/Sources/"
        "GiftOptionsScreen.swift"
    ),
}

MARKER = "GhostBase v1.1U BUILD106_FINAL1"

for name, path in PATHS.items():
    if not path.is_file():
        raise RuntimeError(
            f"[V11U] missing required source {name}: {path}"
        )

sources = {
    name: path.read_text(encoding="utf-8")
    for name, path in PATHS.items()
}

if MARKER in sources["enqueue"]:
    print("[V11U] BUILD106_FINAL1 already materialized")
    raise SystemExit(0)


def once(
    text: str,
    old: str,
    new: str,
    label: str,
) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"[V11U] {label}: "
            f"expected exactly one anchor, found {count}"
        )
    return text.replace(old, new, 1)


def balanced_region(
    text: str,
    token: str,
    *,
    label: str,
) -> tuple[int, int]:
    start = text.find(token)

    if start < 0:
        raise RuntimeError(
            f"[V11U] {label}: start token not found"
        )

    brace = text.find(
        "{",
        start + len(token),
    )

    if brace < 0:
        raise RuntimeError(
            f"[V11U] {label}: opening brace not found"
        )

    depth = 0
    in_string = False
    escaped = False

    i = brace

    while i < len(text):
        ch = text[i]

        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False

            i += 1
            continue

        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1

            if depth == 0:
                return start, i + 1

        i += 1

    raise RuntimeError(
        f"[V11U] {label}: closing brace not found"
    )


# ================================================================
# PRECONDITIONS
#
# V11U intentionally targets the tested Build105 materialized
# source. Do not silently adapt to an unknown generated tree.
# ================================================================

required = {
    "bg": [
        "GhostBase v1.1T BUILD97_STATIC_AVATAR_BLUR1",
        "GhostBase v1.1T BUILD97_STATIC_AVATAR_PIPELINE1",
        "GhostBase v1.1T BUILD97_STATIC_AVATAR_CACHE1",
    ],

    "music_controller": [
        "GhostBase v1.1T MUSIC_HEADER_READABLE_GLASS1",
        "private func updateGhostBaseMusicSurfaces()",
    ],

    "music_controls": [
        "GhostBase v1.1T MUSIC_READABLE_GLASS1",
    ],

    "enqueue": [
        "GhostBase v1.1T BUILD105_FULL1",
        "private func ghostBaseResolveDeletedReplies(",
        "private func ghostBaseReconstructedMedia(",
    ],

    "gift_options": [
        "GhostBase v1.0ZB Seasonal Gifts",
        "GhostBaseSeasonalGiftDescriptor(",
        "5974210632977745012",
        "stickerIndex: 10",
    ],
}

for name, proofs in required.items():
    for proof in proofs:
        if proof not in sources[name]:
            raise RuntimeError(
                f"[V11U] {name}: "
                f"prerequisite missing: {proof}"
            )

backups = dict(sources)

try:

    # ============================================================
    # A. STATIC AVATAR BLUR
    # ============================================================

    bg = sources["bg"]

    old_blur = '''            // MARK: GhostBase v1.1T BUILD97_STATIC_AVATAR_BLUR1
            // Build104 proved 0.60 is still materially stronger than the
            // readable Build97 look. Lower ONLY the static-photo material.
            // Animated avatars keep the already-stable full-strength path.
            if animatedSource == nil {
                self.blurView.alpha = reduced ? 0.24 : 0.38
            } else {
                self.blurView.alpha = 1.0
            }
'''

    new_blur = '''            // MARK: GhostBase v1.1U BUILD106_STATIC_AVATAR_BLUR1
            // Build105 runtime proved that lowering UIVisualEffectView.alpha
            // does not lower blur intensity: it exposes the sharp stretched
            // image beneath it. Keep the persistent blur owner fully opaque.
            //
            // Reduced mode still affects the existing tint/cost policy; it
            // must not turn the scene back into an almost-unblurred avatar.
            self.blurView.alpha = 1.0
'''

    bg = once(
        bg,
        old_blur,
        new_blur,
        "static avatar blur owner",
    )

    sources["bg"] = bg

    # ============================================================
    # B. COMMON GROUPS
    # ============================================================

    peer_item = sources["peer_item"]

    old_late_background = '''                    strongSelf.backgroundNode.isHidden = !item.displayDecorations
                    strongSelf.highlightedBackgroundNode.isHidden = !item.displayDecorations || !item.highlightable
'''

    new_late_background = '''                    // MARK: GhostBase v1.1U BUILD106_COMMON_GROUPS_OWNER1
                    // displayBackground is intentionally false for the
                    // GhostBase Common Groups rows. Do not let this later
                    // decorations pass re-enable their opaque stock cell.
                    strongSelf.backgroundNode.isHidden =
                        !item.displayDecorations || !item.displayBackground
                    strongSelf.highlightedBackgroundNode.isHidden = !item.displayDecorations || !item.highlightable
'''

    peer_item = once(
        peer_item,
        old_late_background,
        new_late_background,
        "Common Groups final background override",
    )

    sources["peer_item"] = peer_item

    # ============================================================
    # C. FULL MUSIC PLAYER
    # ============================================================

    controller = sources["music_controller"]

    start, end = balanced_region(
        controller,
        "    private func updateGhostBaseMusicSurfaces()",
        label="music surface function",
    )

    music_function = r'''    private func updateGhostBaseMusicSurfaces() {
        guard self.isGhostBaseProfileMusicActive else {
            self.dimNode.backgroundColor =
                UIColor(
                    white: 0.0,
                    alpha: 0.5
                )

            self.historyBackgroundContentNode.backgroundColor =
                self.hasAnyHistoryMessages == true
                ? self.presentationData
                    .theme
                    .list
                    .itemModalBlocksBackgroundColor
                : self.presentationData
                    .theme
                    .list
                    .modalPlainBackgroundColor

            self.historyFrameLeftOverlayNode.backgroundColor =
                self.hasAnyHistoryMessages == true
                ? self.presentationData
                    .theme
                    .list
                    .modalBlocksBackgroundColor
                : self.presentationData
                    .theme
                    .list
                    .modalPlainBackgroundColor

            self.historyFrameRightOverlayNode.backgroundColor =
                self.hasAnyHistoryMessages == true
                ? self.presentationData
                    .theme
                    .list
                    .modalBlocksBackgroundColor
                : self.presentationData
                    .theme
                    .list
                    .modalPlainBackgroundColor

            self.historyFrameTopOverlayNode.backgroundColor =
                self.hasAnyHistoryMessages == true
                ? self.presentationData
                    .theme
                    .list
                    .modalBlocksBackgroundColor
                : self.presentationData
                    .theme
                    .list
                    .modalPlainBackgroundColor

            self.historyFrameTopMaskNode.alpha = 1.0

            self.controlsNode.hasPlainBackground =
                !self.historyNode.hasAnyMessages

            self.controlsNode
                .ghostBaseGlassBackgroundEnabled = false

            self.ghostBaseHeaderGlassView?.isHidden = true
            self.ghostBaseHeaderGlassView?.effect = nil
            self.ghostBaseHeaderGlassView?
                .layer
                .borderWidth = 0.0
            self.ghostBaseHeaderGlassView?
                .layer
                .borderColor = nil
            self.ghostBaseHeaderGlassTintView?
                .backgroundColor = .clear

            return
        }

        // MARK: GhostBase v1.1U BUILD106_MUSIC_MOVING_SHEET1
        let isDark =
            self.presentationData
                .theme
                .overallDarkAppearance

        let sheetColor =
            self.presentationData
                .theme
                .list
                .itemBlocksBackgroundColor
                .withAlphaComponent(
                    isDark
                    ? 0.34
                    : 0.42
                )

        self.dimNode.backgroundColor =
            UIColor(
                white: 0.0,
                alpha: 0.055
            )

        self.historyBackgroundContentNode
            .backgroundColor = sheetColor

        self.historyFrameLeftOverlayNode
            .backgroundColor = sheetColor

        self.historyFrameRightOverlayNode
            .backgroundColor = sheetColor

        self.historyFrameTopOverlayNode
            .backgroundColor = sheetColor

        self.historyFrameTopMaskNode.alpha = 0.0

        self.controlsNode.hasPlainBackground = false
        self.controlsNode
            .ghostBaseGlassBackgroundEnabled = true

        self.ghostBaseHeaderGlassView?.isHidden = true
        self.ghostBaseHeaderGlassView?.effect = nil
        self.ghostBaseHeaderGlassView?
            .layer
            .borderWidth = 0.0
        self.ghostBaseHeaderGlassView?
            .layer
            .borderColor = nil
        self.ghostBaseHeaderGlassTintView?
            .backgroundColor = .clear
    }'''

    controller = (
        controller[:start]
        + music_function
        + controller[end:]
    )

    sources["music_controller"] = controller

    controls = sources["music_controls"]

    start, end = balanced_region(
        controls,
        "    private func updateGhostBaseGlassBackground()",
        label="music controls material function",
    )

    controls_function = r'''    // MARK: GhostBase v1.1U BUILD106_MUSIC_CONTROLS1
    private func updateGhostBaseGlassBackground() {
        let isDark =
            self.presentationData
                .theme
                .overallDarkAppearance

        self.backgroundNode.isHidden =
            self.ghostBaseGlassBackgroundEnabled

        if self.ghostBaseGlassBackgroundEnabled {
            self.ghostBaseGlassIsDark = isDark

            self.ghostBaseGlassEffectView.effect =
                UIBlurEffect(
                    style:
                        isDark
                        ? .systemUltraThinMaterialDark
                        : .systemUltraThinMaterialLight
                )

            self.ghostBaseGlassEffectView.alpha = 1.0
            self.ghostBaseGlassEffectView.isHidden = false

            self.ghostBaseGlassEffectView
                .backgroundColor = .clear

            self.ghostBaseGlassEffectView
                .contentView
                .backgroundColor = .clear

            self.ghostBaseGlassEffectView
                .layer
                .borderWidth = UIScreenPixel

            self.ghostBaseGlassEffectView
                .layer
                .borderColor =
                    UIColor.white
                        .withAlphaComponent(
                            isDark
                            ? 0.10
                            : 0.16
                        )
                        .cgColor

            self.ghostBaseGlassTintView
                .backgroundColor =
                    self.presentationData
                        .theme
                        .list
                        .itemBlocksBackgroundColor
                        .withAlphaComponent(
                            isDark
                            ? 0.20
                            : 0.26
                        )
        } else {
            self.ghostBaseGlassEffectView.isHidden = true
            self.ghostBaseGlassEffectView.effect = nil
            self.ghostBaseGlassEffectView.alpha = 1.0

            self.ghostBaseGlassEffectView
                .layer
                .borderWidth = 0.0

            self.ghostBaseGlassEffectView
                .layer
                .borderColor = nil

            self.ghostBaseGlassTintView
                .backgroundColor = .clear
        }
    }'''

    controls = (
        controls[:start]
        + controls_function
        + controls[end:]
    )

    sources["music_controls"] = controls

    # ============================================================
    # D. CUSTOM / PREMIUM EMOJI INSIDE QUOTE
    # ============================================================

    chat_text = sources["chat_text"]

    old_quote_branch = '''            if key == ChatTextInputAttributes.block {
                attributesToRemove.append((key, range))
                quoteRange = quoteRange.union(range)
            } else {
                attributesToRemove.append((key, nsRange))
            }
'''

    new_quote_branch = '''            if key == ChatTextInputAttributes.block {
                attributesToRemove.append((key, range))
                quoteRange = quoteRange.union(range)
            } else if key == ChatTextInputAttributes.customEmoji {
                // MARK: GhostBase v1.1U BUILD106_CUSTOM_EMOJI_QUOTE1
                continue
            } else {
                attributesToRemove.append((key, nsRange))
            }
'''

    chat_text = once(
        chat_text,
        old_quote_branch,
        new_quote_branch,
        "custom emoji quote preservation",
    )

    sources["chat_text"] = chat_text

    # ============================================================
    # E. DELETED PORTABLE REPLY V2
    # ============================================================

    enqueue = sources["enqueue"]

    old_mime = '''                case "video/mp4":
                    ext = "mp4"
                case "audio/ogg", "audio/opus":
                    ext = "ogg"
                case "audio/mpeg":
                    ext = "mp3"
                case "image/gif":
                    ext = "gif"
                default:
                    break
'''

    new_mime = '''                case "video/mp4":
                    ext = "mp4"
                case "video/webm":
                    ext = "webm"
                case "application/x-tgsticker":
                    ext = "tgs"
                case "image/webp":
                    ext = "webp"
                case "audio/ogg", "audio/opus":
                    ext = "ogg"
                case "audio/mpeg":
                    ext = "mp3"
                case "image/gif":
                    ext = "gif"
                default:
                    break
'''

    enqueue = once(
        enqueue,
        old_mime,
        new_mime,
        "sticker cache mime extensions",
    )

    old_plan = '''private struct GhostBaseDeletedReplyPlan {
    let outgoing: EnqueueMessage
    let source: Message?
    let authorName: String?
    let mentionPeerId: PeerId?
}
'''

    new_plan = '''// MARK: GhostBase v1.1U BUILD106_FINAL1
private struct GhostBaseDeletedReplyPlan {
    let outgoing: EnqueueMessage
    let source: Message?
    let sourceGroup: [Message]
    let authorName: String?
    let authorUsername: String?
    let mentionPeerId: PeerId?
}
'''

    enqueue = once(
        enqueue,
        old_plan,
        new_plan,
        "deleted reply plan V2",
    )

    old_build_sig = '''private func ghostBaseBuildPortableDeletedReply(
    outgoing: EnqueueMessage,
    source: Message,
    authorName: String,
    mentionPeerId: PeerId?,
    recoveredMedia: AnyMediaReference?
) -> EnqueueMessage {
'''

    new_build_sig = '''private func ghostBaseBuildPortableDeletedReply(
    outgoing: EnqueueMessage,
    source: Message,
    authorName: String,
    authorUsername: String?,
    mentionPeerId: PeerId?,
    recoveredMedia: AnyMediaReference?,
    forcedLocalGroupingKey: Int64? = nil
) -> EnqueueMessage {
'''

    enqueue = once(
        enqueue,
        old_build_sig,
        new_build_sig,
        "portable reply signature",
    )

    old_author_entity = '''    var entities: [MessageTextEntity] = []
    if let mentionPeerId, authorLength > 0 {
        entities.append(MessageTextEntity(
            range: 0 ..< authorLength,
            type: .TextMention(peerId: mentionPeerId)
        ))
    }
'''

    new_author_entity = '''    var entities: [MessageTextEntity] = []
    if authorLength > 0 {
        // MARK: GhostBase v1.1U BUILD106_PORTABLE_AUTHOR1
        if let authorUsername,
           !authorUsername.isEmpty {
            entities.append(
                MessageTextEntity(
                    range: 0 ..< authorLength,
                    type: .TextUrl(
                        url: "https://t.me/\\(authorUsername)"
                    )
                )
            )
        } else if let mentionPeerId {
            entities.append(
                MessageTextEntity(
                    range: 0 ..< authorLength,
                    type: .TextMention(
                        peerId: mentionPeerId
                    )
                )
            )
        }

        entities.append(
            MessageTextEntity(
                range: 0 ..< authorLength,
                type: .Bold
            )
        )
    }
'''

    enqueue = once(
        enqueue,
        old_author_entity,
        new_author_entity,
        "portable author entities",
    )

    enqueue = once(
        enqueue,
        "        localGroupingKey: localGroupingKey,\n",
        (
            "        localGroupingKey: "
            "forcedLocalGroupingKey ?? localGroupingKey,\n"
        ),
        "portable reply grouping override",
    )

    old_reconstruct_guard = '''    guard source.groupingKey == nil,
          source.media.count == 1 else {
        return nil
    }
'''

    new_reconstruct_guard = '''    // MARK: GhostBase v1.1U BUILD106_GROUPED_MEDIA1
    guard source.media.count == 1 else {
        return nil
    }
'''

    enqueue = once(
        enqueue,
        old_reconstruct_guard,
        new_reconstruct_guard,
        "grouped media reconstruction gate",
    )

    sticker_guard = '''    if let file = media as? TelegramMediaFile, file.isSticker {
        return nil
    }

'''

    if enqueue.count(sticker_guard) != 1:
        raise RuntimeError(
            "[V11U] sticker recovery guard: "
            f"expected one, found {enqueue.count(sticker_guard)}"
        )

    enqueue = enqueue.replace(
        sticker_guard,
        '''    // MARK: GhostBase v1.1U BUILD106_STICKER_RECOVERY1
    // Keep TelegramMediaFile mimeType + attributes.

''',
        1,
    )

    builder_start = enqueue.find(
        "private func ghostBaseBuildPortableDeletedReply("
    )

    builder_end_token = (
        "\n}\n\n"
        "private func ghostBaseReconstructedMedia("
    )

    builder_end = enqueue.find(
        builder_end_token,
        builder_start,
    )

    if builder_end < 0:
        raise RuntimeError(
            "[V11U] album tail helper "
            "insertion point missing"
        )

    helper = r'''

private func ghostBaseBuildRecoveredAlbumTail(
    outgoing: EnqueueMessage,
    recoveredMedia: AnyMediaReference,
    localGroupingKey: Int64
) -> EnqueueMessage {
    guard case let .message(
        _,
        requestedAttributes,
        _,
        userMediaReference,
        threadId,
        _,
        replyToStoryId,
        _,
        _,
        _
    ) = outgoing,
    userMediaReference == nil else {
        return outgoing
    }

    var attributes: [MessageAttribute] = []

    for attribute in requestedAttributes {
        if attribute is ReplyMessageAttribute
            || attribute is TextEntitiesMessageAttribute {
            continue
        }

        attributes.append(attribute)
    }

    return .message(
        text: "",
        attributes: attributes,
        inlineStickers: [:],
        mediaReference: recoveredMedia,
        threadId: threadId,
        replyToMessageId: nil,
        replyToStoryId: replyToStoryId,
        localGroupingKey: localGroupingKey,
        correlationId: nil,
        bubbleUpEmojiOrStickersets: []
    )
}
'''

    enqueue = (
        enqueue[:builder_end + 2]
        + helper
        + enqueue[builder_end + 2:]
    )

    resolver_pos = enqueue.find(
        "private func ghostBaseResolveDeletedReplies("
    )

    tx_start = enqueue.find(
        (
            "    return account.postbox.transaction "
            "{ transaction -> [GhostBaseDeletedReplyPlan] in\n"
        ),
        resolver_pos,
    )

    tx_end_token = (
        "    |> mapToSignal { plans -> "
        "Signal<[EnqueueMessage], NoError> in\n"
    )

    tx_end = enqueue.find(
        tx_end_token,
        tx_start,
    )

    if tx_start < 0 or tx_end < 0:
        raise RuntimeError(
            "[V11U] deleted reply "
            "planning boundaries missing"
        )

    tx_replacement = r'''    return account.postbox.transaction { transaction -> [GhostBaseDeletedReplyPlan] in
        return messages.map { outgoing in
            guard case let .message(
                _, _, _, _, _, replySubject, _, _, _, _
            ) = outgoing,
            let replySubject,
            let source =
                transaction.getMessage(
                    replySubject.messageId
                ),
            let deletedAttribute =
                source.attributes.first(
                    where: {
                        $0 is GhostBaseMessageAttribute
                    }
                ) as? GhostBaseMessageAttribute,
            deletedAttribute.isDeleted else {

                return GhostBaseDeletedReplyPlan(
                    outgoing: outgoing,
                    source: nil,
                    sourceGroup: [],
                    authorName: nil,
                    authorUsername: nil,
                    mentionPeerId: nil
                )
            }

            // MARK: GhostBase v1.1U BUILD106_ALBUM_QUERY1
            let sourceGroup: [Message]

            if source.groupingKey != nil {
                sourceGroup =
                    transaction
                        .getMessageGroup(source.id)
                    ?? [source]
            } else {
                sourceGroup = [source]
            }

            let authorPeer = source.author
            let authorName: String

            if let authorPeer,
               let stored =
                    GhostBasePublicPeerNameStore
                        .name(peerId: authorPeer.id),
               !stored.isEmpty {
                authorName = stored
            } else if let authorPeer {
                let title =
                    EnginePeer(authorPeer)
                        .debugDisplayTitle
                authorName =
                    title.isEmpty
                    ? "Пользователь"
                    : title
            } else {
                authorName = "Пользователь"
            }

            let authorUsername: String?

            if let raw =
                authorPeer?
                    .addressName?
                    .trimmingCharacters(
                        in: .whitespacesAndNewlines
                    ),
               !raw.isEmpty {
                authorUsername =
                    raw.hasPrefix("@")
                    ? String(raw.dropFirst())
                    : raw
            } else {
                authorUsername = nil
            }

            var mentionPeerId: PeerId?

            if ghostBaseCloudDestination,
               authorUsername == nil,
               let authorPeer,
               authorPeer.id.namespace
                    == Namespaces.Peer.CloudUser,
               apiInputUser(authorPeer) != nil {
                mentionPeerId = authorPeer.id
            }

            return GhostBaseDeletedReplyPlan(
                outgoing: outgoing,
                source: source,
                sourceGroup: sourceGroup,
                authorName: authorName,
                authorUsername: authorUsername,
                mentionPeerId: mentionPeerId
            )
        }
    }
'''

    enqueue = (
        enqueue[:tx_start]
        + tx_replacement
        + enqueue[tx_end:]
    )

    map_signal_pos = enqueue.find(
        tx_end_token,
        tx_start,
    )

    loop_start = enqueue.find(
        "                for plan in plans {\n",
        map_signal_pos,
    )

    if loop_start < 0:
        raise RuntimeError(
            "[V11U] deleted reply result loop missing"
        )

    loop_brace = enqueue.find("{", loop_start)

    depth = 0
    i = loop_brace
    in_string = False
    escaped = False
    loop_end = -1

    while i < len(enqueue):
        ch = enqueue[i]

        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    loop_end = i + 1
                    break
        i += 1

    if loop_end < 0:
        raise RuntimeError(
            "[V11U] deleted reply result loop unbalanced"
        )

    loop_replacement = r'''                for plan in plans {
                    guard
                        let source = plan.source,
                        let authorName = plan.authorName
                    else {
                        result.append(plan.outgoing)
                        continue
                    }

                    let recoverySources =
                        source.groupingKey != nil
                        ? plan.sourceGroup
                        : [source]

                    var recoveredGroup: [AnyMediaReference] = []
                    recoveredGroup.reserveCapacity(recoverySources.count)

                    for groupSource in recoverySources {
                        if let recovered =
                            ghostBaseReconstructedMedia(
                                account: account,
                                peerId: peerId,
                                source: groupSource,
                                outgoing: plan.outgoing
                            ) {
                            recoveredGroup.append(recovered)
                        }
                    }

                    // MARK: GhostBase v1.1U BUILD106_ALBUM_RECOVERY1
                    if source.groupingKey != nil,
                       recoveredGroup.count >= 2 {

                        let localGroupingKey =
                            Int64.random(
                                in: Int64.min ... Int64.max
                            )

                        var first =
                            ghostBaseBuildPortableDeletedReply(
                                outgoing: plan.outgoing,
                                source: source,
                                authorName: authorName,
                                authorUsername: plan.authorUsername,
                                mentionPeerId: plan.mentionPeerId,
                                recoveredMedia: recoveredGroup[0],
                                forcedLocalGroupingKey: localGroupingKey
                            )

                        if case let .message(
                            text, _, _, _, _, _, _, _, _, _
                        ) = first,
                        (text as NSString).length > 1024 {
                            first =
                                ghostBaseBuildPortableDeletedReply(
                                    outgoing: plan.outgoing,
                                    source: source,
                                    authorName: authorName,
                                    authorUsername: plan.authorUsername,
                                    mentionPeerId: plan.mentionPeerId,
                                    recoveredMedia: nil
                                )

                            result.append(first)

                            for recovered in recoveredGroup {
                                result.append(
                                    ghostBaseBuildRecoveredAlbumTail(
                                        outgoing: plan.outgoing,
                                        recoveredMedia: recovered,
                                        localGroupingKey: localGroupingKey
                                    )
                                )
                            }
                        } else {
                            result.append(first)

                            for recovered in recoveredGroup.dropFirst() {
                                result.append(
                                    ghostBaseBuildRecoveredAlbumTail(
                                        outgoing: plan.outgoing,
                                        recoveredMedia: recovered,
                                        localGroupingKey: localGroupingKey
                                    )
                                )
                            }
                        }

                        continue
                    }

                    let recovered = recoveredGroup.first

                    var candidate =
                        ghostBaseBuildPortableDeletedReply(
                            outgoing: plan.outgoing,
                            source: source,
                            authorName: authorName,
                            authorUsername: plan.authorUsername,
                            mentionPeerId: plan.mentionPeerId,
                            recoveredMedia: recovered
                        )

                    if recovered != nil,
                       case let .message(
                            text, _, _, _, _, _, _, _, _, _
                       ) = candidate,
                       (text as NSString).length > 1024 {
                        candidate =
                            ghostBaseBuildPortableDeletedReply(
                                outgoing: plan.outgoing,
                                source: source,
                                authorName: authorName,
                                authorUsername: plan.authorUsername,
                                mentionPeerId: plan.mentionPeerId,
                                recoveredMedia: nil
                            )
                    }

                    result.append(candidate)
                }'''

    enqueue = (
        enqueue[:loop_start]
        + loop_replacement
        + enqueue[loop_end:]
    )

    sources["enqueue"] = enqueue

    # ============================================================
    # F. NEW BEAR
    # ============================================================

    gifts = sources["gift_options"]

    if "id: 6046178578163303744" not in gifts:

        football = '''    GhostBaseSeasonalGiftDescriptor(
        id: 5974210632977745012,
        title: "Football Bear",
        price: 50,
        stickerIndex: 10
    )
'''

        bear = '''    GhostBaseSeasonalGiftDescriptor(
        id: 5974210632977745012,
        title: "Football Bear",
        price: 50,
        stickerIndex: 10
    ),
    // MARK: GhostBase v1.1U BUILD106_NEW_BEAR1
    GhostBaseSeasonalGiftDescriptor(
        id: 6046178578163303744,
        title: "Мишка",
        price: 50,
        stickerIndex: 11
    )
'''

        gifts = once(
            gifts,
            football,
            bear,
            "new bear seasonal descriptor",
        )

    else:
        if "stickerIndex: 11" not in gifts:
            raise RuntimeError(
                "[V11U] bear ID already exists in "
                "GiftOptionsScreen but stickerIndex 11 "
                "is not proven"
            )

    sources["gift_options"] = gifts

    # ============================================================
    # G. PRE-WRITE MATERIALIZED SOURCE PROOFS
    # ============================================================

    proofs = [
        ("blur marker", "BUILD106_STATIC_AVATAR_BLUR1" in sources["bg"]),
        ("blur full alpha", "self.blurView.alpha = 1.0" in sources["bg"]),
        ("Common Groups final owner", "!item.displayDecorations || !item.displayBackground" in sources["peer_item"]),
        ("music moving owner", "BUILD106_MUSIC_MOVING_SHEET1" in sources["music_controller"]),
        ("music header glass disabled", "self.ghostBaseHeaderGlassView?.isHidden = true" in sources["music_controller"]),
        ("music controls", "BUILD106_MUSIC_CONTROLS1" in sources["music_controls"]),
        ("custom emoji quote", "BUILD106_CUSTOM_EMOJI_QUOTE1" in sources["chat_text"]),
        ("portable V2 marker", MARKER in sources["enqueue"]),
        ("bold author", "type: .Bold" in sources["enqueue"]),
        ("portable username", '"https://t.me/\\(authorUsername)"' in sources["enqueue"]),
        ("mention fallback", "type: .TextMention(" in sources["enqueue"] and "peerId: mentionPeerId" in sources["enqueue"]),
        ("native album query", "getMessageGroup(source.id)" in sources["enqueue"]),
        ("album local grouping", "BUILD106_ALBUM_RECOVERY1" in sources["enqueue"]),
        ("sticker recovery", "BUILD106_STICKER_RECOVERY1" in sources["enqueue"]),
        ("TGS extension", 'case "application/x-tgsticker":' in sources["enqueue"]),
        ("WebM extension", 'case "video/webm":' in sources["enqueue"]),
        ("new bear ID", "id: 6046178578163303744" in sources["gift_options"]),
        ("new bear index", "stickerIndex: 11" in sources["gift_options"]),
    ]

    failed = [label for label, ok in proofs if not ok]

    if failed:
        raise RuntimeError(
            "[V11U] final proof failure: "
            + ", ".join(failed)
        )

    if sources["gift_options"].count("id: 6046178578163303744") != 1:
        raise RuntimeError("[V11U] new bear descriptor duplicated")

    if "file.isSticker {\n        return nil" in sources["enqueue"]:
        raise RuntimeError(
            "[V11U] old sticker rejection still materialized"
        )

    # ============================================================
    # H. WRITE ONLY AFTER ALL TRANSFORMS + PROOFS SUCCEED
    # ============================================================

    for name, path in PATHS.items():
        path.write_text(
            sources[name],
            encoding="utf-8",
        )

except Exception:
    sources = backups
    raise


print()
print("[V11U] BUILD106_FINAL1 applied")
print("[V11U] blur: full persistent Build105 effect owner; cache/reopen pipeline untouched")
print("[V11U] Common Groups: final displayDecorations override now respects displayBackground")
print("[V11U] Music: native moving historyFrame/historyBackground owners; stacked header glass disabled")
print("[V11U] deleted reply: bold author + username TextUrl / TextMention fallback")
print("[V11U] media: sticker recovery + native Postbox album recovery")
print("[V11U] quote: custom Premium emoji attribute preserved")
print("[V11U] gifts: 6046178578163303744 materialized with DeletedGiftsStickers index 11")
