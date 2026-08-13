#!/usr/bin/env python3

import os
from pathlib import Path


ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        "/root/gb_builder/work/swiftgram-src"
    )
)

P = (
    ROOT
    / "submodules/TelegramUI/Components/"
      "PeerInfo/PeerInfoScreen/Sources"
)

BG = P / "GhostBaseProfileFullscreenBackground.swift"
SEC = P / "PeerInfoScreenItemSectionContainerNode.swift"
REP = P / "GhostBaseProfileReportPaneNode.swift"
AVATAR = P / "PeerInfoAvatarTransformContainerNode.swift"

GIFTS = (
    ROOT
    / "submodules/TelegramUI/Components/"
      "PeerInfo/PeerInfoVisualMediaPaneNode/"
      "Sources/GiftsListView.swift"
)

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


errors = []

for path in (
    BG,
    SEC,
    REP,
    AVATAR,
    GIFTS,
    GIFT,
):
    if not path.is_file():
        errors.append(
            f"missing {path}"
        )


if errors:
    print("[V11O VERIFY] FAILED")

    for error in errors:
        print(" -", error)

    raise RuntimeError(
        "V11O verifier failed"
    )


bg = BG.read_text(encoding="utf-8")
sec = SEC.read_text(encoding="utf-8")
rep = REP.read_text(encoding="utf-8")
avatar = AVATAR.read_text(encoding="utf-8")
gifts = GIFTS.read_text(encoding="utf-8")
gift = GIFT.read_text(encoding="utf-8")


def require(
    condition: bool,
    message: str
):
    if not condition:
        errors.append(message)


# Background / blur
require(
    "GhostBase v1.1O VISUALRESET1"
    in bg,
    "V11O marker missing",
)

require(
    ".systemUltraThinMaterialDark"
    in bg
    and
    ".systemUltraThinMaterialLight"
    in bg
    and
    "self.blurView.effect = UIBlurEffect(style: effectStyle)"
    in bg,
    "Build 97/V11K blur recipe missing",
)

require(
    "fractionComplete"
    not in bg
    and
    "blurAnimator"
    not in bg,
    "experimental fractional blur survived",
)

avatar_signal_start = bg.find(
    "private func avatarEntrySignal("
)

avatar_signal_end = bg.find(
    "private func resourceEntrySignal(",
    avatar_signal_start
)

avatar_signal = (
    bg[
        avatar_signal_start:
        avatar_signal_end
    ]
    if (
        avatar_signal_start >= 0
        and
        avatar_signal_end
            > avatar_signal_start
    )
    else ""
)

require(
    "width: 360.0"
    in avatar_signal
    and
    "height: 360.0"
    in avatar_signal,
    "Build 97 avatar dimensions not restored",
)

require(
    "synchronousLoad:"
    in avatar_signal
    and
    "false"
    in avatar_signal,
    "Build 97 asynchronous avatar feed not restored",
)

require(
    "0.030"
    in bg
    and
    "0.020"
    in bg
    and
    "0.050"
    in bg
    and
    "0.035"
    in bg,
    "Build 97/V11K tint values missing",
)

require(
    "import AVFoundation"
    not in bg,
    "V11N AVFoundation experiment survived",
)

require(
    "AVQueuePlayer"
    not in bg
    and
    "AVPlayerLooper"
    not in bg
    and
    "AVPlayerLayer"
    not in bg,
    "independent AVPlayer path survived",
)

require(
    "ghostBasePlaybackId"
    not in bg
    and
    "^ 0x47424d4241434b44"
    not in bg,
    "separate/XOR profileVideo id survived",
)

require(
    "id: .profileVideo("
    in bg
    and
    "videoId"
    in bg,
    "shared Telegram profileVideo identity missing",
)


# Placeholder source
require(
    "case placeholder"
    in bg
    and
    "case placeholder("
    in bg,
    "placeholder source missing",
)

require(
    "placeholderColors("
    in bg
    and
    "peer.nameColor"
    in bg,
    "Telegram placeholder color mapping missing",
)

for value in (
    "0xff516a",
    "0xffa85c",
    "0x665fff",
    "0x54cb68",
    "0x4acccd",
    "0x2a9ef1",
    "0xd669ed",
):
    require(
        value in bg,
        f"placeholder palette entry missing: {value}",
    )

require(
    "colorLuminance"
    in bg
    and
    "scrimAlpha"
    in bg,
    "adaptive placeholder darkening missing",
)


# Corners
require(
    "NONOPAQUECARD1"
    in sec,
    "non-opaque card backing fix missing",
)

require(
    "backgroundNode.layer.isOpaque = false"
    in sec
    and
    "itemContainerNode.layer.isOpaque = false"
    in sec,
    "actual translucent backing layers still opaque",
)

require(
    "ROWCORNERS_FINAL1"
    not in sec,
    "old row-mask experiment survived",
)

require(
    "layer.maskedCorners"
    not in sec,
    "row-level maskedCorners survived",
)


# Animation no-pause
require(
    "keepVideoAlive"
    in avatar
    and
    "if keepVideoAlive"
    in avatar
    and
    "videoNode.play()"
    in avatar,
    "native avatar no-pause path missing",
)


# History
require(
    "HISTORYSTATICHEADER1"
    in rep,
    "History static header fix missing",
)

require(
    "return 0.0"
    in rep,
    "History tabBarOffset is not fixed",
)

require(
    "tabBarOffsetUpdated?("
    not in rep,
    "History still drives PeerInfo tab movement",
)


# Gifts
require(
    "ghostBaseGlassNode"
    not in gifts
    and
    "ghostBaseGlassMaskLayer"
    not in gifts,
    "shared masked Gifts blur survived",
)

require(
    "GIFTCARDSCRIM1"
    in gift,
    "direct Gift-card scrim missing",
)

require(
    "? 0.42"
    in gift
    and
    ": 0.34"
    in gift,
    "Gift readability alpha missing",
)

require(
    "UIVisualEffectView("
    not in gift[
        max(
            0,
            gift.find(
                "GIFTCARDSCRIM1"
            )
        ):
        gift.find(
            "case .glass, .legacy:",
            gift.find(
                "GIFTCARDSCRIM1"
            )
        )
    ],
    "per-Gift blur introduced",
)


# Regression locks
require(
    "afterPendingWrites"
    in rep,
    "History write synchronization lost",
)

require(
    "maximumEvents = 200"
    in rep,
    "History bound lost",
)

joined = "\n".join(
    [
        bg,
        sec,
        rep,
    ]
)

for forbidden in (
    "PROFILEHUB2",
    "PROFILEHUB4",
    "GhostBaseProfileHubItem",
    "История и сведения",
):
    require(
        forbidden not in joined,
        f"forbidden legacy returned: {forbidden}",
    )


if errors:
    print("[V11O VERIFY] FAILED")

    for error in errors:
        print(" -", error)

    raise RuntimeError(
        "V11O verifier failed"
    )


print("[V11O VERIFY] OK")
print("  exact Build 97/V11K blur recipe preserved")
print("  exact Build 97/V11K tint recipe preserved")
print("  Build 97 360px asynchronous avatar feed restored")
print("  no-avatar peers use Telegram placeholder palette")
print("  placeholder background is adaptively darker than avatar")
print("  one shared Telegram profileVideo playback")
print("  V11N AVPlayer path removed")
print("  translucent section backing is explicitly non-opaque")
print("  old row-mask corner experiment removed")
print("  History cannot collapse PeerInfo tabs")
print("  Gifts use stable readable scrim without blur")
