import importlib.util
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import materialize_profile_observer_foundation as subject


class MaterializationContracts(unittest.TestCase):
    def test_current_product_source_and_toolchain_pin(self):
        self.assertEqual(subject.PIN, '24638bc69bd083981b178dd1e7f921eebbf7fc46')
        for head, version in [(b'wrong\n', b'{}'), (subject.PIN.encode(), b'{"app":"12.9.2","xcode":"26.2","bazel":"8.4.2"}')]:
            with patch.object(subject.subprocess, 'check_output', side_effect=[head, version]):
                with self.assertRaises(RuntimeError):
                    subject.verify_pin(ROOT)

    def test_failed_product_gate_blocks_observer_successor(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            with patch.object(subject, "ROOT", root), patch.object(subject, "verify_pin", return_value=root), patch.object(subject, "materialize_product"), patch.object(subject, "apply_observer") as observer, patch.object(subject.subprocess, "check_output", return_value="builder-sha"), patch.object(subject.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "native-product-gate")):
                with self.assertRaises(subprocess.CalledProcessError):
                    subject.materialize(root, require_native=True)
                observer.assert_not_called()
            import json
            evidence = json.loads((root / "artifacts/profile-observer-materialization.json").read_text())
            self.assertTrue(evidence["baseline_materialized"])
            self.assertFalse(evidence["observer_materialized"])
            self.assertEqual(evidence["native_app_compile"], "not-run")

    def test_build_preserves_current_route_without_release_packaging(self):
        source = (ROOT / 'scripts/build_profile_observer_foundation.sh').read_text()
        self.assertIn('materialize_profile_observer_foundation.py --require-native', source)
        for expected in ['pin_jg13_dependencies.py --verify', 'prepare_jg13_build_rules.py', '//Telegram:Telegram', '--define=buildNumber=183', 'Xcode_27.1', 'USE_BAZEL_VERSION=9.2.0']:
            self.assertIn(expected, source)
        for forbidden in ['package_jg13.py', 'preserve_jg13_ipa.py', 'bazel_build_probe_official.sh', 'install_jerkgram_v12w']:
            self.assertNotIn(forbidden, source)


if __name__ == '__main__':
    unittest.main()
