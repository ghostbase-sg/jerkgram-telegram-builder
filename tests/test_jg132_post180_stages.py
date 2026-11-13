from pathlib import Path
import hashlib,os,shutil,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import jg132_post180 as successor
from jg132_beta3_stages import manifest, apply_stage
SOURCE=Path(os.environ.get('JG_POST180_SOURCE',ROOT/'work/swiftgram-src'))

def hashes(source,names):
    return {n:hashlib.sha256((source/n).read_bytes()).hexdigest() if (source/n).is_file() else None for n in names}

class ExactSuccessors(unittest.TestCase):
    def test_apply_reapply_restore_and_corrupt_refusal(self):
        rows=[manifest(s) for s in successor.stages()]
        names=set().union(*(set(m['owners'])|set(m.get('parent_owners',{})) for m in rows))
        with successor.build180_source_view(SOURCE) as green,tempfile.TemporaryDirectory(prefix='post180-stages-') as tmp:
            source=Path(tmp)
            for name in names:
                if (green/name).is_file():
                    path=source/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(green/name,path)
            before=hashes(source,names)
            # Resume a genuine prefix, proving newly added later stages are not
            # silently skipped just because an earlier stage already exists.
            apply_stage(source,successor.stages()[0])
            successor.apply_all(source);successor.verify_source(source)
            after=hashes(source,names);successor.apply_all(source)
            self.assertEqual(after,hashes(source,names))
            with successor.build180_source_view(source) as restored:self.assertEqual(before,hashes(restored,names))
            protected=next(n for n in rows[-1]['owners'] if (source/n).is_file())
            with (source/protected).open('ab') as file:file.write(b'\n// unexpected mutation\n')
            corrupt=hashes(source,names)
            with self.assertRaises(RuntimeError):successor.apply_all(source)
            self.assertEqual(corrupt,hashes(source,names),'failure must precede every write')

if __name__=='__main__':unittest.main(verbosity=2)
