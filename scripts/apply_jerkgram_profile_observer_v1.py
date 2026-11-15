#!/usr/bin/env python3
"""Reviewed observer successor for the genuine Telegram13.2 Build183 product.

Prevalidate all anchors and payloads before writing anything. Roll back ordinary
write failures; a source materialization interrupted by process death must be
recreated, never silently accepted as a complete installation.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jerkgram_profile_observer_request_patch import REQUEST_PATCHES

REPO = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get('JERKGRAM_SOURCE_ROOT', os.environ.get('GHOSTBASE_SOURCE_ROOT', str(Path.cwd())))).resolve()
PAYLOAD = REPO / 'scripts/jerkgram_profile_observer_v1_payload'
PREFIX = 'submodules/TelegramCore/Sources/'
MANIFEST = '.jerkgram-profile-observer-install.json'
PAYLOAD_NAMES = ('JerkgramProfileObserver.swift', 'JerkgramProfileObserverAdmission.swift',
                 'JerkgramProfileHistoryStore.swift', 'JerkgramProfileObserverRequests.swift')


def require(condition, description):
    if not condition:
        raise RuntimeError('[Profile observer13.2] ' + description)


def replace_once(source, old, new, description):
    require(source.count(old) == 1, f'{description}: anchor count {source.count(old)}')
    return source.replace(old, new, 1)


def marked(source, marker, required):
    if marker not in source:
        return False
    require(source.count(marker) == 1 and all(value in source for value in required), 'incomplete or duplicate ' + marker)
    return True


def patch_core_build(source):
    #13.2 BUILD includes a second test library with its own Postbox dependency.
    head, boundary, tail = source.partition('\nswift_library(\n    name = "TelegramCoreTestsLib",')
    require(bool(boundary), 'core/test library boundary')
    dependency = '        "//submodules/sqlcipher:sqlcipher",\n'
    if dependency in head:
        require(head.count(dependency) == 1, 'duplicate sqlcipher dependency')
        return source
    head = replace_once(head, '        "//submodules/Postbox:Postbox",\n',
                        '        "//submodules/Postbox:Postbox",\n' + dependency, 'core database dependency')
    return head + boundary + tail


def patch_update_peers(source):
    marker = '// MARK: Jerkgram PROFILE_OBSERVER_PEER_UPDATES_V1'
    if marked(source, marker, ['jerkgramProfileObserverUpdatedPeers(', 'jerkgramObserverExcludingPeerId: PeerId? = nil']):
        return source
    source = replace_once(source,
        'func updatePeers(transaction: Transaction, accountPeerId: PeerId, peers: AccumulatedPeers) {',
        'func updatePeers(transaction: Transaction, accountPeerId: PeerId, peers: AccumulatedPeers, jerkgramObserverExcludingPeerId: PeerId? = nil) {',
        'merged peers signature')
    anchor = '    updatePeersCustom(transaction: transaction, peers: parsedPeers, accountPeerId: accountPeerId, update: { _, updated in updated })\n'
    source = replace_once(source, anchor, anchor + '    ' + marker + '\n'
        '    jerkgramProfileObserverUpdatedPeers(transaction: transaction, accountPeerId: accountPeerId, peers: peers, excludingPeerId: jerkgramObserverExcludingPeerId)\n', 'merged identity hook')
    return source


def patch_presence(source):
    marker = '// MARK: Jerkgram PROFILE_OBSERVER_PRESENCE_V1'
    if marked(source, marker, ['jerkgramProfileObserverPresence(', 'previous.isHidden == event.isHidden {']):
        return source
    anchor = ') {\n    GhostBasePresenceStoreV11G.recordPresence(\n'
    source = replace_once(source, anchor, ') {\n    ' + marker + '\n'
        '    jerkgramProfileObserverPresence(accountPeerId: accountPeerId, peerId: peerId, presence: presence)\n'
        '    GhostBasePresenceStoreV11G.recordPresence(\n', 'retained legacy presence owner')
    # Retain the old journal/writer, correct its semantic dedup as well.
    old = ('               previous.status == event.status,\n'
           '               previous.until == event.until,\n'
           '               previous.lastActivity == event.lastActivity,\n'
           '               previous.isHidden == event.isHidden,\n'
           '               event.observedAt - previous.observedAt <= 2 {\n')
    return replace_once(source, old,
        '               previous.status == event.status,\n'
        '               previous.isHidden == event.isHidden {\n', 'legacy presence semantic dedup')


def patch_full_user(source):
    marker = '// MARK: Jerkgram PROFILE_OBSERVER_FULL_USER_V1'
    if marked(source, marker, ['jerkgramProfileObserverFullUser(', 'jerkgramObserverExcludingPeerId: peerId']):
        return source
    old = ('                                let userFullNotifySettings = userFullData.notifySettings\n'
           '                                updatePeers(transaction: transaction, accountPeerId: accountPeerId, peers: parsedPeers)\n')
    return replace_once(source, old,
        '                                let userFullNotifySettings = userFullData.notifySettings\n'
        '                                ' + marker + '\n'
        '                                updatePeers(transaction: transaction, accountPeerId: accountPeerId, peers: parsedPeers, jerkgramObserverExcludingPeerId: peerId)\n'
        '                                if let observedUser = transaction.getPeer(peerId) as? TelegramUser {\n'
        '                                    jerkgramProfileObserverFullUser(accountPeerId: accountPeerId, user: observedUser, about: userFullData.about)\n'
        '                                }\n', 'one full-user observation')


def patch_profile_ui(source):
    marker = '// MARK: Jerkgram PROFILE_OBSERVER_FIRST_OPEN_V1'
    if marked(source, marker, ['jerkgramProfileObserverBegin(', 'jerkgramProfileObserverStartedPeerId']):
        if '    private var jerkgramProfileObserverStartedPeerId: PeerId?\n' in source:
            return replace_once(source,
                '    private var jerkgramProfileObserverStartedPeerId: PeerId?\n',
                '    private var jerkgramProfileObserverStartedPeerId: EnginePeer.Id?\n', 'module-visible enrollment identity')
        require('    private var jerkgramProfileObserverStartedPeerId: EnginePeer.Id?\n' in source,
                'unsupported screen enrollment identity')
        return source
    anchor = ('            ghostBaseRecordObservedProfileV11G(\n'
              '                accountPeerId: self.context.account.peerId,\n'
              '                peer: peer,\n'
              '                cachedData: data.cachedData\n'
              '            )\n')
    source = replace_once(source, anchor, anchor + '            ' + marker + '\n'
        '            if case .user = peer, self.jerkgramProfileObserverStartedPeerId != peer.id {\n'
        '                self.jerkgramProfileObserverStartedPeerId = peer.id\n'
        '                jerkgramProfileObserverBegin(account: self.context.account, peerId: peer.id)\n'
        '            }\n', 'first-open enrollment')
    return replace_once(source, '    private(set) var data: PeerInfoScreenData?\n',
        '    private(set) var data: PeerInfoScreenData?\n    private var jerkgramProfileObserverStartedPeerId: EnginePeer.Id?\n', 'screen enrollment gate')


def patch_account(source):
    marker = '// MARK: Jerkgram PROFILE_OBSERVER_ACCOUNT_KEY_V1'
    if marked(source, marker, ['jerkgramProfileObserverRegister(account: account, encryptionParameters: encryptionParameters)']):
        return source
    old = '                                            return .authorized(Account(accountManager: accountManager, id: id, basePath: path, testingEnvironment: authorizedState.isTestingEnvironment, postbox: postbox, network: network, networkArguments: networkArguments, peerId: authorizedState.peerId, auxiliaryMethods: auxiliaryMethods, supplementary: supplementary, isSupportUser: isSupportUser))\n'
    return replace_once(source, old,
        old.replace('return .authorized(Account(', 'let account = Account(').replace('isSupportUser))', 'isSupportUser)')
        + '                                            ' + marker + '\n'
        '                                            if !supplementary { jerkgramProfileObserverRegister(account: account, encryptionParameters: encryptionParameters) }\n'
        '                                            return .authorized(account)\n', 'authorized account key owner')


PATCHES = {
    'submodules/TelegramCore/BUILD': patch_core_build,
    PREFIX+'UpdatePeers.swift': lambda value: patch_presence(patch_update_peers(value)),
    PREFIX+'TelegramEngine/Peers/UpdateCachedPeerData.swift': patch_full_user,
    PREFIX+'Account/Account.swift': patch_account,
    'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreen.swift': patch_profile_ui,
    **REQUEST_PATCHES,
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def install(root=ROOT):
    root = Path(root)
    names = tuple(PATCHES) + tuple(PREFIX+name for name in PAYLOAD_NAMES)
    manifest_path = root / MANIFEST
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        for name, digest in previous['after'].items():
            require((root/name).is_file() and sha((root/name).read_bytes()) == digest, 'previous installation modified: '+name)
    before = {name: (root/name).read_bytes() if (root/name).exists() else None for name in names}
    after = {}
    for name, patch in PATCHES.items():
        require(before[name] is not None, 'missing source '+name)
        after[name] = patch(before[name].decode('utf-8')).encode('utf-8')
    for name in PAYLOAD_NAMES:
        require((PAYLOAD/name).is_file(), 'missing payload '+name)
        after[PREFIX+name] = (PAYLOAD/name).read_bytes()
    pending = root / (MANIFEST+'.pending')
    require(not pending.exists(), 'interrupted installation; recreate clean source')
    pending.write_text('uncommitted source successor\n')
    written = []
    try:
        for name, data in after.items():
            path = root/name
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
                temporary.write(data)
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, path)
            written.append(name)
        evidence = {'base':'Telegram13.2 Build183', 'before':{name:sha(data) if data is not None else None for name,data in before.items()}, 'after':{name:sha(data) for name,data in after.items()}}
        if manifest_path.exists():
            evidence['before'] = previous['before']
        manifest_path.write_text(json.dumps(evidence, indent=2)+'\n')
        pending.unlink()
    except BaseException:
        for name in reversed(written):
            if before[name] is None:
                (root/name).unlink(missing_ok=True)
            else:
                (root/name).write_bytes(before[name])
        pending.unlink(missing_ok=True)
        raise
    print('[Profile observer13.2] source successor installed; native compilation NOT implied')


if __name__ == '__main__':
    install()
