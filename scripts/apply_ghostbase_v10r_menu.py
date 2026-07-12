#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"

SETTINGS = (
    SRC
    / "submodules/SettingsUI/Sources/GhostBase"
    / "GhostBaseSettingsController.swift"
)

ASSETS = ROOT / "scripts/apply_ghostbase_v10r_assets.py"

MARKER = "// MARK: GhostBase v1.0R Settings Split"


def require(value, message):
    if not value:
        raise RuntimeError(f"[v1.0R MENU] {message}")


def replace_once(text, old, new, label):
    if new in text:
        return text

    require(old in text, f"missing anchor: {label}")
    return text.replace(old, new, 1)


require(SETTINGS.is_file(), f"missing settings: {SETTINGS}")
require(ASSETS.is_file(), f"missing assets patcher: {ASSETS}")

runpy.run_path(str(ASSETS), run_name="__main__")

source = SETTINGS.read_text(encoding="utf-8")

page_enum = r'''
// MARK: GhostBase v1.0R Settings Split
private enum GhostBaseSettingsPage: Equatable {
    case root
    case home
    case ghostMode
    case messages
    case protectedContent
    case mediaStories
    case appearance
    case debugResearch
    case about

    var title: String {
        switch self {
        case .root:
            return "GhostBase"
        case .home:
            return "Основные функции"
        case .ghostMode:
            return "Ghost Mode"
        case .messages:
            return "Сообщения"
        case .protectedContent:
            return "Защищённый контент"
        case .mediaStories:
            return "Медиа и истории"
        case .appearance:
            return "Внешний вид"
        case .debugResearch:
            return "Debug / Research"
        case .about:
            return "О клиенте"
        }
    }
}

'''

if MARKER not in source:
    anchor = "private final class GhostBaseSettingsArguments {"
    require(anchor in source, "arguments class anchor")

    source = source.replace(
        anchor,
        page_enum + anchor,
        1
    )

old_arguments = '''private final class GhostBaseSettingsArguments {
    let updateBool: (String, Bool) -> Void

    init(updateBool: @escaping (String, Bool) -> Void) {
        self.updateBool = updateBool
    }
}'''

new_arguments = '''private final class GhostBaseSettingsArguments {
    let updateBool: (String, Bool) -> Void
    let openPage: (GhostBaseSettingsPage) -> Void

    init(
        updateBool: @escaping (String, Bool) -> Void,
        openPage: @escaping (GhostBaseSettingsPage) -> Void
    ) {
        self.updateBool = updateBool
        self.openPage = openPage
    }
}'''

source = replace_once(
    source,
    old_arguments,
    new_arguments,
    "settings arguments"
)

source = replace_once(
    source,
    '''    case input(Int32, Int32, String, String, String)
    case info(Int32, String)''',
    '''    case input(Int32, Int32, String, String, String)
    case disclosure(Int32, Int32, String, String, GhostBaseSettingsPage)
    case info(Int32, String)''',
    "disclosure enum case"
)

source = replace_once(
    source,
    '''        case let .input(section, _, _, _, _):
            return section
        case let .info(section, _):
            return section''',
    '''        case let .input(section, _, _, _, _):
            return section
        case let .disclosure(section, _, _, _, _):
            return section
        case let .info(section, _):
            return section''',
    "disclosure section"
)

source = replace_once(
    source,
    '''        case let .input(section, index, _, _, _):
            return section * 1000 + index
        case let .info(section, _):
            return section * 1000 + 999''',
    '''        case let .input(section, index, _, _, _):
            return section * 1000 + index
        case let .disclosure(section, index, _, _, _):
            return section * 1000 + index
        case let .info(section, _):
            return section * 1000 + 999''',
    "disclosure stable id"
)

source = replace_once(
    source,
    '''        case let .info(ls, lt):
            if case let .info(rs, rt) = rhs {
                return ls == rs && lt == rt
            }
            return false''',
    '''        case let .disclosure(ls, li, lt, lIcon, lPage):
            if case let .disclosure(rs, ri, rt, rIcon, rPage) = rhs {
                return ls == rs
                    && li == ri
                    && lt == rt
                    && lIcon == rIcon
                    && lPage.title == rPage.title
            }
            return false
        case let .info(ls, lt):
            if case let .info(rs, rt) = rhs {
                return ls == rs && lt == rt
            }
            return false''',
    "disclosure equality"
)

