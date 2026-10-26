"""Local translation boundaries and actual bounded coordinator behavior."""
from pathlib import Path
import os, shutil, subprocess, tempfile, unittest
ROOT=Path(os.environ.get('JG_TRANSLATION_SOURCE',Path(__file__).resolve().parents[1]/'work/swiftgram-src'))
class TranslationTests(unittest.TestCase):
 def read(self,p): return (ROOT/p).read_text()
 def test_local_engine_path_precedes_server_rpc_and_never_falls_back(self):
  s=self.read('submodules/TelegramCore/Sources/TelegramEngine/Messages/Translate.swift')
  body=s.split('private func _internal_translateMessagesByPeerId(',1)[1]
  self.assertLess(body.index('jerkgramTranslateLocalMessages('),body.index('guard let inputPeer'))
  helper=s.split('// JG174 local message translation begin',1)[1].split('// JG174 local message translation end',1)[0]
  self.assertNotIn('account.network.request',helper)
  self.assertIn('jerkgramTranslationSourceMatches',helper)
  self.assertIn('return .skip',helper)
  self.assertIn('entities: []',helper)
 def test_only_translation_uses_local_adapter_and_skips_cloud_bootstrap(self):
  s=self.read('submodules/TelegramUI/Components/TextProcessingScreen/Sources/TextProcessingTranslateContentComponent.swift')
  self.assertTrue('jerkgramTranslateText(context:' in s)
  self.assertTrue('self.localTranslationGeneration' in s)
  self.assertTrue('localTranslationError' in s)
  s=self.read('submodules/TelegramUI/Components/TextProcessingScreen/Sources/TextProcessingScreen.swift')
  self.assertIn('localTranslation ? .single([])',s)
 def test_completed_results_are_versioned_and_not_reused_after_source_changes(self):
  attr=self.read('submodules/TelegramCore/Sources/SyncCore/SyncCore_TranslationMessageAttribute.swift')
  for value in ['jerkgramSourceFingerprint','jg174source','isValidForMessage','private weak var jerkgramCachedMessage']:
   self.assertTrue(value in attr,value)
  core=self.read('submodules/TelegramCore/Sources/TelegramEngine/Messages/Translate.swift')
  for value in ['sha256Digest(encoder.makeData())','poll.textEntities','poll.options','solution.entities','audio.isPending','jerkgramSourceFingerprint: jerkgramTranslationSourceFingerprint(original)']:
   self.assertTrue(value in core,value)
  for owner in ['submodules/TelegramUI/Components/Chat/ChatMessagePollBubbleContentNode/Sources/ChatMessagePollBubbleContentNode.swift','submodules/TelegramUI/Components/Chat/ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift']:
   self.assertTrue('.isValidForMessage(' in self.read(owner))
  history=self.read('submodules/TelegramUI/Sources/ChatHistoryListNode.swift')
  self.assertTrue('jerkgramTranslationSourceMatches(previous, updated)' in history)
  self.assertTrue('jerkgramLocalTranslationIsCurrent(translation, message: message' in history)
 def test_failure_marker_does_not_suppress_unrelated_summary_or_placeholder(self):
  s=self.read('submodules/TelegramUI/Components/Chat/ChatMessageTextBubbleContentNode/Sources/ChatMessageTextBubbleContentNode.swift')
  body=s.split('private func updateIsTranslating(',1)[1]
  self.assertIn('showTextAsPlaceholder || item.controllerInteraction.summarizedMessageIds.contains(item.message.id)',body)
 def test_failure_is_not_completed_pinned_cache_and_all_native_consumers_validate_source(self):
  s=self.read('submodules/TelegramUI/Sources/ChatPinnedMessageTitlePanelNode.swift')
  self.assertIn('!translation.jerkgramUnavailable, translation.isValidForMessage(message)',s)
  for owner,count in [('submodules/GalleryUI/Sources/GalleryController.swift',2),('submodules/GalleryUI/Sources/ChatItemGalleryFooterContentNode.swift',1),('submodules/ListMessageItem/Sources/ListMessageSnippetItemNode.swift',2),('submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift',4)]:
   self.assertGreaterEqual(self.read(owner).count('.isValidForMessage(message)'),count,owner)
   self.assertNotIn('first(where:,',self.read(owner))
 def test_composer_translation_keeps_native_apply_result(self):
  s=self.read('submodules/TelegramUI/Sources/Chat/ChatControllerLoadDisplayNode.swift')
  self.assertTrue('if useSystemTranslation && !jerkgramLocalTranslationAvailable {' in s)
  self.assertTrue('applyResult: { text in' in s)
 def test_chat_failure_is_localized_and_aggregated_without_canceling_successes(self):
  core=self.read('submodules/TelegramCore/Sources/TelegramEngine/Messages/Translate.swift')
  self.assertTrue('outcomes.allSatisfy({ $0 }) ? .single(Void()) : .fail(.generic)' in core)
  chat=self.read('submodules/TranslateUI/Sources/ChatTranslation.swift')
  self.assertTrue('onLocalFailure?()' in chat)
  history=self.read('submodules/TelegramUI/Sources/ChatHistoryListNode.swift')
  self.assertTrue('!self.jerkgramTranslationFailureShown' in history)
  self.assertTrue('presentationData.strings.jerkgram.localTranslationUnavailable' in history)
  self.assertTrue('jerkgramStoreLocalTranslationFailure' in core)
  self.assertTrue('jerkgramUnavailable: true' in core)
 def test_source_edits_bypass_old_throttle_and_generation_changes_are_main_owned(self):
  s=self.read('submodules/TelegramUI/Sources/ChatHistoryListNode.swift')
  self.assertTrue('// JG174 main-queue translation generation ownership' in s)
  self.assertTrue('var changedTranslationSources = Set<MessageId>()' in s)
  self.assertTrue('changedTranslationSources.insert(id)' in s)
  self.assertTrue('self.jerkgramTranslationNeedsImmediateRefresh' in s)
  self.assertTrue('self.translationProcessingManager.process?(Set(changedTranslationSources.map' in s)
 def test_requests_owned_by_visible_chat_lifetime(self):
  s=self.read('submodules/TelegramUI/Sources/ChatHistoryListNode.swift')
  self.assertTrue('private var jerkgramTranslationRequests:' in s)
  self.assertIn('cancelJerkgramTranslations()',s)
  self.assertIn('override public func didExitHierarchy()',s)
 @unittest.skipUnless(shutil.which('swiftc'),'Swift unavailable: actual source/cache fixture runs in macOS CI')
 def test_actual_source_fingerprint_and_weak_validity_cache(self):
  core=self.read('submodules/TelegramCore/Sources/TelegramEngine/Messages/Translate.swift')
  funcs=core.split('// JG174 source fingerprint begin',1)[1].split('// JG174 source fingerprint end',1)[0].replace('public func ', 'func ')
  funcs += core.split('// JG174 local message translation begin',1)[1].split('public func jerkgramTranslationSourceMatches(',1)[0]
  attr=self.read('submodules/TelegramCore/Sources/SyncCore/SyncCore_TranslationMessageAttribute.swift')
  cache=attr.split('    public let jerkgramSourceFingerprint: String?',1)[1].split('    public let additional:',1)[0]
  model='final class TranslationMessageAttribute { let toLang:String; let jerkgramUnavailable:Bool; public let jerkgramSourceFingerprint: String?'+cache+'init(toLang:String,fingerprint:String?,unavailable:Bool=false){self.toLang=toLang;self.jerkgramSourceFingerprint=fingerprint;self.jerkgramUnavailable=unavailable} }'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'main.swift';p.write_text('import Foundation\n'+FINGERPRINT_MOCKS+model+funcs+FINGERPRINT_CHECKS)
   subprocess.run(['swiftc',str(p),'-o',d+'/check'],check=True)
   subprocess.run([d+'/check'],check=True)
 @unittest.skipUnless(shutil.which('swiftc'),'Swift unavailable: actual queue fixture runs in macOS CI')
 def test_actual_coordinator_bounds_dedupe_cancel_cache_and_account_separation(self):
  s=self.read('submodules/TranslateUI/Sources/Translate.swift').split('// JG174 translation queue begin',1)[1].split('// JG174 translation queue end',1)[0]
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'main.swift';p.write_text('import Foundation\n'+s.replace('private final class JerkgramTranslationQueue','final class JerkgramTranslationQueue',1)+FIXTURE)
   subprocess.run(['swiftc',str(p),'-o',d+'/check'],check=True)
   subprocess.run([d+'/check'],check=True)
