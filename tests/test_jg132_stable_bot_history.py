"""Stable182 focused contracts. Native extraction fixtures require Swift; no device claims."""
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JERKGRAM_STABLE_BOT_SOURCE', ROOT.parent/'jerkgram-next/stable182-bot'))
FROZEN = json.loads((ROOT/'tests/fixtures/stable182/bot-frozen181.json').read_text())

class StableBotHistoryTests(unittest.TestCase):
    def read(self, name):
        return (SOURCE/'submodules'/name).read_text()

    def test_sparse_view_is_explicit_and_preserves_durable_holes(self):
        postbox = self.read('Postbox/Sources/MessageHistoryView.swift')
        self.assertIn('locallyAvailableOnly: Bool = false', postbox)
        self.assertIn('if self.locallyAvailableOnly { continue }', postbox)
        self.assertIn('holes: HistoryViewHoles(holesBySpace: [:])', postbox)
        self.assertNotIn('removeHole(peerId:', postbox)
        api = self.read('Postbox/Sources/Postbox.swift')
        self.assertEqual(api.count('locallyAvailableOnly: locallyAvailableOnly'), 3)
        public=codec.declaration(api,'    public func aroundMessageHistoryViewForLocation(\n')
        self.assertIn('locallyAvailableOnly: Bool = false',public)
        self.assertIn('locallyAvailableOnly: locallyAvailableOnly',public)

    def test_scope_checks_own_bot_peer_per_transaction(self):
        text = self.read('TelegramCore/Sources/State/AccountViewTracker.swift')
        self.assertIn('private func jerkgramBotHistoryView(', text)
        helper = text.split('private func jerkgramBotHistoryView(', 1)[1].split('public func aroundMessageOfInterest', 1)[0]
        self.assertIn('transaction.getPeer(account.peerId) as? TelegramUser', helper)
        self.assertIn('user.botInfo != nil', helper)
        self.assertIn('locallyAvailableOnly: true', helper)
        self.assertEqual(text.count('self.jerkgramBotHistoryView('), 3)

    def test_missing_hash_hydration_does_not_restart_history(self):
        history = self.read('TelegramCore/Sources/State/JerkgramBotBridgeHistory.swift')
        self.assertIn('func botBridgeMergeHistoricalPeer(', history)
        self.assertIn('currentUser.accessHash == nil', history)
        self.assertIn('case .personal = accessHash', history)
        self.assertIn('currentUser.withUpdatedAccessHash(accessHash)', history)
        self.assertNotIn('peerMetadataRepairVersion', history)
        policy = self.read('TelegramCore/Sources/State/JerkgramBotReplayPolicy.swift')
        self.assertEqual(hashlib.sha256(policy.encode()).hexdigest(), FROZEN['TelegramCore/Sources/State/JerkgramBotReplayPolicy.swift'])

    def test_optional_business_intro_does_not_block_bot_chat(self):
        text = self.read('TelegramUI/Sources/ChatHistoryViewForLocation.swift')
        self.assertIn('transaction.getPeer(account.peerId) as? TelegramUser', text)
        self.assertIn('if isBot { return .single(true) }', text)

    def test_modern_sending_authorization_and_native_identity_unchanged(self):
        pending=self.read('TelegramCore/Sources/State/PendingMessageManager.swift')
        self.assertEqual(pending.count('let inputPeer = botBridgeInputPeerForSending('),2)
        self.assertIn('own.botInfo != nil',pending)
        self.assertIn('case let .personal(hash)',pending)
        for name in ['TelegramCore/Sources/PendingMessages/EnqueueMessage.swift',
                     'TelegramCore/Sources/ApiUtils/StoreMessage_Telegram.swift',
                     'TelegramCore/Sources/Authorization.swift',
                     'TelegramCore/Sources/Utils/CanSendMessagesToPeer.swift']:
            self.assertEqual(hashlib.sha256((SOURCE/'submodules'/name).read_bytes()).hexdigest(), FROZEN[name], name)



FIX = ROOT/'tests/fixtures/stable182'
NATIVE = FIX/'bot-native'
spec = importlib.util.spec_from_file_location('stable182_codec', ROOT/'tests/test_jg131_beta2_bot_codec.py')
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)

