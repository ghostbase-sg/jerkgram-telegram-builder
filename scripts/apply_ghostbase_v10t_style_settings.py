#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = (
    ROOT
    / "work/swiftgram-src/submodules/SettingsUI/Sources/GhostBase"
    / "GhostBaseSettingsController.swift"
)

def require(value, message):
    if not value:
        raise RuntimeError(f"[v1.0T-style] {message}")

def replace_once(text, old, new, label):
    require(old in text, f"missing anchor: {label}")
    return text.replace(old, new, 1)

require(FILE.is_file(), f"missing source: {FILE}")
text = FILE.read_text(encoding="utf-8")

state_marker = "GhostBase v1.0T send style state"

if state_marker not in text:
    text = replace_once(
        text,
        "struct GhostBaseSettingsState: Equatable {\n",
        '''// MARK: GhostBase v1.0T send style state
private let ghostBaseSendTextStyleKey =
    "GhostBase.Messages.SendTextStyle"

private enum GhostBaseSettingsEntryTag:
    Equatable, ItemListItemTag
{
    case sendTextStyle

    func isEqual(to other: ItemListItemTag) -> Bool {
        guard let other = other as? GhostBaseSettingsEntryTag else {
            return false
        }
        return self == other
    }
}

struct GhostBaseSettingsState: Equatable {
''',
        "state marker"
    )

    text = replace_once(
        text,
        '''    var saveEditHistory: Bool
    var showEditHistory: Bool

    var protectedEnabled: Bool
''',
        '''    var saveEditHistory: Bool
    var showEditHistory: Bool
    var sendTextStyle: String

    var protectedEnabled: Bool
''',
        "state property"
    )

    text = replace_once(
        text,
        '''            saveEditHistory: ghostBaseBool(GhostBaseKey.saveEditHistory, defaultValue: true),
            showEditHistory: ghostBaseBool(GhostBaseKey.showEditHistory, defaultValue: true),

            protectedEnabled: ghostBaseBool(GhostBaseKey.protectedEnabled, defaultValue: true),
''',
        '''            saveEditHistory: ghostBaseBool(GhostBaseKey.saveEditHistory, defaultValue: true),
            showEditHistory: ghostBaseBool(GhostBaseKey.showEditHistory, defaultValue: true),
            sendTextStyle: ghostBaseString(
                ghostBaseSendTextStyleKey,
                defaultValue: "normal"
            ),

            protectedEnabled: ghostBaseBool(GhostBaseKey.protectedEnabled, defaultValue: true),
''',
        "state load"
    )

    text = replace_once(
        text,
        '''        UserDefaults.standard.set(self.saveEditHistory, forKey: GhostBaseKey.saveEditHistory)
        UserDefaults.standard.set(self.showEditHistory, forKey: GhostBaseKey.showEditHistory)

        UserDefaults.standard.set(self.protectedEnabled, forKey: GhostBaseKey.protectedEnabled)
''',
        '''        UserDefaults.standard.set(self.saveEditHistory, forKey: GhostBaseKey.saveEditHistory)
        UserDefaults.standard.set(self.showEditHistory, forKey: GhostBaseKey.showEditHistory)
        UserDefaults.standard.set(
            self.sendTextStyle,
            forKey: ghostBaseSendTextStyleKey
        )

        UserDefaults.standard.set(self.protectedEnabled, forKey: GhostBaseKey.protectedEnabled)
''',
        "state save"
    )

row_marker = "GhostBase v1.0T send style row"

