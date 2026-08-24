import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
CORE = REPO / "scripts/apply_jerkgram_v12g_build118_core1.py"
OVERLAY = REPO / "scripts/apply_jerkgram_v12g_build118_time_machine1.py"


def load_overlay():
    spec = importlib.util.spec_from_file_location("build118_tm", OVERLAY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Build118TimeMachineTests(unittest.TestCase):
    def test_materializes_reference_only_engine(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = os.environ.copy()
            env["JERKGRAM_SOURCE_ROOT"] = str(root)
            subprocess.run([sys.executable, str(CORE)], cwd=REPO, env=env, check=True)
            result = subprocess.run(
                [sys.executable, str(OVERLAY)], cwd=REPO, env=env,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            index = (root / "submodules/JerkgramCore/Sources/JerkgramTimeMachineIndex.swift").read_text()
            diff = (root / "submodules/JerkgramCore/Sources/JerkgramTextDiff.swift").read_text()
            self.assertIn("public struct JerkgramTimeMachineQuery", index)
            self.assertIn("eventIds", index)
            self.assertIn("upperSequence", index)
            self.assertNotIn("mediaBytes", index)
            self.assertNotIn("messageText", index)
            self.assertIn("Array(old)", diff)
            self.assertIn("Array(new)", diff)

    def test_same_text_different_ids_survive_and_filters_intersect(self):
        tm = load_overlay()
        rows = [
            {"eventId": "a", "account": 1, "chat": 9, "kind": "deletedMessage", "sender": 7, "search": "same"},
            {"eventId": "b", "account": 1, "chat": 9, "kind": "deletedMessage", "sender": 7, "search": "same"},
            {"eventId": "c", "account": 1, "chat": 9, "kind": "editedMessage", "sender": 8, "search": "same"},
            {"eventId": "d", "account": 2, "chat": 9, "kind": "deletedMessage", "sender": 7, "search": "same"},
        ]
        result = tm.query_records(rows, account=1, chat=9, kinds={"deletedMessage"}, sender=7, text="same")
        self.assertEqual([row["eventId"] for row in result], ["a", "b"])

    def test_diff_does_not_split_emoji_zwj_cluster(self):
        tm = load_overlay()
        old = "hello 👨‍👩‍👧‍👦 world"
        new = "hello 👨‍👩‍👧‍👦 brave world"
        operations = tm.reference_diff(old, new)
        self.assertIn(("equal", "👨‍👩‍👧‍👦"), operations)
        self.assertNotIn(("delete", "👨"), operations)


if __name__ == "__main__":
    unittest.main()
