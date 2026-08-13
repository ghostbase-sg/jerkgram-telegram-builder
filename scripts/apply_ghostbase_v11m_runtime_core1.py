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
    / "submodules/TelegramUI/Components/"
      "PeerInfo/PeerInfoScreen/Sources"
)

BG = P / "GhostBaseProfileFullscreenBackground.swift"
SCR = P / "PeerInfoScreen.swift"
SEC = P / "PeerInfoScreenItemSectionContainerNode.swift"
REP = P / "GhostBaseProfileReportPaneNode.swift"

SET = (
    ROOT
    / "submodules/SettingsUI/Sources/GhostBase/"
      "GhostBaseSettingsController.swift"
)

COMP = (
    ROOT
    / "submodules/TelegramUI/Components"
)


def component_source(
    module: str,
    filename: str,
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


PRIVATE_CALL = component_source(
    "CallScreen",
    "PrivateCallScreen.swift",
)

required = [
    BG,
    SCR,
    SEC,
    REP,
    SET,
    PRIVATE_CALL,
]

for path in required:
    if not path.is_file():
        raise RuntimeError(
            f"[V11M-A] missing: {path}"
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
            f"[V11M-A] {label}: "
            f"expected 1 found {count}"
        )

    return text.replace(
        old,
        new,
        1,
    )


bg = BG.read_text(encoding="utf-8")
scr = SCR.read_text(encoding="utf-8")
sec = SEC.read_text(encoding="utf-8")
rep = REP.read_text(encoding="utf-8")
settings = SET.read_text(encoding="utf-8")

private_call = PRIVATE_CALL.read_text(
    encoding="utf-8"
)


if "GhostBase v1.1M RUNTIMECORE1" in bg:
    print("[V11M-A] already materialized")
    raise SystemExit(0)


# ============================================================
# 1. LIVE SETTINGS + REAL OFF TEARDOWN
# ============================================================

settings = replace_once(
    settings,
    '''            next.save()
            return next
''',
    '''            let ghostBaseVisualSettingsChanged =
                current.glassEnabled != next.glassEnabled
                || current.profileAvatarBlur != next.profileAvatarBlur
                || current.profileAnimatedBackground != next.profileAnimatedBackground
                || current.profileBlurTint != next.profileBlurTint
                || current.profileBlurReduced != next.profileBlurReduced

            next.save()

            if ghostBaseVisualSettingsChanged {
                NotificationCenter.default.post(
                    name: Notification.Name(
                        "GhostBase.ProfileVisualSettingsDidChange.V11M"
                    ),
                    object: nil
                )
            }

            return next
''',
    "Settings live visual notification",
)


bg = replace_once(
    bg,
    '''final class GhostBaseProfileBackgroundView: UIView {
''',
    '''final class GhostBaseProfileBackgroundView: UIView {
    // MARK: GhostBase v1.1M RUNTIMECORE1
    private static let visualSettingsDidChange =
        Notification.Name(
            "GhostBase.ProfileVisualSettingsDidChange.V11M"
        )
''',
    "BG V11M marker",
)


bg = replace_once(
    bg,
    '''    private let context: AccountContext
    private let settings: GhostBaseProfileBlurSettings
''',
    '''    private let context: AccountContext
    private var settings: GhostBaseProfileBlurSettings
    private var visualSettingsObserver: NSObjectProtocol?
''',
    "BG live settings state",
)


bg = replace_once(
    bg,
    '''        self.addSubview(self.imageView)
        self.addSubview(self.blurView)
        self.addSubview(self.tintView)
    }
''',
    '''        self.addSubview(self.imageView)
        self.addSubview(self.blurView)
        self.addSubview(self.tintView)

        self.visualSettingsObserver =
            NotificationCenter.default.addObserver(
                forName:
                    Self.visualSettingsDidChange,
                object: nil,
                queue: .main,
                using: { [weak self] _ in
                    self?.refreshLiveSettings()
                }
            )
    }
''',
    "BG settings observer",
)


bg = replace_once(
    bg,
    '''    deinit {
        self.sourceDisposable.dispose()
    }
''',
    '''    deinit {
        if let visualSettingsObserver =
            self.visualSettingsObserver {

            NotificationCenter.default.removeObserver(
                visualSettingsObserver
            )
        }

        self.sourceDisposable.dispose()
    }

    private func tearDownForDisabledSettings() {
        self.sourceDisposable.set(nil)

        self.currentLoadKey = nil
        self.currentStateKey = nil

        self.clearAnimatedMedia()

        self.imageView.image = nil
        self.blurView.effect = nil

        self.tintView.backgroundColor =
            .clear

        self.backgroundColor = .clear

        self.usesCustomBackground =
            false

        self.isHidden = true
    }

    private func refreshLiveSettings() {
        guard let settings =
            GhostBaseProfileBlurSettings
                .loadEnabled()
        else {
            self.tearDownForDisabledSettings()
            return
        }

        self.settings = settings
        self.isHidden = false

        if !settings
            .animatedBackgroundEnabled {

            self.clearAnimatedMedia()
        }

        self.currentStateKey = nil
        self.requestUpdate?()
    }
''',
    "BG teardown/live refresh",
)


bg = replace_once(
    bg,
    '''    func update(
        peer: EnginePeer?,
        cachedData: EngineCachedPeerData?,
        presentationData: PresentationData,
        isSettings: Bool,
        avatarItem: PeerInfoAvatarListItem?
    ) {
        let source = self.resolveSource(
''',
    '''    func update(
        peer: EnginePeer?,
        cachedData: EngineCachedPeerData?,
        presentationData: PresentationData,
        isSettings: Bool,
        avatarItem: PeerInfoAvatarListItem?
    ) {
        guard let liveSettings =
            GhostBaseProfileBlurSettings
                .loadEnabled()
        else {
            self.tearDownForDisabledSettings()
            return
        }

        self.settings = liveSettings
        self.isHidden = false

        let source = self.resolveSource(
''',
    "BG update reload settings",
)


# ============================================================
# 2. VIDEO BACKDROP — SAME MEDIABOX, SEPARATE PLAYBACK ID
# ============================================================

bg = replace_once(
    bg,
    '''        let content = NativeVideoContent(
            id: .profileVideo(
                videoId,
                nil
            ),
''',
    '''        // V11M:
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
''',
    "BG independent video playback identity",
)


# ============================================================
# 3. FINAL AVATAR RESOURCE ONLY
# ============================================================

avatar_start = bg.find(
    "    private func avatarEntrySignal(\n"
)

avatar_end = bg.find(
    "    private func resourceEntrySignal(\n",
    avatar_start,
)

if (
    avatar_start < 0
    or avatar_end <= avatar_start
):
    raise RuntimeError(
        "[V11M-A] avatarEntrySignal "
        "boundaries missing"
    )


new_avatar_function = '''    private func avatarEntrySignal(
        peer: EnginePeer,
        representation: TelegramMediaImageRepresentation,
        identity: String,
        fallback: UIColor
    ) -> Signal<GhostBaseProfileBackgroundCacheEntry?, NoError>? {
        // MARK: GhostBase v1.1M FINALAVATARRESOURCE1
        //
        // Decode only the completed representation
        // resource from Telegram MediaBox.
        //
        // Do not persist intermediate UI-helper
        // thumbnail versions.
        return self.resourceEntrySignal(
            resource:
                representation.resource,
            identity:
                identity,
            fallback:
                fallback
        )
    }

'''

bg = (
    bg[:avatar_start]
    + new_avatar_function
    + bg[avatar_end:]
)


# ============================================================
# 4. ALLOW BACKDROP TO RELAYOUT ON LIVE SETTINGS CHANGE
# ============================================================

scr = replace_once(
    scr,
    '''        if let ghostBaseProfileBackgroundView = self.ghostBaseProfileBackgroundView {
            self.view.insertSubview(ghostBaseProfileBackgroundView, at: 0)
        }
        
        self.paneContainerNode.parentController = controller
''',
    '''        if let ghostBaseProfileBackgroundView = self.ghostBaseProfileBackgroundView {
            self.view.insertSubview(
                ghostBaseProfileBackgroundView,
                at: 0
            )

            ghostBaseProfileBackgroundView
                .requestUpdate = { [weak self] in

                guard
                    let self,
                    let (
                        layout,
                        navigationHeight
                    ) = self.validLayout
                else {
                    return
                }

                self.containerLayoutUpdated(
                    layout:
                        layout,
                    navigationHeight:
                        navigationHeight,
                    transition:
                        .immediate,
                    additive:
                        false
                )
            }
        }
        
        self.paneContainerNode.parentController = controller
''',
    "PeerInfo live background relayout",
)


# ============================================================
# 5. TRIANGLES — MASK THE WHOLE SECTION
# ============================================================

sec = replace_once(
    sec,
    '''    private let ghostBaseItemMaskLayer =
        CAShapeLayer()
''',
    '''    private let ghostBaseSectionMaskLayer =
        CAShapeLayer()
''',
    "Section whole-layer mask property",
)


marker_start = sec.find(
    "            // MARK: GhostBase v1.1L SECTIONMASK1\n"
)

block_end_token = '''        } else {
            self.itemContainerNode.layer.mask =
                nil
        }
'''

block_end = sec.find(
    block_end_token,
    marker_start,
)

if (
    marker_start < 0
    or block_end < 0
):
    raise RuntimeError(
        "[V11M-A] old section mask "
        "block missing"
    )

block_end += len(
    block_end_token
)


new_section_mask = '''            // MARK: GhostBase v1.1M SECTIONMASKFINAL1
            //
            // Clip the entire section rather than one
            // child container. Any native descendant
            // is physically unable to leak square
            // black corners outside the card.
            self.itemContainerNode.cornerRadius =
                0.0

            self.itemContainerNode.clipsToBounds =
                false

            self.itemContainerNode.layer.mask =
                nil

            if hasCorners {
                let maskPath =
                    UIBezierPath()

                if backgroundFrame.minY > 0.0 {
                    maskPath.append(
                        UIBezierPath(
                            rect: CGRect(
                                x: 0.0,
                                y: 0.0,
                                width: width,
                                height:
                                    backgroundFrame
                                        .minY
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
                                width:
                                    width,
                                height:
                                    contentHeight
                                    - backgroundFrame
                                        .maxY
                            )
                        )
                    )
                }

                self.ghostBaseSectionMaskLayer
                    .frame =
                    CGRect(
                        origin: .zero,
                        size: CGSize(
                            width:
                                width,
                            height:
                                contentHeight
                        )
                    )

                self.ghostBaseSectionMaskLayer
                    .path =
                    maskPath.cgPath

                self.layer.mask =
                    self.ghostBaseSectionMaskLayer
            } else {
                self.layer.mask = nil
            }
        } else {
            self.itemContainerNode.layer.mask =
                nil

            self.layer.mask =
                nil
        }
'''


sec = (
    sec[:marker_start]
    + new_section_mask
    + sec[block_end:]
)


# ============================================================
# 6. HISTORY — PRESENTATION + CLAMP
# ============================================================

rep = replace_once(
    rep,
    '''        self.scrollNode.view.alwaysBounceVertical = true
''',
    '''        self.scrollNode.view.alwaysBounceVertical = false
''',
    "History disable overscroll",
)


rep = replace_once(
    rep,
    '''    private var didStartLoading = false
    private var wasVisible = false
''',
    '''    private var didStartLoading = false
    private var wasVisible = false
    private var isApplyingScrollClamp = false
''',
    "History clamp state",
)


old_legacy = '''        if let oldHistory = defaults.string(
            forKey: oldBase + "History"
        ),
           !oldHistory.isEmpty {

            sections.append(
                "Старый журнал PROFILEINTEL2\\n"
                + oldHistory
            )
        }
'''

new_legacy = '''        // V11M:
        // Keep legacy PROFILEINTEL2 persisted
        // for compatibility, but never render
        // raw debug/key=value text to the user.
        _ = defaults.string(
            forKey:
                oldBase + "History"
        )
'''

rep = replace_once(
    rep,
    old_legacy,
    new_legacy,
    "History hide raw legacy dump",
)


load_anchor = '''    private static func loadReport(
'''


pretty_helper = r'''    // MARK: GhostBase v1.1M HISTORYPRESENTATION1
    private static func prettyGiftHistoryReport(
        _ raw: String
    ) -> String {
        let rawLines =
            raw.split(
                whereSeparator: {
                    $0.isNewline
                }
            )
            .map(
                String.init
            )

        guard !rawLines.isEmpty else {
            return "История подарков пока пуста."
        }

        var result: [String] = []

        let firstLine =
            rawLines[0]

        if let colon =
            firstLine.lastIndex(
                of: ":"
            ) {

            let count =
                firstLine[
                    firstLine.index(
                        after: colon
                    )...
                ]
                .trimmingCharacters(
                    in:
                        .whitespacesAndNewlines
                )

            result.append(
                "История подарков"
            )

            result.append(
                "Записей: \(count)"
            )
        } else {
            result.append(
                "История подарков"
            )
        }

        let labels: [String: String] = [
            "giftId":
                "ID подарка",
            "uniqueId":
                "Уникальный ID",
            "slug":
                "Slug",
            "number":
                "Номер",
            "sender":
                "Отправитель",
            "senderId":
                "ID отправителя",
            "username":
                "Username",
            "text":
                "Сообщение",
            "first":
                "Первое наблюдение",
            "lastVisible":
                "Последнее наблюдение",
            "last":
                "Последнее наблюдение"
        ]

        for rawLine
            in rawLines.dropFirst() {

            let parts =
                rawLine.components(
                    separatedBy:
                        " · "
                )

            var block: [String] = []

            for (
                index,
                originalPart
            ) in parts.enumerated() {

                let part =
                    originalPart
                        .trimmingCharacters(
                            in:
                                .whitespacesAndNewlines
                        )

                guard !part.isEmpty else {
                    continue
                }

                if index == 0 {
                    block.append(part)
                    continue
                }

                if (
                    part.lowercased()
                        == "видимый"
                    || part.lowercased()
                        == "visible"
                ) {
                    block.append(
                        "Статус: видимый"
                    )
                    continue
                }

                if part.hasPrefix(
                    "Подарок "
                ) {
                    block.insert(
                        part,
                        at: 0
                    )
                    continue
                }

                guard let equals =
                    part.firstIndex(
                        of: "="
                    )
                else {
                    block.append(part)
                    continue
                }

                let key =
                    String(
                        part[..<equals]
                    )
                    .trimmingCharacters(
                        in:
                            .whitespacesAndNewlines
                    )

                var value =
                    String(
                        part[
                            part.index(
                                after: equals
                            )...
                        ]
                    )
                    .trimmingCharacters(
                        in:
                            .whitespacesAndNewlines
                    )

                if (
                    value == "nil"
                    || value.isEmpty
                ) {
                    continue
                }

                if (
                    value.hasPrefix("'")
                    && value.hasSuffix("'")
                    && value.count >= 2
                ) {
                    value.removeFirst()
                    value.removeLast()
                }

                if (
                    key == "username"
                    && !value.hasPrefix("@")
                ) {
                    value =
                        "@" + value
                }

                let label =
                    labels[key]
                    ?? key

                block.append(
                    "\(label): \(value)"
                )
            }

            if !block.isEmpty {
                result.append("")

                result.append(
                    block.joined(
                        separator: "\n"
                    )
                )
            }
        }

        return result.joined(
            separator: "\n"
        )
    }

'''


if rep.count(load_anchor) != 1:
    raise RuntimeError(
        "[V11M-A] history loadReport "
        "anchor missing"
    )


rep = rep.replace(
    load_anchor,
    pretty_helper
    + load_anchor,
    1,
)


rep = replace_once(
    rep,
    '''        case .giftHistory:
            let report = ghostBaseGiftHistoryReport(
                accountPeerId: accountPeerId,
                peerId: peerId
            )
            return report.isEmpty ? "История подарков пока пуста." : report
''',
    '''        case .giftHistory:
            let report =
                ghostBaseGiftHistoryReport(
                    accountPeerId:
                        accountPeerId,
                    peerId:
                        peerId
                )

            return report.isEmpty
                ? "История подарков пока пуста."
                : self.prettyGiftHistoryReport(
                    report
                )
''',
    "History pretty gift report",
)


rep = replace_once(
    rep,
    '''    func scrollViewDidScroll(_ scrollView: UIScrollView) {
        self.tabBarOffsetUpdated?(.immediate)
    }
''',
    '''    func scrollViewDidScroll(
        _ scrollView: UIScrollView
    ) {
        if !self.isApplyingScrollClamp {
            let minimumY =
                -scrollView
                    .contentInset
                    .top

            let maximumY =
                max(
                    minimumY,
                    scrollView
                        .contentSize
                        .height
                    - scrollView
                        .bounds
                        .height
                    + scrollView
                        .contentInset
                        .bottom
                )

            let clampedY =
                min(
                    maximumY,
                    max(
                        minimumY,
                        scrollView
                            .contentOffset
                            .y
                    )
                )

            if abs(
                clampedY
                - scrollView
                    .contentOffset
                    .y
            ) > 0.5 {
                self.isApplyingScrollClamp =
                    true

                scrollView.setContentOffset(
                    CGPoint(
                        x: 0.0,
                        y: clampedY
                    ),
                    animated: false
                )

                self.isApplyingScrollClamp =
                    false
            }
        }

        self.tabBarOffsetUpdated?(
            .immediate
        )
    }
''',
    "History hard scroll clamp",
)


# ============================================================
# 7. CALL BUTTON MATERIAL
# ============================================================

private_call = replace_once(
    private_call,
    '''        let ghostBaseNativeAuxAlpha:
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
    '''        // MARK: GhostBase v1.1M CALLCONTROLS1
        //
        // blurredLayer is also the material
        // revealed by Telegram's native
        // call-button masks.
        //
        // Keep that layer alive. Hide only
        // the fullscreen stock/blob backdrop.
        genericAlphaTransition.setAlpha(
            layer:
                self.backgroundLayer
                    .blurredLayer,
            alpha:
                1.0
        )

        genericAlphaTransition.setAlpha(
            layer:
                self.blobBackgroundLayer,
            alpha:
                self.ghostBaseBackdropEnabled
                ? 0.0
                : 1.0
        )
''',
    "Call button material restore",
)


# ============================================================
# WRITE ONLY AFTER ALL ANCHORS PASSED
# ============================================================

for path, text in [
    (BG, bg),
    (SCR, scr),
    (SEC, sec),
    (REP, rep),
    (SET, settings),
    (PRIVATE_CALL, private_call),
]:
    path.write_text(
        text,
        encoding="utf-8",
    )


print("[V11M-A] applied")
print("  completed MediaBox avatar source only")
print("  independent animated backdrop playback identity")
print("  immediate live-settings / OFF teardown")
print("  whole-section final rounded mask")
print("  readable gift history + bounded scrolling")
print("  1:1 call button material restored")
