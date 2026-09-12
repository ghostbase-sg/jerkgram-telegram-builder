#!/usr/bin/env python3
from pathlib import Path
import os
import re

ROOT = Path(os.environ.get('JERKGRAM_SOURCE_ROOT', os.environ.get('GHOSTBASE_SOURCE_ROOT', str(Path.cwd())))).resolve()
FETCH = ROOT / 'submodules/TelegramCore/Sources/Network/FetchV2.swift'
SETTINGS = ROOT / 'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift'
STRINGS = ROOT / 'submodules/TelegramPresentationData/Sources/JerkgramStrings.swift'

KEY = 'jerkgram.global.DownloadBoost'
FETCH_MARKER = '// MARK: Jerkgram Build140 Download Boost1'
SETTINGS_MARKER = '// MARK: Jerkgram Build140 Download Boost Settings1'
STRINGS_MARKER = '// MARK: Jerkgram Build140 Download Boost Strings1'


def require(value, message):
    if not value:
        raise RuntimeError('[Build140 Download Boost] ' + message)


def replace_once(text, old, new, label):
    count = text.count(old)
    require(count == 1, f'{label}: expected one anchor, found {count}')
    return text.replace(old, new, 1)


def block_bounds(text, signature):
    start = text.find(signature)
    require(start >= 0, 'block missing: ' + signature)
    brace = text.find('{', start)
    require(brace >= 0, 'opening brace missing: ' + signature)
    depth = 0
    in_string = False
    escaped = False
    for index in range(brace, len(text)):
        ch = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return start, index + 1
    raise RuntimeError('[Build140 Download Boost] unbalanced block: ' + signature)


FETCH_HELPER = f'''{FETCH_MARKER}
private let jerkgramDownloadBoostKey = "{KEY}"

private func jerkgramDownloadBoostMode() -> String {{
    return UserDefaults.standard.string(forKey: jerkgramDownloadBoostKey) ?? "off"
}}

private func jerkgramDownloadPartSize(_ defaultPartSize: Int64, fileSize: Int64?) -> Int64 {{
    guard let fileSize, fileSize > 1 * 1024 * 1024 else {{
        return defaultPartSize
    }}
    switch jerkgramDownloadBoostMode() {{
    case "medium":
        return 512 * 1024
    case "maximum":
        return 1024 * 1024
    default:
        return defaultPartSize
    }}
}}

private func jerkgramDownloadMaxPendingParts(_ defaultValue: Int) -> Int {{
    switch jerkgramDownloadBoostMode() {{
    case "medium":
        return 8
    case "maximum":
        return 12
    default:
        return defaultValue
    }}
}}

'''


def patch_fetch_v2(text):
    if FETCH_MARKER in text:
        require(text.count(FETCH_MARKER) == 1, 'Fetch marker count')
        return text
    require('import Foundation' in text, 'FetchV2 Foundation import missing')
    anchor = 'private let possiblePartLengths:'
    idx = text.find(anchor)
    require(idx >= 0, 'FetchV2 possiblePartLengths anchor missing')
    text = text[:idx] + FETCH_HELPER + text[idx:]
    text = replace_once(text, 'self.defaultPartSize = 512 * 1024', 'self.defaultPartSize = jerkgramDownloadPartSize(512 * 1024, fileSize: self.size)', 'story part size')
    text = replace_once(text, 'self.defaultPartSize = 128 * 1024', 'self.defaultPartSize = jerkgramDownloadPartSize(128 * 1024, fileSize: self.size)', 'default part size')
    text = replace_once(text, 'maxPendingParts: 6,', 'maxPendingParts: jerkgramDownloadMaxPendingParts(6),', 'pending parts')
    require('self.cdnPartSize = 128 * 1024' in text, 'CDN part size changed/missing')
    return text


SETTINGS_HELPER = f'''{SETTINGS_MARKER}
private let jerkgramDownloadBoostKey = "{KEY}"

private func jerkgramDownloadBoostMode() -> String {{
    return UserDefaults.standard.string(forKey: jerkgramDownloadBoostKey) ?? "off"
}}

private func jerkgramDownloadBoostMenuTitle(_ value: String) -> String {{
    let isRussian = (Locale.current.languageCode ?? "en").lowercased().hasPrefix("ru")
    switch value {{
    case "medium":
        return isRussian ? "Среднее" : "Medium"
    case "maximum":
        return isRussian ? "Максимальное" : "Maximum"
    default:
        return isRussian ? "Выключено" : "Off"
    }}
}}

private func jerkgramDownloadBoostMenuItems(
    selected: String,
    select: @escaping (String) -> Void
) -> [ContextMenuItem] {{
    return ["off", "medium", "maximum"].map {{ value in
        let prefix = value == selected ? "✓ " : ""
        return .action(
            ContextMenuActionItem(
                text: prefix + jerkgramDownloadBoostMenuTitle(value),
                textLayout: .singleLine,
                icon: {{ _ in nil }},
                action: {{ _, dismiss in
                    select(value)
                    dismiss(.default)
                }}
            )
        )
    }}
}}

'''

