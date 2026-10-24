"""Sponsored-only Core suppression after exact Build165; no history filtering."""
import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'patches/jg13-sponsored.sha256.json'
ADS = 'submodules/TelegramCore/Sources/TelegramEngine/Messages/AdMessages.swift'
SEARCH = 'submodules/TelegramCore/Sources/TelegramEngine/Peers/AdPeers.swift'
POLICY = 'submodules/TelegramCore/Sources/Utils/JerkgramSponsoredContentPolicy.swift'
SETTINGS = 'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift'
STRINGS = 'submodules/TelegramPresentationData/Sources/JerkgramStrings.swift'
PAYLOAD = ROOT / 'scripts/payloads/JerkgramSponsoredContentPolicy.swift'

REPLACEMENTS = {
    ADS: [
        ('func toMessage(peerId: PeerId, transaction: Transaction) -> Message? {\n', 'func toMessage(peerId: PeerId, transaction: Transaction, removeSponsored: Bool) -> Message? {\n            guard JerkgramSponsoredContentPolicy.shouldDisplay(isSponsored: self.messageType == .sponsored, removeSponsored: removeSponsored) else { return nil }\n'),
        ('    private let messageId: EngineMessage.Id?\n', '    private let messageId: EngineMessage.Id?\n    private let removeSponsored: Bool\n'),
        ('        self.messageId = messageId\n\n', '        self.messageId = messageId\n        let removeSponsored = JerkgramSponsoredContentPolicy.removeSponsored(accountPeerId: account.peerId.toInt64())\n        self.removeSponsored = removeSponsored\n\n'),
        ('        let messageId = self.messageId\n', '        let messageId = self.messageId\n        let removeSponsored = self.removeSponsored\n'),
        ('message.toMessage(peerId: peerId, transaction: transaction)', 'message.toMessage(peerId: peerId, transaction: transaction, removeSponsored: removeSponsored)'),
    ],
    SEARCH: [
        ('func _internal_searchAdPeers(account: Account, query: String) -> Signal<[AdPeer], NoError> {\n', 'func _internal_searchAdPeers(account: Account, query: String) -> Signal<[AdPeer], NoError> {\n    if JerkgramSponsoredContentPolicy.removeSponsored(accountPeerId: account.peerId.toInt64()) { return .single([]) }\n'),
    ],
    SETTINGS: [
        ('    var downloadBoost: String = "off"', '    var removeSponsored: Bool = false\n    var downloadBoost: String = "off"'),
        ('            downloadBoost: JerkgramDownloadBoostSettings.readStoredMode', '            removeSponsored: JerkgramSponsoredContentPolicy.readStoredValue(accountPeerId: accountPeerId),\n            downloadBoost: JerkgramDownloadBoostSettings.readStoredMode'),
        ('        JerkgramDownloadBoostSettings.preferenceKey: .string(state.downloadBoost),', '        JerkgramSponsoredContentPolicy.preferenceKey: .bool(state.removeSponsored),\n        JerkgramDownloadBoostSettings.preferenceKey: .string(state.downloadBoost),'),
        ('    JerkgramDownloadBoostSettings.update(accountPeerId: accountPeerId, rawValue: current.downloadBoost)', '    JerkgramSponsoredContentPolicy.update(accountPeerId: accountPeerId, enabled: current.removeSponsored)\n    JerkgramDownloadBoostSettings.update(accountPeerId: accountPeerId, rawValue: current.downloadBoost)'),
        ('        JerkgramDownloadBoostSettings.preferenceKey,', '        JerkgramSponsoredContentPolicy.preferenceKey,\n        JerkgramDownloadBoostSettings.preferenceKey,'),
        ('            .header(2, strings.backup),', '            .toggle(1, 51, JerkgramSponsoredContentPolicy.preferenceKey, strings.removeSponsored, state.removeSponsored),\n            .info(1, strings.removeSponsoredHint),\n            .header(2, strings.backup),'),
        ('            case GhostBaseKey.chatSave:', '            case JerkgramSponsoredContentPolicy.preferenceKey:\n                updated.removeSponsored = value\n            case GhostBaseKey.chatSave:'),
    ],
    STRINGS: [
        ('    case downloadBoost\n', '    case removeSponsored\n    case removeSponsoredHint\n    case downloadBoost\n'),
        ('    public var downloadBoost:', '    public var removeSponsored: String { self.text(.removeSponsored) }\n    public var removeSponsoredHint: String { self.text(.removeSponsoredHint) }\n    public var downloadBoost:'),
        ('        .downloadBoost: "Download Boost",', '        .removeSponsored: "Remove Sponsored Messages",\n        .removeSponsoredHint: "Hides Telegram sponsored messages and sponsored search results. This does not change your Telegram Premium status. Reopen the chat or media viewer, or refresh search after changing this setting.",\n        .downloadBoost: "Download Boost",'),
        ('        .downloadBoost: "Ускорение загрузки",', '        .removeSponsored: "Убирать рекламу",\n        .removeSponsoredHint: "Скрывает рекламные сообщения Telegram и рекламу в поиске. Не изменяет статус Telegram Premium. После изменения переоткройте чат или просмотр медиа либо обновите поиск.",\n        .downloadBoost: "Ускорение загрузки",'),
    ],
}

