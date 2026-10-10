import os,json,hashlib,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('JG13_SOURCE',ROOT/'work/swiftgram-src'))
CORE='submodules/TelegramCore/Sources/Utils/JerkgramPerformanceDiagnostics.swift'
HISTORY='submodules/TelegramUI/Sources/ChatHistoryListNode.swift'
BACKEND='submodules/TelegramUI/Sources/CoreListChatHistoryBackend.swift'
class HistoryDetailTests(unittest.TestCase):
    def test_observed_operations_do_not_require_a_slow_event(self):
        s=(SOURCE/CORE).read_text()
        self.assertIn('private var operationsObserved: UInt64 = 0',s)
        self.assertIn('self.operationsObserved |= operation.bit',s)
        self.assertIn('operationsEntered=',s)
        self.assertIn('self.operationsObserved = 0',s)
        self.assertIn('thread=',s)
    def test_actual_history_and_send_boundaries(self):
        history=(SOURCE/HISTORY).read_text()
        for name in ('historyPrepare','historyComplete','historyApply','historyMap'):
            self.assertIn('beginOperation(.'+name+')',history)
        backend=(SOURCE/BACKEND).read_text()
        for name in ('historyCoreTransaction','historyRowLayout','historyRowBuild'):
            self.assertIn('beginOperation(.'+name+')',backend)
        panel=(SOURCE/'submodules/TelegramUI/Components/Chat/ChatTextInputPanelNode/Sources/ChatTextInputPanelNode.swift').read_text()
        self.assertIn('beginOperation(.inputSend)',panel)
        chat=(SOURCE/'submodules/TelegramUI/Sources/ChatController.swift').read_text()
        self.assertIn('beginOperation(.inputState)',chat)
        state = chat[chat.index('    func updateChatPresentationInterfaceState(transition:'):]
        self.assertIn('completion: @escaping (ContainedViewLayoutTransition) -> Void = { _ in }) {\n        let jgOperation = JerkgramPerformanceDiagnostics.shared.beginOperation(.inputState)', state)
        self.assertIn('beginOperation(.sendEnqueue)',chat)
        self.assertIn('beginOperation(.sendDispatch)',chat)
    def test_single_pass_bounds_in_actual_caller(self):
        history=(SOURCE/HISTORY).read_text()
        self.assertIn('// JG155 bounds begin',history)
        self.assertIn('previousIds.reserveCapacity(previous.originalView.entries.count)',history)
        self.assertNotIn('previous.originalView.entries.map { $0.message.id }',history)
        self.assertNotIn('previous.originalView.entries.map { $0.message.index }.max()',history)
        script=(ROOT/'tests/run_jg13_history_bounds.py').read_text()
        self.assertIn("split('// JG155 bounds begin'",script)
        self.assertIn('expectedIds',script)
        self.assertIn('expectedIndex',script)
        self.assertIn('xcrun',script)
if __name__=='__main__':unittest.main()
