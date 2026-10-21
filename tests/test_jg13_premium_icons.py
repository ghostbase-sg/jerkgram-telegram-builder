"""Exact App Icons delta, repeat refusal and resource/regression integrity."""
import importlib
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/swiftgram-src'))
sys.path.insert(0, str(ROOT / 'scripts'))

class PremiumIconsTests(unittest.TestCase):
    def test_three_gates_are_scoped_to_app_icons(self):
        item = (SOURCE / 'submodules/SettingsUI/Sources/Themes/ThemeSettingsAppIconItem.swift').read_text()
        self.assertIn('enum JerkgramAppIconAccess', item, 'App Icons capability has not been implemented')
        stage = importlib.import_module('materialize_jg13_premium_icons')
        stage.verify_icons(SOURCE)

    def test_exact_roundtrip_repeat_and_tamper_refusal(self):
        self.assertTrue((ROOT / 'scripts/materialize_jg13_premium_icons.py').exists(), 'Missing guarded App Icons stage')
        stage = importlib.import_module('materialize_jg13_premium_icons')
        manifest = stage.read_manifest()
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            for name in set(manifest['owners']) | set(manifest['locks']):
                target = fixture / name
                target.parent.mkdir(parents=True, exist_ok=True)
                text = (SOURCE / name).read_bytes()
                if name in manifest['owners']:
                    text = stage.restore_owner(name, text.decode()).encode()
                target.write_bytes(text)
            stage.apply_icons(fixture)
            stage.verify_icons(fixture)
            with self.assertRaises(RuntimeError): stage.apply_icons(fixture)
            for name in manifest['owners']:
                target = fixture / name
                original = target.read_bytes()
                target.write_bytes(original + b'\n// tamper\n')
                with self.assertRaises(RuntimeError): stage.verify_icons(fixture)
                target.write_bytes(original)
            for name in manifest['locks']:
                target = fixture / name
                original = target.read_bytes()
                target.write_bytes(original + b'\n')
                with self.assertRaises(RuntimeError): stage.verify_icons(fixture)
                target.write_bytes(original)

if __name__ == '__main__': unittest.main()