STRINGS_EXTENSION = f'''

{STRINGS_MARKER}
public extension JerkgramStrings {{
    var downloadBoostSection: String {{
        self.languageCode == "ru" ? "ЗАГРУЗКА" : "DOWNLOAD"
    }}

    var downloadBoostTitle: String {{
        self.languageCode == "ru" ? "Ускоренная загрузка" : "Download Boost"
    }}

    func downloadBoostValue(_ value: String) -> String {{
        switch value {{
        case "medium":
            return self.languageCode == "ru" ? "Среднее" : "Medium"
        case "maximum":
            return self.languageCode == "ru" ? "Максимальное" : "Maximum"
        default:
            return self.languageCode == "ru" ? "Выключено" : "Off"
        }}
    }}

    var downloadBoostInfo: String {{
        if self.languageCode == "ru" {{
            return "Для файлов больше 1 МБ увеличивает размер частей и число параллельных запросов. Маленькие файлы и CDN остаются в штатном режиме Telegram."
        }} else {{
            return "For files over 1 MB, increases part size and parallel requests. Small files and CDN keep Telegram defaults."
        }}
    }}
}}
'''


def patch_strings_text(text):
    if STRINGS_MARKER in text:
        require(text.count(STRINGS_MARKER) == 1, 'strings marker count')
        return text
    require('JerkgramStrings' in text, 'JerkgramStrings owner missing')
    return text.rstrip() + STRINGS_EXTENSION + '\n'


DOWNLOAD_MENU_WIRING = '''    // MARK: Jerkgram Build140 Download Boost Menu1
    openDownloadBoostImpl = { [weak controller] in
        guard let controller = controller else {
            return
        }

        var sourceNode: ASDisplayNode?
        controller.forEachItemNode { itemNode in
            guard
                let disclosureNode = itemNode as? ItemListDisclosureItemNode,
                let tag = disclosureNode.tag
            else {
                return
            }
            if GhostBaseSettingsEntryTag.downloadBoost.isEqual(to: tag) {
                sourceNode = disclosureNode
            }
        }
        guard let sourceNode = sourceNode else {
            return
        }

        let presentationData = context.sharedContext.currentPresentationData.with { $0 }
        let selected = jerkgramDownloadBoostMode()
        let items = jerkgramDownloadBoostMenuItems(selected: selected, select: { mode in
            UserDefaults.standard.set(mode, forKey: jerkgramDownloadBoostKey)
            updateState { current in
                var updated = current
                updated.downloadBoostRefreshNonce &+= 1
                return updated
            }
        })
        let menu = makeContextController(
            context: context,
            presentationData: presentationData,
            source: .controller(
                GhostBaseSendStyleContextSource(
                    controller: controller,
                    sourceNode: sourceNode
                )
            ),
            items: .single(ContextController.Items(content: .list(items)))
        )
        controller.present(menu, in: .window(.root))
    }

'''


