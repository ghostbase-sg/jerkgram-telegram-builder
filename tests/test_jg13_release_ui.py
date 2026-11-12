import importlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

def apply_fixture(stage,source):
    from jg132_baseline import enabled
    if enabled():
        from jg132_source_fixtures import apply_exact_delta_fixture
        return apply_exact_delta_fixture(stage,source)
    return stage.apply_release_ui(source)

class ReleaseUiTests(unittest.TestCase):
    def test_identity_matches_release_and_package_uses_config(self):
        config = json.loads((ROOT / 'jerkgram-migration.json').read_text())
        self.assertEqual(config['product_display_version'], '1.2.0 Beta 3')
        self.assertEqual(config['product_technical_version'], '1.2.0-beta.3')
        package = (ROOT / 'scripts/package_jg13.py').read_text()
        self.assertNotIn('Jerkgram-1.1.0-Beta-1-Build', package)
    def test_about_only_cleanup_is_exact_and_rejects_repeat(self):
        stage = importlib.import_module('configure_jg13_release_ui')
        from jg132_baseline import enabled
        canonical = ROOT / 'work/final157' / stage.OWNER
        if enabled() or not canonical.exists():
            canonical = Path(os.environ.get('JG13_SOURCE',ROOT / 'work/swiftgram-src')) / stage.OWNER
            final = canonical.read_text()
            parent = stage.restore_parent(final)
        else:
            parent = canonical.read_text()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            target = source / stage.OWNER
            target.parent.mkdir(parents=True)
            target.write_text(parent)
            apply_fixture(stage, source)
            stage.verify_release_ui(source)
            text = target.read_text()
            about = text.split('    if page == .about {', 1)[1].split('    if page == .debugResearch {', 1)[0]
            self.assertNotIn('performanceStart', about)
            self.assertNotIn('Диагностика производительности', about)
            self.assertIn('JerkgramReleaseIdentity.displayVersion', about)
            self.assertEqual(stage.restore_parent(text), parent)
            with self.assertRaises(RuntimeError): apply_fixture(stage, source)
            target.write_text(parent + '\n// changed\n')
            with self.assertRaises(RuntimeError): apply_fixture(stage, source)
            self.assertEqual(target.read_text(), parent + '\n// changed\n')
if __name__ == '__main__': unittest.main()
