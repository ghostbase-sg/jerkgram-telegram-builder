"""Bounded contracts for actual row stages and nested detail preservation."""
import os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('JG13_SOURCE',ROOT/'work/swiftgram-src'))
class RowDetailTests(unittest.TestCase):
    def test_existing_slow_summary_prefix_remains_compatible(self):
        s=(SOURCE/'submodules/TelegramCore/Sources/Utils/JerkgramPerformanceDiagnostics.swift').read_text()
        self.assertTrue('suppressedSlowEvents=\\(self.suppressedSlowEvents) limit=\\(self.slowEventLimit) nestedSlowEventsSuppressed=' in s, 'existing native capture summary contract must retain its exact prefix')
    def test_actual_row_stages(self):
        s=(SOURCE/'submodules/TelegramUI/Components/Chat/ChatMessageItemImpl/Sources/ChatMessageItemImpl.swift').read_text()
        for op in ('historyNodeCreate','historyNodeSetup','historyNodeCompute','historyNodeApply'):
            self.assertIn('measureOperation(.'+op+')',s)
        self.assertEqual(s.count('measureOperation(.historyNodeCompute)'),2)
        self.assertEqual(s.count('measureOperation(.historyNodeSetup)'),2)
        self.assertEqual(s.count('measureOperation(.historyNodeApply)'),2)
    def test_actual_plain_text_send_path(self):
        s=(SOURCE/'submodules/TelegramUI/Sources/ChatControllerNode.swift').read_text()
        self.assertIn('completion: @escaping () -> Void = {}) {\n        let jgOperation = JerkgramPerformanceDiagnostics.shared.beginOperation(.sendCurrent)',s)
        self.assertIn('measureOperation(.sendEnqueue) { self.sendMessages(messages, silentPosting, scheduleTime, repeatPeriod, messages.count > 1, postpone) }',s)
    def test_nested_dedup_preserves_aggregate_before_filtering(self):
        s=(SOURCE/'submodules/TelegramCore/Sources/Utils/JerkgramPerformanceDiagnostics.swift').read_text()
        self.assertIn('public func measureOperation<T>',s)
        self.assertIn('nestedSlowEventsSuppressed',s)
        self.assertIn('lastDetailedMainSpan',s)
        self.assertLess(s.index('self.timings[stage] = (old.count + 1'),s.index('// JG156 nested detail'))
        self.assertIn('childDuration >= milliseconds * 0.90',s)
        self.assertIn('sessionGeneration != nil, Thread.isMainThread',s)
        self.assertIn('private let slowEventLimit = 96',s)
        self.assertIn('timings.count < 32',s)
        self.assertIn('capacity = 512',s)
if __name__=='__main__':unittest.main()
