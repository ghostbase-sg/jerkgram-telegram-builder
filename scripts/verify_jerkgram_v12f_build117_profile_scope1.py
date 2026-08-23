#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()

PROFILE = ROOT / (
    "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/"
    "Sources/PeerInfoData.swift"
)


def require(value, message):
    if not value:
        raise RuntimeError("[verify Build117 profile scope] " + message)


def verify(text):
    require(
        text.count("BUILD117_SETTINGS_PROFILE_SCOPE1") == 1,
        "scope marker count != 1",
    )
    require("BUILD116_PROFILE_SCOPE1" not in text, "Build116 universal helper survived")
    require("isSettings: Bool = false" in text, "default route flag missing")
    require("if isSettings {\n        return availablePanes" in text, "Settings stock-pane branch missing")
    require("isSettings: isSettings" in text, "route flag is not passed to helper")

    start = text.find("func peerInfoScreenSettingsData(")
    end = text.find("\nfunc peerInfoScreenData(", start)
    require(start >= 0 and end > start, "Settings data function boundary missing")
    settings_region = text[start:end]
    constructor_count = settings_region.count("PeerInfoScreenData(")
    require(constructor_count >= 1, "Settings constructors missing")
    settings_flagged_constructors = re.findall(
        r"businessConnectedBot:\s*[^,\n\)]+,\n"
        r"[ \t]*isSettings:\s*true\n[ \t]*\)",
        settings_region,
    )
    require(
        len(settings_flagged_constructors) == constructor_count,
        "not every Settings constructor has isSettings: true",
    )

    ordinary_region = text[end:]
    require(
        not re.search(
            r"businessConnectedBot:\s*[^,\n\)]+,\n"
            r"[ \t]*isSettings:\s*true\n[ \t]*\)",
            ordinary_region,
        ),
        "ordinary profile was incorrectly marked as Settings",
    )
    for pane in (
        "ghostBaseProfileHistory",
        "ghostBasePresence",
        "ghostBaseGiftHistory",
        "ghostBasePersonalChannel",
    ):
        require(pane in text, "ordinary profile pane missing: " + pane)


def main():
    require(PROFILE.is_file(), "source owner missing: " + str(PROFILE))
    verify(PROFILE.read_text(encoding="utf-8"))
    print("[verify Build117 profile scope] GREEN: Settings-only suppression")


if __name__ == "__main__":
    main()
