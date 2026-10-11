"""Storage contracts; actual ten-minute Swift execution is a separate CI gate."""
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/swiftgram-src'))
CORE = 'submodules/TelegramCore/Sources/Utils/JerkgramPerformanceDiagnostics.swift'

class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.source = (SOURCE / CORE).read_text()

    def test_one_second_sampler_uses_five_second_max_blocks(self):
        self.assertIn('repeating: 1.0', self.source)
        self.assertIn('recordUtilitySampleLocked(now:', self.source)
        self.assertIn('recordMainWaitLocked(submittedAt:', self.source)
        self.assertIn('private let telemetryBlockSeconds = 5.0', self.source)
        self.assertIn('cpuMax', self.source)
        self.assertIn('waitMax', self.source)

    def test_operation_summary_precedes_the_32_key_gate(self):
        measure = self.source.split('public func measure(_ stage:', 1)[1].split('// Route labels', 1)[0]
        self.assertIn('recordOperationLocked(', measure)
        self.assertLess(measure.index('recordOperationLocked('), measure.index('self.timings.count < 32'))
        self.assertIn('private var operationSummaries: [Operation: OperationSummary]', self.source)

    def test_late_detail_has_independent_input_and_history_windows(self):
        self.assertIn('private let detailWindowSeconds = 20.0', self.source)
        self.assertIn('operation.isInputOrSend', self.source)
        self.assertIn('retainDetailLocked(', self.source)
        self.assertIn('retainedDetailLinesLocked()', self.source)

    def test_critical_records_share_the_total_512_bound(self):
        self.assertIn('private func trimAuxiliaryLinesLocked()', self.source)
        self.assertIn('self.capacity - self.telemetryBlocks.count - self.retainedDetailCountLocked - self.captureBoundaries.count', self.source)
        self.assertIn('durationSeconds=', self.source)
        self.assertIn('auxiliaryDropped=', self.source)

    def test_capture_counts_without_sorting_the_detail_reservoir(self):
        trim = self.source.split('private func trimAuxiliaryLinesLocked()', 1)[1].split('private func appendLocked', 1)[0]
        self.assertNotIn('retainedDetailLinesLocked()', trim)
        self.assertIn('private var retainedSamples: [Int: DetailSample]', self.source)
        self.assertIn('private var sampleReferences: [Int: Int]', self.source)

    def test_recognized_overflow_stages_remain_measured(self):
        self.assertIn('recordFixedOverflowLocked(', self.source)
        self.assertIn('fixedStageOverflow stage=', self.source)
        self.assertIn('unsupportedTimingSamplesDropped=', self.source)

    def test_native_retention_gate_runs_before_application_build(self):
        build = (ROOT / 'scripts/build_jg13.sh').read_text()
        self.assertIn('python3 tests/run_jg13_capture_retention.py', build)
        self.assertLess(build.index('run_jg13_capture_retention.py'), build.index('pin_jg13_dependencies.py'))

if __name__ == '__main__':
    unittest.main()
