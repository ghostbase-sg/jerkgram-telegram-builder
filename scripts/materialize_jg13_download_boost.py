"""Download Boost: exact four-owner delta after Build164, no transport/upload edits."""
import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'patches/jg13-download-boost.sha256.json'
FETCH = 'submodules/TelegramCore/Sources/Network/FetchV2.swift'
POLICY = 'submodules/TelegramCore/Sources/Network/JerkgramDownloadBoostPolicy.swift'
SETTINGS = 'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift'
STRINGS = 'submodules/TelegramPresentationData/Sources/JerkgramStrings.swift'
PAYLOAD = ROOT / 'scripts/payloads/JerkgramDownloadBoostPolicy.swift'

BOOST_CONTROLLER = '''private func jerkgramDownloadBoostController(context: AccountContext, selected: String, select: @escaping (String) -> Void) -> ViewController {
    let selectedPromise = ValuePromise(selected, ignoreRepeated: true)
    let arguments = GhostBaseSendStylePageArguments(select: { value in
        selectedPromise.set(value)
        select(value)
    })
    let signal = combineLatest(context.sharedContext.presentationData, selectedPromise.get())
    |> deliverOnMainQueue
    |> map { presentationData, value -> (ItemListControllerState, (ItemListNodeState, Any)) in
        let strings = presentationData.strings.jerkgram
        let options = [("off", strings.downloadBoostOff), ("medium", strings.downloadBoostMedium), ("maximum", strings.downloadBoostMaximum)]
        let entries: [GhostBaseSendStylePageEntry] = options.enumerated().map { index, option in
            return .option(Int32(index), option.0, option.1, value == option.0)
        }
        let state = ItemListControllerState(presentationData: ItemListPresentationData(presentationData), title: .text(strings.downloadBoost), leftNavigationButton: nil, rightNavigationButton: nil, backNavigationButton: ItemListBackButton(title: presentationData.strings.Common_Back), animateChanges: false)
        let list = ItemListNodeState(presentationData: ItemListPresentationData(presentationData), entries: entries, style: .blocks, ensureVisibleItemTag: nil, emptyStateItem: nil, animateChanges: false)
        return (state, (list, arguments as Any))
    }
    return ItemListController(context: context, state: signal)
}

'''

BOOST_ITEM = '''        case let .downloadBoost(_, _, value):
            let strings = presentationData.strings.jerkgram
            let label = value == "maximum" ? strings.downloadBoostMaximum : (value == "medium" ? strings.downloadBoostMedium : strings.downloadBoostOff)
            return ItemListDisclosureItem(presentationData: presentationData, systemStyle: .glass, title: strings.downloadBoost, label: label, labelStyle: .text, sectionId: self.section, style: .blocks, disclosureStyle: .arrow, action: { arguments.openDownloadBoost() })

'''

