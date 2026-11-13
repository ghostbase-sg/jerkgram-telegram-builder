"""Actual Settings feed construction/lifecycle before vs after; boundary facades."""
from pathlib import Path
import hashlib, os, shutil, subprocess, sys, tempfile, unittest
import test_jg131_beta2_bot_codec as codec
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from jg132_wave2a2 import OWNER, STAGE, apply, green_view
from jg132_beta3_stages import manifest
SOURCE=Path(os.environ.get('JG_WAVE2A2_SOURCE',ROOT/'work/swiftgram-src'))
FIX=ROOT/'tests/fixtures/wave2a2'

def assembled(source, fixed):
    text=(source/OWNER).read_text()
    controller=codec.declaration(text,'private final class JerkgramDiagnosticSettingsController').replace('private final class','final class',1)
    state=codec.declaration(text,'private enum JerkgramAboutChannelState').replace('private enum','enum',1)
    anchor='    let aboutVisibility = ' if fixed else '    let aboutChannelSignal = '
    start=text.index(anchor);end=text.index('    var openAboutChannelImpl:',start)
    creation=text[start:end]
    callback=''
    if fixed:
        callback=codec.declaration(text,'    if page == .about {\n        controller.aboutVisibilityChanged')
    helper=codec.declaration(text,'private func jerkgramVisibleFeed<T>') if fixed else ''
    return (FIX/'lifecycle-boundaries.swift').read_text()+'\n'+state+'\n'+controller+'\n'+helper+'\nprivate func makeOwner(_ context: AccountContext, page: Page) -> JerkgramDiagnosticSettingsController {\n'+creation+'\nlet controller = JerkgramDiagnosticSettingsController()\n'+callback+'\ncontroller.feeds = [aboutChannelSignal.start(next: { _ in context.tracker.deliveries += 1 }), aboutCommunitySignal.start(next: { _ in context.tracker.deliveries += 1 })]\nreturn controller\n}\nlet fixed = '+str(fixed).lower()+'\n'+(FIX/'lifecycle-matrix.swift').read_text()

class Lifecycle(unittest.TestCase):
    def test_exact_one_owner_reapply_reverse_and_refusal(self):
        m=manifest(STAGE);self.assertEqual(set(m['owners']),{OWNER})
        names=set(m['owners'])|set(m['parent_owners'])
        with green_view(SOURCE) as green,tempfile.TemporaryDirectory(prefix='wave2a2-stage-') as d:
            trial=Path(d)
            for name in names:
                if (green/name).is_file():
                    target=trial/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(green/name,target)
            before=(trial/OWNER).read_bytes();apply(trial);after=(trial/OWNER).read_bytes();apply(trial)
            self.assertEqual((trial/OWNER).read_bytes(),after)
            with green_view(trial) as restored:self.assertEqual((restored/OWNER).read_bytes(),before)
            (trial/OWNER).write_bytes(after+b'\n// changed\n');bad=(trial/OWNER).read_bytes()
            with self.assertRaises(RuntimeError):apply(trial)
            self.assertEqual((trial/OWNER).read_bytes(),bad)
    def test_actual_before_after_assembly(self):
        with green_view(SOURCE) as before:
            for fixed,path in ((False,before),(True,SOURCE)):
                code=assembled(path,fixed)
                self.assertIn('aboutCommunitySignal.start',code)
                self.assertIn('deinit {',code)
                self.assertNotIn('/* REAL_',code)
    def test_native_before_after_lifecycle_counts(self):
        if not shutil.which('xcrun'):
            if os.environ.get('JG_WAVE2A2_REQUIRE_NATIVE')=='1':self.fail('Wave2A2 requires native Swift/xcrun')
            self.skipTest('macOS Swift unavailable; component counts pending')
        with green_view(SOURCE) as before,tempfile.TemporaryDirectory(prefix='wave2a2-native-') as d:
            for fixed,path in ((False,before),(True,SOURCE)):
                main=Path(d)/'main.swift';main.write_text(assembled(path,fixed))
                for optimization in ('-Onone','-O'):
                    executable=Path(d)/'lifecycle'
                    compile=subprocess.run(['xcrun','swiftc','-swift-version','5','-warnings-as-errors',optimization,str(main),'-o',str(executable)],text=True,capture_output=True,timeout=120)
                    self.assertEqual(compile.returncode,0,compile.stdout+compile.stderr)
                    result=subprocess.run([str(executable)],text=True,capture_output=True,timeout=20)
                    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                    print(result.stdout.strip(),flush=True)

if __name__=='__main__':unittest.main(verbosity=2)
