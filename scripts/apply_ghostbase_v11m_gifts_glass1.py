#!/usr/bin/env python3

import os
from pathlib import Path

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

COMP = (
    ROOT
    / "submodules/TelegramUI/Components"
)


def component_source(
    module: str,
    filename: str
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


GIFT_ITEM = component_source(
    "GiftItemComponent",
    "GiftItemComponent.swift"
)

GIFT_VIEW = component_source(
    "GiftViewScreen",
    "GiftViewScreen.swift"
)

GIFT_PAGER = component_source(
    "GiftViewScreen",
    "GiftPagerComponent.swift"
)

GIFTS_LIST = (
    ROOT
    / "submodules/TelegramUI/Components/"
      "PeerInfo/PeerInfoVisualMediaPaneNode/"
      "Sources/GiftsListView.swift"
)

required = [
    GIFT_ITEM,
    GIFT_VIEW,
    GIFT_PAGER,
    GIFTS_LIST,
]

for path in required:
    if not path.is_file():
        raise RuntimeError(
            f"[V11M-B1] missing: {path}"
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
            f"[V11M-B1] {label}: "
            f"expected 1 found {count}"
        )

    return text.replace(
        old,
        new,
        1
    )


gift = GIFT_ITEM.read_text(
    encoding="utf-8"
)

gifts = GIFTS_LIST.read_text(
    encoding="utf-8"
)

view = GIFT_VIEW.read_text(
    encoding="utf-8"
)

pager = GIFT_PAGER.read_text(
    encoding="utf-8"
)


if "GhostBase v1.1M GIFTSGLASS1" in gifts:
    print("[V11M-B1] already materialized")
    raise SystemExit(0)


# ============================================================
# 1. Dedicated GiftItem style
#
# Do NOT hijack Telegram's ordinary .glass style.
# OFF / non-profile Gifts remain Official.
# ============================================================

gift = replace_once(
    gift,
    '''    public enum Style {
        case glass
        case legacy
    }
''',
    '''    public enum Style {
        case glass
        case ghostBase
        case legacy
    }
''',
    "Gift style enum"
)


# All geometry/selection behavior of GhostBase
# matches Telegram glass.
gift = gift.replace(
    "case .glass:",
    "case .glass, .ghostBase:"
)


old_background = '''                    switch component.style {
                    case .glass, .ghostBase:
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
'''

new_background = '''                    switch component.style {
                    case .ghostBase:
                        // MARK: GhostBase v1.1M GIFTCARDMASK1
                        //
                        // One shared NavigationBackgroundNode
                        // in GiftsListView owns the real blur.
                        self.backgroundLayer.backgroundColor =
                            UIColor.clear.cgColor

                    case .glass, .legacy:
                        // Preserve Official Telegram outside
                        // GhostBase profile Gifts.
                        self.backgroundLayer.backgroundColor =
                            component
                                .theme
                                .list
                                .itemBlocksBackgroundColor
                                .cgColor
                    }
'''

gift = replace_once(
    gift,
    old_background,
    new_background,
    "Gift shared-glass background"
)


# ============================================================
# 2. ONE shared blur for all visible gift cards
# ============================================================

gifts = replace_once(
    gifts,
    '''    private var starsItems: [AnyHashable: (StarGiftReference?, ComponentView<Empty>)] = [:]
''',
    '''    private var starsItems: [AnyHashable: (StarGiftReference?, ComponentView<Empty>)] = [:]

    // MARK: GhostBase v1.1M GIFTSGLASS1
    //
    // One reusable material node for the whole grid.
    // Visible GiftItem frames form its mask.
    private var ghostBaseGlassNode:
        NavigationBackgroundNode?

    private let ghostBaseGlassMaskLayer =
        CAShapeLayer()
''',
    "Gifts shared-glass properties"
)


load_more_anchor = '''    func loadMore() {
        self.profileGifts.loadMore()
    }
'''

glass_method = '''    private func updateGhostBaseGlass(
        presentationData: PresentationData
    ) {
        guard
            GhostBaseProfileBlurSettings
                .loadEnabled() != nil
        else {
            if let ghostBaseGlassNode =
                self.ghostBaseGlassNode {

                self.ghostBaseGlassNode =
                    nil

                ghostBaseGlassNode
                    .view
                    .layer
                    .mask =
                    nil

                ghostBaseGlassNode
                    .view
                    .removeFromSuperview()
            }

            return
        }

        let ghostBaseGlassNode:
            NavigationBackgroundNode

        if let current =
            self.ghostBaseGlassNode {

            ghostBaseGlassNode =
                current
        } else {
            ghostBaseGlassNode =
                NavigationBackgroundNode(
                    color: .clear,
                    enableBlur: true,
                    enableSaturation: false
                )

            ghostBaseGlassNode
                .isUserInteractionEnabled =
                false

            self.ghostBaseGlassNode =
                ghostBaseGlassNode

            self.insertSubview(
                ghostBaseGlassNode.view,
                at: 0
            )
        }

        ghostBaseGlassNode.frame =
            self.bounds

        ghostBaseGlassNode.update(
            size:
                self.bounds.size,
            transition:
                .immediate
        )

        let isDark =
            presentationData
                .theme
                .overallDarkAppearance

        // Same density as GhostBase profile
        // action-button material.
        ghostBaseGlassNode.updateColor(
            color: UIColor(
                white:
                    isDark
                    ? 0.0
                    : 1.0,
                alpha:
                    isDark
                    ? 0.16
                    : 0.20
            ),
            enableBlur: true,
            transition: .immediate
        )

        let maskPath =
            UIBezierPath()

        for (_, item)
            in self.starsItems {

            guard
                let view =
                    item.1.view,
                view.superview === self,
                !view.isHidden,
                view.alpha > 0.01
            else {
                continue
            }

            maskPath.append(
                UIBezierPath(
                    roundedRect:
                        view.frame,
                    cornerRadius:
                        16.0
                )
            )
        }

        self.ghostBaseGlassMaskLayer
            .frame =
            self.bounds

        self.ghostBaseGlassMaskLayer
            .path =
            maskPath.cgPath

        ghostBaseGlassNode
            .view
            .layer
            .mask =
            self.ghostBaseGlassMaskLayer
    }

'''

if gifts.count(load_more_anchor) != 1:
    raise RuntimeError(
        "[V11M-B1] Gifts loadMore anchor missing"
    )

gifts = gifts.replace(
    load_more_anchor,
    load_more_anchor
    + "\n"
    + glass_method,
    1
)


gifts = replace_once(
    gifts,
    '''        guard let starsProducts = self.starsProducts, let params = self.currentParams else {
            return 0.0
        }
''',
    '''        guard let starsProducts = self.starsProducts, let params = self.currentParams else {
            return 0.0
        }

        let ghostBaseGlassEnabled =
            GhostBaseProfileBlurSettings
                .loadEnabled() != nil
''',
    "Gifts glass enabled state"
)


gifts = replace_once(
    gifts,
    '''                        GiftItemComponent(
                            context: self.context,
                            style: .glass,
''',
    '''                        GiftItemComponent(
                            context: self.context,
                            style:
                                ghostBaseGlassEnabled
                                ? .ghostBase
                                : .glass,
''',
    "Gifts GhostBase style"
)


gifts = replace_once(
    gifts,
    '''        return contentHeight
    }
        
    func update(size: CGSize,''',
    '''        self.updateGhostBaseGlass(
            presentationData:
                params.presentationData
        )

        return contentHeight
    }
        
    func update(size: CGSize,''',
    "Gifts glass mask update"
)


# ============================================================
# 3. OPENED PROFILE GIFT
#
# GiftViewScreen already uses SheetComponent style .glass.
# The black appearance came from:
# - GiftPager dim = black 0.4
# - opaque action-sheet background.
#
# Only .profileGift + GhostBase gets lighter scene-aware glass.
# ============================================================

pager = replace_once(
    pager,
    '''            transition.setFrame(view: self.dimView, frame: CGRect(origin: CGPoint(), size: availableSize), completion: nil)
''',
    '''            let ghostBaseProfileGift =
                GhostBaseProfileBlurSettings
                    .loadEnabled() != nil
                && component.items.contains(
                    where: { item in
                        if case .profileGift =
                            item.subject {

                            return true
                        } else {
                            return false
                        }
                    }
                )

            self.dimView.backgroundColor =
                UIColor(
                    white: 0.0,
                    alpha:
                        ghostBaseProfileGift
                        ? 0.12
                        : 0.4
                )

            transition.setFrame(view: self.dimView, frame: CGRect(origin: CGPoint(), size: availableSize), completion: nil)
''',
    "Opened gift dim"
)


view = replace_once(
    view,
    '''            let sheet = sheet.update(
                component: SheetComponent<EnvironmentType>(
''',
    '''            // MARK: GhostBase v1.1M PROFILEGIFTGLASS1
            let ghostBaseProfileGift:
                Bool

            if
                case .profileGift =
                    context.component.subject,
                GhostBaseProfileBlurSettings
                    .loadEnabled() != nil
            {
                ghostBaseProfileGift =
                    true
            } else {
                ghostBaseProfileGift =
                    false
            }

            let ghostBaseSheetColor:
                UIColor

            if ghostBaseProfileGift {
                ghostBaseSheetColor =
                    UIColor(
                        white:
                            environment
                                .theme
                                .overallDarkAppearance
                            ? 0.0
                            : 1.0,
                        alpha:
                            environment
                                .theme
                                .overallDarkAppearance
                            ? 0.16
                            : 0.20
                    )
            } else {
                ghostBaseSheetColor =
                    environment
                        .theme
                        .actionSheet
                        .opaqueItemBackgroundColor
            }

            let sheet = sheet.update(
                component: SheetComponent<EnvironmentType>(
''',
    "Opened gift sheet context"
)


view = replace_once(
    view,
    '''                    backgroundColor: .color(environment.theme.actionSheet.opaqueItemBackgroundColor),
''',
    '''                    backgroundColor:
                        .color(
                            ghostBaseSheetColor
                        ),
''',
    "Opened gift sheet background"
)


# ============================================================
# WRITE ONLY AFTER ALL ANCHORS PASSED
# ============================================================

for path, text in [
    (GIFT_ITEM, gift),
    (GIFTS_LIST, gifts),
    (GIFT_VIEW, view),
    (GIFT_PAGER, pager),
]:
    path.write_text(
        text,
        encoding="utf-8"
    )


print("[V11M-B1] applied")
print("  one shared NavigationBackgroundNode for Gifts")
print("  visible gift cards are rounded blur masks")
print("  Official .glass style restored outside GhostBase")
print("  opened profile gift uses lighter glass sheet")
print("  opened profile gift black dim reduced")
