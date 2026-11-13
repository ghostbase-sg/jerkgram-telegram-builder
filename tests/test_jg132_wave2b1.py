"""Actual-owner regressions and mandatory native capture/Settings typechecks."""
from pathlib import Path
import os, platform, shutil, subprocess, sys, tempfile, unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('JG_WAVE2B1_SOURCE',ROOT.parent/'jerkgram-next/wave2b1-source'))
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'scripts')]
from test_jg131_beta2_bot_codec import declaration
SETTINGS='submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift'
CORE='submodules/TelegramCore/Sources/Utils/JerkgramPerformanceDiagnostics.swift'
TAGS='submodules/TelegramUI/Sources/ChatSearchTitleAccessoryPanelNode.swift'
def read(name):return (SOURCE/name).read_text()
def settings_model():
    text=read(SETTINGS);text=text[text.index('private enum GhostBaseSettingsEntry:'):]
    text=text[:text.index('    func item(')]+'}\n'
    return '''import Foundation
typealias ItemListSectionId = Int32
protocol ItemListNodeEntry: Comparable {}
struct EnginePeer: Equatable {}
enum GhostBaseSettingsPage { case test; var title: String { "test" } }
'''+text+'''
private let savedOn = GhostBaseSettingsEntry.toggle(1,1,"key","title",true,enabled:true)
private let savedOff = GhostBaseSettingsEntry.toggle(1,1,"key","title",true,enabled:false)
precondition(savedOn != savedOff, "master changes must invalidate native list rows")
precondition(savedOn.stableId == savedOff.stableId)
private let boostOn = GhostBaseSettingsEntry.downloadBoost(2,1,"maximum",enabled:true)
private let boostOff = GhostBaseSettingsEntry.downloadBoost(2,1,"maximum",enabled:false)
precondition(boostOn != boostOff)
precondition(GhostBaseSettingsEntry.input(1,2,"k","t","0") == .input(1,2,"k","t","0"))
precondition(GhostBaseSettingsEntry.toggle(1,1,"key","title",true) == savedOn)
print("Actual Settings enum typechecked; OFF/ON row identity and saved values preserved")
'''

def profile_probe_fixture():
    name='submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift'
    before=(ROOT.parent/'jerkgram-next/wave2b1-before'/name).read_text() if (ROOT.parent/'jerkgram-next/wave2b1-before'/name).is_file() else None
    # In CI use the exact inverse stage view, never a personal workspace.
    if before is None:
        from jg132_post181 import stage_source_view
        from jg132_beta3_stages import parent_source_view
        with stage_source_view(SOURCE,'post182-wave2b1-followup') as current, parent_source_view(current,'post182-wave2b1-followup') as parent:
            before=(parent/name).read_text()
    old=declaration(before,'final class JerkgramProfilePerformanceProbe')
    new=declaration(read(name),'final class JerkgramProfilePerformanceProbe')
    facade='''import Foundation
final class JerkgramPerformanceDiagnostics {
 static let shared=JerkgramPerformanceDiagnostics()
 var isRecording=false; var measureCalls=0; var recordCalls=0
 func measure(_ stage:String,milliseconds:Double,startedAt:Double?=nil,owner:Int?=nil) {measureCalls += 1}
 func record(_ text:String) {recordCalls += 1}
}
final class Logger {static let shared=Logger();var calls=0;func log(_ topic:String,_ text:String) {calls += 1}}
'''
    return facade+old.replace('class JerkgramProfilePerformanceProbe','class Before')+'\n'+new.replace('class JerkgramProfilePerformanceProbe','class After')+'''
let diagnostics=JerkgramPerformanceDiagnostics.shared
let before=Before();before.context="settings"
for _ in 0..<1000 { let time=before.begin(.header);before.end(.header,time) }
before.summary("fixture",sourceRetained:false,outputRetained:false)
precondition(diagnostics.measureCalls==1000 && diagnostics.recordCalls==1 && Logger.shared.calls==1)
diagnostics.measureCalls=0;diagnostics.recordCalls=0;Logger.shared.calls=0
let after=After();after.context="settings"
for _ in 0..<1000 { let time=after.begin(.header);precondition(time==0);after.end(.header,time) }
after.summary("fixture",sourceRetained:false,outputRetained:false)
precondition(diagnostics.measureCalls==0 && diagnostics.recordCalls==0 && Logger.shared.calls==0)
diagnostics.isRecording=true
for _ in 0..<1000 { let time=after.begin(.header);precondition(time>0);after.end(.header,time) }
after.summary("fixture",sourceRetained:false,outputRetained:false)
precondition(diagnostics.measureCalls==1000 && diagnostics.recordCalls==1 && Logger.shared.calls==1)
print("Actual profile probe: 1000 OFF spans -> zero timing/record/logger calls; ON measurement retained. Facade counts, no UI-speed claim.")
'''

