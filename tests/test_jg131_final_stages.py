from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import jg131_final_stages as stages

class SourceViewTests(unittest.TestCase):
    def test_changed_added_removed_owners_leave_original_bytes_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            original=Path(d)/'original';original.mkdir()
            (original/'a').mkdir();(original/'other').mkdir()
            (original/'a/file').write_bytes(b'new')
            (original/'a/added').write_bytes(b'added')
            (original/'a/unchanged').write_bytes(b'untouched')
            (original/'other/input').write_bytes(b'input')
            view=stages.source_view(original,Path(d)/'view',{'a/file':b'old','a/added':None,'new/tree/item':b'created'})
            self.assertEqual((view/'a/file').read_bytes(),b'old')
            self.assertFalse((view/'a/added').exists())
            self.assertEqual((view/'new/tree/item').read_bytes(),b'created')
            self.assertEqual((view/'other/input').read_bytes(),b'input')
            self.assertEqual((original/'a/file').read_bytes(),b'new')
            self.assertEqual((original/'a/added').read_bytes(),b'added')
            self.assertFalse((original/'new').exists())
    def test_bad_paths_are_rejected_before_a_view_is_created(self):
        with tempfile.TemporaryDirectory() as d:
            original=Path(d)/'original';original.mkdir()
            for key in ['/tmp/escape','a/../../escape']:
                view=Path(d)/'view'
                with self.assertRaises(ValueError): stages.source_view(original,view,{key:b'x'})
                self.assertFalse(view.exists())
if __name__=='__main__': unittest.main()
