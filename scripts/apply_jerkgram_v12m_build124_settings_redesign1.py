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
STARS_MARKER = "// MARK: Jerkgram v1.2M BUILD124_STARS_REDESIGN1"
DATA_MARKER = "// MARK: Jerkgram v1.2M BUILD124_DATA_REDESIGN1"
TIME_MACHINE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_TIME_MACHINE_REDESIGN1"
TIME_MACHINE_FINAL_MARKER = "// MARK: Jerkgram v1.2M BUILD124_TIME_MACHINE_FINAL_UI1"
STRINGS_MARKER = "// MARK: Jerkgram v1.2M BUILD124_SETTINGS_REDESIGN_STRINGS1"


PAGE_SUMMARIES = {
    "home": "strings.build124HomeSummary(state.profileEnabled, state.glassEnabled, state.localStarsEnabled)",
    "ghostMode": "strings.build124GhostSummary(state.readMessages, state.typingActions, state.presence, state.scheduledSend)",
    "messages": "strings.build124MessagesSummary(state.saveDeleted, state.saveEditHistory, state.preserveDeletedMedia)",
    "protectedContent": "strings.build124ProtectedSummary(state.protectedEnabled, state.oneTimeSave)",
    "mediaStories": "strings.build124MediaSummary(state.oneTimeSave, state.storySave)",
    "appearance": "strings.build124AppearanceSummary(state.glassEnabled, state.showRamUnderClock, state.messageSeconds)",
    "debugResearch": "strings.build124DiagnosticsSummary",
    "about": "strings.build124AboutSummary",
}


STRINGS_EXTENSION = r'''

// MARK: Jerkgram v1.2M BUILD124_SETTINGS_REDESIGN_STRINGS1
public extension JerkgramStrings {
    private func build124StateWord(_ enabled: Bool) -> String {
        if self.languageCode == "ru" {
            return enabled ? "вкл." : "выкл."
        } else {
            return enabled ? "on" : "off"
        }
    }

    func build124HomeSummary(_ profile: Bool, _ glass: Bool, _ stars: Bool) -> String {
        if self.languageCode == "ru" {
            return "Профиль: \(build124StateWord(profile)) · Glass: \(build124StateWord(glass)) · Stars: \(build124StateWord(stars))"
        } else {
            return "Profile: \(build124StateWord(profile)) · Glass: \(build124StateWord(glass)) · Stars: \(build124StateWord(stars))"
        }
    }

    func build124GhostSummary(_ read: Bool, _ typing: Bool, _ presence: Bool, _ scheduled: Bool) -> String {
        let active = [read, typing, presence, scheduled].filter { $0 }.count
        if self.languageCode == "ru" {
            return "Активно базовых режимов: \(active) из 4"
        } else {
            return "Core privacy modes active: \(active) of 4"
        }
    }

    func build124MessagesSummary(_ deleted: Bool, _ edits: Bool, _ media: Bool) -> String {
        if self.languageCode == "ru" {
            return "Удалённые: \(build124StateWord(deleted)) · Правки: \(build124StateWord(edits)) · Медиа: \(build124StateWord(media))"
        } else {
            return "Deleted: \(build124StateWord(deleted)) · Edits: \(build124StateWord(edits)) · Media: \(build124StateWord(media))"
        }
    }

    func build124ProtectedSummary(_ enabled: Bool, _ oneTime: Bool) -> String {
        if self.languageCode == "ru" {
            return "Защита: \(build124StateWord(enabled)) · Одноразовые медиа: \(build124StateWord(oneTime))"
        } else {
            return "Protection: \(build124StateWord(enabled)) · One-time media: \(build124StateWord(oneTime))"
        }
    }

    func build124MediaSummary(_ oneTime: Bool, _ stories: Bool) -> String {
        if self.languageCode == "ru" {
            return "Одноразовые медиа: \(build124StateWord(oneTime)) · Истории: \(build124StateWord(stories))"
        } else {
            return "One-time media: \(build124StateWord(oneTime)) · Stories: \(build124StateWord(stories))"
        }
    }

    func build124AppearanceSummary(_ glass: Bool, _ ram: Bool, _ seconds: Bool) -> String {
        if self.languageCode == "ru" {
            return "Glass: \(build124StateWord(glass)) · RAM: \(build124StateWord(ram)) · Секунды: \(build124StateWord(seconds))"
        } else {
            return "Glass: \(build124StateWord(glass)) · RAM: \(build124StateWord(ram)) · Seconds: \(build124StateWord(seconds))"
        }
    }

    var build124DiagnosticsSummary: String {
        if self.languageCode == "ru" {
            return "Диагностика и исследовательские инструменты Jerkgram"
        } else {
            return "Jerkgram diagnostics and research tools"
        }
    }

    var build124AboutSummary: String {
        return "Jerkgram · Official Telegram 12.9.2 · Build 124 Canary"
    }

    func build124DataSummary(_ duration: String, _ mediaLimit: String, _ accountPeerId: Int64) -> String {
        if self.languageCode == "ru" {
            return "\(duration) · \(mediaLimit) · аккаунт \(accountPeerId)"
        } else {
            return "\(duration) · \(mediaLimit) · account \(accountPeerId)"
        }
    }

    func build124TimeMachineSummary(_ loaded: Int, _ activeKinds: Int, _ authorScoped: Bool) -> String {
        if self.languageCode == "ru" {
            let author = authorScoped ? "автор выбран" : "все авторы"
            return "Загружено \(loaded) · фильтров \(activeKinds) · \(author)"
        } else {
            let author = authorScoped ? "author selected" : "all authors"
            return "\(loaded) loaded · \(activeKinds) filters · \(author)"
        }
    }
}
'''


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 settings redesign] " + message)


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
    raise RuntimeError("[Build124 settings redesign] unbalanced block: " + signature)