source = replace_once(
    source,
    '''        case let .info(_, text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)''',
    '''        case let .disclosure(_, _, title, iconName, page):
            return ItemListDisclosureItem(
                presentationData: presentationData,
                systemStyle: .glass,
                icon: UIImage(bundleImageName: iconName),
                title: title,
                label: "",
                labelStyle: .text,
                sectionId: self.section,
                style: .blocks,
                disclosureStyle: .arrow,
                action: {
                    arguments.openPage(page)
                }
            )

        case let .info(_, text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)''',
    "disclosure item"
)

source = replace_once(
    source,
    '''private func ghostBaseSettingsEntries(state: GhostBaseSettingsState, context: AccountContext) -> [GhostBaseSettingsEntry] {''',
    '''private func ghostBaseSettingsEntries(
    state: GhostBaseSettingsState,
    context: AccountContext,
    page: GhostBaseSettingsPage
) -> [GhostBaseSettingsEntry] {''',
    "entries page argument"
)

entries_anchor = '''    let footer = GhostBaseSettingsSection.footer.rawValue
'''

entries_block = r'''    let footer = GhostBaseSettingsSection.footer.rawValue

    if page == .root {
        return [
            .disclosure(0, 1, "Основные функции", "GhostBaseHome", .home),
            .disclosure(0, 2, "Ghost Mode", "GhostBaseGhostMode", .ghostMode),
            .disclosure(0, 3, "Сообщения", "GhostBaseMessages", .messages),
            .disclosure(0, 4, "Защищённый контент", "GhostBaseProtectedContent", .protectedContent),
            .disclosure(0, 5, "Медиа и истории", "GhostBaseMediaStories", .mediaStories),
            .disclosure(0, 6, "Внешний вид", "GhostBaseAppearance", .appearance),
            .disclosure(0, 7, "Debug / Research", "GhostBaseDebugResearch", .debugResearch),
            .disclosure(0, 8, "О клиенте", "GhostBaseAbout", .about)
        ]
    }

    if page == .home {
        let balance = state.localStarsAmount.isEmpty
            ? "0"
            : state.localStarsAmount

        return [
            .header(0, "Основные функции"),
            .toggle(0, 1, GhostBaseKey.profileEnabled, "Карточка профиля", state.profileEnabled),
            .toggle(0, 2, GhostBaseKey.showIds, "Показывать ID", state.showIds),
            .toggle(0, 3, GhostBaseKey.showDCs, "Показывать DC", state.showDCs),
            .toggle(0, 4, GhostBaseKey.showRegistration, "Дата регистрации", state.showRegistration),
            .toggle(0, 5, GhostBaseKey.localStarsEnabled, "Локальный баланс Stars", state.localStarsEnabled),
            .input(0, 6, GhostBaseKey.localStarsAmount, "Баланс Stars", state.localStarsAmount),
            .info(0, "Текущий визуальный баланс: \(balance) ⭐")
        ]
    }

    if page == .ghostMode {
        return [
            .header(0, "Ghost Mode"),
            .toggle(0, 1, GhostBaseKey.readMessages, "Read Ghost", state.readMessages),
            .toggle(0, 2, GhostBaseKey.typingActions, "Скрыть набор текста", state.typingActions),
            .toggle(0, 3, GhostBaseKey.recordingActions, "Скрыть запись", state.recordingActions),
            .toggle(0, 4, GhostBaseKey.uploadingActions, "Скрыть загрузку", state.uploadingActions),
            .toggle(0, 5, GhostBaseKey.stickerActivity, "Скрыть выбор стикера", state.stickerActivity),
            .toggle(0, 6, GhostBaseKey.gameActivity, "Скрыть игровую активность", state.gameActivity),
            .toggle(0, 7, GhostBaseKey.emojiActivity, "Скрыть выбор эмодзи", state.emojiActivity),
            .toggle(0, 8, GhostBaseKey.presence, "Скрыть онлайн", state.presence)
        ]
    }

    if page == .messages {
        return [
            .header(0, "Сообщения"),
            .toggle(0, 1, GhostBaseKey.scheduledSend, "Отложенная отправка", state.scheduledSend),
            .info(0, "История редактирования и сохранение удалённых сообщений доступны через меню сообщения.")
        ]
    }

    if page == .protectedContent {
        return [
            .header(0, "Защищённый контент"),
            .toggle(0, 1, GhostBaseKey.protectedEnabled, "Включить обход защиты", state.protectedEnabled),
            .toggle(0, 2, GhostBaseKey.protectedGalleryShare, "Поделиться из галереи", state.protectedGalleryShare),
            .toggle(0, 3, GhostBaseKey.protectedGallerySave, "Сохранить из галереи", state.protectedGallerySave),
            .toggle(0, 4, GhostBaseKey.protectedGalleryCopy, "Копировать из галереи", state.protectedGalleryCopy),
            .toggle(0, 5, GhostBaseKey.chatSave, "Сохранить из чата", state.chatSave),
            .toggle(0, 6, GhostBaseKey.chatCopy, "Копировать из чата", state.chatCopy),
            .toggle(0, 7, GhostBaseKey.chatForward, "Переслать из чата", state.chatForward),
            .toggle(0, 8, GhostBaseKey.allowScreenshots, "Разрешить скриншоты", state.allowScreenshots),
            .toggle(0, 9, GhostBaseKey.allowScreenRecording, "Разрешить запись экрана", state.allowScreenRecording)
        ]
    }

    if page == .mediaStories {
        return [
            .header(0, "Медиа и истории"),
            .toggle(0, 1, GhostBaseKey.oneTimeScreenshots, "Скриншоты одноразовых медиа", state.oneTimeScreenshots),
            .toggle(0, 2, GhostBaseKey.oneTimeScreenRecording, "Запись одноразовых медиа", state.oneTimeScreenRecording),
            .toggle(0, 3, GhostBaseKey.oneTimeSave, "Сохранение одноразовых медиа", state.oneTimeSave),
            .toggle(0, 4, GhostBaseKey.storySave, "Сохранение историй", state.storySave)
        ]
    }

    if page == .appearance {
        return [
            .header(0, "Внешний вид"),
            .info(0, "Настройки оформления GhostBase будут добавляться в этот раздел.")
        ]
    }

    if page == .about {
        let bundleId = Bundle.main.bundleIdentifier ?? "unknown"

        return [
            .header(0, "О клиенте"),
            .info(0, """
GhostBase
Base: Official Telegram 12.8
Version: v1.0R
Bundle ID: \(bundleId)
""")
        ]
    }
'''