REPLACEMENTS = {
    FETCH: [
        ('            maxPendingParts: Int,\n            decryptionState:', '            maxPendingParts: Int,\n            initialWindow: Int = fastDownloadInitialWindow,\n            decryptionState:'),
        ('            self.maxPendingParts = maxPendingParts\n', '            self.maxPendingParts = maxPendingParts\n            self.window = initialWindow\n'),
        ('        private let defaultPartSize: Int64\n', '        private let defaultPartSize: Int64\n        private let jerkgramBoost: JerkgramDownloadBoostPolicy.Parameters\n'),
        ('''            if isStory {
                self.defaultPartSize = 512 * 1024
            } else {
                self.defaultPartSize = 128 * 1024
            }
''', '''            self.jerkgramBoost = JerkgramDownloadBoostPolicy.parameters(mode: JerkgramDownloadBoostSettings.mode(accountPeerId: accountPeerId.toInt64()), size: size, isStory: isStory, fastDownloads: self.fastDownloads, encrypted: encryptionKey != nil)
            self.defaultPartSize = self.jerkgramBoost.partSize
'''),
        ('            self.masterPendingParts = self.fastDownloads ? fastDownloadMasterPendingParts : 6', '            self.masterPendingParts = self.jerkgramBoost.maxPendingParts'),
        ('            self.cdnPendingParts = self.fastDownloads ? fastDownloadCdnPendingParts : 6\n', '''            self.cdnPendingParts = self.fastDownloads ? fastDownloadCdnPendingParts : 6
            if self.jerkgramBoost.mode != .off && JerkgramDownloadBoostSettings.takeDebugLogSlot() {
                Logger.shared.log("JerkgramDownloadBoost", "mode=" + self.jerkgramBoost.mode.rawValue + " path=DC rust=" + String(self.fastDownloads) + " part=" + String(self.defaultPartSize) + " pending=" + String(self.masterPendingParts) + " initialWindow=" + String(self.jerkgramBoost.initialWindow))
            }
'''),
        ('                    case let .cdnRedirect(cdnData):\n', '''                    case let .cdnRedirect(cdnData):
                        if self.jerkgramBoost.mode != .off && JerkgramDownloadBoostSettings.takeDebugLogSlot() {
                            Logger.shared.log("JerkgramDownloadBoost", "mode=" + self.jerkgramBoost.mode.rawValue + " path=CDN stock part=" + String(self.cdnPartSize) + " pending=" + String(self.cdnPendingParts))
                        }
'''),
        # All three master-state creation paths; CDN-state constructors remain stock.
        ('maxPendingParts: self.masterPendingParts,\n', 'maxPendingParts: self.masterPendingParts, initialWindow: self.jerkgramBoost.initialWindow,\n'),
        ('state.partSize = min(state.maxPartSize, fastDownloadLargePartSize)', 'state.partSize = min(state.maxPartSize, self.jerkgramBoost.adaptiveLargePartSize)'),
    ],
    SETTINGS: [
        ('    var sendTextStyle: String', '    var downloadBoost: String = "off"\n    var sendTextStyle: String'),
        ('            sendTextStyle: jerkgramScopedString', '            downloadBoost: JerkgramDownloadBoostSettings.readStoredMode(accountPeerId: accountPeerId).rawValue,\n            sendTextStyle: jerkgramScopedString'),
        ('    return [\n        GhostBaseKey.profileEnabled:', '    return [\n        JerkgramDownloadBoostSettings.preferenceKey: .string(state.downloadBoost),\n        GhostBaseKey.profileEnabled:'),
        ('    defer { JerkgramHotSettings.invalidate() }', '    defer { JerkgramHotSettings.invalidate() }\n    JerkgramDownloadBoostSettings.update(accountPeerId: accountPeerId, rawValue: current.downloadBoost)'),
        ('    ]).union(JerkgramHotSettings.keys)', '        JerkgramDownloadBoostSettings.preferenceKey,\n    ]).union(JerkgramHotSettings.keys)'),
        ('    let openSendTextStyle: () -> Void', '    let openDownloadBoost: () -> Void\n    let openSendTextStyle: () -> Void'),
        ('        openSendTextStyle: @escaping () -> Void', '        openDownloadBoost: @escaping () -> Void,\n        openSendTextStyle: @escaping () -> Void'),
        ('        self.openSendTextStyle = openSendTextStyle', '        self.openDownloadBoost = openDownloadBoost\n        self.openSendTextStyle = openSendTextStyle'),
        ('    case selector(Int32, Int32, String, String)', '    case downloadBoost(Int32, Int32, String)\n    case selector(Int32, Int32, String, String)'),
        ('        case let .selector(section, _, _, _):', '        case let .downloadBoost(section, _, _):\n            return section\n        case let .selector(section, _, _, _):'),
        ('        case let .selector(section, index, _, _):', '        case let .downloadBoost(section, index, _):\n            return section * 1000 + index\n        case let .selector(section, index, _, _):'),
        ('        case let .selector(ls, li, lt, lv):', '        case let .downloadBoost(ls, li, lv):\n            if case let .downloadBoost(rs, ri, rv) = rhs { return ls == rs && li == ri && lv == rv }\n            return false\n        case let .selector(ls, li, lt, lv):'),
        ('        case let .selector(_, _, title, value):', BOOST_ITEM + '        case let .selector(_, _, title, value):'),
        ('.toggle(0, 4, GhostBaseKey.storySave, strings.storySave, state.storySave)\n', '.toggle(0, 4, GhostBaseKey.storySave, strings.storySave, state.storySave),\n            .downloadBoost(0, 5, state.downloadBoost),\n            .info(1, strings.downloadBoostHint)\n'),
        ('private func ghostBaseSettingsPageController(', BOOST_CONTROLLER + 'private func ghostBaseSettingsPageController('),
        ('    var openSendTextStyleImpl: (() -> Void)?', '    var openDownloadBoostImpl: (() -> Void)?\n    var openSendTextStyleImpl: (() -> Void)?'),
        ('    }, openSendTextStyle: {', '    }, openDownloadBoost: {\n        openDownloadBoostImpl?()\n    }, openSendTextStyle: {'),
        ('    openSendTextStyleImpl = { [weak controller] in', '''    openDownloadBoostImpl = { [weak controller] in
        let picker = jerkgramDownloadBoostController(context: context, selected: stateValue.with { $0.downloadBoost }, select: { mode in
            updateState { current in
                var updated = current
                updated.downloadBoost = mode
                return updated
            }
        })
        controller?.push(picker)
    }

    openSendTextStyleImpl = { [weak controller] in'''),
    ],
    STRINGS: [
        ('    case mediaAndStories\n', '    case mediaAndStories\n    case downloadBoost\n    case downloadBoostOff\n    case downloadBoostMedium\n    case downloadBoostMaximum\n    case downloadBoostHint\n'),
        ('    public var mediaAndStories:', '    public var downloadBoost: String { self.text(.downloadBoost) }\n    public var downloadBoostOff: String { self.text(.downloadBoostOff) }\n    public var downloadBoostMedium: String { self.text(.downloadBoostMedium) }\n    public var downloadBoostMaximum: String { self.text(.downloadBoostMaximum) }\n    public var downloadBoostHint: String { self.text(.downloadBoostHint) }\n    public var mediaAndStories:'),
        ('        .mediaAndStories: "Media & Stories",', '        .downloadBoost: "Download Boost",\n        .downloadBoostOff: "Off",\n        .downloadBoostMedium: "Medium",\n        .downloadBoostMaximum: "Maximum",\n        .downloadBoostHint: "Increases client-side download parallelism. It does not bypass Telegram Premium server limits. Applies to new download sessions.",\n        .mediaAndStories: "Media & Stories",'),
        ('        .mediaAndStories: "Медиа и истории",', '        .downloadBoost: "Ускорение загрузки",\n        .downloadBoostOff: "Выкл.",\n        .downloadBoostMedium: "Среднее",\n        .downloadBoostMaximum: "Максимальное",\n        .downloadBoostHint: "Увеличивает параллелизм загрузки на стороне клиента. Не снимает серверные ограничения Telegram Premium. Применяется к новым сеансам загрузки.",\n        .mediaAndStories: "Медиа и истории",'),
    ],
}