class Followup(unittest.TestCase):
    def test_tag_alert_and_menu_api_compatibility(self):
        text=read(TAGS)
        self.assertIn('import PresentationDataUtils', text)
        self.assertIn('"//submodules/PresentationDataUtils:PresentationDataUtils"', read('submodules/TelegramUI/BUILD'))
        error=declaration(text,'private func presentLocalTagError(')
        self.assertIn('textAlertController(context: self.context', error)
        local=declaration(text,'private func updateLocalSavedTags(')
        self.assertNotIn('icon: nil',local)
        self.assertIn('icon: { _ in nil }',local)

    def test_enabled_participates_in_native_entry_diff(self):
        text=read(SETTINGS)
        self.assertIn('case toggle(Int32, Int32, String, String, Bool, enabled: Bool = true)',text)
        arm=text.split('case let .toggle(ls,',1)[1].split('case let .input(',1)[0]
        self.assertIn('le == re',arm)
        page=text.split('if page == .localPremium {',1)[1].split('if page == .stars {',1)[0]
        self.assertEqual(page.count('enabled: masterEnabled'),7)
        self.assertIn('forName: JerkgramLocalPremiumPolicy.changed',text)
    def test_off_preview_uses_native_balance_and_flushes_switch(self):
        text=read('submodules/SettingsUI/Sources/Jerkgram/JerkgramGramEditorController.swift')
        self.assertIn('else if let nativeBalance',text)
        self.assertIn('formatTonAmountText(nativeBalance',text)
        self.assertIn('amount = "…"',text)
        switch=text.split('setEnabled: { value in',1)[1].split('setAmount:',1)[0]
        self.assertIn('autosave.flush()',switch)
        balance=read('submodules/AccountContext/Sources/JerkgramLocalGramBalance.swift')
        self.assertIn('guard enabled(accountPeerId: accountPeerId, defaults: defaults) else { return nil }',balance)
    def test_disabled_profile_probe_does_no_timing_or_logging(self):
        name='submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift'
        probe=declaration(read(name),'final class JerkgramProfilePerformanceProbe')
        self.assertIn('guard JerkgramPerformanceDiagnostics.shared.isRecording else { return 0 }',declaration(probe,'func begin('))
        self.assertIn('guard started > 0 else { return }',declaration(probe,'func end('))
        summary=declaration(probe,'func summary(')
        self.assertLess(summary.index('guard JerkgramPerformanceDiagnostics.shared.isRecording'),summary.index('Logger.shared.log'))
        # No new runtime recorder, frame loop or render/layout mutation.
        self.assertNotIn('CADisplayLink',probe)
        self.assertNotIn('DispatchSource',probe)
    def test_local_tag_bar_uses_actual_native_renderer_and_prompts(self):
        text=read(TAGS)
        local=declaration(text,'private func updateLocalSavedTags(')
        self.assertIn('view = ItemView(context:',local)
        self.assertNotIn('LocalButton(',local)
        self.assertNotIn('presentTagPremiumPaywall',local)
        self.assertNotIn('jerkgramPresentSavedTagsController',local)
        self.assertIn('savedTagNameAlertController',declaration(text,'private func openLocalTagEditor('))
        menu=read('submodules/TelegramUI/Sources/JerkgramSavedTagsController.swift')
        entry=declaration(menu,'func jerkgramPresentSavedTagsController(')
        self.assertIn('session.presentNative()',entry)
        self.assertNotIn('jerkgramSavedTagsController(',entry)
        self.assertIn('self.nativeSheet?.dismissAnimated()', declaration(menu,'func stop()'))
        self.assertIn('self.nativeNamePrompt?.dismissAnimated()', declaration(menu,'func stop()'))
        self.assertIn('self.localNamePrompt?.dismissAnimated()', text)
        self.assertIn('savedTagNameAlertController',declaration(menu,'private func nativeName('))
        self.assertNotIn('setSavedMessageTagTitle',declaration(menu,'private func nativeName('))
    def test_native_actual_owners(self):
        if not shutil.which('xcrun'):
            if os.environ.get('JG_STABLE182_REQUIRE_NATIVE')=='1':self.fail('Wave2B.1 native owner checks require macOS')
            self.skipTest('macOS native owner checks pending')
        with tempfile.TemporaryDirectory(prefix='wave2b1-native-') as directory:
            root=Path(directory)
            for label,source in [('settings',settings_model()),('profile-probe',profile_probe_fixture())]:
                main=root/'main.swift';main.write_text(source)
                output=root/label
                subprocess.run(['xcrun','swiftc','-O',str(main),'-o',str(output)],check=True,timeout=180)
                subprocess.run([str(output)],check=True,timeout=30)
if __name__=='__main__':unittest.main(verbosity=2)