def patch_settings_text(text):
    if SETTINGS_MARKER in text:
        require(text.count(SETTINGS_MARKER) == 1, 'Settings marker count')
        return text

    state_anchor = 'struct GhostBaseSettingsState: Equatable {'
    require(state_anchor in text, 'settings state owner missing')
    text = text.replace(state_anchor, SETTINGS_HELPER + state_anchor, 1)

    text = replace_once(
        text,
        state_anchor,
        state_anchor + '\n    var downloadBoostRefreshNonce: Int32',
        'download boost refresh state field',
    )
    load_anchor = 'return GhostBaseSettingsState('
    require(text.count(load_anchor) == 1, 'settings state constructor count')
    text = text.replace(load_anchor, load_anchor + '\n            downloadBoostRefreshNonce: 0,', 1)

    text = replace_once(text, '    case sendTextStyle\n', '    case sendTextStyle\n    case downloadBoost\n', 'download boost item tag')

    text = replace_once(
        text,
        '    let openSendTextStyle: () -> Void\n',
        '    let openSendTextStyle: () -> Void\n    let openDownloadBoost: () -> Void\n',
        'download boost argument property',
    )
    text = replace_once(
        text,
        '        openSendTextStyle: @escaping () -> Void\n',
        '        openSendTextStyle: @escaping () -> Void,\n        openDownloadBoost: @escaping () -> Void\n',
        'download boost init parameter',
    )
    text = replace_once(
        text,
        '        self.openSendTextStyle = openSendTextStyle\n',
        '        self.openSendTextStyle = openSendTextStyle\n        self.openDownloadBoost = openDownloadBoost\n',
        'download boost init assignment',
    )

    text = replace_once(
        text,
        '    case selector(Int32, Int32, String, String)\n',
        '    case selector(Int32, Int32, String, String)\n    case downloadBoost(Int32, Int32, String, String)\n',
        'download boost entry case',
    )
    text = replace_once(
        text,
        '        case let .selector(section, _, _, _):\n            return section\n',
        '        case let .selector(section, _, _, _):\n            return section\n        case let .downloadBoost(section, _, _, _):\n            return section\n',
        'download boost section',
    )
    text = replace_once(
        text,
        '        case let .selector(section, index, _, _):\n            return section * 1000 + index\n',
        '        case let .selector(section, index, _, _):\n            return section * 1000 + index\n        case let .downloadBoost(section, index, _, _):\n            return section * 1000 + index\n',
        'download boost stable id',
    )

    equality_anchor = '''        case let .selector(ls, li, lt, lv):
            if case let .selector(rs, ri, rt, rv) = rhs {
                return ls == rs && li == ri
                    && lt == rt && lv == rv
            }
            return false
'''
    equality_new = equality_anchor + '''        case let .downloadBoost(ls, li, lt, lv):
            if case let .downloadBoost(rs, ri, rt, rv) = rhs {
                return ls == rs && li == ri
                    && lt == rt && lv == rv
            }
            return false
'''
    text = replace_once(text, equality_anchor, equality_new, 'download boost equality')

    selector_item = '''        case let .selector(_, _, title, value):
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
'''
    boost_item = selector_item + '''        case let .downloadBoost(_, _, title, value):
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
                    arguments.openDownloadBoost()
                },
                tag: GhostBaseSettingsEntryTag.downloadBoost
            )
'''
    text = replace_once(text, selector_item, boost_item, 'download boost item renderer')

    page_start, page_end = block_bounds(text, 'if page == .mediaStories {')
    page = text[page_start:page_end]
    return_index = page.find('return [')
    require(return_index >= 0, 'mediaStories return array missing')
    open_index = page.find('[', return_index)
    depth = 0
    close_index = None
    for i in range(open_index, len(page)):
        if page[i] == '[':
            depth += 1
        elif page[i] == ']':
            depth -= 1
            if depth == 0:
                close_index = i
                break
    require(close_index is not None, 'mediaStories return array unbalanced')
    body = page[open_index + 1:close_index]
    section_ids = [int(v) for v in re.findall(r'\.(?:header|toggle|info|input|disclosure|valueDisclosure|selector|downloadBoost)\(\s*(-?\d+)', body)]
    nonnegative = [v for v in section_ids if v >= 0]
    require(nonnegative, 'mediaStories section ids missing')
    section = max(nonnegative) + 1
    separator = '' if body.rstrip().endswith(',') else ','
    insertion = (
        separator
        + f'\n            .header({section}, strings.downloadBoostSection),'
        + f'\n            .downloadBoost({section}, 1, strings.downloadBoostTitle, strings.downloadBoostValue(jerkgramDownloadBoostMode())),'
        + f'\n            .info({section}, strings.downloadBoostInfo)'
    )
    page = page[:close_index] + insertion + page[close_index:]
    text = text[:page_start] + page + text[page_end:]

    text = replace_once(
        text,
        '    var openSendTextStyleImpl: (() -> Void)?\n',
        '    var openSendTextStyleImpl: (() -> Void)?\n    var openDownloadBoostImpl: (() -> Void)?\n',
        'download boost callback storage',
    )
    text = replace_once(
        text,
        '''    }, openSendTextStyle: {
        openSendTextStyleImpl?()
    })
''',
        '''    }, openSendTextStyle: {
        openSendTextStyleImpl?()
    }, openDownloadBoost: {
        openDownloadBoostImpl?()
    })
''',
        'download boost callback argument',
    )

    anchor = '    pushController = { [weak controller] target in\n'
    require(text.count(anchor) == 1, 'pushController menu anchor count')
    text = text.replace(anchor, DOWNLOAD_MENU_WIRING + anchor, 1)

    require(text.count(SETTINGS_MARKER) == 1, 'Settings marker final count')
    require(text.count('UserDefaults.standard.set(mode, forKey: jerkgramDownloadBoostKey)') == 1, 'global write count')
    return text


def main():
    require(FETCH.is_file(), 'FetchV2 owner missing: ' + str(FETCH))
    require(SETTINGS.is_file(), 'Settings owner missing: ' + str(SETTINGS))
    require(STRINGS.is_file(), 'Strings owner missing: ' + str(STRINGS))
    FETCH.write_text(patch_fetch_v2(FETCH.read_text(encoding='utf-8')), encoding='utf-8')
    SETTINGS.write_text(patch_settings_text(SETTINGS.read_text(encoding='utf-8')), encoding='utf-8')
    STRINGS.write_text(patch_strings_text(STRINGS.read_text(encoding='utf-8')), encoding='utf-8')
    print('[Build140 Download Boost] SOURCE PATCHED: Off=stock, Medium=512KiB/8, Maximum=1MiB/12; CDN untouched')


if __name__ == '__main__':
    main()
