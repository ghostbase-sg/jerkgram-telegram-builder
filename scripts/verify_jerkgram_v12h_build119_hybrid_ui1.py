#!/usr/bin/env python3

from pathlib import Path
import os


REPO = Path(__file__).resolve().parents[1]
ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()

SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
DATA = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramDataAndBackupController.swift"
TIME_MACHINE = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramTimeMachineController.swift"
APPLY = REPO / "scripts/apply_jerkgram_v12h_build119_hybrid_ui1.py"

EXPECTED_ARTIFACT = "Jerkgram-build119"
MARKER = "BUILD119_HYBRID_UI1"


def require(value, message):
    if not value:
        raise RuntimeError("[Build119 hybrid UI verify] " + message)


def block(text, signature):
    start = text.find(signature)
    require(start >= 0, "owner missing: " + signature)
    brace = text.find("{", start)
    require(brace >= 0, "opening brace missing: " + signature)
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
    raise RuntimeError("[Build119 hybrid UI verify] unbalanced owner: " + signature)


def main():
    for path in (SETTINGS, STRINGS, DATA, TIME_MACHINE, APPLY):
        require(path.is_file(), "missing file: " + str(path))

    settings = SETTINGS.read_text(encoding="utf-8")
    strings = STRINGS.read_text(encoding="utf-8")
    data = DATA.read_text(encoding="utf-8")
    time_machine = TIME_MACHINE.read_text(encoding="utf-8")
    apply = APPLY.read_text(encoding="utf-8")

    # Settings owner / route invariants.
    require(settings.count("case stars") == 1, "Stars route owner count != 1")
    require(settings.count("case .stars:") >= 2, "Stars canonical/localized title routes missing")
    require(settings.count("case valueDisclosure") == 1, "valueDisclosure owner count != 1")
    require("systemStyle: .glass" in settings, "Build119 compact material missing")

    root = block(settings, "if page == .root {")
    require(".valueDisclosure(" in root and '"Jerkgram"' in root, "root Jerkgram summary missing")
    require("strings.build119Summary" in root, "root Build119 value missing")
    require("strings.features" in root, "root feature grouping missing")
    require("strings.debugResearch" not in root, "release Debug / Research row survived")
    for route in (
        "strings.basicFunctions",
        "strings.ghostMode",
        "strings.messages",
        "strings.protectedContent",
        "strings.mediaAndStories",
        "strings.appearance",
        "strings.dataAndBackup",
        "strings.about",
    ):
        require(route in root, "root route missing: " + route)

    home = block(settings, "if page == .home {")
    require("strings.starsOverrideSummary" in home, "Basic Functions Stars summary missing")
    require(".valueDisclosure(" in home and ".stars" in home, "Basic Functions Stars route missing")
    require(
        not (".input(" in home and "GhostBaseKey.localStarsAmount" in home),
        "legacy permanent Stars input survived Basic Functions",
    )
    require("GhostBaseKey.localStarsEnabled" not in home, "legacy permanent Stars toggle survived Basic Functions")

    stars = block(settings, "if page == .stars {")
    require("GhostBaseKey.localStarsEnabled" in stars, "Stars enable control missing")
    require("GhostBaseKey.localStarsAmount" in stars, "Stars numeric editor missing")
    require("strings.change" in stars, "Stars editor action header missing")
    require("strings.starsEditorHint" in stars, "Stars local-only explanation missing")

    about = block(settings, "if page == .about {")
    require("BUILD118_ABOUT_CHANNEL_CARDS1" in about, "Build118 About channel/community cards lost")
    require("strings.aboutBuild119Summary" in about, "Build119 About identity missing")
    require("Build: 118" not in about, "Build118 About identity survived")

    # Localization is semantic and follows the existing JerkgramStrings language owner.
    for token in (
        "BUILD119_HYBRID_STRINGS1",
        "var build119Summary",
        "var features",
        "var change",
        "func starsOverrideSummary",
        "var starsEditorHint",
        "var aboutBuild119Summary",
        "func build119DataSummary",
        "func build119TimeMachineSummary",
        'self.languageCode == "ru"',
    ):
        require(token in strings, "Build119 strings invariant missing: " + token)

    # Data UI: visual summary only; account/retention/archive owners stay intact.
    for token in (
        "BUILD119_DATA_SUMMARY1",
        "case summary(Int32, Int32, String, String)",
        "strings.build119DataSummary",
        "JerkgramRetentionRuntime.configuration",
        "jerkgramPresentArchiveExport",
        "jerkgramPresentArchiveImport",
        "configuration.accountPeerId",
        '"Build119"',
        '"Archive v2"',
    ):
        require(token in data, "Data UI invariant missing: " + token)

    # Build118 paging contract must survive Build119 Time Machine polish.
    for token in (
        "BUILD118_TIME_MACHINE_UI1",
        "BUILD119_TIME_MACHINE_SUMMARY1",
        "case summary(Int32, Int32, String, String)",
        "strings.build119TimeMachineSummary",
        "Queue.concurrentDefaultQueue().async",
        "eventPage(",
        "limit: 250",
        "loadNextPage",
        "page.hasMore",
    ):
        require(token in time_machine, "Build118 paging contract / Build119 summary missing: " + token)

    # Build119 visual patch must remain bounded away from native profile geometry.
    for forbidden in (
        "PeerInfoScreen.swift",
        "PeerInfoHeaderNode.swift",
        "PeerInfoPaneContainerNode.swift",
        "PeerInfoScreenItemSectionContainerNode.swift",
    ):
        require(forbidden not in apply, "Build119 unexpectedly targets profile geometry: " + forbidden)

    # The artifact name is kept here so source preflight and workflow contract use one visible identity.
    require(EXPECTED_ARTIFACT == "Jerkgram-build119", "Jerkgram-build119 identity drift")

    print("[Build119 hybrid UI verify] GREEN")
    print("[Build119 hybrid UI verify] Settings route/value layer + Stars editor verified")
    print("[Build119 hybrid UI verify] Data/Time Machine summaries preserve Build118 behavior contracts")
    print("[Build119 hybrid UI verify] profile geometry untouched by Build119 overlay")


if __name__ == "__main__":
    main()