def block_text(text: str, signature: str) -> str:
    start, end = block_bounds(text, signature)
    return text[start:end]


def replace_block(text: str, signature: str, replacement: str) -> str:
    start, end = block_bounds(text, signature)
    return text[:start] + replacement + text[end:]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    require(count == 1, f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def add_page_summary(block: str, expression: str) -> str:
    if PAGE_MARKER in block:
        return block
    match = re.search(
        r'(?m)^(?P<indent>[ \t]*)(?:return|var\s+[A-Za-z_][A-Za-z0-9_]*(?:\s*:\s*\[[^\]]+\])?\s*=)\s*\[\s*$',
        block,
    )
    if match is not None:
        indent = match.group("indent") + "    "
        insertion = (
            match.group(0)
            + "\n"
            + indent + PAGE_MARKER + "\n"
            + indent + ".info(-1, " + expression + "),"
        )
        return block[:match.start()] + insertion + block[match.end():]

    append_match = re.search(r'(?m)^(?P<indent>[ \t]*)entries\.append\(', block)
    require(append_match is not None, "page entries array anchor missing")
    insertion = (
        append_match.group("indent")
        + PAGE_MARKER + "\n"
        + append_match.group("indent")
        + "entries.append(.info(-1, " + expression + "))\n"
    )
    return block[:append_match.start()] + insertion + block[append_match.start():]


def remove_script_added_toggle_icons(text: str) -> str:
    marker = "// MARK: Jerkgram v1.2L BUILD123_SETTINGS_TOGGLE_ICONS1"
    if marker not in text:
        return text
    helper_start = text.index(marker)
    signature = "private func jerkgramSettingsToggleIcon(_ key: String) -> UIImage?"
    _, helper_end = block_bounds(text, signature)
    text = text[:helper_start] + text[helper_end:]
    text, count = re.subn(
        r"(?m)^([ \t]*)icon: jerkgramSettingsToggleIcon\(key\),\n",
        "",
        text,
    )
    require(count == 1, "script-added Settings toggle icon call missing")
    require("jerkgramSettingsToggleIcon" not in text, "script-added Settings toggle icon survived")
    return text


def patch_settings_text(text: str) -> str:
    if MARKER in text:
        return text

    text = remove_script_added_toggle_icons(text)

    root = block_text(text, "if page == .root {")
    require(root.count(".disclosure(") == 9, "root must keep exactly nine Telegram-native destinations")
    require('"Jerkgram",' not in root, "root hero must not be restored")

    for page, expression in PAGE_SUMMARIES.items():
        signature = f"if page == .{page} {{"
        block = block_text(text, signature)
        block = add_page_summary(block, expression)
        if page == "about":
            block = block.replace("strings.aboutBuild119Summary", "strings.build124AboutSummary")
            require("aboutBuild119Summary" not in block, "stale Build119 About identity survived")
        text = replace_block(text, signature, block)

    owner = "private func ghostBaseSettingsEntries("
    start = text.find(owner)
    require(start >= 0, "settings entries owner missing")
    text = text[:start] + MARKER + "\n" + text[start:]

    root_after = block_text(text, "if page == .root {")
    require(root_after.count(".disclosure(") == 9, "root destination topology changed")
    require(PAGE_MARKER not in root_after, "internal summary leaked into root Settings")
    return text


def patch_strings_text(text: str) -> str:
    if STRINGS_MARKER in text:
        return text
    return text + STRINGS_EXTENSION


def patch_stars_text(text: str) -> str:
    if STARS_MARKER in text:
        return text
    require("BUILD122_STARS_DRAFT_EDITOR1" in text, "Build122 Stars draft editor prerequisite missing")

    preview_old = '''case let .preview(_, amount, status):
            return ItemListDisclosureItem(
                presentationData: presentationData,
                title:''' 
    preview_new = '''// MARK: Jerkgram v1.2M BUILD124_STARS_REDESIGN1
        case let .preview(_, amount, status):
            return ItemListDisclosureItem(
                presentationData: presentationData, systemStyle: .glass,
                title:'''
    if preview_old in text:
        text = replace_once(text, preview_old, preview_new, "Stars preview glass")
    else:
        # Synthetic/unit fixtures use less indentation; preserve the same source contract.
        fixture_old = '''case let .preview(_, amount, status):
    return ItemListDisclosureItem(
        presentationData: presentationData,
        title:'''
        fixture_new = '''// MARK: Jerkgram v1.2M BUILD124_STARS_REDESIGN1
case let .preview(_, amount, status):
    return ItemListDisclosureItem(
        presentationData: presentationData, systemStyle: .glass,
        title:'''
        text = replace_once(text, fixture_old, fixture_new, "Stars preview glass")

    toggle_patterns = (
        ("presentationData: presentationData, title: title, value: value,", "presentationData: presentationData, systemStyle: .glass, title: title, value: value,"),
    )
    changed = False
    for old, new in toggle_patterns:
        if old in text:
            text = text.replace(old, new, 1)
            changed = True
            break
    require(changed, "Stars toggle glass anchor missing")
    require("Common_Cancel" in text and "Common_Save" in text, "Stars Save/Cancel semantics disappeared")
    require("jerkgramCommitStarsDraft" in text, "Stars draft commit owner disappeared")
    return text


def patch_data_text(text: str) -> str:
    if DATA_MARKER in text:
        return text
    require("BUILD119_DATA_SUMMARY1" in text, "Build119 Data summary prerequisite missing")
    text = text.replace(
        "// MARK: Jerkgram v1.2H BUILD119_DATA_SUMMARY1",
        "// MARK: Jerkgram v1.2H BUILD119_DATA_SUMMARY1\n" + DATA_MARKER,
        1,
    )
    require("build119DataSummary" in text, "Build119 Data summary call missing")
    text = text.replace("build119DataSummary", "build124DataSummary")
    require('strings.exportArchive, "Build119", "export"' in text, "stale Build119 export label anchor missing")
    text = text.replace(
        'strings.exportArchive, "Build119", "export"',
        'strings.exportArchive, "Build124 Canary", "export"',
        1,
    )

    action_start = text.find('case let .action(_, _, title, value, action):')
    require(action_start >= 0, "Data action renderer missing")
    action_end = text.find("\n        }", action_start)
    if action_end < 0:
        action_end = min(len(text), action_start + 4000)
    action_block = text[action_start:action_end]
    if "presentationData: presentationData,\n                title:" in action_block:
        action_block = action_block.replace(
            "presentationData: presentationData,\n                title:",
            "presentationData: presentationData, systemStyle: .glass,\n                title:",
            1,
        )
        text = text[:action_start] + action_block + text[action_end:]
    require('action == "export" || action == "import" || action == "cleanup"' in text, "Data export/import/cleanup actions disappeared")
    require("ItemListActionItem" in text, "Data action semantics disappeared")
    return text


def matching_call_end(text: str, start: int) -> int:
    opening = text.find("(", start)
    require(opening >= 0, "Time Machine call opening parenthesis missing")
    depth = 0
    for index in range(opening, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index + 1
    raise RuntimeError("[Build124 settings redesign] unbalanced Time Machine call")


def remove_time_machine_summary_entry(text: str) -> str:
    entries_start = text.find("var entries: [JerkgramTimeMachineUIEntry] = [")
    require(entries_start >= 0, "Time Machine entries owner missing")
    summary_start = text.find(".summary(", entries_start)
    require(summary_start >= 0, "Time Machine technical summary entry missing")
    summary_end = matching_call_end(text, summary_start)
    while summary_end < len(text) and text[summary_end] in " \t\n":
        summary_end += 1
    if summary_end < len(text) and text[summary_end] == ",":
        summary_end += 1
    return text[:summary_start] + text[summary_end:]


def patch_time_machine_final_ui(text: str) -> str:
    if TIME_MACHINE_FINAL_MARKER in text:
        return text
    text = remove_time_machine_summary_entry(text)
    filter_start = text.find("case let .filter(_, _, title, value, kind):")
    require(filter_start >= 0, "Time Machine filter renderer missing")
    filter_end = text.find("\n        case ", filter_start + 1)
    if filter_end < 0:
        filter_end = text.find("\nvar entries:", filter_start)
    require(filter_end >= 0, "Time Machine filter renderer boundary missing")
    prefix = text[filter_start:filter_end]
    indent_match = re.match(r"(?m)^(\s*)case let", prefix)
    require(indent_match is not None, "Time Machine filter indentation missing")
    indent = indent_match.group(1)
    replacement = f'''{indent}{TIME_MACHINE_FINAL_MARKER}
{indent}case let .filter(_, _, title, value, kind):
{indent}    if let kind {{
{indent}        return ItemListSwitchItem(
{indent}            presentationData: presentationData, systemStyle: .glass,
{indent}            title: title, value: value == "✓",
{indent}            sectionId: self.section, style: .blocks,
{indent}            updated: {{ _ in arguments.toggleKind(kind) }}
{indent}        )
{indent}    }} else {{
{indent}        return ItemListDisclosureItem(
{indent}            presentationData: presentationData, systemStyle: .glass,
{indent}            title: title, label: value, labelStyle: .text,
{indent}            sectionId: self.section, style: .blocks,
{indent}            disclosureStyle: .none,
{indent}            action: {{ arguments.selectSender() }}
{indent}        )
{indent}    }}'''
    return text[:filter_start] + replacement + text[filter_end:]


def patch_time_machine_text(text: str) -> str:
    if TIME_MACHINE_MARKER not in text:
        require("BUILD119_TIME_MACHINE_SUMMARY1" in text, "Build119 Time Machine summary prerequisite missing")
        text = text.replace(
            "// MARK: Jerkgram v1.2H BUILD119_TIME_MACHINE_SUMMARY1",
            "// MARK: Jerkgram v1.2H BUILD119_TIME_MACHINE_SUMMARY1\n" + TIME_MACHINE_MARKER,
            1,
        )

    require("build119TimeMachineSummary" in text, "Build119 Time Machine summary call missing")
    text = text.replace("build119TimeMachineSummary", "build124TimeMachineSummary")
    text = patch_time_machine_final_ui(text)
    require("Queue.concurrentDefaultQueue().async" in text, "Time Machine off-main loading disappeared")
    require(
        re.search(r"eventPage\s*\([^)]*\blimit\s*:\s*250\b", text, re.DOTALL) is not None,
        "Time Machine bounded paging disappeared",
    )
    return text


def main() -> None:
    for path in (SETTINGS, STRINGS, STARS, DATA, TIME_MACHINE):
        require(path.is_file(), "materialized target missing: " + str(path))

    settings = SETTINGS.read_text(encoding="utf-8")
    require("BUILD123_SETTINGS_SYSTEM1" in settings, "Build123 Settings visual system prerequisite missing")
    require("BUILD122_SETTINGS_RELEASE1" in settings, "Build122 Telegram-native root prerequisite missing")
    settings = patch_settings_text(settings)

    strings = patch_strings_text(STRINGS.read_text(encoding="utf-8"))
    stars = patch_stars_text(STARS.read_text(encoding="utf-8"))
    data = patch_data_text(DATA.read_text(encoding="utf-8"))
    time_machine = patch_time_machine_text(TIME_MACHINE.read_text(encoding="utf-8"))

    SETTINGS.write_text(settings, encoding="utf-8")
    STRINGS.write_text(strings, encoding="utf-8")
    STARS.write_text(stars, encoding="utf-8")
    DATA.write_text(data, encoding="utf-8")
    TIME_MACHINE.write_text(time_machine, encoding="utf-8")

    print("[Build124 settings redesign] GREEN")
    print("[Build124 settings redesign] root remains Telegram-native; internal Jerkgram pages share compact glass summaries")
    print("[Build124 settings redesign] Stars/Data/Time Machine retain their functional owners and use Build124 Canary identity")


if __name__ == "__main__":
    main()