if row_marker not in text:
    text = replace_once(
        text,
        '''private final class GhostBaseSettingsArguments {
    let updateBool: (String, Bool) -> Void
    let openPage: (GhostBaseSettingsPage) -> Void

    init(
        updateBool: @escaping (String, Bool) -> Void,
        openPage: @escaping (GhostBaseSettingsPage) -> Void
    ) {
        self.updateBool = updateBool
        self.openPage = openPage
    }
}
''',
        '''// MARK: GhostBase v1.0T send style row
private final class GhostBaseSettingsArguments {
    let updateBool: (String, Bool) -> Void
    let openPage: (GhostBaseSettingsPage) -> Void
    let openSendTextStyle: () -> Void

    init(
        updateBool: @escaping (String, Bool) -> Void,
        openPage: @escaping (GhostBaseSettingsPage) -> Void,
        openSendTextStyle: @escaping () -> Void
    ) {
        self.updateBool = updateBool
        self.openPage = openPage
        self.openSendTextStyle = openSendTextStyle
    }
}
''',
        "arguments"
    )

    text = replace_once(
        text,
        '''    case disclosure(Int32, Int32, String, String, GhostBaseSettingsPage)
    case info(Int32, String)
''',
        '''    case disclosure(Int32, Int32, String, String, GhostBaseSettingsPage)
    case selector(Int32, Int32, String, String)
    case info(Int32, String)
''',
        "selector case"
    )

    text = replace_once(
        text,
        '''        case let .disclosure(section, _, _, _, _):
            return section
        case let .info(section, _):
''',
        '''        case let .disclosure(section, _, _, _, _):
            return section
        case let .selector(section, _, _, _):
            return section
        case let .info(section, _):
''',
        "selector section"
    )

    text = replace_once(
        text,
        '''        case let .disclosure(section, index, _, _, _):
            return section * 1000 + index
        case let .info(section, _):
''',
        '''        case let .disclosure(section, index, _, _, _):
            return section * 1000 + index
        case let .selector(section, index, _, _):
            return section * 1000 + index
        case let .info(section, _):
''',
        "selector stable id"
    )

if row_marker not in text:
    raise RuntimeError("[v1.0T-style] row marker was not installed")

if "case let .selector(ls, li, lt, lv):" not in text:
    text = replace_once(
        text,
        '''            return false
        case let .info(ls, lt):
''',
        '''            return false
        case let .selector(ls, li, lt, lv):
            if case let .selector(rs, ri, rt, rv) = rhs {
                return ls == rs && li == ri
                    && lt == rt && lv == rv
            }
            return false
        case let .info(ls, lt):
''',
        "selector equality"
    )

    text = replace_once(
        text,
        '''        case let .info(_, text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)
''',
        '''        case let .selector(_, _, title, value):
            return ItemListDisclosureItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: title,
                label: value,
                labelStyle: .text,
                sectionId: self.section,
                style: .blocks,
                disclosureStyle: .arrow,
                action: {
                    arguments.openSendTextStyle()
                },
                tag: GhostBaseSettingsEntryTag.sendTextStyle
            )

        case let .info(_, text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)
''',
        "selector item"
    )

    text = replace_once(
        text,
        '''            .info(1, "Выключение функций не удаляет уже сохранённые данные.")
''',
        '''            .info(1, "Выключение функций не удаляет уже сохранённые данные."),

            .header(2, "Отправка текста"),
            .selector(
                2,
                5,
                "Стиль отправки",
                state.sendTextStyle
            ),
            .info(
                2,
                "Стиль применяется после нажатия кнопки отправки."
            )
''',
        "messages selector"
    )

if "var openSendTextStyleImpl: (() -> Void)?" not in text:
    text = replace_once(
        text,
        '''    let arguments = GhostBaseSettingsArguments(updateBool: { key, value in
''',
        '''    var openSendTextStyleImpl: (() -> Void)?

    let arguments = GhostBaseSettingsArguments(updateBool: { key, value in
''',
        "menu callback variable"
    )

    text = replace_once(
        text,
        '''    }, openPage: { selectedPage in
        pushController?(
            ghostBaseSettingsPageController(
                context: context,
                page: selectedPage
            )
        )
    })

    let signal = combineLatest(context.sharedContext.presentationData, statePromise.get())
''',
        '''    }, openPage: { selectedPage in
        pushController?(
            ghostBaseSettingsPageController(
                context: context,
                page: selectedPage
            )
        )
    }, openSendTextStyle: {
        openSendTextStyleImpl?()
    })

    let signal = combineLatest(context.sharedContext.presentationData, statePromise.get())
''',
        "menu callback wiring"
    )

FILE.write_text(text, encoding="utf-8")

require(state_marker in text, "state marker missing")
require(row_marker in text, "row marker missing")

print("[v1.0T-style] settings model and row applied")
