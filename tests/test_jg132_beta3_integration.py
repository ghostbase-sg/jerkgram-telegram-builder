"""Common Beta3 pipeline keeps predecessors, new native checks and app dependency."""
from pathlib import Path
import json,os,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class Integration(unittest.TestCase):
 def test_earlier_native_owner_does_not_mark_baseline_as_beta3(self):
  sys.path.insert(0,str(ROOT/'scripts'))
  import jg132_baseline as baseline
  import jg132_beta3_stages as stages
  source=Path(os.environ.get('JG_BETA3_SOURCE',ROOT/'work/swiftgram-src'))
  with stages.baseline_source_view(source) as before:
   for order in (18,32):
    with baseline.source_boundary_view(before,order) as prefix:
     self.assertEqual(baseline.boundary(prefix),order)
     # Removing the old custom entry restores one genuine native owner to
     # upstream bytes, so that file already equals Beta3 at an early prefix.
     if order==18:
      m=stages.manifest(stages.STAGES[-1])
      self.assertTrue(any(stages.digest((prefix/n).read_bytes())==row['after_sha256'] for n,row in m['owners'].items() if (prefix/n).is_file()))
     self.assertFalse(stages.is_present(prefix))
 def test_common_identity_and_final_gate_order(self):
  c=json.loads((ROOT/'jerkgram-migration.json').read_text())
  self.assertEqual((c['build_number'],c['artifact_suffix'],c['upstream_new_version']),(180,'BETA3','13.2'))
  for n in ['scripts/build_jg13.sh','.github/workflows/no-ads-native.yml']:
   s=(ROOT/n).read_text()
   steps=['python3 tests/run_jg131_saved_tags.py --require-native --require-full-source',"python3 -m unittest discover -s tests -p 'test_jg1312*.py'",'python3 scripts/materialize_jg132_beta3.py','python3 tests/run_jg132_beta3.py --require-native --require-full-source']
   indices=[s.index(v) for v in steps];self.assertEqual(indices,sorted(indices))
   self.assertTrue(all(s.count(v)==1 for v in steps))
  s=(ROOT/'scripts/build_jg13.sh').read_text()
  self.assertLess(s.index('tests/run_jg132_beta3.py'),s.index('"${BAZEL_BIN:-bazelisk}" build'))
  self.assertIn('--define=buildNumber=180',s)
  s=(ROOT/'.github/workflows/build.yml').read_text()
  self.assertIn('needs: source-preflight',s)
  self.assertIn('      - dev/beta3-history-native-tags-180\n',s)
  for suffix in ['.ipa','.json']:self.assertIn('artifacts/Jerkgram-1.2.0-Build180-BETA3'+suffix,s)
 def test_native_gate_refuses_missing_toolchain(self):
  r=subprocess.run([sys.executable,str(ROOT/'tests/run_jg132_beta3.py'),'--require-native'],env=dict(os.environ,PATH=''),capture_output=True,text=True)
  self.assertNotEqual(r.returncode,0);self.assertIn('Beta3 requires macOS',r.stdout+r.stderr)
 def test_full_source_gate_refuses_partial_projection(self):
  with tempfile.TemporaryDirectory() as d:
   r=subprocess.run([sys.executable,str(ROOT/'tests/run_jg132_beta3.py'),'--require-full-source'],env=dict(os.environ,JG_BETA3_SOURCE=d),capture_output=True,text=True)
  self.assertNotEqual(r.returncode,0);self.assertNotIn('source gates PASS',r.stdout+r.stderr)
if __name__=='__main__':unittest.main(verbosity=2)
