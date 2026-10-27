from pathlib import Path
import os,shutil,subprocess,tempfile,unittest
ROOT=Path(os.environ.get('JG_TRANSLATION_SOURCE',Path(__file__).resolve().parents[1]/'work/swiftgram-src'))
class DownloadPolicyTests(unittest.TestCase):
 def test_background_preflight_before_apple_translation_and_manual_only_opt_in(self):
  s=(ROOT/'submodules/TranslateUI/Sources/Translate.swift').read_text()
  body=s.split('.translationTask(self.configuration',1)[1]
  self.assertIn('LanguageAvailability().status(from:',body)
  self.assertLess(body.index('canTranslate(jobId:'),body.index('try await translationSession.translations('))
  self.assertIn('TranslationSession(installedSource:',body)
  self.assertIn('allowDownloads: true',s.split('public func jerkgramTranslateText',1)[1])
  self.assertIn('self.translate(texts: texts, fromLang: fromLang, toLang: toLang, allowDownloads: false)',s)
 @unittest.skipUnless(shutil.which('swiftc'),'actual production queue fixture requires Swift on CI')
 def test_actual_queue_download_intent_and_cancelled_preflight(self):
  s=(ROOT/'submodules/TranslateUI/Sources/Translate.swift').read_text().split('// JG174 translation queue begin',1)[1].split('// JG174 translation queue end',1)[0]
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'main.swift';p.write_text('import Foundation\n'+s.replace('private final class JerkgramTranslationQueue','final class JerkgramTranslationQueue',1)+CHECKS)
   subprocess.run(['swiftc',str(p),'-o',d+'/check'],check=True);subprocess.run([d+'/check'],check=True)
CHECKS=r'''
let q=JerkgramTranslationQueue()
let automatic=q.enqueue(texts:["x":"hello"],from:"en",to:"ru",completion:{_ in })!
let manual=q.enqueue(texts:["x":"hello"],from:"en",to:"ru",allowDownloads:true,completion:{_ in })!
assert(automatic.0 != manual.0) // background requests never inherit interactive consent
let first=q.begin()!
assert(!q.canTranslate(jobId:first.id,installed:false))
assert(q.canTranslate(jobId:first.id,installed:true))
q.cancel(jobId:automatic.0,subscriberId:automatic.1)
assert(!q.canTranslate(jobId:first.id,installed:true))
for callback in q.finish(jobId:first.id,result:nil) {callback()}
let second=q.begin()!
assert(q.canTranslate(jobId:second.id,installed:false))
q.cancel(jobId:manual.0,subscriberId:manual.1)
assert(!q.canTranslate(jobId:second.id,installed:false))
for callback in q.finish(jobId:second.id,result:nil) {callback()}
assert(q.workItems==0 && q.pending.isEmpty)
print("download intent, missing model, canceled availability check PASS")
'''
if __name__=='__main__': unittest.main()
