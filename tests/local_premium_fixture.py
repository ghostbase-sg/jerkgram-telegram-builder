"""Extract real production state/read/write/lifecycle code; UI sinks are fixtures."""
from pathlib import Path
from test_jg131_local_premium import body, ROOT, SETTINGS, STRINGS, FIXTURES


def native_source(tree):
    g = (tree / SETTINGS).read_text()
    read = lambda name: (tree / name).read_text()
    section = lambda text, start, end: text[text.index(start):text.index(end, text.index(start))]
    account = read('submodules/TelegramCore/Sources/Account/Account.swift')
    download = read('submodules/TelegramCore/Sources/Network/JerkgramDownloadBoostPolicy.swift')
    pieces = [
        'import Foundation',
        (ROOT / 'tests/fixtures/build176/foundation_sinks.swift').read_text(),
        (FIXTURES / 'shell.swift').read_text(),
        section(g, 'private enum GhostBaseKey {', 'private func ghostBaseIsValidStarsAmountInput'),
        'private let ghostBaseSendTextStyleKey = "jerkgram.Messages.SendTextStyle"',
        section(g, 'private func jerkgramScopedSettingsKey(', '// Regression sentinel'),
        body(g, 'struct GhostBaseSettingsState:'),
        body(account, 'public enum JerkgramHotSettings {'),
        read('submodules/TelegramCore/Sources/Utils/JerkgramSponsoredContentPolicy.swift').replace('import Foundation', ''),
        download.split('enum JerkgramDownloadBoostPolicy {')[0].replace('import Foundation', ''),
        body(read('submodules/TelegramCore/Sources/TelegramEngine/Peers/ChatListFiltering.swift'), 'public enum JerkgramDefaultFolderSettings {'),
        body(read('submodules/TelegramCore/Sources/TelegramEngine/Messages/Translate.swift'), 'public enum JerkgramTranslationSettings {'),
        body(read('submodules/SettingsUI/Sources/Themes/ThemeSettingsAppIconItem.swift'), 'enum JerkgramAppIconAccess {'),
        # The real language resolver and entire text catalog, with one external
        # PresentationStrings boundary supplied by shell.swift.
        (tree / STRINGS).read_text().replace('import PresentationStrings', ''),
        body(g, 'private final class JerkgramDiagnosticSettingsController:'),
        'private func makePage(_ accountPeerId: Int64) -> FixturePage {\n'
        + 'let context = FixtureContext(accountPeerId)\n'
        + 'let initialState = GhostBaseSettingsState.load(accountPeerId: accountPeerId)\n'
        + 'let statePromise = ValuePromise(initialState, ignoreRepeated: false)\n'
        + 'let stateValue = Atomic(value: initialState)\n'
        + body(g, 'let reloadSettings: () -> Void =') + '\n'
        + body(g, 'let updateState: ((GhostBaseSettingsState) -> GhostBaseSettingsState) -> Void =') + '\n'
        + 'let controller = JerkgramDiagnosticSettingsController()\n'
        + 'controller.refreshSettingsOnAppearance = reloadSettings\n'
        + 'return FixturePage(controller: controller, current: { stateValue.with { $0 } }, update: updateState, promise: statePromise)\n}',
        (FIXTURES / 'main.swift').read_text(),
    ]
    return '\n'.join(pieces)