if "if page == .root {" not in source:
    require(entries_anchor in source, "entries insertion anchor")

    source = source.replace(
        entries_anchor,
        entries_block,
        1
    )

start = source.index(
    "private func ghostBaseSettingsEntries("
)

brace = source.index("{", start)
depth = 0
end = None

for index in range(brace, len(source)):
    char = source[index]

    if char == "{":
        depth += 1
    elif char == "}":
        depth -= 1

        if depth == 0:
            end = index
            break

require(end is not None, "entries function closing brace")

entries_function = source[start:end + 1]

old_return = "    return entries\n}"

new_return = '''    if page == .debugResearch {
        return entries.filter {
            $0.section == debug
        }
    }

    return entries
}'''

if new_return not in entries_function:
    require(
        old_return in entries_function,
        "entries final return"
    )

    entries_function = entries_function.replace(
        old_return,
        new_return,
        1
    )

    source = (
        source[:start]
        + entries_function
        + source[end + 1:]
    )

old_controller = '''public func ghostBaseSettingsController(context: AccountContext) -> ViewController {'''

new_controller = '''public func ghostBaseSettingsController(
    context: AccountContext
) -> ViewController {
    let rawPage = UserDefaults.standard.string(
        forKey: "GhostBase.Settings.InitialPage"
    ) ?? "home"

    UserDefaults.standard.removeObject(
        forKey: "GhostBase.Settings.InitialPage"
    )

    let page: GhostBaseSettingsPage

    switch rawPage {
    case "ghostMode":
        page = .ghostMode
    case "messages":
        page = .messages
    case "protectedContent":
        page = .protectedContent
    case "mediaStories":
        page = .mediaStories
    case "appearance":
        page = .appearance
    case "debugResearch":
        page = .debugResearch
    case "about":
        page = .about
    default:
        page = .home
    }

    return ghostBaseSettingsPageController(
        context: context,
        page: page
    )
}

private func ghostBaseSettingsPageController(
    context: AccountContext,
    page: GhostBaseSettingsPage
) -> ViewController {'''

