"""Two perf hunks: exact scope + actual-algorithm Foundation native evidence."""
from pathlib import Path
import os
import shutil
import tempfile
import unittest
from wave2a1_native import PANEL, HISTORY, declaration, literal, predicate, verify_fixture, assemble, run_native

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG_WAVE2A1_SOURCE', ROOT.parent / 'jerkgram-next/perf-wave2a1/source'))
BEFORE = Path(os.environ.get('JG_WAVE2A1_BEFORE', ROOT.parent / 'jerkgram-next/perf-wave2a1/before'))


class Wave2A1(unittest.TestCase):
    def test_two_exact_behavior_preserving_hunks(self):
        old = (BEFORE / PANEL).read_text()
        new = (SOURCE / PANEL).read_text()
        self.assertEqual(literal(old), 'attributedString(from: state.content).string')
        self.assertEqual(literal(new), 'state.content.plainText')
        self.assertEqual(new, old.replace('literalText: { attributedString(from: state.content).string }', 'literalText: { state.content.plainText }', 1))
        # Every native/legacy/marked-text/live/config/selection/reentrancy guard,
        # normal rendering setter and send/paste/undo path is byte-preserved.
        old = (BEFORE / HISTORY).read_text()
        new = (SOURCE / HISTORY).read_text()
        old_predicate, new_predicate = predicate(old), predicate(new)
        self.assertTrue(new_predicate.startswith('if !ghostBaseShowDeleted {'))
        self.assertEqual(old.replace(old_predicate, '<PREDICATE>', 1), new.replace(new_predicate, '<PREDICATE>', 1))
        self.assertEqual(old_predicate.count('first(where:'), 1)
        self.assertEqual(new_predicate.count('first(where:'), 1)

    def test_pinned_inputs_and_actual_native_assembly(self):
        verify_fixture(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            source = assemble(ROOT, SOURCE, BEFORE, Path(tmp)).read_text()
            self.assertIn(declaration((ROOT / 'tests/fixtures/wave2a1/official/submodules/TelegramCore/Sources/ChatInputContent/ChatInputContentModel.swift').read_text(), 'public var plainText: String'), source)
            self.assertIn('oldAllows', source)
            self.assertIn('newAllows', source)
            self.assertNotIn('/* EXACT_', source)

    def test_native_behavior_and_operation_counts(self):
        if not shutil.which('xcrun') or not shutil.which('swiftc'):
            if os.environ.get('JG_WAVE2A1_REQUIRE_NATIVE') == '1':
                self.fail('Wave2A1 native verification requires macOS Swift/xcrun; no behavioral PASS available')
            self.skipTest('No macOS Swift/xcrun; actual-algorithm behavior/counters remain pending')
        run_native(ROOT, SOURCE, BEFORE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