def native_fixtures():
    core = SOURCE/'submodules/TelegramCore/Sources'
    history = (core/'State/JerkgramBotBridgeHistory.swift').read_text()
    policy = codec.policy(history)
    replay = (core/'State/JerkgramBotReplayPolicy.swift').read_text().replace('import Foundation', '')
    combined = policy + replay
    anchors = ['private func botBridgeValidatedAccount(', 'private func botBridgeWriteProgress(',
               'private struct BotBridgeHistoryPage', 'private func botBridgeReplyPeerIds(',
               'func botBridgeMergeHistoricalPeer(', 'private func importBotBridgeHistoryPage(']
    storage = (FIX/'bot-storage.swift').read_text().replace('/* REAL_POLICY */', combined).replace('/* REAL_STORAGE */', '\n'.join(codec.declaration(history, a) for a in anchors))
    factory = codec.declaration((SOURCE/'submodules/Postbox/Sources/MessageHistoryView.swift').read_text(), 'private func locallyAvailableHistoryState(')
    sampler = codec.declaration((NATIVE/'MessageHistoryViewState.swift').read_text(), 'private func sampleEntries(')
    view = (FIX/'bot-view.swift').read_text().replace('/* REAL_VIEW_FACTORY */', factory).replace('/* REAL_NATIVE_SAMPLE_ENTRIES */', sampler)
    copying = codec.declaration((core/'SyncCore/SyncCore_TelegramUser.swift').read_text(), 'func withUpdatedAccessHash(')
    fields = re.findall(r'(\w+): self\.\w+', copying)
    fields = [f for f in fields if f != 'id']
    peer = """import Foundation
struct PeerId: Equatable { struct Id: Equatable { let value: Int64; func _internalGetInt64Value() -> Int64 { value } }; let id: Id }
protocol Peer { var id: PeerId { get } }
enum TelegramPeerAccessHash: Equatable { case personal(Int64), genericPublic(Int64); var value: Int64 { switch self { case let .personal(v), let .genericPublic(v): return v } } }
struct TelegramUser: Peer { let id: PeerId; let accessHash: TelegramPeerAccessHash?;
""" + '\n'.join('let '+f+(': Int64?' if f=='botInfo' else ': Int64') for f in fields) + '\n' + copying + """
}
struct TelegramGroup: Peer { let id: PeerId }
struct TelegramChannel: Peer { let id: PeerId; let accessHash: TelegramPeerAccessHash? }
struct TelegramCommunity: Peer { let id: PeerId; let accessHash: TelegramPeerAccessHash? }
enum Api { enum InputPeer { struct User { let userId: Int64; let accessHash: Int64 }; struct Chat { let chatId: Int64 }; struct Channel { let channelId: Int64; let accessHash: Int64 }; case inputPeerUser(User), inputPeerChat(Chat), inputPeerChannel(Channel) } }
"""
    peer += codec.declaration((NATIVE/'ApiUtils.swift').read_text(), 'func apiInputPeer(_ peer: Peer)') + '\n'
    peer += codec.declaration(history, 'func botBridgeMergeHistoricalPeer(') + '\n'
    peer += 'final class Transaction { var peers: [Int64: Peer] = [:]; func getPeer(_ id: PeerId) -> Peer? { peers[id.id.value] } }\n'
    peer += codec.declaration((core/'State/PendingMessageManager.swift').read_text(), 'private func botBridgeInputPeerForSending(') + '\n'
    peer += 'func user(_ id: Int64 = 1, hash: TelegramPeerAccessHash? = nil, bot: Bool = false) -> TelegramUser { TelegramUser(id: PeerId(id: .init(value: id)), accessHash: hash, '+', '.join(f+(': bot ? 1 : nil' if f=='botInfo' else ': '+str(i+100)) for i,f in enumerate(fields))+') }\n'
    peer += """
let current = user()
precondition(apiInputPeer(current) == nil)
let merged = botBridgeMergeHistoricalPeer(current, user(hash: .personal(555))) as! TelegramUser
for (a, b) in zip(Mirror(reflecting: current).children, Mirror(reflecting: merged).children) where a.label != "accessHash" { precondition(String(describing: a.value) == String(describing: b.value)) }
guard case let .inputPeerUser(wire) = apiInputPeer(merged)! else { fatalError("modern wire peer unavailable") }
precondition(wire.userId == 1 && wire.accessHash == 555)
precondition((botBridgeMergeHistoricalPeer(current, user(2, hash: .personal(666))) as! TelegramUser).accessHash == nil)
precondition((botBridgeMergeHistoricalPeer(current, user(hash: .genericPublic(666))) as! TelegramUser).accessHash == nil)
precondition((botBridgeMergeHistoricalPeer(current, user(hash: .personal(0))) as! TelegramUser).accessHash == nil)
precondition((botBridgeMergeHistoricalPeer(user(hash: .personal(777)), user(hash: .personal(555))) as! TelegramUser).accessHash == .personal(777))
let tx=Transaction()
let selfId=PeerId(id:.init(value:9))
func wireHash(_ p:Api.InputPeer?)->Int64? { guard let p else { return nil }; switch p { case let .inputPeerUser(v):return v.accessHash;case let .inputPeerChannel(v):return v.accessHash;case .inputPeerChat:return -1 } }
tx.peers[9]=user(9,bot:true)
precondition(wireHash(botBridgeInputPeerForSending(transaction:tx,accountPeerId:selfId,peer:user()))==0)
precondition(wireHash(botBridgeInputPeerForSending(transaction:tx,accountPeerId:selfId,peer:user(hash:.genericPublic(333))))==0)
precondition(wireHash(botBridgeInputPeerForSending(transaction:tx,accountPeerId:selfId,peer:user(hash:.personal(444))))==444)
let channel=TelegramChannel(id:PeerId(id:.init(value:11)),accessHash:nil)
precondition(wireHash(botBridgeInputPeerForSending(transaction:tx,accountPeerId:selfId,peer:channel))==0)
let minChannel=TelegramChannel(id:channel.id,accessHash:.genericPublic(333))
precondition(wireHash(botBridgeInputPeerForSending(transaction:tx,accountPeerId:selfId,peer:minChannel))==0)
tx.peers[9]=user(9)
precondition(botBridgeInputPeerForSending(transaction:tx,accountPeerId:selfId,peer:user())==nil)
precondition(wireHash(botBridgeInputPeerForSending(transaction:tx,accountPeerId:selfId,peer:user(hash:.genericPublic(333))))==333)
tx.peers.removeAll()
precondition(botBridgeInputPeerForSending(transaction:tx,accountPeerId:selfId,peer:user())==nil)
print("PASS Stable182 real peer merge/copy and bot-only native send conversion")
"""
    return {'storage': storage, 'view': view, 'peer': peer, 'codec': 'import Foundation\n'+combined+(FIX/'bot-codec.swift').read_text()}