intermediate_controller = """public func ghostBaseSettingsController(
    context: AccountContext
) -> ViewController {
    return ghostBaseSettingsPageController(
        context: context,
        page: .root
    )
}

private func ghostBaseSettingsPageController(
    context: AccountContext,
    page: GhostBaseSettingsPage
) -> ViewController {"""

if new_controller not in source:
    if intermediate_controller in source:
        source = source.replace(
            intermediate_controller,
            new_controller,
            1
        )
    else:
        source = replace_once(
            source,
            old_controller,
            new_controller,
            "root controller wrapper"
        )

arguments_anchor = '''    let arguments = GhostBaseSettingsArguments(updateBool: { key, value in'''

if "var pushController: ((ViewController) -> Void)?" not in source:
    require(arguments_anchor in source, "arguments creation")

    source = source.replace(
        arguments_anchor,
        '''    var pushController: ((ViewController) -> Void)?

    let arguments = GhostBaseSettingsArguments(updateBool: { key, value in''',
        1
    )

arguments_start = source.index(
    "    let arguments = GhostBaseSettingsArguments(updateBool:"
)

signal_start = source.index(
    "\n\n    let signal = combineLatest",
    arguments_start
)

arguments_segment = source[
    arguments_start:signal_start
]

if "openPage: { selectedPage in" not in arguments_segment:
    close_index = arguments_segment.rfind("    })")

    require(
        close_index >= 0,
        "arguments closing anchor"
    )

    arguments_segment = (
        arguments_segment[:close_index]
        + '''    }, openPage: { selectedPage in
        pushController?(
            ghostBaseSettingsPageController(
                context: context,
                page: selectedPage
            )
        )
    })'''
        + arguments_segment[close_index + len("    })"):]
    )

    source = (
        source[:arguments_start]
        + arguments_segment
        + source[signal_start:]
    )

source = replace_once(
    source,
    '''entries: ghostBaseSettingsEntries(state: state, context: context),''',
    '''entries: ghostBaseSettingsEntries(
                state: state,
                context: context,
                page: page
            ),''',
    "entries controller call"
)

source = replace_once(
    source,
    '''title: .text("GhostBase"),''',
    '''title: .text(page.title),''',
    "page title"
)

source = replace_once(
    source,
    '''    return ItemListController(context: context, state: signal)
}''',
    '''    let controller = ItemListController(
        context: context,
        state: signal
    )

    pushController = { [weak controller] target in
        controller?.push(target)
    }

    return controller
}''',
    "controller navigation"
)

SETTINGS.write_text(
    source,
    encoding="utf-8"
)

result = SETTINGS.read_text(encoding="utf-8")

for needle in (
    MARKER,
    "GhostBaseHome",
    "GhostBaseGhostMode",
    "GhostBaseMessages",
    "GhostBaseProtectedContent",
    "GhostBaseMediaStories",
    "GhostBaseAppearance",
    "GhostBaseDebugResearch",
    "GhostBaseAbout",
    "ghostBaseSettingsPageController",
):
    require(needle in result, f"proof missing: {needle}")

print("[v1.0R MENU] 8-section settings split OK")

# MARK: GhostBase v1.0R Main Settings Group

import re

