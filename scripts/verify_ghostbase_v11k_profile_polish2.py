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
    / "submodules/TelegramUI/Components/PeerInfo/"
      "PeerInfoScreen/Sources"
)


paths = {
    "bg":
        P
        / "GhostBaseProfileFullscreenBackground.swift",

    "hdr":
        P
        / "PeerInfoHeaderNode.swift",

    "sec":
        P
        / "PeerInfoScreenItemSectionContainerNode.swift",

    "scr":
        P
        / "PeerInfoScreen.swift",

    "rep":
        P
        / "GhostBaseProfileReportPaneNode.swift",

    "pane":
        P
        / "PeerInfoPaneContainerNode.swift",

    "groups":
        P
        / "Panes/PeerInfoGroupsInCommonPaneNode.swift",

    "members":
        P
        / "Panes/PeerInfoMembersPane.swift",

    "gifts":
        ROOT
        / "submodules/TelegramUI/Components/PeerInfo/"
          "PeerInfoVisualMediaPaneNode/Sources/"
          "PeerInfoGiftsPaneNode.swift",

    "star":
        ROOT
        / "submodules/TelegramCore/Sources/"
          "TelegramEngine/Payments/StarGifts.swift",
}


errors = []


for key, path in paths.items():
    if not path.is_file():
        errors.append(
            f"missing {path}"
        )


text = {}

if not errors:
    text = {
        key:
            path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        for key, path
        in paths.items()
    }


def require(
    condition: bool,
    message: str,
):
    if not condition:
        errors.append(
            message
        )


if not errors:
    require(
        "GhostBase v1.1K PROFILEPOLISH2"
        in text["bg"],
        "background V11K marker missing",
    )

    require(
        "GhostBase.ProfileVisualTone.V11K"
        in text["bg"],
        "persistent tone missing",
    )

    require(
        "maximumPersistentTones =\n        96"
        in text["bg"]
        or
        "maximumPersistentTones = 96"
        in text["bg"],
        "persistent tone bound missing",
    )


    avatar_position = text["bg"].find(
            "if self.settings.avatarBlurInProfile"
        )

    premium_position = text["bg"].find(
            "if let status = peer.emojiStatus",
            avatar_position,
        )

    require(
        avatar_position >= 0
        and premium_position
            > avatar_position,
        "avatar-preferred source "
        "is not before Premium",
    )


    require(
        "if let settings = GhostBaseProfileGlassRuntime.loadSettings()"
        in text["scr"],
        "Settings profile background "
        "not enabled",
    )


    require(
        "isSettings ? nil : GhostBaseProfileGlassRuntime.loadSettings()"
        not in text["hdr"],
        "Settings header still bypasses glass",
    )


    require(
        "GhostBase v1.1K HEADERGLASS2"
        in text["hdr"],
        "header glass marker missing",
    )


    require(
        "diameter * 0.5"
        not in text["hdr"],
        "round-button takeover present",
    )


    require(
        "self.isAvatarExpanded || hasBackground || self.ghostBaseProfileGlassSettings != nil"
        in text["hdr"],
        "music glass path missing",
    )


    require(
        "GhostBase v1.1K READABILITY2"
        in text["sec"],
        "readability scrim missing",
    )


    require(
        "self.itemContainerNode.cornerRadius ="
        in text["sec"],
        "section content clipping missing",
    )


    require(
        "UIVisualEffectView("
        not in text["sec"],
        "per-section blur returned",
    )


    require(
        "afterPendingWrites"
        in text["rep"]
        and
        "wasVisible"
        in text["rep"],
        "history synchronization/reload missing",
    )


    require(
        "static let maximumEvents = 200"
        in text["rep"],
        "history bound lost",
    )


    require(
        "ghostBaseGlassEnabled: self.ghostBaseGlassEnabled"
        in text["pane"],
        "pane glass propagation missing",
    )


    require(
        "isDark ? 0.08 : 0.12"
        in text["pane"]
        or
        "? 0.08"
        in text["pane"],
        "pane root alpha not reduced",
    )


    require(
        "self.listMaskView.tintColor =\n                .clear"
        in text["groups"]
        or
        "self.listMaskView.tintColor = .clear"
        in text["groups"],
        "Common Groups black overlay "
        "not removed",
    )


    require(
        "self.listMaskView.tintColor =\n                .clear"
        in text["members"]
        or
        "self.listMaskView.tintColor = .clear"
        in text["members"],
        "Members black overlay "
        "not removed",
    )


    require(
        "systemStyle: .glass"
        in text["members"]
        and
        "hideBackground: true"
        in text["members"],
        "native member glass row "
        "behavior lost",
    )


    require(
        "self.backgroundNode.backgroundColor =\n                .clear"
        in text["gifts"]
        or
        "self.backgroundNode.backgroundColor = .clear"
        in text["gifts"],
        "Gifts root black background "
        "not removed",
    )


    require(
        "panelEdgeContent"
        in text["gifts"]
        and
        "self.ghostBaseGlassEnabled"
        in text["gifts"],
        "Gifts bottom black edge "
        "not removed",
    )


    bearGenerator = (
        Path(
            os.environ.get(
                "GHOSTBASE_BUILDER_ROOT",
                "/root/gb_builder"
            )
        )
        / "scripts"
        / "apply_ghostbase_v10zh_gifthistory2.py"
    )

    bearGeneratorText = (
        bearGenerator.read_text(
            encoding="utf-8"
        )
        if bearGenerator.is_file()
        else ""
    )

    require(
        "6046178578163303744"
        in text["star"],
        "bear ID missing from materialized StarGifts.swift",
    )


if errors:
    print(
        "[V11K VERIFY] FAILED"
    )

    for error in errors:
        print(
            " -",
            error,
        )

    raise RuntimeError(
        "V11K verifier failed"
    )


print("[V11K VERIFY] OK")
print("  wallpaper / avatar / Premium selector")
print("  persistent source-keyed tone")
print("  Settings/self profile uses same scene")
print("  stock geometry + glass buttons/music")
print("  readable clipped info surfaces")
print("  history waits pending writes and reloads")
print("  Gifts background continues to bottom")
print("  Common Groups black mask removed")
print("  Members black mask removed")
print("  bear 6046178578163303744 recognized")
