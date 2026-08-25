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

SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
DATA = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramDataAndBackupController.swift"
TIME_MACHINE = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramTimeMachineController.swift"

MARKER = "// MARK: Jerkgram v1.2H BUILD119_HYBRID_UI1"


def require(value, message):
    if not value:
        raise RuntimeError("[Build119 hybrid UI] " + message)


def replace_once(text, old, new, label):
    count = text.count(old)
    require(count == 1, f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)


def block_bounds(text, signature):
    start = text.find(signature)
    require(start >= 0, "block missing: " + signature)
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
                return start, index + 1
    raise RuntimeError("[Build119 hybrid UI] unbalanced block: " + signature)


def replace_block(text, signature, replacement):
    start, end = block_bounds(text, signature)
    return text[:start] + replacement + text[end:]


def patch_page_routes(text):
    text = replace_once(
        text,
        "    case dataAndBackup\n",
        "    case dataAndBackup\n    case stars\n",
        "Stars page enum",
    )
    text = replace_once(
        text,
        '''        case .dataAndBackup:
            return "Data and Backup"
''',
        '''        case .dataAndBackup:
            return "Data and Backup"
        case .stars:
            return "Stars"
''',
        "Stars canonical title",
    )
    text = replace_once(
        text,
        '''        case .dataAndBackup:
            return strings.dataAndBackup
''',
        '''        case .dataAndBackup:
            return strings.dataAndBackup
        case .stars:
            return strings.starsBalance
''',
        "Stars localized title",
    )
    return text


def patch_value_disclosure_entry(text):
    text = replace_once(
        text,
        "    case disclosure(Int32, Int32, String, String, GhostBaseSettingsPage)\n",
        "    case disclosure(Int32, Int32, String, String, GhostBaseSettingsPage)\n"
        "    case valueDisclosure(Int32, Int32, String, String, String?, GhostBaseSettingsPage)\n",
        "value disclosure case",
    )
    text = replace_once(
        text,
        '''        case let .disclosure(section, _, _, _, _):
            return section
''',
        '''        case let .disclosure(section, _, _, _, _):
            return section
        case let .valueDisclosure(section, _, _, _, _, _):
            return section
''',
        "value disclosure section",
    )
    text = replace_once(
        text,
        '''        case let .disclosure(section, index, _, _, _):
            return section * 1000 + index
''',
        '''        case let .disclosure(section, index, _, _, _):
            return section * 1000 + index
        case let .valueDisclosure(section, index, _, _, _, _):
            return section * 1000 + index
''',
        "value disclosure stable id",
    )
    equality_anchor = '''        case let .info(ls, lt):
            if case let .info(rs, rt) = rhs {'''
    equality = '''        case let .valueDisclosure(ls, li, lt, lv, lIcon, lPage):
            if case let .valueDisclosure(rs, ri, rt, rv, rIcon, rPage) = rhs {
                return ls == rs && li == ri && lt == rt && lv == rv
                    && lIcon == rIcon && lPage.title == rPage.title
            }
            return false
        case let .info(ls, lt):
            if case let .info(rs, rt) = rhs {'''
    text = replace_once(text, equality_anchor, equality, "value disclosure equality")

    renderer_anchor = '''        case let .info(_, text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)'''
    renderer = '''        // MARK: Jerkgram v1.2H BUILD119_HYBRID_UI1
        case let .valueDisclosure(_, _, title, value, iconName, page):
            return ItemListDisclosureItem(
                presentationData: presentationData,
                systemStyle: .glass,
                icon: iconName.flatMap { UIImage(bundleImageName: $0) },
                title: title,
                label: value,
                labelStyle: .text,
                sectionId: self.section,
                style: .blocks,
                disclosureStyle: .arrow,
                action: {
                    arguments.openPage(page)
                }
            )

        case let .info(_, text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)'''
    return replace_once(text, renderer_anchor, renderer, "value disclosure renderer")


