"""Exercise backend selection changes against real materialized history source."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
OWNER = "submodules/TelegramUI/Sources/ChatHistoryListNode.swift"

class BackendTests(unittest.TestCase):
    def module(self):
        path = ROOT / "scripts/materialize_jg13_history_backend.py"
        self.assertTrue(path.exists(), "history backend final stage is missing")
        spec = importlib.util.spec_from_file_location("history_backend", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_real_owner_selects_existing_listview_and_restores_exactly(self):
        m = self.module()
        current = (ROOT / "work/swiftgram-src" / OWNER).read_text()
        parent = m.restore(current) if "// Jerkgram: use the established asynchronous ListView backend by default." in current else current
        updated = m.transform(parent)
        self.assertIn("var useCoreListBackend = false", updated)
        self.assertNotIn("var useCoreListBackend = rotated", updated)
        self.assertEqual(m.restore(updated), parent)
        self.assertIn("let listView = ListViewImpl()", updated)
        self.assertIn('context.getAppConfigValue("ios_killswitch_disable_corelist_chat_backend")', updated)
        with self.assertRaises(RuntimeError): m.transform(updated)
        with self.assertRaises(RuntimeError): m.transform(parent + "\n// unexpected change\n")
        with self.assertRaises(RuntimeError): m.restore(updated + "\n// unexpected change\n")

    def test_failed_stage_does_not_mutate_owner(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / OWNER
            target.parent.mkdir(parents=True)
            target.write_text("unexpected source")
            with self.assertRaises(RuntimeError): m.apply_backend(Path(temp))
            self.assertEqual(target.read_text(), "unexpected source")

if __name__ == "__main__": unittest.main()