FIXTURE=r'''
let queue = JerkgramTranslationQueue()
var a=0, b=0, failed=0
let first=queue.enqueue(texts:["account1/message1":"hello"],from:"en",to:"ru",completion:{ if $0 != nil {a += 1} })!
let duplicate=queue.enqueue(texts:["account1/message1":"hello"],from:"en",to:"ru",completion:{ if $0 != nil {b += 1} })!
assert(first.0==duplicate.0 && queue.workItems==1)
let job=queue.begin()!
assert(queue.begin()==nil && queue.nextLanguagePair==nil)
queue.cancel(jobId:first.0,subscriberId:first.1)
assert(queue.active != nil && queue.workItems==1)
for callback in queue.finish(jobId:job.id,result:["account1/message1":"привет"]) {callback()}
assert(a==0 && b==1 && queue.workItems==0)
_ = queue.enqueue(texts:["account1/message1":"hello"],from:"en",to:"ru",completion:{ if $0 != nil { b += 1 } })
assert(b==2 && queue.pending.isEmpty)
let other=queue.enqueue(texts:["account2/message1":"hello"],from:"en",to:"ru",completion:{ _ in })!
assert(queue.pending.count==1)
queue.cancel(jobId:other.0,subscriberId:other.1)
assert(queue.workItems==0 && queue.pending.isEmpty)
for i in 0..<64 { _ = queue.enqueue(texts:["\(i)":"x"],from:"en",to:"ru",completion:{ _ in }) }
_ = queue.enqueue(texts:["overflow":"x"],from:"en",to:"ru",completion:{if $0==nil {failed += 1}})
assert(failed==1 && queue.workItems==64)
while let job=queue.begin() { for c in queue.finish(jobId:job.id,result:nil) {c()} }
assert(queue.workItems==0 && queue.workBytes==0)
_ = queue.enqueue(texts:["huge":String(repeating:"я",count:9000)],from:"ru",to:"en",completion:{if $0==nil {failed += 1}})
assert(failed==2 && queue.pending.isEmpty)
let cancelled=queue.enqueue(texts:["cancelled":"text"],from:"en",to:"ru",completion:{_ in fatalError("late cancelled result")})!
let cancelledJob=queue.begin()!
queue.cancel(jobId:cancelled.0,subscriberId:cancelled.1)
assert(queue.begin()==nil && queue.active != nil)
for c in queue.finish(jobId:cancelledJob.id,result:["cancelled":"текст"]) {c()}
assert(queue.workItems==0)
// Missing/empty result is failure, not a cached untranslated original.
_ = queue.enqueue(texts:["partial":"hello"],from:"en",to:"ru",completion:{if $0==nil {failed += 1}})
let partial=queue.begin()!
for c in queue.finish(jobId:partial.id,result:[:]) {c()}
assert(failed==3)
for i in 0..<300 {
 let k="cache\(i)"; _ = queue.enqueue(texts:[k:"hello"],from:"en",to:"ru",completion:{ _ in })
 let j=queue.begin()!;for c in queue.finish(jobId:j.id,result:[k:"привет"]) {c()}
 assert(queue.cacheItems<=256 && queue.cacheBytes<=1024*1024)
}
let timeoutQueue=JerkgramTranslationQueue()
var timeoutNotified=0
_ = timeoutQueue.enqueue(texts:["timeout":"hello"],from:"en",to:"ru",completion:{if $0==nil {timeoutNotified += 1}})
let timedJob=timeoutQueue.begin()!
for callback in timeoutQueue.expire(jobId:timedJob.id) {callback()}
assert(timeoutNotified==1 && timeoutQueue.active != nil && timeoutQueue.begin()==nil)
for callback in timeoutQueue.finish(jobId:timedJob.id,result:["timeout":"привет"]) {callback()}
assert(timeoutNotified==1 && timeoutQueue.workItems==0 && timeoutQueue.cacheItems==0)
let byteQueue=JerkgramTranslationQueue()
for i in 0..<8 { _ = byteQueue.enqueue(texts:["bytes\(i)":String(repeating:"я",count:8192)],from:"ru",to:"en",completion:{ _ in }) }
assert(byteQueue.workItems==8 && byteQueue.workBytes==128*1024)
var byteRejected=false
_ = byteQueue.enqueue(texts:["byteOverflow":"x"],from:"en",to:"ru",completion:{if $0==nil {byteRejected=true}})
assert(byteRejected && byteQueue.workItems==8)
print("local translation bounded queue PASS")
'''
FINGERPRINT_MOCKS = 'import CryptoKit\nvar hashCalls = 0\nfunc sha256Digest(_ data: Data) -> Data { hashCalls += 1; return Data(SHA256.hash(data: data)) }\nfinal class PostboxEncoder {\n var fields: [String: Data] = [:]\n private func store<T: Encodable>(_ value: T, _ key: String) { let encoder=JSONEncoder();encoder.outputFormatting=[.sortedKeys];fields[key]=try! encoder.encode(value) }\n func encodeString(_ value: String, forKey key: String) { store(value,key) }\n func encodeBool(_ value: Bool, forKey key: String) { store(value,key) }\n func encodeObjectArray<T: Encodable>(_ value: [T], forKey key: String) { store(value,key) }\n func makeData() -> Data { let encoder=JSONEncoder();encoder.outputFormatting=[.sortedKeys];return try! encoder.encode(fields) }\n}\nstruct Entity: Codable { let kind: String; let offset: Int }\nfinal class Entities { let entities: [Entity];init(_ entities:[Entity]) {self.entities=entities} }\nfinal class RichTextMessageAttribute {}\nfinal class AudioTranscriptionMessageAttribute { let text:String;let isPending:Bool;init(_ text:String,_ pending:Bool=false){self.text=text;self.isPending=pending} }\nfinal class GhostBaseMessageAttribute { let isDeleted:Bool;init(_ deleted:Bool){self.isDeleted=deleted} }\nstruct Option: Codable { let text:String;let entities:[Entity];let opaqueIdentifier:String }\nstruct Solution { let text:String;let entities:[Entity] }\nstruct Results { let solution:Solution?;let votes:Int }\nfinal class TelegramMediaPoll {\n let text:String;let textEntities:[Entity];let options:[Option];let results:Results\n init(_ text:String, options:[Option], solution:Solution?=nil,votes:Int=0){self.text=text;self.textEntities=[];self.options=options;self.results=Results(solution:solution,votes:votes)}\n}\nfinal class Message {\n let id:Int=1;let threadId:Int?=nil;let text:String;let textEntitiesAttribute:Entities?;let attributes:[AnyObject];let media:[AnyObject]\n init(_ text:String="",entities:[Entity]=[],attributes:[AnyObject]=[],media:[AnyObject]=[]) {self.text=text;self.textEntitiesAttribute=Entities(entities);self.attributes=attributes;self.media=media}\n}\n'
FINGERPRINT_CHECKS = 'let original=Message("Hello")\nlet fingerprint=jerkgramTranslationSourceFingerprint(original)\nlet translation=TranslationMessageAttribute(toLang:"ru",fingerprint:fingerprint)\nassert(translation.isValidForMessage(original))\nlet afterFirst=hashCalls\nassert(translation.isValidForMessage(original) && hashCalls==afterFirst) // no per-layout hashing\nassert(!translation.isValidForMessage(Message("Changed")))\nassert(!translation.isValidForMessage(Message("Hello",entities:[Entity(kind:"bold",offset:0)])))\nassert(!translation.isValidForMessage(Message("Hello",attributes:[GhostBaseMessageAttribute(true)])))\nassert(!translation.isValidForMessage(Message("Hello",attributes:[RichTextMessageAttribute()])))\nlet options=[Option(text:"Yes",entities:[],opaqueIdentifier:"y"),Option(text:"No",entities:[],opaqueIdentifier:"n")]\nlet poll=Message(media:[TelegramMediaPoll("Question",options:options)])\nlet pollHash=jerkgramTranslationSourceFingerprint(poll)\nassert(pollHash==jerkgramTranslationSourceFingerprint(Message(media:[TelegramMediaPoll("Question",options:options,votes:5)])))\nassert(pollHash != jerkgramTranslationSourceFingerprint(Message(media:[TelegramMediaPoll("Changed",options:options)])))\nassert(pollHash != jerkgramTranslationSourceFingerprint(Message(media:[TelegramMediaPoll("Question",options:Array(options.reversed()))])))\nassert(pollHash != jerkgramTranslationSourceFingerprint(Message(media:[TelegramMediaPoll("Question",options:options,solution:Solution(text:"Answer",entities:[]))])))\nlet audio=Message(attributes:[AudioTranscriptionMessageAttribute("speech")])\nlet audioHash=jerkgramTranslationSourceFingerprint(audio)\nassert(audioHash != jerkgramTranslationSourceFingerprint(Message(attributes:[AudioTranscriptionMessageAttribute("changed")])))\nassert(audioHash != jerkgramTranslationSourceFingerprint(Message(attributes:[AudioTranscriptionMessageAttribute("speech",true)])))\nassert(jerkgramLocalMessageTexts(audio)==["speech"])\nassert(jerkgramLocalMessageTexts(Message("caption",attributes:[AudioTranscriptionMessageAttribute("speech")]))==nil)\nassert(jerkgramLocalTranslationIsCurrent(translation,message:original,toLang:"ru"))\nassert(!jerkgramLocalTranslationIsCurrent(translation,message:original,toLang:"en"))\nlet cloud=TranslationMessageAttribute(toLang:"ru",fingerprint:nil)\nassert(cloud.isValidForMessage(original)) // existing cloud cache remains backward compatible\nassert(!jerkgramLocalTranslationIsCurrent(cloud,message:original,toLang:"ru")) // local requests replace unversioned cache\nweak var released:Message?\ndo {let temporary=Message("Hello");released=temporary;assert(translation.isValidForMessage(temporary))}\nassert(released==nil) // validity cache cannot retain old history\nprint("translation source fingerprint/cache validity PASS")\n\nlet failed=TranslationMessageAttribute(toLang:"ru",fingerprint:fingerprint,unavailable:true)\nlet failedMessage=Message("Hello",attributes:[failed])\nassert(jerkgramLocalTranslationUnavailable(failedMessage,toLang:"ru"))\nassert(!jerkgramLocalTranslationUnavailable(failedMessage,toLang:"en"))\nassert(!jerkgramLocalTranslationIsCurrent(failed,message:failedMessage,toLang:"ru"))\n'
if __name__=='__main__':unittest.main()
