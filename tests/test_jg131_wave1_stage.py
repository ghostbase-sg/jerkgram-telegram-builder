"""Execute the dependent stage: exact apply, reverse and atomic preflight refusal."""
from pathlib import Path
import importlib.util,sys,tempfile,unittest,subprocess,json,os
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
SOURCE=Path(os.environ.get('JG_WAVE1_SOURCE',ROOT/'work/swiftgram-src'))
def apply_fixture(stage,source):
 from jg132_baseline import enabled
 if enabled():
  from jg132_source_fixtures import apply_exact_delta_fixture
  return apply_exact_delta_fixture(stage,source)
 return stage.apply_wave1(source)
class WaveStageTests(unittest.TestCase):
 def stage(self):
  self.assertTrue(importlib.util.find_spec('materialize_jg131_performance_wave1') is not None,'missing dependent remediation stage')
  import materialize_jg131_performance_wave1 as stage
  return stage
 def test_exact_parent_roundtrip(self):
  stage=self.stage()
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   for n in stage.manifest()['owners']:
    p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((SOURCE/n).read_bytes())
   subprocess.run(['git','apply','--reverse','--whitespace=nowarn',str(stage.PATCH)],cwd=root,check=True)
   before={n:(root/n).read_bytes() for n in stage.manifest()['owners']}
   apply_fixture(stage,root);stage.verify_wave1(root)
   for n in before:self.assertEqual(stage.parent_bytes(n,(root/n).read_bytes()),before[n])
 def test_bad_last_parent_refuses_before_first_mutation(self):
  stage=self.stage()
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   for n in stage.manifest()['owners']:
    p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((SOURCE/n).read_bytes())
   subprocess.run(['git','apply','--reverse','--whitespace=nowarn',str(stage.PATCH)],cwd=root,check=True)
   names=list(stage.manifest()['owners']);(root/names[-1]).write_bytes(b'corrupted parent')
   before={n:(root/n).read_bytes() for n in names}
   with self.assertRaises(RuntimeError):apply_fixture(stage,root)
   self.assertEqual(before,{n:(root/n).read_bytes() for n in names})
 def test_reapply_is_rejected_without_mutation(self):
  stage=self.stage()
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   for n in stage.manifest()['owners']:
    p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((SOURCE/n).read_bytes())
   with self.assertRaises(RuntimeError):apply_fixture(stage,root)
   stage.verify_wave1(root)
if __name__=='__main__':unittest.main()