def patch_root(text):
    start, end = block_bounds(text, "if page == .root {")
    block = text[start:end]
    require("strings.basicFunctions" in block, "root Basic Functions route missing")
    require("strings.dataAndBackup" in block, "root Data and Backup route missing")
    require("strings.about" in block, "root About route missing")

    debug_pattern = re.compile(
        r'(?m)^\s*\.disclosure\([^\n]*strings\.debugResearch[^\n]*\),?\s*\n?'
    )
    block, debug_count = debug_pattern.subn("", block, count=1)
    require(debug_count == 1, "release Debug / Research row: expected exactly one")

    block = block.replace(".disclosure(0,", ".disclosure(1,")
    return_anchor = "        return [\n"
    require(block.count(return_anchor) == 1, "root return array anchor mismatch")
    hero = '''        return [
            .valueDisclosure(
                0, 0,
                "Jerkgram",
                strings.build119Summary,
                "GhostBaseAbout",
                .about
            ),
            .header(1, strings.features),
'''
    block = block.replace(return_anchor, hero, 1)
    return text[:start] + block + text[end:]


def patch_stars(text):
    start, end = block_bounds(text, "if page == .home {")
    block = text[start:end]

    toggle_pattern = re.compile(
        r'(?m)^[ \t]*\.toggle\([^\n]*GhostBaseKey\.localStarsEnabled[^\n]*\),?\s*\n'
    )
    block, toggle_count = toggle_pattern.subn("", block, count=1)
    require(toggle_count == 1, "expected exactly one legacy Stars toggle")

    input_pattern = re.compile(
        r'(?m)^[ \t]*\.input\([^\n]*GhostBaseKey\.localStarsAmount[^\n]*\),?\s*\n'
    )
    block, input_count = input_pattern.subn("", block, count=1)
    require(input_count == 1, "expected exactly one legacy Stars input")

    info_pattern = re.compile(
        r'(?m)^(?P<indent>[ \t]*)\.info\((?P<section>\d+),\s*strings\.currentVisualBalance\(balance\)\)(?P<comma>,?)\s*$'
    )
    match = info_pattern.search(block)
    require(match is not None, "visual Stars balance summary missing")
    replacement = (
        match.group("indent")
        + ".valueDisclosure("
        + match.group("section")
        + ", 50, strings.starsBalance, "
        + "strings.starsOverrideSummary(state.localStarsEnabled, balance), nil, .stars)"
        + match.group("comma")
    )
    block = block[:match.start()] + replacement + block[match.end():]
    require("GhostBaseKey.localStarsAmount" not in block, "permanent Stars input survived Basic Functions")
    text = text[:start] + block + text[end:]

    stars_block = '''    // MARK: Jerkgram v1.2H BUILD119_STARS_EDITOR1
    if page == .stars {
        let balance = state.localStarsAmount.isEmpty ? "0" : state.localStarsAmount
        return [
            .header(0, strings.starsBalance),
            .toggle(
                0, 1,
                GhostBaseKey.localStarsEnabled,
                strings.localStarsBalance,
                state.localStarsEnabled
            ),
            .info(0, strings.starsOverrideSummary(state.localStarsEnabled, balance)),
            .header(1, strings.change),
            .input(
                1, 1,
                GhostBaseKey.localStarsAmount,
                strings.starsBalance,
                state.localStarsAmount
            ),
            .info(1, strings.starsEditorHint)
        ]
    }

'''
    anchor = "    if page == .ghostMode {"
    require(text.count(anchor) == 1, "Ghost Mode insertion anchor mismatch")
    return text.replace(anchor, stars_block + anchor, 1)


def patch_about(text):
    start, end = block_bounds(text, "if page == .about {")
    block = text[start:end]
    require("BUILD118_ABOUT_CHANNEL_CARDS1" in block, "Build118 About cards prerequisite missing")
    pattern = re.compile(r'\.info\(1,\s*"Jerkgram[^\n]*Build: 118"\)')
    block, count = pattern.subn(".info(1, strings.aboutBuild119Summary)", block, count=1)
    require(count == 1, "Build118 About footer mismatch")
    return text[:start] + block + text[end:]


