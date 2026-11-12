"""Exact successor stages: all parents before writes, idempotency and reversal."""
from pathlib import Path
import difflib,hashlib,importlib.util,json,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import jg132_beta3_stages as stages

class ExactStages(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup); self.root=Path(self.tmp.name)
  self.source=self.root/'source';self.source.mkdir();self.assets=self.root/'assets';self.assets.mkdir()
  self.oldRoot=stages.ROOT;stages.ROOT=self.assets;self.addCleanup(setattr,stages,'ROOT',self.oldRoot)
  (self.assets/'patches').mkdir();self.path='submodules/Owner.swift';self.guard='submodules/Guard.swift'
  (self.source/'submodules').mkdir();(self.source/self.path).write_text('before\n');(self.source/self.guard).write_text('guard\n')
  self.make('fixture',{'submodules/Owner.swift':('before\n','after\n'),'submodules/New.swift':(None,'new\n')})
 def make(self,name,owners):
  digest=lambda b:hashlib.sha256(b.encode()).hexdigest() if b is not None else None
  patch=''.join(''.join(difflib.unified_diff((a or '').splitlines(True),(b or '').splitlines(True),fromfile='a/'+n if a is not None else '/dev/null',tofile='b/'+n)) for n,(a,b) in owners.items())
  (self.assets/'patches'/f'{name}.patch').write_text(patch)
  m={'upstream_sha':stages.UPSTREAM,'patch_sha256':digest(patch),'owners':{n:dict(before_sha256=digest(a),after_sha256=digest(b)) for n,(a,b) in owners.items()},'parent_owners':{self.guard:digest('guard\n')}}
  (self.assets/'patches'/f'{name}.sha256.json').write_text(json.dumps(m));return m
 def test_apply_reapply_reverse(self):
  stages.apply_stage(self.source,'fixture');stages.apply_stage(self.source,'fixture');stages.verify_stage(self.source,'fixture')
  self.assertEqual((self.source/self.path).read_text(),'after\n')
  with stages.parent_source_view(self.source,'fixture') as p:
   self.assertEqual((p/self.path).read_text(),'before\n');self.assertFalse((p/'submodules/New.swift').exists());self.assertEqual((p/self.guard).read_text(),'guard\n')
 def test_composed_repeat_and_restore_overlapping_owners(self):
  self.make('second',{'submodules/Owner.swift':('after\n','final\n')})
  old=stages.STAGES;stages.STAGES=('fixture','second');self.addCleanup(setattr,stages,'STAGES',old)
  stages.apply_all(self.source);stages.apply_all(self.source)
  with stages.baseline_source_view(self.source) as p:self.assertEqual((p/self.path).read_text(),'before\n')
 def test_last_corrupt_parent_refuses_all_writes(self):
  (self.source/'submodules/New.swift').write_text('foreign\n')
  with self.assertRaises(RuntimeError):stages.apply_stage(self.source,'fixture')
  self.assertEqual((self.source/self.path).read_text(),'before\n')
 def test_guard_refuses_before_and_after(self):
  stages.apply_stage(self.source,'fixture');(self.source/self.guard).write_text('wrong\n')
  with self.assertRaises(RuntimeError):stages.apply_stage(self.source,'fixture')
 def test_tampered_patch_refused(self):
  with (self.assets/'patches/fixture.patch').open('a') as f:f.write('\n')
  with self.assertRaises(RuntimeError):stages.apply_stage(self.source,'fixture')
  self.assertEqual((self.source/self.path).read_text(),'before\n')
 def test_unknown_pin_and_escape_refused(self):
  p=self.assets/'patches/fixture.sha256.json';m=json.loads(p.read_text());m['upstream_sha']='foreign';p.write_text(json.dumps(m))
  with self.assertRaises(RuntimeError):stages.manifest('fixture')
  with self.assertRaises(ValueError):stages.manifest('../fixture')
if __name__=='__main__':unittest.main(verbosity=2)
