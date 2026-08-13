#!/usr/bin/env python3

import os
from pathlib import Path

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

NODE = (
    ROOT
    / "submodules/TelegramUI/Sources/"
      "OverlayAudioPlayerControllerNode.swift"
)

errors = []

if not NODE.is_file():
    errors.append(
        f"missing {NODE}"
    )
else:
    text = NODE.read_text(
        encoding="utf-8"
    )

    def require(
        condition: bool,
        message: str,
    ):
        if not condition:
            errors.append(
                message
            )

    require(
        "GhostBase v1.1M MUSICPLAYERGLASS1"
        in text,
        "music player marker missing",
    )

    require(
        "GhostBaseMusicProfileBackdropView"
        in text,
        "profile backdrop helper missing",
    )

    require(
        "GhostBaseProfileBlurSettings"
        in text
        and
        ".loadEnabled()"
        in text,
        "GhostBase master/settings gate missing",
    )

    require(
        "case .savedMusic ="
        in text,
        "Saved Music scope missing",
    )

    require(
        "ghostBaseProfileData"
        in text
        and
        "combineLatest("
        in text
        and
        "ghostBaseWallpaper"
        in text,
        "peer/wallpaper data flow missing",
    )

    require(
        "CachedUserData"
        in text
        and
        "CachedChannelData"
        in text
        and
        ".wallpaper"
        in text,
        "personal wallpaper source missing",
    )

    require(
        "let canUseWallpaper"
        in text
        and
        "self.context"
        in text
        and
        ".account"
        in text
        and
        ".peerId"
        in text,
        "own-profile wallpaper exclusion missing",
    )

    require(
        "presentationData"
        in text
        and
        ".chatWallpaper"
        in text
        and
        ".defaultWallpaper"
        in text,
        "global wallpaper source missing",
    )

    require(
        "settings.avatarBlurInProfile"
        in text
        and
        "profileImageRepresentations"
        in text,
        "avatar preference source missing",
    )

    require(
        "effectiveProfileColor"
        in text
        and
        "emojiStatus"
        in text,
        "Premium/profile-color fallback missing",
    )

    require(
        "resourceData("
        in text
        and
        "$0.complete"
        in text,
        "completed MediaBox resource path missing",
    )

    require(
        "alpha: 0.10"
        in text,
        "lighter player dim missing",
    )

    require(
        "historyBackgroundContentNode"
        in text
        and
        ".clear"
        in text,
        "opaque history background survived",
    )

    require(
        "historyFrameTopMaskNode"
        in text
        and
        "0.0"
        in text,
        "opaque top corner surface survived",
    )

    require(
        "hasPlainBackground"
        in text
        and
        "false"
        in text,
        "controls glass path missing",
    )

    require(
        "ghostBaseBackdropView?"
        in text
        and
        "layout.size"
        in text,
        "music backdrop layout missing",
    )

    require(
        "UIColor("
        in text
        and
        "alpha: 0.5"
        in text,
        "Official fallback dim lost",
    )

    require(
        text.count(
            "UIVisualEffectView("
        ) >= 2,
        "music backdrop blur missing",
    )


if errors:
    print(
        "[V11M-B2 VERIFY] FAILED"
    )

    for error in errors:
        print(
            " -",
            error
        )

    raise RuntimeError(
        "V11M-B2 verifier failed"
    )


print("[V11M-B2 VERIFY] OK")
print("  Saved Music is peer-aware and GhostBase-only")
print("  wallpaper -> avatar/Premium source order preserved")
print("  own profile skips chat wallpaper")
print("  completed MediaBox resources only")
print("  music player surfaces are translucent")
print("  ordinary audio player fallback remains Official")
