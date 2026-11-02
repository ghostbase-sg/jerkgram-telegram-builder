"""Task2 guards plus extracted production Swift fixtures, pending macOS Swift.
Facades replace transport/Signal/FileManager boundaries, never diagnostic policy.
"""
import hashlib,json,os,shutil,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TASK2=Path(os.environ.get('JERKGRAM_BOTBRIDGE_TASK2_ARTIFACTS',ROOT/'tests/fixtures/botbridge1/provenance'))
BEFORE=Path(os.environ.get('JERKGRAM_BOTBRIDGE_TASK2_BEFORE',ROOT/'work/botbridge-task1-view'))
SOURCE=Path(os.environ.get('JERKGRAM_BOTBRIDGE_SOURCE',str(ROOT/'work/swiftgram-src')))
CORE=SOURCE/'submodules/TelegramCore/Sources'
FIX=Path(__file__).parent/'fixtures/botbridge1'
def method(t,a):
 s=t.index(a); i=t.index('{',s)+1; d=1
 while d: d+=(t[i]=='{')-(t[i]=='}'); i+=1
 return t[s:i]
class DiagnosticsTests(unittest.TestCase):
 def diag(self):
  p=CORE/'State/JerkgramBotBridgeDiagnostics.swift'
  self.assertTrue(p.exists(),'missing production bounded diagnostics recorder/request/lifecycle implementation')
  return p.read_text()
 def test_production_privacy_boundary(self):
  t=self.diag()
  for bad in ['.parameters','.errorDescription','UserDefaults','Logger.','String(describing:', 'Mirror(']: self.assertNotIn(bad,t)
  self.assertIn('case readAck = "read_ack"',t)
 def test_scope_before_requests_and_restored_terminal(self):
  m=(CORE/'State/AccountStateManager.swift').read_text()
  start=method(m,'func jerkgramStartBotBridgeHistory(recordId: Int64, lifetime:')
  self.assertIn('admit(progress.generation)',start)
  self.assertLess(start.index('admit(progress.generation)'),start.index('let controller ='))
  h=(CORE/'State/JerkgramBotBridgeHistory.swift').read_text()
  self.assertIn('.restoredTerminal',method(h,'func start()'))
 def test_observer_cold_weak_and_original_fastpath(self):
  n=(CORE/'Network/Network.swift').read_text()
  for anchor in ['func request<T>(', 'func requestWithAdditionalInfo<T>(']:
   f=method(n,anchor)
   self.assertIn('[requestService, botBridgeRegistration]',f)
   self.assertLess(f.index('return Signal'),f.index('botBridgeRegistration.begin('))
   self.assertIn('guard let observation = observation else { return disposable }',f)
   self.assertNotIn('[self]',f)
   self.assertIn('observation?.finish(.parseFailure',f)
   self.assertIn('observation?.finish(.rpcFailure',f)
  self.assertIn('acknowledged: nil',method(n,'func request<T>('))
 def test_modern_worker_normalization(self):
  manifest=TASK2/'MODERN-WRITE-PROOF.json'
  self.assertTrue(manifest.exists(),'missing exact allowed-diff proof')
  proof=json.loads(manifest.read_text())
  frozen={row['path']:row['sha256'] for row in json.loads((TASK2/'MODERN-WRITE-BASELINE.json').read_text())['files']}
  for row in proof['files']:
   self.assertEqual(row['modern_sha256'],frozen[row['path']])
   after=(SOURCE/row['path']).read_text()
   # The proof stores a deterministic ordered edit list; reverse each exact occurrence.
   for edit in reversed(row['edits']):
    self.assertIn(edit['after'],after); after=after.replace(edit['after'],edit['before'],1)
   self.assertEqual(hashlib.sha256(after.encode()).hexdigest(),row['modern_sha256'],row['path'])
 def test_exact_network_observer_normalization(self):
  path='submodules/TelegramCore/Sources/Network/Network.swift'
  text=(SOURCE/path).read_text()
  allowed=[('    let botBridgeRegistration = BotBridgeScopeRegistration()\n',''),('            self?.botBridgeRegistration.lifecycle(.authKeyUnknown)\n',''),(', diagnosticContext: BotBridgeOperationContext? = nil',''),('        let botBridgeRegistration = self.botBridgeRegistration\n',''),('[requestService, botBridgeRegistration]','[requestService]'),('            let observation = botBridgeRegistration.begin(method: data.0.name, context: diagnosticContext)\n',''),('                    observation?.acknowledge()\n',''),('                            observation?.finish(.result)\n',''),('                            observation?.finish(.parseFailure, errorCode: 500)\n',''),('                        observation?.finish(.rpcFailure, errorCode: failure.error.errorCode)\n',''),('            let disposable = requestService.add(request)\n            guard let observation = observation else { return disposable }\n            return ActionDisposable {\n                observation.cancel()\n                disposable.dispose()\n            }','            return requestService.add(request)')]
  for after,before in allowed:
   self.assertIn(after,text)
   text=text.replace(after,before)
  self.assertEqual(text,(BEFORE/path).read_text(),'Network algorithms/policy/metadata/deps must recover byte for byte')
  frozen={row['path']:row['sha256'] for row in json.loads((TASK2/'MODERN-WRITE-BASELINE.json').read_text())['files']}
  self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),frozen[path])
 def test_remaining_modern_owners_unchanged(self):
  baseline=json.loads((TASK2/'MODERN-WRITE-BASELINE.json').read_text())
  # Task1's already accepted changes have their own immutable provenance proof.
  accepted={'Account/Account.swift','Authorization.swift','State/AccountStateManager.swift','State/AccountStateManagementUtils.swift'}
  normalized={'State/PendingMessageManager.swift','PendingMessages/StandaloneSendMessage.swift','Network/Network.swift'}
  for row in baseline['files']:
   relative=row['path'].removeprefix('submodules/TelegramCore/Sources/')
   if relative not in accepted|normalized:
    self.assertEqual(hashlib.sha256((SOURCE/row['path']).read_bytes()).hexdigest(),row['sha256'],row['path'])
 def test_cold_logout_and_weak_export(self):
  a=(CORE/'Account/AccountManager.swift').read_text(); f=method(a,'public func logoutFromAccount(')
  self.assertLess(f.index('return Signal'),f.index('BotBridgeDiagnosticRegistry.shared.notify'))
  self.assertIn('reconcile(namespace: accountManager',a)
  ui=SOURCE/'submodules/SettingsUI/Sources/Jerkgram'
  self.assertIn('case "botbridgeDiagnostics":',(ui/'JerkgramDataAndBackupController.swift').read_text())
  helper=method((ui/'JerkgramArchiveFlowController.swift').read_text(),'public func jerkgramPresentBotBridgeDiagnosticExport(')
  self.assertIn('[weak controller]',helper)
  self.assertIn('jerkgramReleaseBotBridgeDiagnosticExport',helper)
 def test_review_fix_generation_bound_lifecycle(self):
  d=self.diag(); a=(CORE/'Account/AccountManager.swift').read_text()
  self.assertIn('final class BotBridgeDiagnosticTarget',d,'deferred lifecycle token must bind original generation/epoch')
  self.assertIn('let diagnosticTarget = BotBridgeDiagnosticRegistry.shared.target(',a)
  self.assertIn('notify(target: diagnosticTarget, kind: .cleanupResult)',a)
 def test_review_fix_truthful_deletion_boundary(self):
  d=self.diag(); a=(CORE/'Account/AccountManager.swift').read_text()
  self.assertNotIn('value.lifecycle(.deletionScheduled)',method(d,'func reconcile('))
  self.assertIn('botBridgeScheduleAccountDirectoryDeletion(directoryName:',a)
  b=a[a.index('for (id, _, _) in beginList {'):] if 'for (id, _, _) in beginList {' in a else ''
  self.assertFalse(b,'beginList preserves validPaths; it must not imply deletion scheduling')
 def test_review_fix_enumeration_fails_closed(self):
  d=self.diag()
  self.assertIn('private func files() throws -> [URL]',d)
  self.assertNotIn('?? []',method(d,'private func files('))
  self.assertIn('try self.files()',method(d,'func export('))
  self.assertIn('listDirectory: @escaping',d,'actual filesystem enumeration needs an injectable boundary')
 def test_final_review_record_ttl_is_physical_and_bounded(self):
  d=self.diag(); prune=method(d,'private func prune(')
  self.assertIn('value.wall >= cutoff',prune,'retention must inspect record age even when atomic rewrite refreshes mtime')
  self.assertIn('retained.count > 8',prune)
  self.assertLess(prune.index('retained.count > 8'),prune.index('Data(contentsOf:'))
  self.assertIn('kept.write(to: url, options: .atomic)',prune,'expired physical records must be removed, not export-filtered only')
  self.assertIn('self.expiredRecords',prune)
 def test_final_review_registry_denials_are_export_visible_without_sink(self):
  d=self.diag(); registry=method(d,'final class BotBridgeDiagnosticRegistry')
  register=method(registry,'func register(')
  for reason in ['capacity','duplicateTarget','invalidGeneration']: self.assertIn('botBridgeIncrement(&deniedAdmissions.'+reason+')',register,'admission failure reasons must have separate finite counters')
  self.assertIn('admissionDenied: BotBridgeDiagnosticRegistry.shared.admissionLoss',method(d,'func export('))
  self.assertIn('let admissionDenied: BotBridgeDiagnosticAdmissionLoss',method(d,'private struct BotBridgeDiagnosticEnvelope'))
  self.assertNotIn('BotBridgeDiagnosticSink',registry,'registry rejection must not allocate a sink or schedule I/O')
 def test_native_final_review_physical_record_ttl(self):
  d=self.diag().split('// BEGIN BOTBRIDGE DIAGNOSTICS\n')[1].split('// END BOTBRIDGE DIAGNOSTICS')[0]
  self.run_swift('import Foundation\n'+d+(FIX/'diagnostic_record_ttl.swift').read_text())
 def test_native_final_review_registry_admission_loss(self):
  d=self.diag().split('// BEGIN BOTBRIDGE DIAGNOSTICS\n')[1].split('// END BOTBRIDGE DIAGNOSTICS')[0]
  self.run_swift('import Foundation\n'+d+(FIX/'diagnostic_admission_loss.swift').read_text())
 def run_swift(self,text):
  compiler=shutil.which('swiftc')
  if compiler is None: self.skipTest('Swift unavailable on Linux: actual production native fixture pending macOS')
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'main.swift';src.write_text(text); exe=Path(d)/'fixture'
   result=subprocess.run([compiler,str(src),'-o',str(exe)],capture_output=True,text=True,timeout=90)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertIn('PASS',result.stdout)
 def test_native_actual_recorder_registry_sink(self):
  t=self.diag(); foundation=t.split('// BEGIN BOTBRIDGE DIAGNOSTICS\n')[1].split('// END BOTBRIDGE DIAGNOSTICS')[0]
  self.run_swift('import Foundation\n'+foundation+(FIX/'diagnostics.swift').read_text())
 def test_native_filesystem_failure_policy(self):
  d=self.diag().split('// BEGIN BOTBRIDGE DIAGNOSTICS\n')[1].split('// END BOTBRIDGE DIAGNOSTICS')[0]
  self.run_swift('import Foundation\n'+d+(FIX/'diagnostic_filesystem_failure.swift').read_text())
 def test_native_actual_sink_resources(self):
  d=self.diag().split('// BEGIN BOTBRIDGE DIAGNOSTICS\n')[1].split('// END BOTBRIDGE DIAGNOSTICS')[0]
  self.run_swift('import Foundation\n'+d+(FIX/'diagnostic_resources.swift').read_text())
 def test_native_actual_logout_registry(self):
  d=self.diag().split('// BEGIN BOTBRIDGE DIAGNOSTICS\n')[1].split('// END BOTBRIDGE DIAGNOSTICS')[0]
  a=(CORE/'Account/AccountManager.swift').read_text()
  self.run_swift('import Foundation\n'+d+(FIX/'diagnostic_lifecycle.swift').read_text().replace('/* REAL_LOGOUT */',method(a,'public func logoutFromAccount(')))
 def test_history_export_fixture_extracts_actual_adapter(self):
  d=self.diag()
  self.assertIn('func botBridgeDiagnosticHistory(',d,'history export mapping requires direct fixture execution')
  adapter=method(d,'func botBridgeDiagnosticHistory(')
  self.assertIn('reservedAttempts: event.reservedRequests',adapter)
  self.assertIn('insertedChats: event.insertedChats',adapter)
 def test_native_history_export_adapter(self):
  d=self.diag(); h=(CORE/'State/JerkgramBotBridgeHistory.swift').read_text()
  policy=h.split('// BEGIN BOTBRIDGE POLICY\n')[1].split('// END BOTBRIDGE POLICY')[0]
  foundation=d.split('// BEGIN BOTBRIDGE DIAGNOSTICS\n')[1].split('// END BOTBRIDGE DIAGNOSTICS')[0]
  adapter=method(d,'private func botBridgeDiagnosticTuple(')+'\n'+method(d,'func botBridgeDiagnosticHistory(')
  self.run_swift('import Foundation\n'+policy+'\n'+method(h,'struct BotBridgeHistoryEvent')+'\n'+foundation+'\n'+adapter+'\n'+(FIX/'diagnostic_history_export.swift').read_text())
 def test_native_actual_request_boundary(self):
  self.diag()
  n=(CORE/'Network/Network.swift').read_text(); d=self.diag().split('// BEGIN BOTBRIDGE DIAGNOSTICS\n')[1].split('// END BOTBRIDGE DIAGNOSTICS')[0]
  f=(FIX/'diagnostic_requests.swift').read_text().replace('/* REAL_REQUESTS */',method(n,'func request<T>(')+'\n'+method(n,'func requestWithAdditionalInfo<T>(')).replace('/* REAL_WORKER_CONTEXT */',method(self.diag(),'func botBridgeOperationContext('))
  self.run_swift('import Foundation\n'+d+f)
 def test_final_history_core_and_poll_unchanged(self):
  h=(CORE/'State/JerkgramBotBridgeHistory.swift').read_text(); before=(BEFORE/'submodules/TelegramCore/Sources/State/JerkgramBotBridgeHistory.swift').read_text()
  self.assertEqual(h.split('// BEGIN BOTBRIDGE POLICY\n')[1].split('// END BOTBRIDGE POLICY')[0],before.split('// BEGIN BOTBRIDGE POLICY\n')[1].split('// END BOTBRIDGE POLICY')[0])
  for name in ['private func importBotBridgeHistoryPage(', 'private final class BotBridgePageLease', 'private func botBridgePage(', 'private func botBridgeValidatedAccount(']: self.assertEqual(method(h,name),method(before,name))
  m=(CORE/'State/AccountStateManager.swift').read_text()
  self.assertIn((TASK2/'MODERN-POLL-DIFFERENCE-BASELINE.swift.txt').read_text(),m)
  self.assertEqual(method(m,'func addCustomOperation<T, E>'),method((BEFORE/'submodules/TelegramCore/Sources/State/AccountStateManager.swift').read_text(),'func addCustomOperation<T, E>'))
 def test_native_final_postbox_callbacks(self):
  text=(SOURCE/'submodules/Postbox/Sources/Postbox.swift').read_text()
  impl=method(text,'fileprivate func addMessages(transaction:')
  entries=method(text,'public func addMessages(')+'\n'+method(text,'public func addHistoricalMessagesWithoutInteractiveActions(')
  fixture=(FIX/'postbox.swift').read_text().replace('/* REAL_IMPL */',impl).replace('/* REAL_ENTRIES */',entries)
  self.run_swift(fixture)
 def test_native_final_actual_history_controller(self):
  text=(CORE/'State/JerkgramBotBridgeHistory.swift').read_text()
  policy=text.split('// BEGIN BOTBRIDGE POLICY\n')[1].split('// END BOTBRIDGE POLICY')[0]
  shared=(FIX/'storage.swift').read_text().split('/* REAL_STORAGE */')[0].replace('/* REAL_POLICY */',policy)
  shared+='\nextension AuthorizedAccountState { struct Live { let pts: Int32 = 7; let qts: Int32 = 8; let date: Int32 = 9; let seq: Int32 = 10 }; var state: Live? { Live() } }\n'
  names=['struct BotBridgeHistoryEvent','private func botBridgeValidatedAccount(','private func botBridgeReadProgress(','func jerkgramPrepareBotBridgeHistory(','private func botBridgeWriteProgress(','func botBridgeObservedLive(','private func botBridgeCursor(','private struct BotBridgeHistoryPage','private func botBridgePage(','private func botBridgeReplyPeerIds(','private func importBotBridgeHistoryPage(','private final class BotBridgePageLease','final class BotBridgeHistoryController']
  fixture=(FIX/'controller.swift').read_text().replace('/* SHARED_STORAGE_FACADES */',shared).replace('/* REAL_CONTROLLER_AND_DEPENDENCIES */','\n'.join(method(text,n) for n in names))
  fixture+='\n' + (FIX/'diagnostic_history.swift').read_text()
  self.run_swift(fixture)
if __name__=='__main__': unittest.main()
