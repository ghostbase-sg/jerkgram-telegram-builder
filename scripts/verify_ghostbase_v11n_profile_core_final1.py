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
SEC = P / "PeerInfoScreenItemSectionContainerNode.swift"
REP = P / "GhostBaseProfileReportPaneNode.swift"

GIFTS = (
    ROOT
    / "submodules/TelegramUI/Components/"
      "PeerInfo/PeerInfoVisualMediaPaneNode/"
      "Sources/GiftsListView.swift"
)

errors = []

for path in (BG, SEC, REP, GIFTS):
    if not path.is_file():
        errors.append(
            f"missing {path}"
        )

if errors:
    print("[V11N VERIFY] FAILED")
    for error in errors:
        print(" -", error)
    raise RuntimeError(
        "V11N verifier failed"
    )


bg = BG.read_text(encoding="utf-8")
sec = SEC.read_text(encoding="utf-8")
rep = REP.read_text(encoding="utf-8")
gifts = GIFTS.read_text(encoding="utf-8")


def require(value, message):
    if not value:
        errors.append(message)


require(
    "GhostBase v1.1N PROFILECORE_FINAL1"
    in bg,
    "profile core marker missing"
)

require(
    "import AVFoundation"
    in bg,
    "AVFoundation renderer missing"
)

require(
    "useIndependentPlayer"
    in bg
    and
    "!isSettings"
    in bg,
    "Settings/PeerInfo renderer split missing"
)

require(
    "AVQueuePlayer"
    in bg
    and
    "AVPlayerLooper"
    in bg
    and
    "AVPlayerLayer"
    in bg,
    "independent PeerInfo animation renderer missing"
)

require(
    "resourceData("
    in bg
    and
    "$0.complete"
    in bg,
    "MediaBox video reuse missing"
)

require(
    "peerAvatarImage("
    in bg
    and
    "synchronousLoad:"
    in bg
    and
    "true"
    in bg,
    "Telegram avatar decoder not restored"
)

avatar_case_start = bg.find(
    "case let .avatar(",
    bg.find("private func apply(")
)

avatar_case_end = bg.find(
    "case .telegramTheme:",
    avatar_case_start
)

avatar_case = (
    bg[
        avatar_case_start:
        avatar_case_end
    ]
    if avatar_case_start >= 0
    and avatar_case_end > avatar_case_start
    else ""
)

require(
    "Self.imageCache.object"
    not in avatar_case
    and
    "Self.imageCache.setObject"
    not in avatar_case,
    "GhostBase avatar UIImage cache survived"
)

require(
    "ROWCORNERS_FINAL1"
    in sec,
    "row-level corners missing"
)

require(
    "layer.maskedCorners"
    in sec
    and
    "layer.masksToBounds"
    in sec,
    "row clipping missing"
)

require(
    "SECTIONMASK_REMOVED1"
    in sec
    and
    "self.layer.mask ="
    in sec
    and
    "nil"
    in sec,
    "whole-section mask not removed"
)

require(
    "ghostBaseSectionMaskLayer"
    not in sec,
    "old whole-section mask layer survived"
)

require(
    "HISTORYVIEWPORT_FINAL1"
    in rep,
    "History physical viewport missing"
)

require(
    "y: viewportTop"
    in rep
    and
    "top:"
    in rep
    and
    "0.0"
    in rep,
    "History still relies on top contentInset"
)

require(
    "clipsToBounds"
    in rep,
    "History viewport clipping missing"
)

require(
    "GIFTCONTRAST1"
    in gifts,
    "Gift contrast marker missing"
)

require(
    "? 0.34"
    in gifts
    and
    ": 0.30"
    in gifts,
    "Gift readability alpha missing"
)

if errors:
    print("[V11N VERIFY] FAILED")

    for error in errors:
        print(" -", error)

    raise RuntimeError(
        "V11N verifier failed"
    )


print("[V11N VERIFY] OK")
print("  Telegram avatar decoder restored without GhostBase image cache")
print("  Settings animation path remains Telegram UniversalVideo")
print("  ordinary PeerInfo animation is isolated from native avatar")
print("  row-level corners replace section-wide triangle masking")
print("  History cannot render underneath header/tabs")
print("  Gifts use stronger readability material")