MAIN_ITEMS = (
    SRC
    / "submodules"
    / "TelegramUI"
    / "Components"
    / "PeerInfo"
    / "PeerInfoScreen"
    / "Sources"
    / "PeerInfoSettingsItems.swift"
)

MAIN_MARKER = (
    "// MARK: GhostBase v1.0R Main Settings Group"
)

require(
    MAIN_ITEMS.is_file(),
    f"missing main settings source: {MAIN_ITEMS}"
)

items_source = MAIN_ITEMS.read_text(
    encoding="utf-8"
)

if MAIN_MARKER not in items_source:
    action_needle = (
        "interaction.openSettings(.ghostbase)"
    )

    action_index = items_source.find(
        action_needle
    )

    require(
        action_index >= 0,
        "existing GhostBase main-settings row not found"
    )

    append_start = items_source.rfind(
        "items[.",
        0,
        action_index
    )

    require(
        append_start >= 0,
        "GhostBase append start not found"
    )

    line_start = (
        items_source.rfind(
            "\n",
            0,
            append_start
        )
        + 1
    )

    indent = items_source[
        line_start:append_start
    ]

    section_match = re.search(
        r"items\[\.(\w+)\]",
        items_source[
            append_start:action_index
        ]
    )

    require(
        section_match is not None,
        "GhostBase settings section not found"
    )

    section = section_match.group(1)

    open_index = items_source.find(
        "(",
        append_start
    )

    require(
        open_index >= 0,
        "GhostBase append opening bracket not found"
    )

    depth = 0
    append_end = None

    for index in range(
        open_index,
        len(items_source)
    ):
        character = items_source[index]

        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1

            if depth == 0:
                append_end = index + 1
                break

    require(
        append_end is not None,
        "GhostBase append closing bracket not found"
    )

    rows = [
        (
            0,
            "GhostBase",
            "GhostBaseHome",
            "home",
        ),
        (
            1,
            "Ghost Mode",
            "GhostBaseGhostMode",
            "ghostMode",
        ),
        (
            2,
            "Messages",
            "GhostBaseMessages",
            "messages",
        ),
        (
            3,
            "Protected Content",
            "GhostBaseProtectedContent",
            "protectedContent",
        ),
        (
            4,
            "Media & Stories",
            "GhostBaseMediaStories",
            "mediaStories",
        ),
        (
            5,
            "Appearance",
            "GhostBaseAppearance",
            "appearance",
        ),
        (
            6,
            "Debug / Research",
            "GhostBaseDebugResearch",
            "debugResearch",
        ),
        (
            7,
            "About",
            "GhostBaseAbout",
            "about",
        ),
    ]

    generated = [MAIN_MARKER]

    for item_id, title, icon, page in rows:
        generated.append(
            f'''items[.{section}]!.append(
    PeerInfoScreenDisclosureItem(
        id: {item_id},
        text: "{title}",
        icon: UIImage(
            bundleImageName: "{icon}"
        ),
        action: {{
            UserDefaults.standard.set(
                "{page}",
                forKey: "GhostBase.Settings.InitialPage"
            )
            interaction.openSettings(.ghostbase)
        }}
    )
)'''
        )

    replacement = (
        "\n" + indent
    ).join(generated)

    items_source = (
        items_source[:append_start]
        + replacement
        + items_source[append_end:]
    )

    MAIN_ITEMS.write_text(
        items_source,
        encoding="utf-8"
    )

result_items = MAIN_ITEMS.read_text(
    encoding="utf-8"
)

for required_icon in (
    "GhostBaseHome",
    "GhostBaseGhostMode",
    "GhostBaseMessages",
    "GhostBaseProtectedContent",
    "GhostBaseMediaStories",
    "GhostBaseAppearance",
    "GhostBaseDebugResearch",
    "GhostBaseAbout",
):
    require(
        required_icon in result_items,
        f"main row missing: {required_icon}"
    )

require(
    result_items.count(
        "GhostBase.Settings.InitialPage"
    ) >= 8,
    "not all main settings actions were added"
)

print(
    "[v1.0R MENU] main Telegram settings group: 8 rows OK"
)
