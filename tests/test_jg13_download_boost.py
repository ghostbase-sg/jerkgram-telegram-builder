import importlib
from pathlib import Path
import os
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/swiftgram-src'))
sys.path.insert(0, str(ROOT / 'scripts'))

class DownloadBoostTests(unittest.TestCase):
    def test_bounded_stage_exists_and_verifies_real_source(self):
        self.assertTrue((ROOT / 'scripts/materialize_jg13_download_boost.py').exists(), 'Download Boost stage is missing')
        importlib.import_module('materialize_jg13_download_boost').verify_boost(SOURCE)
        settings = (SOURCE / 'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift').read_text()
        self.assertIn('downloadBoost: JerkgramDownloadBoostSettings.readStoredMode(accountPeerId: accountPeerId).rawValue,', settings)
        self.assertNotIn('downloadBoost: jerkgramScopedString', settings)

    def test_repeat_and_tamper_are_rejected(self):
        self.assertTrue((ROOT / 'patches/jg13-download-boost.sha256.json').exists(), 'Reviewed Download Boost owner manifest is missing')
        stage = importlib.import_module('materialize_jg13_download_boost')
        m = stage.read_manifest()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            for name in set(m['owners']) | set(m['locks']):
                target = source / name
                target.parent.mkdir(parents=True, exist_ok=True)
                data = (SOURCE / name).read_bytes()
                if name in m['owners']:
                    restored = stage.restore_owner(name, data.decode())
                    if restored is None: continue
                    data = restored.encode()
                target.write_bytes(data)
            stage.apply_boost(source)
            stage.verify_boost(source)
            with self.assertRaises(RuntimeError): stage.apply_boost(source)
            for name in set(m['owners']) | set(m['locks']):
                target = source / name
                original = target.read_bytes()
                target.write_bytes(original + b'\n// tampered\n')
                with self.assertRaises(RuntimeError): stage.verify_boost(source)
                target.write_bytes(original)

if __name__ == '__main__': unittest.main()
