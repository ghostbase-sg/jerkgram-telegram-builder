#!/usr/bin/env python3

import os
from pathlib import Path

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

P = (
    ROOT
    / "submodules/TelegramUI/Components/"
      "PeerInfo/PeerInfoScreen/Sources"
)

BG = P / "GhostBaseProfileFullscreenBackground.swift"
HDR = P / "PeerInfoHeaderNode.swift"
SEC = P / "PeerInfoScreenItemSectionContainerNode.swift"
PANE = P / "PeerInfoPaneContainerNode.swift"
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
    (
        path
        for path in GLASS_CANDIDATES
        if path.is_file()
    ),
    None
)

CALL = (
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

paths = [
    BG,
    HDR,
    SEC,
    PANE,
    REP,
    SETTINGS,
    CALL,
    PRIVATE_CALL,
    COVER,
    GIFT,
]

if GLASS is not None:
    paths.append(GLASS)

errors = []

for path in paths:
    if not path.is_file():
        errors.append(
            f"missing {path}"
        )

if GLASS is None:
    errors.append(
        "GhostBaseGlass.swift missing"
    )

if errors:
    print("[V11L VERIFY] FAILED")

    for error in errors:
        print(" -", error)

    raise RuntimeError(
        "V11L verifier failed"
    )

bg = BG.read_text(encoding="utf-8")
hdr = HDR.read_text(encoding="utf-8")
sec = SEC.read_text(encoding="utf-8")
pane = PANE.read_text(encoding="utf-8")
rep = REP.read_text(encoding="utf-8")
settings = SETTINGS.read_text(encoding="utf-8")
glass = GLASS.read_text(encoding="utf-8")
cover = COVER.read_text(encoding="utf-8")
gift = GIFT.read_text(encoding="utf-8")
call = CALL.read_text(encoding="utf-8")
private_call = PRIVATE_CALL.read_text(
    encoding="utf-8"
)


def require(
    condition: bool,
    message: str
):
    if not condition:
        errors.append(message)


require(
    "GhostBase v1.1L PROFILESTATE1"
    in bg,
    "profile state marker missing"
)

require(
    "GhostBase.ProfileBlur.Animated"
    in glass
    and
    "animatedBackgroundEnabled"
    in glass,
    "animated runtime setting missing"
)

require(
    "Анимированный фон"
    in settings
    and
    "profileAnimatedBackground"
    in settings,
    "animated Settings toggle missing"
)

require(
    "case GhostBaseKey.profileAnimatedBackground:"
    in settings,
    "animated Settings toggle action missing"
)

require(
    "GhostBaseAnimatedMediaSource"
    in bg
    and
    "UniversalVideoNode"
    in bg
    and
    "loopVideo: true"
    in bg,
    "animated profile renderer missing"
)

require(
    '''synchronousLoad:
                    true'''
    in bg,
    "avatar MediaBox synchronous cache hit missing"
)

require(
    "let immediateTint" in bg
    and "Self.persistentTint(" in bg
    and "identity: loadKey" in bg
    and "?? fallback" in bg,
    "persistent per-source immediate tone fallback missing"
)

require(
    "animatedSource"
    in bg
    and
    "animatedIdentity:"
    in bg,
    "animated identity missing from profile state"
)

wallpaper_start = bg.find(
    "private func wallpaperEntrySignal("
)

wallpaper_end = bg.find(
    "private func avatarEntrySignal(",
    wallpaper_start
)

wallpaper_function = (
    bg[
        wallpaper_start:
        wallpaper_end
    ]
    if
    wallpaper_start >= 0
    and
    wallpaper_end > wallpaper_start
    else
    ""
)

require(
    wallpaper_function.count(
        "case let .file(file):"
    ) == 1,
    "wallpaper .file case duplicated/missing"
)

require(
    "setGhostBaseBackgroundFillAlpha"
    in cover,
    "Premium fill-only control missing"
)

require(
    "backgroundCoverView.alpha = 1.0"
    in hdr
    and
    "setGhostBaseBackgroundFillAlpha"
    in hdr,
    "header still fades entire Premium cover"
)

require(
    '''? 0.08
                    : 0.16'''
    not in hdr,
    "old whole-cover 0.08/0.16 fade survived"
)

require(
    "GhostBase v1.1L UNIFIEDMATERIAL1"
    in pane
    and
    "self.backgroundColor = .clear"
    in pane,
    "pane full-width tone band not removed"
)

require(
    "GhostBase v1.1L SECTIONMASK1"
    in sec
    and
    "ghostBaseItemMaskLayer"
    in sec,
    "precise section mask missing"
)

require(
    '''self.itemContainerNode.cornerRadius =
                radius'''
    not in sec,
    "old whole-container corner radius survived"
)

require(
    "UIVisualEffectView("
    not in sec,
    "per-section blur returned"
)

require(
    "GhostBase v1.1L HISTORYMULTILINE1"
    in rep
    and
    "maximumNumberOfLines = 0"
    in rep,
    "history multiline fix missing"
)

require(
    "static let maximumEvents = 200"
    in rep,
    "history bound lost"
)

require(
    "afterPendingWrites"
    in rep,
    "V11K history synchronization lost"
)

require(
    "GhostBase v1.1L HIDEPHONEHEADER1"
    in hdr
    and
    "GhostBase.Appearance.HideOwnPhone"
    in hdr,
    "third own-phone hiding location missing"
)

require(
    "GhostBase v1.1L GIFTGLASS1"
    in gift,
    "lighter Gifts glass missing"
)

require(
    "switch component.style"
    in gift
    and
    "case .glass:"
    in gift
    and
    "case .legacy:"
    in gift,
    "Gift style switch not preserved safely"
)

require(
    "component.style == .glass"
    not in gift,
    "Gift Style Equatable assumption survived"
)

require(
    "GhostBase v1.1L CALLBACKDROP1"
    in call
    and
    "GhostBaseCallBackdropView"
    in call,
    "1:1 call backdrop missing"
)

require(
    "ghostBaseBackdropEnabled"
    in private_call,
    "PrivateCallScreen backdrop switch missing"
)

require(
    "self.ghostBaseBackdropView"
    in call
    and
    "updateGhostBaseBackdrop("
    in call,
    "call backdrop not updated from peer/avatar"
)

joined = "\n".join([
    bg,
    hdr,
    sec,
    pane,
    rep,
])

for forbidden in (
    "PROFILEHUB2",
    "PROFILEHUB4",
    "GhostBaseProfileHubItem",
    "История и сведения",
):
    require(
        forbidden not in joined,
        f"forbidden legacy profile returned: {forbidden}"
    )

if errors:
    print("[V11L VERIFY] FAILED")

    for error in errors:
        print(" -", error)

    raise RuntimeError(
        "V11L verifier failed"
    )

print("[V11L VERIFY] OK")
print("  avatar reopen uses source-keyed persistent fallback + synchronous cache hit")
print("  animated video-avatar profile backdrop enabled and looped")
print("  Premium emoji-pattern remains full opacity")
print("  pane tone bands removed + precise section mask installed")
print("  history multiline output enabled and bounded")
print("  own phone Settings-header hiding restored")
print("  Gifts use lighter glass surface without per-item blur")
print("  1:1 calls use static avatar/Premium GhostBase backdrop")
print("  bear is intentionally outside V11L verification")
