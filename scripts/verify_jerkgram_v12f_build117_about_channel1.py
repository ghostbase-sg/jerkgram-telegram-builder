#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"


def require(value, message):
    if not value:
        raise RuntimeError("[verify Build117 About channel] " + message)


def verify(settings, strings):
    require(settings.count("BUILD117_ABOUT_CHANNEL_CARD1") == 2, "About markers missing")
    require("BUILD116_ABOUT_COMMUNITY1" not in settings, "static Build116 About survived")
    for token in (
        "JerkgramAboutChannelState",
        "case aboutChannel",
        "ItemListPeerItem(",
        'resolvePeerByName(name: "JerkgramApp"',
        "aroundMessageHistoryViewForLocation",
        "String(compact.prefix(160))",
        "aboutChannelState: aboutChannelState",
        "navigateToChatController",
    ):
        require(token in settings, "About invariant missing: " + token)
    require(settings.count('name: "JerkgramApp"') == 1, "channel resolver count != 1")
    require("Build: 117" in settings, "About build label is stale")
    require("Bundle ID:" not in settings[settings.index("BUILD117_ABOUT_CHANNEL_CARD1"):], "Bundle ID exposed")
    for key in ("communityLoading", "communityUnavailable", "communityNoPosts"):
        require("case " + key in strings, "string key missing: " + key)
        require("self.text(." + key + ")" in strings, "string accessor missing: " + key)


def main():
    for path in (SETTINGS, STRINGS):
        require(path.is_file(), "source owner missing: " + str(path))
    verify(SETTINGS.read_text(encoding="utf-8"), STRINGS.read_text(encoding="utf-8"))
    print("[verify Build117 About channel] GREEN: live native channel credit")


if __name__ == "__main__":
    main()
