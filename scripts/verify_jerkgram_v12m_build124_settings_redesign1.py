#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
STARS = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramStarsEditorController.swift"
DATA = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramDataAndBackupController.swift"
TIME_MACHINE = ROOT / "submodules/TelegramUI/Components/Chat/ChatSearchNavigationContentNode/Sources/JerkgramTimeMachineController.swift"

MARKER = "// MARK: Jerkgram v1.2M BUILD124_SETTINGS_REDESIGN1"
PAGE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_SETTINGS_PAGE_SUMMARY1"
PAGES = ("home", "ghostMode", "messages", "protectedContent", "mediaStories", "appearance", "debugResearch", "about")


def fail(message: str) -> None:
    raise SystemExit("[verify Build124 settings redesign] ERROR: " + message)


def require(value: bool, message: str) -> None:
    if not value:
        fail(message)


def block_bounds(text: str, signature: str) -> tuple[int, int]:
    start = text.find(signature)
    require(start >= 0, "block missing: " + signature)
    brace = text.find("{", start)
    require(brace >= 0, "opening brace missing: " + signature)
    depth = 0
    in_string = False
    escaped = False
    for index in range(brace, len(text)):
        ch = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return start, index + 1
    fail("unbalanced block: " + signature)


def block_text(text: str, signature: str) -> str:
    start, end = block_bounds(text, signature)
    return text[start:end]


def main() -> None:
    for path in (SETTINGS, STRINGS, STARS, DATA, TIME_MACHINE):
        require(path.is_file(), "target missing: " + str(path))

    settings = SETTINGS.read_text(encoding="utf-8")
    strings = STRINGS.read_text(encoding="utf-8")
    stars = STARS.read_text(encoding="utf-8")
    data = DATA.read_text(encoding="utf-8")
    time_machine = TIME_MACHINE.read_text(encoding="utf-8")

    require(settings.count(MARKER) == 1, "Settings redesign owner must exist exactly once")
    root = block_text(settings, "if page == .root {")
    require(root.count(".disclosure(") == 9, "root must retain nine Telegram-native destinations")
    require(PAGE_MARKER not in root, "internal summary leaked into root Settings")
    require('"Jerkgram",' not in root, "Build119 root hero was restored")

    for page in PAGES:
        block = block_text(settings, f"if page == .{page} {{")
        require(PAGE_MARKER not in block, f"{page}: state-count summary must not be shown")
        require(".info(-1," not in block, f"{page}: injected state-count row must not be shown")

    require("aboutBuild119Summary" not in block_text(settings, "if page == .about {"), "About still reports Build119")
    require("BUILD123_SETTINGS_SYSTEM1" in settings, "Build123 shared Telegram-native visual system disappeared")
    require("JerkgramSettingsSectionHeaderItem" in settings, "shared section-header owner disappeared")
    require("JerkgramSettingsStatusItem" in settings, "shared status/glass owner disappeared")
    require("JerkgramSettingsDidImport" in settings, "Build124 archive-import live refresh bridge disappeared")

    for token in (
        "build124HomeSummary", "build124GhostSummary", "build124MessagesSummary",
        "build124ProtectedSummary", "build124MediaSummary", "build124AppearanceSummary",
        "build124DiagnosticsSummary", "build124AboutSummary", "build124DataSummary",
        "build124TimeMachineSummary",
    ):
        require(token in strings, "localized Build124 string owner missing: " + token)
    require('self.languageCode == "ru"' in strings, "Build124 redesign copy is not Telegram-language aware")
    require("Build 124 Canary" in strings, "Build124 Canary identity missing from redesign copy")

    require("BUILD124_STARS_REDESIGN1" in stars, "Stars redesign marker missing")
    require(stars.count("systemStyle: .glass") >= 2, "Stars preview/toggle are not using coherent glass surfaces")
    require("Common_Cancel" in stars and "Common_Save" in stars, "Stars Save/Cancel navigation disappeared")
    require("jerkgramCommitStarsDraft" in stars, "Stars draft commit owner disappeared")
    require("state != initial" in stars, "Stars dirty-state semantics disappeared")

    require("BUILD124_DATA_REDESIGN1" in data, "Data redesign marker missing")
    require("build124DataSummary" in data and "build119DataSummary" not in data, "Data still uses Build119 summary identity")
    require('strings.exportArchive, "Build124 Canary", "export"' in data, "Data export row still reports an older build")
    require('action == "export" || action == "import" || action == "cleanup"' in data, "Data explicit action semantics disappeared")
    require("ItemListActionItem" in data, "Data export/import/cleanup buttons disappeared")
    require("systemStyle: .glass" in data, "Data summary/disclosure material is not glass")

    require("BUILD124_TIME_MACHINE_FINAL_UI1" in time_machine, "Time Machine final UI marker missing")
    require(
        "build119TimeMachineSummary" not in time_machine and "build124TimeMachineSummary" not in time_machine,
        "Time Machine technical summary survived",
    )
    require(".summary(0, 1," not in time_machine, "Time Machine technical summary entry survived")
    require("ItemListSwitchItem" in time_machine, "Time Machine filters are not native switches")
    require("systemStyle: .glass" in time_machine, "Time Machine filters lost glass material")
    require("Queue.concurrentDefaultQueue().async" in time_machine, "Time Machine loading moved off its background queue owner")
    require(
        re.search(r"eventPage\s*\([^)]*\blimit\s*:\s*250\b", time_machine, re.DOTALL) is not None,
        "Time Machine bounded paging disappeared",
    )
    require("loadMore" in time_machine, "Time Machine load-more behavior disappeared")

    print("[verify Build124 settings redesign] SOURCE VERIFIED")
    print("[verify Build124 settings redesign] Telegram-native root preserved; internal destinations omit injected state-count surfaces")
    print("[verify Build124 settings redesign] Stars/Data/Time Machine functional owners and bounded loading are preserved")


if __name__ == "__main__":
    main()
