"""Bot live replay integration, separate from unavailable server history."""
import os, unittest, shutil, subprocess, tempfile
from pathlib import Path
ROOT=Path(os.environ.get('JG_BOT_SOURCE',Path(__file__).resolve().parents[1]/'work/swiftgram-src'))
CORE='submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift'
class BotReplayTests(unittest.TestCase):
 def test_bot_metadata_never_uses_user_only_dialog_rpc(self):
  s=(ROOT/CORE).read_text()
  body=s.split('private func resolveMissingPeerChatInfos(',1)[1].split('var missingPeers:',1)[0]
  self.assertIn('jerkgramIsBotAccount(accountPeerId:',body)
  self.assertIn('return .single((state, false))',body)
 def test_received_messages_get_local_inclusion_without_moving_archive_or_cutoff(self):
  s=(ROOT/CORE).read_text()
  self.assertIn('func jerkgramIncludeBotMessagePeers',s)
  f=s.split('// JG174 bot persistence begin',1)[1].split('// JG174 bot persistence end',1)[0]
  self.assertIn('transaction.messageExists(id: id)',f)
  self.assertIn('if case .notIncluded = transaction.getPeerChatListInclusion',f)
  self.assertIn('minTimestamp: nil',f)
  self.assertIn('shouldExcludePeerFromChatList',f)
  self.assertNotIn('getDifference',f)
  replay=s.split('func replayFinalState(',1)[1]
  self.assertLess(replay.index('transaction.addMessages(messages, location: location)'),replay.index('jerkgramIncludeBotMessagePeers('))
 @unittest.skipUnless(shutil.which('swiftc'), 'Swift compiler unavailable; production replay helper fixture requires macOS CI')
 def test_actual_replay_helper_preserves_history_archive_pins_and_account_boundaries(self):
  source=(ROOT/CORE).read_text().split('// JG174 bot persistence begin\n',1)[1].split('// JG174 bot persistence end',1)[0]
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'main.swift';p.write_text('import Foundation\n'+MOCKS+source+FIXTURE)
   subprocess.run(['swiftc',str(p),'-o',d+'/check'],check=True)
   subprocess.run([d+'/check'],check=True)
MOCKS = r'''
struct PeerId: Hashable { let value: Int }
protocol Peer: AnyObject { var excluded: Bool { get } }
final class TelegramUser: Peer {
 let botInfo: String?
 let excluded: Bool
 init(bot: Bool, excluded: Bool = false) { self.botInfo = bot ? "bot" : nil; self.excluded = excluded }
}
struct MessageId: Hashable { let peerId: PeerId; let namespace: Int }
enum StoreId { case Id(MessageId), Partial }
struct StoreMessage { let id: StoreId }
enum Namespaces { enum Message { static let Cloud = 0 } }
enum Group: Equatable { case root, archive }
enum Inclusion: Equatable {
 case notIncluded
 case ifHasMessagesOrOneOf(groupId: Group, pinningIndex: Int?, minTimestamp: Int?)
}
final class Transaction {
 var peers: [PeerId: Peer] = [:]
 var messages = Set<MessageId>()
 var inclusions: [PeerId: Inclusion] = [:]
 var writes = 0
 func getPeer(_ id: PeerId) -> Peer? { self.peers[id] }
 func messageExists(id: MessageId) -> Bool { self.messages.contains(id) }
 func getPeerChatListInclusion(_ id: PeerId) -> Inclusion { self.inclusions[id] ?? .notIncluded }
 func updatePeerChatListInclusion(_ id: PeerId, inclusion: Inclusion) { self.inclusions[id] = inclusion; self.writes += 1 }
}
var marker = false
func ghostBaseIsBotAccount(_ id: PeerId) -> Bool { marker }
func shouldExcludePeerFromChatList(transaction: Transaction, peerId: PeerId, peer: Peer) -> Bool { peer.excluded }
'''
FIXTURE = r'''
let own = PeerId(value: 1), a = PeerId(value: 2), archived = PeerId(value: 3), missing = PeerId(value: 4), excluded = PeerId(value: 5)
let tx = Transaction()
tx.peers[own] = TelegramUser(bot: true)
for id in [a, archived, missing] { tx.peers[id] = TelegramUser(bot: false) }
tx.peers[excluded] = TelegramUser(bot: false, excluded: true)
let ids = [a, archived, missing, excluded].map { MessageId(peerId: $0, namespace: 0) }
tx.messages = Set(ids.filter { $0.peerId != missing })
let originalArchive = Inclusion.ifHasMessagesOrOneOf(groupId: .archive, pinningIndex: 7, minTimestamp: 123)
tx.inclusions[archived] = originalArchive
let batch = ids.map { StoreMessage(id: .Id($0)) }
jerkgramIncludeBotMessagePeers(transaction: tx, accountPeerId: own, messages: batch)
assert(tx.writes == 1)
assert(tx.getPeerChatListInclusion(a) == .ifHasMessagesOrOneOf(groupId: .root, pinningIndex: nil, minTimestamp: nil))
assert(tx.getPeerChatListInclusion(archived) == originalArchive)
assert(tx.getPeerChatListInclusion(missing) == .notIncluded)
assert(tx.getPeerChatListInclusion(excluded) == .notIncluded)
jerkgramIncludeBotMessagePeers(transaction: tx, accountPeerId: own, messages: batch)
assert(tx.writes == 1 && tx.messages.count == 3) // duplicate update never moves cutoff/deletes data
// Another newly delivered peer works without any shadow-import state.
tx.messages.insert(ids[2])
jerkgramIncludeBotMessagePeers(transaction: tx, accountPeerId: own, messages: [batch[2]])
assert(tx.writes == 2)
// An actual own user peer overrides stale bot marker; other account is untouched.
marker = true
tx.peers[own] = TelegramUser(bot: false)
tx.inclusions[a] = .notIncluded
jerkgramIncludeBotMessagePeers(transaction: tx, accountPeerId: own, messages: batch)
assert(tx.writes == 2 && tx.getPeerChatListInclusion(a) == .notIncluded)
assert(tx.getPeerChatListInclusion(archived) == originalArchive)
print("bot live replay inclusion PASS")
'''
if __name__=='__main__':unittest.main()
