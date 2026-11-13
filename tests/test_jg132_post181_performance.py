"""One Wave2A3 fix: reuse sorted per-chat cache ranges; actual Swift fragments/store."""
from pathlib import Path
import os, shutil, subprocess, sys, tempfile, unittest
from test_jg131_beta2_bot_codec import declaration
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
OWNER='submodules/JerkgramCore/Sources/JerkgramStore.swift'
SOURCE=Path(os.environ.get('JG_STABLE182_SOURCE',ROOT.parent/'jerkgram-next/stable182-perf'))
STAGE='post181-performance-wave2a3'

def production_pair():
    from jg132_beta3_stages import parent_source_view
    from jg132_post181 import stage_source_view
    from contextlib import ExitStack
    stack=ExitStack()
    after=stack.enter_context(stage_source_view(SOURCE,STAGE))
    before=stack.enter_context(parent_source_view(after,STAGE))
    return stack,before,after

def fragment(source):
    text=(source/OWNER).read_text()
    anchors=['    private func filteredRecords(', '    private func groupedRecordsByChat(',
             '    private func mergeAscending(', '    private func recordComesEarlier(']
    if '    private func sequenceUpperBound(' in text:anchors.append('    private func sequenceUpperBound(')
    return '\n'.join(declaration(text,a).replace('private func ', 'func ',1) for a in anchors)

def assembled(before,after):
    facade='''import Foundation
var reads=0
struct JerkgramEventId: Comparable { let value:Int; static func < (a:Self,b:Self)->Bool {a.value<b.value} }
struct JerkgramTimeMachineIndexRecord: Equatable {
 let rawSequence:Int64; let rawChat:Int64; let eventId:JerkgramEventId
 var sequence:Int64 { reads += 1; return rawSequence }
 var chatPeerId:Int64 { reads += 1; return rawChat }
}
'''
    return facade+'\nstruct Before {\n'+fragment(before)+'\n}\nstruct After {\n'+fragment(after)+'\n}\n'+(ROOT/'tests/fixtures/wave2a3/range-matrix.swift').read_text()

class CachedRange(unittest.TestCase):
    def test_exact_owner_and_production_assembly(self):
        holder,before,after=production_pair()
        with holder:
            self.assertIn('sequenceUpperBound',assembled(before,after))
            self.assertNotIn('sequenceUpperBound',fragment(before))
            from jg132_beta3_stages import manifest
            self.assertEqual(set(manifest(STAGE)['owners']),{OWNER})
            # Mutation is read-only query work, no persistence/flush/cleanup delta.
            old=(before/OWNER).read_text();new=(after/OWNER).read_text()
            self.assertEqual(old[:old.index('    private func filteredRecords(')],new[:new.index('    private func filteredRecords(')])
            self.assertEqual(old[old.index('    public func events('):],new[new.index('    public func events('):])

    def test_native_real_components(self):
        if not shutil.which('xcrun'):
            if os.environ.get('JG_STABLE182_REQUIRE_NATIVE')=='1':self.fail('Wave2A3 requires native Swift/xcrun')
            self.skipTest('Native component metrics pending macOS')
        holder,before,after=production_pair()
        with holder,tempfile.TemporaryDirectory(prefix='wave2a3-native-') as directory:
            path=Path(directory)
            cases=[('ranges',assembled(before,after))]
            for label,source in [('before',before),('after',after)]:
                text='\n'.join((source/'submodules/JerkgramCore/Sources'/name).read_text() for name in ['JerkgramModels.swift','JerkgramIndex.swift'])
                text+='\n'+declaration((source/OWNER).read_text(),'public protocol JerkgramEventStore')
                text+='\n'+declaration((source/OWNER).read_text(),'public final class JerkgramJSONLEventStore')
                text+='\n'+(ROOT/'tests/fixtures/wave2a3/store-matrix.swift').read_text()
                cases.append((label,text))
            for label,code in cases:
                (path/'main.swift').write_text(code)
                for opt in ['-Onone','-O']:
                    result=subprocess.run(['xcrun','swiftc','-swift-version','5',opt,str(path/'main.swift'),'-o',str(path/'test')],capture_output=True,text=True,timeout=120)
                    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                    result=subprocess.run([str(path/'test')],capture_output=True,text=True,timeout=60)
                    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                    print(label,opt,result.stdout.strip(),flush=True)

if __name__=='__main__':unittest.main(verbosity=2)