def digest(data): return hashlib.sha256(data).hexdigest()

def canonical(name, text):
    if name == STRINGS:
        from materialize_jg13_download_boost import canonical as boost_canonical
        return boost_canonical(name, text)
    return text

def read_manifest():
    m = json.loads(MANIFEST.read_text())
    c = json.loads((ROOT / 'jerkgram-migration.json').read_text())
    boost = json.loads((ROOT / 'patches/jg13-download-boost.sha256.json').read_text())
    if m['upstream_sha'] != c['upstream_new_sha'] or set(m['owners']) != {*REPLACEMENTS, POLICY}:
        raise RuntimeError('Sponsored scope/upstream changed')
    for name in (SETTINGS, STRINGS):
        if m['owners'][name]['before_sha256'] != boost['owners'][name]['after_sha256']:
            raise RuntimeError('Sponsored stage must follow exact Download Boost: ' + name)
    return m

def transform(name, text):
    if name == POLICY: return PAYLOAD.read_text()
    for old, new in REPLACEMENTS[name]:
        count = 2 if name == ADS and old == 'message.toMessage(peerId: peerId, transaction: transaction)' else 1
        if text.count(old) != count: raise RuntimeError(f'Sponsored anchor count changed: {name}: {old[:70]}')
        text = text.replace(old, new)
    return text

def restore_owner(name, text):
    m = read_manifest(); text = canonical(name, text)
    if digest(text.encode()) != m['owners'][name]['after_sha256']: raise RuntimeError('Sponsored final owner changed: ' + name)
    if name == POLICY: return None
    for old, new in reversed(REPLACEMENTS[name]): text = text.replace(new, old)
    if digest(text.encode()) != m['owners'][name]['before_sha256']: raise RuntimeError('Sponsored parent bytes lost: ' + name)
    return text

def without_sponsored(name, text):
    m = read_manifest()
    if name in m['owners'] and digest(canonical(name,text).encode()) == m['owners'][name]['after_sha256']:
        return restore_owner(name,text)
    return text

def check_locks(source, m):
    for name, expected in m['locks'].items():
        from materialize_jg13_history_backend import preceding_owner
        text = preceding_owner(name, (Path(source)/name).read_text())
        if digest(text.encode()) != expected: raise RuntimeError('Sponsored unrelated owner changed: ' + name)

def verify_sponsored(source):
    m = read_manifest()
    for name in m['owners']: restore_owner(name, (Path(source)/name).read_text())
    check_locks(source,m)
    text = (ROOT/'scripts/configure_jg13.py').read_text()
    tree = ast.parse(text)
    calls = [n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id == 'apply_sponsored']
    if len(calls) != 1 or len(calls[0].args) != 1 or not isinstance(calls[0].args[0],ast.Name) or calls[0].args[0].id != 'SOURCE': raise RuntimeError('Sponsored canonical stage missing/duplicated')
    if text.index('    apply_boost(SOURCE)') >= text.index('    apply_sponsored(SOURCE)'): raise RuntimeError('Sponsored stage must follow Download Boost')
    if '    verify_sponsored(SOURCE)' not in (ROOT/'scripts/verify_jg13_source.py').read_text(): raise RuntimeError('Sponsored root verifier missing')
    return {name: {'after_sha256': values['after_sha256']} for name,values in m['owners'].items()}

def apply_sponsored(source):
    source=Path(source); m=read_manifest(); check_locks(source,m); outputs={}
    for name,values in m['owners'].items():
        p=source/name
        if name == POLICY:
            if p.exists(): raise RuntimeError('Sponsored duplicate policy')
            text=''
        else:
            text=p.read_text()
            if digest(text.encode()) != values['before_sha256']: raise RuntimeError('Sponsored wrong parent or repeat: ' + name)
        output=transform(name,text)
        if digest(output.encode()) != values['after_sha256']: raise RuntimeError('Sponsored output changed: ' + name)
        outputs[name]=output
    for name,text in outputs.items(): (source/name).write_text(text)
    verify_sponsored(source)
    print('Sponsored-only Core delta VERIFIED; recommendations/history/tracking owners preserved; NOT RUNTIME TESTED')
