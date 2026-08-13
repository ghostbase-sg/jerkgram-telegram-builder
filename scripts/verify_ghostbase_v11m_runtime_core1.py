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


CALL = component_source(
    "CallScreen",
    "PrivateCallScreen.swift",
)


paths = [
    BG,
    SCR,
    SEC,
    REP,
    SET,
    CALL,
]

errors = []

for path in paths:
    if not path.is_file():
        errors.append(
            f"missing {path}"
        )


if errors:
    print("[V11M-A VERIFY] FAILED")

    for error in errors:
        print(" -", error)

    raise RuntimeError(
        "V11M-A verifier failed"
    )


bg = BG.read_text(encoding="utf-8")
scr = SCR.read_text(encoding="utf-8")
sec = SEC.read_text(encoding="utf-8")
rep = REP.read_text(encoding="utf-8")
settings = SET.read_text(encoding="utf-8")
call = CALL.read_text(encoding="utf-8")


def require(
    condition: bool,
    message: str,
):
    if not condition:
        errors.append(message)


require(
    "GhostBase v1.1M RUNTIMECORE1"
    in bg,
    "runtime core marker missing",
)

require(
    "GhostBase.ProfileVisualSettingsDidChange.V11M"
    in bg
    and
    "GhostBase.ProfileVisualSettingsDidChange.V11M"
    in settings,
    "live settings notification missing",
)

require(
    "private var settings: GhostBaseProfileBlurSettings"
    in bg,
    "background settings are still immutable",
)

require(
    "tearDownForDisabledSettings()"
    in bg
    and
    "self.clearAnimatedMedia()"
    in bg
    and
    "self.isHidden = true"
    in bg,
    "true runtime teardown missing",
)

require(
    "ghostBasePlaybackId"
    in bg
    and
    "^ 0x47424d4241434b44"
    in bg,
    "independent animated playback identity missing",
)


avatar_start = bg.find(
    "private func avatarEntrySignal("
)

avatar_end = bg.find(
    "private func resourceEntrySignal(",
    avatar_start,
)

avatar_function = (
    bg[
        avatar_start:
        avatar_end
    ]
    if (
        avatar_start >= 0
        and avatar_end > avatar_start
    )
    else ""
)


require(
    "FINALAVATARRESOURCE1"
    in avatar_function,
    "final avatar resource marker missing",
)

require(
    "peerAvatarImage("
    not in avatar_function,
    "avatar UI-helper thumbnail pipeline still used",
)

require(
    "self.resourceEntrySignal("
    in avatar_function
    and
    "resource:"
    in avatar_function
    and
    "representation.resource"
    in avatar_function,
    "completed MediaBox avatar resource path missing",
)

require(
    "ghostBaseProfileBackgroundView"
    in scr
    and
    ".requestUpdate"
    in scr
    and
    "containerLayoutUpdated("
    in scr,
    "live background relayout hook missing",
)


require(
    "GhostBase v1.1M SECTIONMASKFINAL1"
    in sec,
    "whole-section mask marker missing",
)

require(
    "self.layer.mask ="
    "\n                    self.ghostBaseSectionMaskLayer"
    in sec,
    "whole-section layer mask missing",
)

require(
    "ghostBaseItemMaskLayer"
    not in sec,
    "old child-only triangle mask survived",
)

require(
    "UIVisualEffectView("
    not in sec,
    "per-section blur returned",
)


require(
    "GhostBase v1.1M HISTORYPRESENTATION1"
    in rep,
    "history presentation formatter missing",
)

require(
    "self.scrollNode.view.alwaysBounceVertical = false"
    in rep,
    "history bounce still enabled",
)

require(
    "isApplyingScrollClamp"
    in rep
    and
    "let clampedY"
    in rep,
    "history offset clamp missing",
)

require(
    "prettyGiftHistoryReport"
    in rep
    and
    "self.prettyGiftHistoryReport"
    in rep,
    "gift history is still raw",
)

require(
    '"Старый журнал PROFILEINTEL2\\n"'
    not in rep,
    "raw PROFILEINTEL2 dump still rendered",
)

require(
    "static let maximumEvents = 200"
    in rep,
    "history bound lost",
)

require(
    "afterPendingWrites"
    in rep,
    "history pending-write synchronization lost",
)


require(
    "GhostBase v1.1M CALLCONTROLS1"
    in call,
    "call-controls fix missing",
)

require(
    "self.backgroundLayer"
    ".blurredLayer"
    in call
    and
    "alpha:"
    in call,
    "call blurred button material not restored",
)

require(
    "ghostBaseNativeAuxAlpha"
    not in call,
    "old call material alpha-kill survived",
)


joined = "\n".join([
    bg,
    scr,
    sec,
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
        (
            "forbidden legacy profile "
            f"returned: {forbidden}"
        ),
    )


if errors:
    print("[V11M-A VERIFY] FAILED")

    for error in errors:
        print(" -", error)

    raise RuntimeError(
        "V11M-A verifier failed"
    )


print("[V11M-A VERIFY] OK")
print("  stable completed avatar resource")
print("  independent animated backdrop playback identity")
print("  immediate OFF / live-settings teardown")
print("  whole-section final mask")
print("  readable bounded history + hard scroll clamp")
print("  1:1 call button material restored")