def patch_settings(text):
    require(MARKER not in text, "Settings overlay already applied")
    require("BUILD118_ACCOUNT_SETTINGS_SCOPE1" in text, "Build118 account settings prerequisite missing")
    text = patch_page_routes(text)
    text = patch_value_disclosure_entry(text)
    text = patch_root(text)
    text = patch_stars(text)
    text = patch_about(text)
    return text


STRINGS_EXTENSION = r'''

// MARK: Jerkgram v1.2H BUILD119_HYBRID_STRINGS1
public extension JerkgramStrings {
    var build119Summary: String {
        self.languageCode == "ru"
            ? "Build 119 · Official Telegram 12.9.2"
            : "Build 119 · Official Telegram 12.9.2"
    }
    var features: String {
        self.languageCode == "ru" ? "Функции" : "Features"
    }
    var change: String {
        self.languageCode == "ru" ? "Изменить" : "Change"
    }
    func starsOverrideSummary(_ enabled: Bool, _ balance: String) -> String {
        if self.languageCode == "ru" {
            return enabled ? "Локально · \(balance) ⭐" : "Выключено · \(balance) ⭐"
        } else {
            return enabled ? "Local · \(balance) ⭐" : "Off · \(balance) ⭐"
        }
    }
    var starsEditorHint: String {
        self.languageCode == "ru"
            ? "Это только локальное отображение баланса. Реальный баланс Telegram не изменяется."
            : "This changes only the local displayed balance. Your real Telegram balance is not modified."
    }
    var aboutBuild119Summary: String {
        "Jerkgram\nOfficial Telegram 12.9.2\nBuild 119"
    }
    func build119DataSummary(_ duration: String, _ mediaLimit: String, _ accountPeerId: Int64) -> String {
        if self.languageCode == "ru" {
            return "\(duration) · \(mediaLimit) · ID \(accountPeerId)"
        } else {
            return "\(duration) · \(mediaLimit) · ID \(accountPeerId)"
        }
    }
    func build119TimeMachineSummary(_ loaded: Int, _ activeKinds: Int, _ authorScoped: Bool) -> String {
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


def patch_strings(text):
    require("BUILD119_HYBRID_STRINGS1" not in text, "Build119 strings already applied")
    return text + STRINGS_EXTENSION


def patch_data(text):
    require("BUILD118_DATA_BACKUP_UI1" in text, "Build118 Data UI prerequisite missing")
    require("BUILD119_DATA_SUMMARY1" not in text, "Build119 Data summary already applied")
    text = text.replace(
        "// MARK: Jerkgram v1.2G BUILD118_DATA_BACKUP_UI1",
        "// MARK: Jerkgram v1.2G BUILD118_DATA_BACKUP_UI1\n// MARK: Jerkgram v1.2H BUILD119_DATA_SUMMARY1",
        1,
    )
    text = replace_once(
        text,
        "    case header(Int32, String)\n    case action(Int32, Int32, String, String, String)\n",
        "    case header(Int32, String)\n    case summary(Int32, Int32, String, String)\n    case action(Int32, Int32, String, String, String)\n",
        "Data summary case",
    )
    text = replace_once(
        text,
        "        case let .header(section, _), let .action(section, _, _, _, _), let .toggle(section, _, _, _, _), let .info(section, _): return section\n",
        "        case let .header(section, _), let .summary(section, _, _, _), let .action(section, _, _, _, _), let .toggle(section, _, _, _, _), let .info(section, _): return section\n",
        "Data summary section",
    )
    text = replace_once(
        text,
        '''        case let .header(section, _): return section * 1000
        case let .action(section, index, _, _, _), let .toggle(section, index, _, _, _): return section * 1000 + index
''',
        '''        case let .header(section, _): return section * 1000
        case let .summary(section, index, _, _): return section * 1000 + index
        case let .action(section, index, _, _, _), let .toggle(section, index, _, _, _): return section * 1000 + index
