"""Build180 performance port: two exact hot path changes and native parity."""
from pathlib import Path
import os
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from jg132_beta3_stages import parent_source_view
from beta3_performance_native import PANEL, HISTORY, MODEL, CONVERSION, literal, predicate, verify_fixture, assemble, run_native

SOURCE = Path(os.environ.get('JG_BETA3_SOURCE', ROOT / 'work/swiftgram-src')).resolve()
STAGE = 'beta3-performance-wave2a1'


class PerformancePort(unittest.TestCase):
    def test_only_two_reviewed_hot_path_sections_change(self):
        with parent_source_view(SOURCE, STAGE) as before:
            old = (before / PANEL).read_text()
            new = (SOURCE / PANEL).read_text()
            self.assertEqual(literal(old), 'attributedString(from: state.content).string')
            self.assertEqual(literal(new), 'state.content.plainText')
            self.assertEqual(new, old.replace(
                'literalText: { attributedString(from: state.content).string }',
                'literalText: { state.content.plainText }', 1))
            old = (before / HISTORY).read_text()
            new = (SOURCE / HISTORY).read_text()
            old_predicate, new_predicate = predicate(old), predicate(new)
            self.assertTrue(new_predicate.startswith('if !ghostBaseShowDeleted {'))
            self.assertEqual(old.replace(old_predicate, '<PREDICATE>', 1),
                             new.replace(new_predicate, '<PREDICATE>', 1))
            self.assertEqual(old_predicate.count('first(where:'), 1)
            self.assertEqual(new_predicate.count('first(where:'), 1)

    def test_actual_132_model_and_projection_assemble(self):
        verify_fixture(ROOT, SOURCE)
        with parent_source_view(SOURCE, STAGE) as before:
            with tempfile.TemporaryDirectory() as tmp:
                text = assemble(ROOT, SOURCE, before, Path(tmp)).read_text()
                self.assertIn('public var plainText: String', text)
                self.assertIn('func officialAttributedString(', text)
                self.assertIn('oldAllows', text)
                self.assertIn('newAllows', text)
                self.assertNotIn('/* EXACT_', text)

    def test_native_parity_and_operation_counts(self):
        if not shutil.which('xcrun') or not shutil.which('swiftc'):
            if os.environ.get('JG_BETA3_REQUIRE_NATIVE') == '1':
                self.fail('Build180 performance native parity requires macOS Swift/xcrun')
            self.skipTest('macOS Swift/xcrun unavailable; native behavior still pending')
        with parent_source_view(SOURCE, STAGE) as before:
            run_native(ROOT, SOURCE, before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
