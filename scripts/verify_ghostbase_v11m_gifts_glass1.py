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
        candidate = (
            directory
            / "Sources"
            / filename
        )

        if candidate.is_file():
            return candidate

    return direct


GIFT = component_source(
    "GiftItemComponent",
    "GiftItemComponent.swift"
)

VIEW = component_source(
    "GiftViewScreen",
    "GiftViewScreen.swift"
)

PAGER = component_source(
    "GiftViewScreen",
    "GiftPagerComponent.swift"
)

LIST = (
    ROOT
    / "submodules/TelegramUI/Components/"
      "PeerInfo/PeerInfoVisualMediaPaneNode/"
      "Sources/GiftsListView.swift"
)

errors = []

for path in (
    GIFT,
    VIEW,
    PAGER,
    LIST,
):
    if not path.is_file():
        errors.append(
            f"missing {path}"
        )

if errors:
    print("[V11M-B1 VERIFY] FAILED")

    for error in errors:
        print(" -", error)

    raise RuntimeError(
        "V11M-B1 verifier failed"
    )

gift = GIFT.read_text(encoding="utf-8")
view = VIEW.read_text(encoding="utf-8")
pager = PAGER.read_text(encoding="utf-8")
gifts = LIST.read_text(encoding="utf-8")


def require(
    condition: bool,
    message: str
):
    if not condition:
        errors.append(message)


require(
    "case ghostBase"
    in gift,
    "dedicated GiftItem GhostBase style missing"
)

require(
    "GhostBase v1.1M GIFTCARDMASK1"
    in gift,
    "GiftItem shared-mask marker missing"
)

require(
    "UIColor.clear.cgColor"
    in gift,
    "GhostBase GiftItem background is not clear"
)

require(
    "case .glass, .legacy:"
    in gift
    and
    "itemBlocksBackgroundColor"
    in gift,
    "Official GiftItem material not restored"
)

require(
    "GhostBase v1.1M GIFTSGLASS1"
    in gifts,
    "shared Gifts glass marker missing"
)

require(
    "NavigationBackgroundNode"
    in gifts
    and
    "ghostBaseGlassMaskLayer"
    in gifts,
    "shared NavigationBackgroundNode/mask missing"
)

require(
    "style:"
    in gifts
    and
    "? .ghostBase"
    in gifts,
    "profile Gifts not switched to GhostBase style"
)

ghostBaseMarker = gift.find(
    "GhostBase v1.1M GIFTCARDMASK1"
)

ghostBaseBranchEnd = gift.find(
    "case .glass, .legacy:",
    ghostBaseMarker
)

ghostBaseBranch = (
    gift[
        ghostBaseMarker:
        ghostBaseBranchEnd
    ]
    if (
        ghostBaseMarker >= 0
        and ghostBaseBranchEnd
            > ghostBaseMarker
    )
    else ""
)

require(
    "UIVisualEffectView("
    not in ghostBaseBranch,
    "per-gift blur introduced inside GhostBase card branch"
)

require(
    gifts.count(
        "NavigationBackgroundNode("
    ) >= 1
    and
    "ghostBaseGlassNode"
    in gifts,
    "shared Gifts blur owner missing"
)

require(
    "GhostBase v1.1M PROFILEGIFTGLASS1"
    in view,
    "opened profile gift glass marker missing"
)

require(
    "ghostBaseSheetColor"
    in view,
    "opened gift translucent sheet missing"
)

require(
    "ghostBaseProfileGift"
    in pager
    and
    "? 0.12"
    in pager,
    "opened gift dim reduction missing"
)

if errors:
    print("[V11M-B1 VERIFY] FAILED")

    for error in errors:
        print(" -", error)

    raise RuntimeError(
        "V11M-B1 verifier failed"
    )

print("[V11M-B1 VERIFY] OK")
print("  one shared Gifts blur node")
print("  rounded gift masks without per-item blur")
print("  Official material preserved outside GhostBase")
print("  opened profile gift uses lighter glass")
