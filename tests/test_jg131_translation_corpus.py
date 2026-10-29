"""Validate inputs and review coverage, never invent backend outputs."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CorpusCoverage(unittest.TestCase):
    def test_four_directions_cover_eight_input_classes_with_bounded_inputs(self):
        corpus = json.loads((ROOT / 'docs/translation/translation-corpus.json').read_text())
        pairs = {('ru', 'en'), ('en', 'ru'), ('ru', 'de'), ('de', 'ru')}
        kinds = {'ordinary', 'slang', 'emoji', 'url', 'mention', 'newline', 'long', 'mixed'}
        cases = corpus['cases']
        self.assertEqual(len(cases), 32)
        self.assertEqual({(c['source_language'], c['target_language'], c['kind']) for c in cases}, {(s, t, k) for s, t in pairs for k in kinds})
        self.assertEqual(len({c['id'] for c in cases}), 32)
        for case in cases:
            self.assertTrue(case['text'].strip(), case['id'])
            self.assertLessEqual(len(case['text'].encode()), 16 * 1024, case['id'])
            for token in case['protected_tokens']:
                self.assertIn(token, case['text'])
        # Publishing a source gate is not evidence that any backend was run.
        self.assertEqual(corpus['status'], 'INPUT_CORPUS_ONLY_NOT_RUNTIME_RESULTS')
        self.assertTrue(all(c['result'] == 'NOT_RUN' and c['apple_baseline_output'] is None and c['enhanced_output'] is None for c in cases))


if __name__ == '__main__':
    unittest.main()
