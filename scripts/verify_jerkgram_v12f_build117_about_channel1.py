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


def block_region(text, opening, after=0):
    start = text.find(opening, after)
    require(start >= 0, "block missing: " + opening)
    brace = text.find("{", start)
    require(brace >= 0, "block brace missing: " + opening)
    depth = 0
    in_string = False
    escaped = False
    for index in range(brace, len(text)):
        character = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise RuntimeError(
        "[verify Build117 About channel] unbalanced block: " + opening
    )


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
    about_start = settings.index("BUILD117_ABOUT_CHANNEL_CARD1")
    about = block_region(settings, "if page == .about", about_start)
    require("Bundle ID:" not in about, "Bundle ID exposed")
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