class StableBotNativeTests(unittest.TestCase):
    maxDiff = 2000
    def test_extraction_has_real_owners_and_no_unfilled_markers(self):
        fixtures = native_fixtures()
        for value in fixtures.values(): self.assertNotIn('/* REAL_', value)
        self.assertIn('func botBridgeMergeHistoricalPeer(', fixtures['storage'])
        self.assertIn('private func sampleEntries(', fixtures['view'])
        self.assertIn('func apiInputPeer(_ peer: Peer)', fixtures['peer'])

    def test_pinned_native_sources(self):
        expected = {'MessageHistoryView.swift': '37945abd086a6364fe9f177660450e09bc60c0b0', 'ChatHistoryViewForLocation.swift': '36b6e68c3a746e559d243fd73f53582422104d51', 'MessageHistoryViewState.swift': '570a197fa04dad4049fbee2c92da39cf4689d90a', 'ApiUtils.swift': '5bb7052bdfe6039fd50cb46c5bc45e57a62714ba'}
        for name, digest in expected.items():
            data = (NATIVE/name).read_bytes()
            self.assertEqual(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(), digest, name)

    def test_native_real_functions_both_optimizations(self):
        if not shutil.which('swiftc'):
            if os.environ.get('JG_STABLE182_REQUIRE_NATIVE') == '1': self.fail('Stable182 native Swift gate unavailable')
            self.skipTest('Swift unavailable: real importer/view/modern peer execution pending')
        for name, text in native_fixtures().items():
            if name == 'codec': continue
            for optimization in ['-O', '-Onone']:
                with self.subTest(name=name, optimization=optimization), tempfile.TemporaryDirectory(prefix='stable182-bot-') as tmp:
                    folder = Path(tmp); main = folder/'main.swift'; main.write_text(text); binary = folder/'native'
                    result = subprocess.run(['swiftc', '-swift-version', '5', optimization, str(main), '-o', str(binary)], capture_output=True, text=True, timeout=120)
                    self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                    result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                    self.assertIn('PASS', result.stdout)

    def test_actual_postbox_codec_both_optimizations(self):
        if not shutil.which('swiftc') or not shutil.which('xcrun'):
            if os.environ.get('JG_STABLE182_REQUIRE_NATIVE') == '1': self.fail('Stable182 actual Postbox codec requires macOS Swift/Clang')
            self.skipTest('macOS Swift/Clang unavailable: actual Postbox codec execution pending')
        for optimization in ['-O', '-Onone']:
            with self.subTest(optimization=optimization), tempfile.TemporaryDirectory(prefix='stable182-bot-codec-') as tmp:
                binary = codec.compile_fixture(Path(tmp), optimization, main_override=native_fixtures()['codec'])
                result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                self.assertIn('PASS Stable182 actual Postbox', result.stdout)

if __name__ == '__main__': unittest.main()