''',
        "Data summary stable id",
    )
    text = replace_once(
        text,
        '''        case let .action(_, _, title, value, action):
            return ItemListDisclosureItem(''',
        '''        case let .summary(_, _, title, value):
            return ItemListDisclosureItem(
                presentationData: presentationData, systemStyle: .glass,
                title: title, label: value, labelStyle: .text,
                sectionId: self.section, style: .blocks,
                disclosureStyle: .none, action: nil
            )
        case let .action(_, _, title, value, action):
            return ItemListDisclosureItem(''',
        "Data summary renderer",
    )

    replacement = '''private func jerkgramDataEntries(state: JerkgramDataUIState, strings: JerkgramStrings) -> [JerkgramDataUIEntry] {
    let policy = state.configuration.accountPolicy
    let summary = strings.build119DataSummary(
        jerkgramDurationTitle(policy.historyDuration, strings: strings),
        jerkgramMediaLimitTitle(policy.mediaByteLimit, strings: strings),
        state.configuration.accountPeerId
    )
    var entries: [JerkgramDataUIEntry] = [
        .summary(0, 1, strings.dataAndBackup, summary),
        .header(1, strings.retentionRules),
        .action(1, 1, strings.historyDuration, jerkgramDurationTitle(policy.historyDuration, strings: strings), "duration"),
        .action(1, 2, strings.recoveredMediaLimit, jerkgramMediaLimitTitle(policy.mediaByteLimit, strings: strings), "media"),
        .toggle(1, 3, strings.archiveSecretChats, "secretChats", policy.archiveSecretChats),
        .action(1, 4, strings.perChatRules, "", "perChat"),
        .action(1, 5, strings.cleanupExpired, "", "cleanup"),
    ]
    if policy.historyDuration == .forever && policy.mediaByteLimit == .unlimited {
        entries.append(.info(1, strings.foreverUnlimitedWarning + " (Forever + Unlimited)"))
    }
    entries.append(contentsOf: [
        .header(2, strings.backup),
        .action(2, 1, strings.exportArchive, "Build119", "export"),
        .action(2, 2, strings.importArchive, "Archive v2", "import"),
        .info(2, strings.backupAccountHint(state.configuration.accountPeerId)),
    ])
    return entries
}'''
    return replace_block(text, "private func jerkgramDataEntries(", replacement)


def patch_time_machine(text):
    require("BUILD118_TIME_MACHINE_UI1" in text, "Build118 Time Machine prerequisite missing")
    require("BUILD119_TIME_MACHINE_SUMMARY1" not in text, "Build119 Time Machine summary already applied")
    text = text.replace(
        "// MARK: Jerkgram v1.2G BUILD118_TIME_MACHINE_UI1",
        "// MARK: Jerkgram v1.2G BUILD118_TIME_MACHINE_UI1\n// MARK: Jerkgram v1.2H BUILD119_TIME_MACHINE_SUMMARY1",
        1,
    )
    text = replace_once(
        text,
        "    case header(Int32, String)\n    case filter(Int32, Int32, String, String, JerkgramEventKind?)\n",
        "    case header(Int32, String)\n    case summary(Int32, Int32, String, String)\n    case filter(Int32, Int32, String, String, JerkgramEventKind?)\n",
        "Time Machine summary case",
    )
    text = replace_once(
        text,
        "        case let .header(section, _), let .filter(section, _, _, _, _), let .result(section, _, _, _, _), let .info(section, _), let .loadMore(section, _): return section\n",
        "        case let .header(section, _), let .summary(section, _, _, _), let .filter(section, _, _, _, _), let .result(section, _, _, _, _), let .info(section, _), let .loadMore(section, _): return section\n",
        "Time Machine summary section",
    )
    text = replace_once(
        text,
        '''        case let .header(section, _): return section * 1000
        case let .filter(section, index, _, _, _), let .result(section, index, _, _, _): return section * 1000 + index
''',
        '''        case let .header(section, _): return section * 1000
        case let .summary(section, index, _, _): return section * 1000 + index
        case let .filter(section, index, _, _, _), let .result(section, index, _, _, _): return section * 1000 + index
''',
        "Time Machine summary stable id",
    )
    text = replace_once(
        text,
        '''        case let .filter(_, _, title, value, kind):
            return ItemListDisclosureItem(''',
        '''        case let .summary(_, _, title, value):
            return ItemListDisclosureItem(
                presentationData: presentationData, systemStyle: .glass,
                title: title, label: value, labelStyle: .text,
                sectionId: self.section, style: .blocks,
                disclosureStyle: .none, action: nil
            )
        case let .filter(_, _, title, value, kind):
            return ItemListDisclosureItem(''',
        "Time Machine summary renderer",
    )
    old_entries = '''        var entries: [JerkgramTimeMachineUIEntry] = [
            .header(0, strings.timeMachineFilters),
            .filter(0, 1, strings.timeMachineDeleted, state.kinds.contains(.deletedMessage) ? "✓" : "", .deletedMessage),
            .filter(0, 2, strings.timeMachineEdited, state.kinds.contains(.editedMessage) ? "✓" : "", .editedMessage),
            .filter(0, 3, strings.timeMachineMedia, state.kinds.contains(.recoveredMedia) ? "✓" : "", .recoveredMedia),
            .filter(0, 4, strings.timeMachineAuthor, state.senderPeerId.map(String.init) ?? strings.timeMachineAllAuthors, nil),
            .header(1, strings.timeMachineResults),
        ]
        for (index, event) in results.enumerated() {
            let text = event.payload.text ?? event.payload.previousText ?? event.eventId.rawValue
            entries.append(.result(1, Int32(index + 1), String(text.prefix(80)), jerkgramEventKindTitle(event.kind, strings: strings), event))
        }
        if results.isEmpty { entries.append(.info(1, strings.timeMachineEmpty)) }
        if page.hasMore { entries.append(.loadMore(1, strings.timeMachineLoadMore)) }'''
    new_entries = '''        var entries: [JerkgramTimeMachineUIEntry] = [
            .summary(
                0, 1,
                strings.timeMachine,
                strings.build119TimeMachineSummary(
                    results.count,
                    state.kinds.count,
                    state.senderPeerId != nil
                )
            ),
            .header(1, strings.timeMachineFilters),
            .filter(1, 1, strings.timeMachineDeleted, state.kinds.contains(.deletedMessage) ? "✓" : "", .deletedMessage),
            .filter(1, 2, strings.timeMachineEdited, state.kinds.contains(.editedMessage) ? "✓" : "", .editedMessage),
            .filter(1, 3, strings.timeMachineMedia, state.kinds.contains(.recoveredMedia) ? "✓" : "", .recoveredMedia),
            .filter(1, 4, strings.timeMachineAuthor, state.senderPeerId.map(String.init) ?? strings.timeMachineAllAuthors, nil),
            .header(2, strings.timeMachineResults),
        ]
        for (index, event) in results.enumerated() {
            let text = event.payload.text ?? event.payload.previousText ?? event.eventId.rawValue
            entries.append(.result(2, Int32(index + 1), String(text.prefix(80)), jerkgramEventKindTitle(event.kind, strings: strings), event))
        }
        if results.isEmpty { entries.append(.info(2, strings.timeMachineEmpty)) }
        if page.hasMore { entries.append(.loadMore(2, strings.timeMachineLoadMore)) }'''
    return replace_once(text, old_entries, new_entries, "Time Machine entries")


def main():
    for path in (SETTINGS, STRINGS, DATA, TIME_MACHINE):
        require(path.is_file(), "missing target: " + str(path))

    settings = patch_settings(SETTINGS.read_text(encoding="utf-8"))
    strings = patch_strings(STRINGS.read_text(encoding="utf-8"))
    data = patch_data(DATA.read_text(encoding="utf-8"))
    time_machine = patch_time_machine(TIME_MACHINE.read_text(encoding="utf-8"))

    SETTINGS.write_text(settings, encoding="utf-8")
    STRINGS.write_text(strings, encoding="utf-8")
    DATA.write_text(data, encoding="utf-8")
    TIME_MACHINE.write_text(time_machine, encoding="utf-8")

    print("[Build119 hybrid UI] Jerkgram Settings, Stars, Data and Time Machine visual layer installed")


if __name__ == "__main__":
    main()
