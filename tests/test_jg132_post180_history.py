"""Actual replay/controller/codec fixtures; native execution requires macOS."""
from pathlib import Path
import os, shutil, subprocess, tempfile, unittest
import test_jg131_beta2_bot_codec as codec
import test_jg132_bot_reset_recovery as recovery

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('JG_POST180_SOURCE',ROOT/'work/swiftgram-src'))
CORE=SOURCE/'submodules/TelegramCore/Sources'
FIX=ROOT/'tests/fixtures/post180'

def policy():
    original=(CORE/'State/JerkgramBotBridgeHistory.swift').read_text()
    return 'import Foundation\n'+codec.policy(original)+'\n'+(CORE/'State/JerkgramBotReplayPolicy.swift').read_text()

def controller():
    recovery.CORE=CORE
    assembled=recovery.controller_main().split('// R1: suspended reservation')[0]
    queue='func async(_ f: @escaping () -> Void) { tasks.append(f) }'
    after='func after(_ delay: Double, _ f: @escaping () -> Void) { let t = SwiftSignalKit.Timer(timeout: delay, repeat: false, completion: f, queue: self); t.start() }'
    assert assembled.count(queue)==1
    assembled=assembled.replace('enqueue: { manager.enqueue($0) }, ','').replace('let queue = self.queue, manager = self.manager, clock = self.clock','let queue = self.queue, clock = self.clock')
    return assembled.replace(queue,queue+'\n'+after)+'\n'+(CORE/'State/JerkgramBotReplayPolicy.swift').read_text()+'\n'+(FIX/'history-controller.swift').read_text()

class History(unittest.TestCase):
    def test_actual_fixture_assembly(self):
        code=controller()
        self.assertIn(codec.declaration((CORE/'State/JerkgramBotBridgeHistory.swift').read_text(),'final class BotBridgeHistoryController'),code)
        self.assertNotIn('/* REAL_',code)
        self.assertIn('24600',code)
    def test_actual_policy_codec_and_controller_native(self):
        if not shutil.which('xcrun'):
            if os.environ.get('JG_BETA3_REQUIRE_NATIVE')=='1':self.fail('post180 requires native Swift/Clang/xcrun')
            self.skipTest('native replay execution requires macOS')
        codec.OWNER=CORE/'State/JerkgramBotBridgeHistory.swift'
        with tempfile.TemporaryDirectory(prefix='post180-history-') as directory:
            folder=Path(directory)
            for opt in ('-Onone','-O'):
                executable=codec.compile_fixture(folder,opt,main_override=policy()+(FIX/'history-policy.swift').read_text())
                result=subprocess.run([str(executable)],capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                (folder/'controller.swift').write_text(controller())
                result=subprocess.run(['xcrun','swiftc','-swift-version','5','-warnings-as-errors',opt,str(folder/'controller.swift'),'-o',str(folder/'controller')],capture_output=True,text=True,timeout=120)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                result=subprocess.run([str(folder/'controller')],capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main(verbosity=2)
