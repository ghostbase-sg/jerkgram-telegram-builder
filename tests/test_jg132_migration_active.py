"""Production HEAD guards and current stage API semantics, with hermetic inputs."""
from pathlib import Path
import subprocess,tempfile,unittest
from jg132_migration_fixtures import baseline,GenuinePristineFactory,hashes

class CurrentStageAPI(unittest.TestCase):
    def test_frozen_identity_comes_from_verified_baseline_delta(self):
        identity=baseline.baseline_identity()
        self.assertEqual(identity['build_number'],179)
        self.assertEqual(identity['product_display_version'],'1.2.0 Beta 2')
        self.assertEqual(identity['upstream_new_version'],'13.1.2')
        import materialize_jg13_download_boost as boost
        text='public static let build = "999"';self.assertEqual(boost.canonical(boost.STRINGS,text),text)

    def test_genuine_source_factory_refuses_missing_head(self):
        with tempfile.TemporaryDirectory() as td:
            factory=GenuinePristineFactory(Path(td))
            with self.assertRaises(RuntimeError):factory.populate(Path(td)/'pristine')
            self.assertFalse((Path(td)/'pristine').exists())

    def test_known18_prefix_accepts_verified_repeats_without_writes(self):
        with tempfile.TemporaryDirectory(prefix='jg132-active-hermetic-') as td:
            root=GenuinePristineFactory().populate(Path(td)/'source')
            baseline.apply_range(root,1,18,require_head=False);before=hashes(root)
            baseline.apply_stage(root,'jg13-stars-gift',require_head=False)
            baseline.apply_stage(root,'identity',require_head=False)
            self.assertEqual(hashes(root),before)
            with self.assertRaises(RuntimeError):baseline.apply_stage(root,'identity')
            self.assertEqual(hashes(root),before)
            repeated=subprocess.run(['git','apply','--check',str(baseline.patch(baseline.chain()[17]))],cwd=root,capture_output=True)
            self.assertNotEqual(repeated.returncode,0)
            p=root/'submodules/TelegramUI/Sources/ChatController.swift';p.write_bytes(p.read_bytes()+b'\n// corrupt\n');damaged=hashes(root)
            with self.assertRaises(RuntimeError):baseline.apply_stage(root,'jg13-stars-gift',require_head=False)
            self.assertEqual(hashes(root),damaged)

if __name__=='__main__':unittest.main()