def digest(data): return hashlib.sha256(data).hexdigest()

def read_manifest():
    m = json.loads(MANIFEST.read_text())
    c = json.loads((ROOT / 'jerkgram-migration.json').read_text())
    icons = json.loads((ROOT / 'patches/jg13-premium-icons.sha256.json').read_text())
    if m['upstream_sha'] != c['upstream_new_sha'] or set(m['owners']) != {FETCH, SETTINGS, STRINGS, POLICY}:
        raise RuntimeError('Download Boost scope/pin changed')
    if m['owners'][SETTINGS]['before_sha256'] != icons['owners'][SETTINGS]['after_sha256']:
        raise RuntimeError('Download Boost must follow exact Build164 Settings')
    return m

def canonical(name, text):
    if name == STRINGS:
        c = json.loads((ROOT / 'jerkgram-migration.json').read_text())
        for key, old, new in [('displayVersion','1.0.2',c['product_display_version']),('technicalVersion','1.0.2',c['product_technical_version']),('build','138',str(c['build_number'])),('telegramBase','12.9.2',c['upstream_new_version'])]:
            text = text.replace(f'public static let {key} = "{new}"', f'public static let {key} = "{old}"')
        text = re.sub(r'public static let build = "\d+"', 'public static let build = "138"', text)
    return text

