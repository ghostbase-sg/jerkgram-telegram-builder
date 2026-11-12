"""The backend native fixture follows the actual 13.2 public module factory."""
from pathlib import Path
import importlib.util,unittest,os
ROOT=Path(__file__).resolve().parents[1]
class Fixture(unittest.TestCase):
 def test_actual_factory_selection_and_trace_inputs_assembled(self):
  spec=importlib.util.spec_from_file_location('backend',ROOT/'tests/run_jg13_history_backend.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  m.OWNER=Path(os.environ.get('JG13_SOURCE', ROOT/'work/swiftgram-src'))/'submodules/TelegramUI/Sources/ChatHistoryListNode.swift'
  text=m.fixture()
  self.assertIn('public func makeCoreListChatHistoryBackend(rotated: Bool, scrollTrace: Bool = false)',text)
  self.assertIn('CoreListScrollTrace.isEnabled = scrollTrace',text)
  self.assertIn('for trace in [false, true]',text)
  self.assertIn('coreListScrollTrace: trace',text)
if __name__=='__main__':unittest.main()
