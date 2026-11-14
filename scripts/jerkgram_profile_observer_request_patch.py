"""Pinned-source integration for event-driven Profile Observer requests."""


def _once(source, old, new, description):
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f'[Profile observer requests] {description}: anchor count {count}')
    return source.replace(old, new, 1)


def patch_request_interpreter(source):
    marker = '// MARK: Jerkgram PROFILE_OBSERVER_USER_INVALIDATION_V1'
    if marker in source:
        if source.count(marker) != 1:
            raise RuntimeError('duplicate observer user invalidation hook')
        return source
    anchor = '            case let .updateChat(updateChatData):\n'
    return _once(source, anchor,
        '            ' + marker + '\n'
        '            case let .updateUser(updateUserData):\n'
        '                let observedPeerId = PeerId(namespace: Namespaces.Peer.CloudUser, id: PeerId.Id._internalFromInt64Value(updateUserData.userId))\n'
        '                if jerkgramProfileObserverMightWatch(accountPeerId: accountPeerId, peerId: observedPeerId) {\n'
        '                    updatedState.jerkgramObserverInvalidate(observedPeerId)\n'
        '                }\n'
        + anchor, '13.2 user invalidation interpreter')


def patch_request_replay(source):
    marker = '// MARK: Jerkgram PROFILE_OBSERVER_REPLAY_USER_V1'
    if marker in source:
        if source.count(marker) != 1:
            raise RuntimeError('duplicate observer direct replay hook')
        return source
    anchor = (
        '            updatePeersCustom(transaction: transaction, peers: [peer], accountPeerId: accountPeerId, update: { _, updated in\n'
        '                return updated\n'
        '            })\n'
    )
    if anchor not in source:
        anchor = anchor.replace(', accountPeerId: accountPeerId, update:', ', update:')
    return _once(source, anchor, anchor +
        '            ' + marker + '\n'
        '            if let observedUser = transaction.getPeer(id) as? TelegramUser {\n'
        '                jerkgramProfileObserverUpdatedUser(accountPeerId: accountPeerId, user: observedUser)\n'
        '            }\n', '13.2 direct identity replay')


def patch_request_intermediate_state(source):
    marker = '// MARK: Jerkgram PROFILE_OBSERVER_INVALIDATION_STATE_V1'
    if marker in source:
        if source.count(marker) != 1:
            raise RuntimeError('duplicate observer final state field')
        return source
    source = _once(source, '    var externallyUpdatedPeerId = Set<PeerId>()\n',
        '    var externallyUpdatedPeerId = Set<PeerId>()\n'
        '    ' + marker + '\n'
        '    var jerkgramObserverInvalidatedPeerIds = Set<PeerId>()\n'
        '    private var jerkgramObserverInvalidationOverflow = false\n'
        '    mutating func jerkgramObserverInvalidate(_ peerId: PeerId) {\n'
        '        if self.jerkgramObserverInvalidatedPeerIds.contains(peerId) { return }\n'
        '        guard self.jerkgramObserverInvalidatedPeerIds.count < 4096 else {\n'
        '            if !self.jerkgramObserverInvalidationOverflow {\n'
        '                self.jerkgramObserverInvalidationOverflow = true\n'
        '                NSLog("[Jerkgram Profile Observer] update batch BIO invalidation capacity reached")\n'
        '            }\n'
        '            return\n'
        '        }\n'
        '        self.jerkgramObserverInvalidatedPeerIds.insert(peerId)\n'
        '    }\n', 'mutable observer invalidation state')
    source = _once(source, '        self.externallyUpdatedPeerId.formUnion(other.externallyUpdatedPeerId)\n',
        '        self.externallyUpdatedPeerId.formUnion(other.externallyUpdatedPeerId)\n'
        '        for peerId in other.jerkgramObserverInvalidatedPeerIds { self.jerkgramObserverInvalidate(peerId) }\n', 'branch invalidation merge')
    source = _once(source, '    let externallyUpdatedPeerId: Set<PeerId>\n',
        '    let externallyUpdatedPeerId: Set<PeerId>\n'
        '    let jerkgramObserverInvalidatedPeerIds: Set<PeerId>\n', 'final observer events')
    source = _once(source, '&& self.externallyUpdatedPeerId.isEmpty &&',
        '&& self.externallyUpdatedPeerId.isEmpty && self.jerkgramObserverInvalidatedPeerIds.isEmpty &&', 'observer event emptiness')
    # A defaulted argument preserves all existing explicit constructors.
    anchor = 'updatedEmojiGameInfo: EmojiGameInfo?) {'
    source = _once(source, anchor,
        'updatedEmojiGameInfo: EmojiGameInfo?, jerkgramObserverInvalidatedPeerIds: Set<PeerId> = []) {', 'observer event constructor')
    source = _once(source, '        self.externallyUpdatedPeerId = externallyUpdatedPeerId\n',
        '        self.externallyUpdatedPeerId = externallyUpdatedPeerId\n'
        '        self.jerkgramObserverInvalidatedPeerIds = jerkgramObserverInvalidatedPeerIds\n', 'observer event constructor assignment')
    source = _once(source, '        self.externallyUpdatedPeerId = state.state.state.externallyUpdatedPeerId\n',
        '        self.externallyUpdatedPeerId = state.state.state.externallyUpdatedPeerId\n'
        '        self.jerkgramObserverInvalidatedPeerIds = state.state.state.jerkgramObserverInvalidatedPeerIds\n', 'observer replay event extraction')
    source = _once(source, '            updatedEmojiGameInfo: other.updatedEmojiGameInfo ?? self.updatedEmojiGameInfo\n',
        '            updatedEmojiGameInfo: other.updatedEmojiGameInfo ?? self.updatedEmojiGameInfo,\n'
        '            jerkgramObserverInvalidatedPeerIds: jerkgramProfileObserverUnionInvalidations(self.jerkgramObserverInvalidatedPeerIds, other.jerkgramObserverInvalidatedPeerIds)\n', 'observer event union')
    return source