def transform(name, text):
    if name == POLICY: return PAYLOAD.read_text()
    for old, new in REPLACEMENTS[name]:
        count = 3 if name == FETCH and old.startswith('maxPendingParts: self.masterPendingParts,') else 1
        if text.count(old) != count: raise RuntimeError(f'Download Boost anchor count {text.count(old)} != {count}: {name}: {old[:65]}')
        text = text.replace(old, new)
    return text

def restore_owner(name, text):
    from materialize_jg13_sponsored import without_sponsored
    text = without_sponsored(name, text)
    m = read_manifest()
    text = canonical(name, text)
    if digest(text.encode()) != m['owners'][name]['after_sha256']: raise RuntimeError('Download Boost final owner changed: ' + name)
    if name == POLICY: return None
    for old, new in reversed(REPLACEMENTS[name]): text = text.replace(new, old)
    if digest(text.encode()) != m['owners'][name]['before_sha256']: raise RuntimeError('Download Boost preceding owner lost: ' + name)
    return text

def without_boost(name, text):
    from materialize_jg13_sponsored import without_sponsored
    text = without_sponsored(name, text)
    m = read_manifest()
    if name in m['owners'] and digest(canonical(name, text).encode()) == m['owners'][name]['after_sha256']:
        return restore_owner(name, text)
    return text

def check_locks(source, m):
    for name, expected in m['locks'].items():
        if digest((Path(source) / name).read_bytes()) != expected: raise RuntimeError('Download Boost upload/transport/App Icons regression lock changed: ' + name)

def verify_boost(source):
    m = read_manifest()
    for name in m['owners']: restore_owner(name, (Path(source) / name).read_text())
    check_locks(source, m)
    config = ast.parse((ROOT / 'scripts/configure_jg13.py').read_text())
    calls = [n for n in ast.walk(config) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'apply_boost']
    if len(calls) != 1 or len(calls[0].args) != 1 or not isinstance(calls[0].args[0], ast.Name) or calls[0].args[0].id != 'SOURCE': raise RuntimeError('Download Boost canonical apply call missing/duplicated')
    config_text = (ROOT / 'scripts/configure_jg13.py').read_text()
    if config_text.index('    apply_icons(SOURCE)') >= config_text.index('    apply_boost(SOURCE)'): raise RuntimeError('Download Boost must follow App Icons')
    verifier = ast.parse((ROOT / 'scripts/verify_jg13_source.py').read_text())
    if not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id == 'verify_boost' for n in ast.walk(verifier)): raise RuntimeError('Canonical Download Boost verification missing')
    return {n: {'after_sha256': v['after_sha256']} for n,v in m['owners'].items()}

def apply_boost(source):
    source = Path(source); m = read_manifest(); check_locks(source,m); outputs = {}
    for name, values in m['owners'].items():
        p = source/name
        if name == POLICY:
            if p.exists(): raise RuntimeError('Download Boost duplicate policy')
            text = ''
        else:
            text = p.read_text()
            if digest(text.encode()) != values['before_sha256']: raise RuntimeError('Download Boost wrong parent or repeat: ' + name)
        updated = transform(name,text)
        if digest(updated.encode()) != values['after_sha256']: raise RuntimeError('Download Boost output changed: ' + name)
        outputs[name] = updated
    for name,text in outputs.items(): (source/name).write_text(text)
    verify_boost(source)
    print('Download Boost: exact four-owner patch, stock Off and upload/transport/App Icons locks VERIFIED; NOT RUNTIME TESTED')