def patch_request_event_hub(source):
    marker = '// MARK: Jerkgram PROFILE_OBSERVER_INVALIDATION_PIPE_V1'
    if marker in source:
        if source.count(marker) != 1:
            raise RuntimeError('duplicate observer invalidation pipe')
        return source
    anchor = '    private let externallyUpdatedPeerIdsPipe = ValuePipe<[PeerId]>()\n'
    source = _once(source, anchor,
        '    ' + marker + '\n'
        '    private let jerkgramObserverInvalidatedPeerIdsPipe = ValuePipe<[PeerId]>()\n'
        '    var jerkgramProfileObserverInvalidatedPeerIds: Signal<[PeerId], NoError> {\n'
        '        return self.jerkgramObserverInvalidatedPeerIdsPipe.signal()\n'
        '    }\n\n' + anchor, 'observer event hub pipe')
    anchor = '        if !events.externallyUpdatedPeerId.isEmpty {\n'
    return _once(source, anchor,
        '        if !events.jerkgramObserverInvalidatedPeerIds.isEmpty {\n'
        '            self.jerkgramObserverInvalidatedPeerIdsPipe.putNext(Array(events.jerkgramObserverInvalidatedPeerIds))\n'
        '        }\n\n' + anchor, 'post-replay observer delivery')


def patch_request_state_manager(source):
    marker = '// MARK: Jerkgram PROFILE_OBSERVER_INVALIDATION_SIGNAL_V1'
    if marker in source:
        if source.count(marker) != 1:
            raise RuntimeError('duplicate observer manager signal')
        return source
    anchor = '        var externallyUpdatedPeerIds: Signal<[PeerId], NoError> {\n'
    source = _once(source, anchor,
        '        ' + marker + '\n'
        '        var jerkgramProfileObserverInvalidatedPeerIds: Signal<[PeerId], NoError> {\n'
        '            return self.eventHub.jerkgramProfileObserverInvalidatedPeerIds\n'
        '        }\n\n' + anchor, 'observer manager implementation accessor')
    anchor = '    var externallyUpdatedPeerIds: Signal<[PeerId], NoError> {\n'
    # Match the outer accessor including preceding newline, excluding the Impl.
    return _once(source, '\n' + anchor,
        '\n    var jerkgramProfileObserverInvalidatedPeerIds: Signal<[PeerId], NoError> {\n'
        '        return self.impl.signalWith { impl, subscriber in\n'
        '            return impl.jerkgramProfileObserverInvalidatedPeerIds.start(next: subscriber.putNext, error: subscriber.putError, completed: subscriber.putCompletion)\n'
        '        }\n'
        '    }\n' + '\n' + anchor, 'observer manager public accessor')


def patch_request_account_context(source):
    marker = '// MARK: Jerkgram PROFILE_OBSERVER_ACCOUNT_REQUESTS_V1'
    if marker in source:
        if source.count(marker) != 1 or source.count('jerkgramProfileObserverRequestsDisposable?.dispose()') != 1:
            raise RuntimeError('incomplete observer account lifecycle hook')
        return source
    source = _once(source,
        '    private var isFrozenDisposable: Disposable?\n',
        '    private var isFrozenDisposable: Disposable?\n'
        '    ' + marker + '\n'
        '    private var jerkgramProfileObserverRequestsDisposable: Disposable?\n',
        'account request owner')
    anchor = '        self.engine = TelegramEngine(account: account)\n'
    source = _once(source, anchor, anchor +
        '        if !temp {\n'
        '            self.jerkgramProfileObserverRequestsDisposable = jerkgramProfileObserverManage(\n'
        '                account: account,\n'
        '                inForeground: sharedContext.applicationBindings.applicationInForeground\n'
        '            )\n'
        '        }\n', 'account request startup')
    source = _once(source,
        '        self.isFrozenDisposable?.dispose()\n',
        '        self.isFrozenDisposable?.dispose()\n'
        '        self.jerkgramProfileObserverRequestsDisposable?.dispose()\n',
        'account request teardown')
    return source


REQUEST_PATCHES = {
    'submodules/TelegramCore/Sources/State/Sync/UpdateInterpreter.swift': patch_request_interpreter,
    'submodules/TelegramCore/Sources/State/Sync/StateReplay+Peers.swift': patch_request_replay,
    'submodules/TelegramCore/Sources/Account/AccountIntermediateState.swift': patch_request_intermediate_state,
    'submodules/TelegramCore/Sources/State/AccountStateEventHub.swift': patch_request_event_hub,
    'submodules/TelegramCore/Sources/State/AccountStateManager.swift': patch_request_state_manager,
    'submodules/TelegramUI/Sources/AccountContext.swift': patch_request_account_context,
}
