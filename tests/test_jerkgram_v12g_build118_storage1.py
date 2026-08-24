import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
CORE_OVERLAY = REPO / "scripts/apply_jerkgram_v12g_build118_core1.py"
STORAGE_OVERLAY = REPO / "scripts/apply_jerkgram_v12g_build118_storage1.py"


def load_storage_overlay():
    spec = importlib.util.spec_from_file_location("build118_storage", STORAGE_OVERLAY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Build118StorageTests(unittest.TestCase):
    def materialize(self, root: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["JERKGRAM_SOURCE_ROOT"] = str(root)
        core = subprocess.run(
            [sys.executable, str(CORE_OVERLAY)],
            cwd=REPO,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(core.returncode, 0, core.stdout)
        return subprocess.run(
            [sys.executable, str(STORAGE_OVERLAY)],
            cwd=REPO,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

    def test_defaults_and_explicit_unlimited_modes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.materialize(root)
            self.assertEqual(result.returncode, 0, result.stdout)
            source = (
                root / "submodules/JerkgramCore/Sources/JerkgramRetention.swift"
            ).read_text(encoding="utf-8")
            self.assertIn("historyDuration: .days30", source)
            self.assertIn("mediaByteLimit: .gigabytes1", source)
            self.assertIn("archiveSecretChats: false", source)
            self.assertIn("case forever", source)
            self.assertIn("case unlimited", source)
            self.assertIn("case disabled", source)
            self.assertIn("public enum JerkgramRetentionRuntime", source)
            self.assertIn("jerkgram.retention.account.\\(accountPeerId)", source)
            self.assertIn("jerkgram.account.\\(accountPeerId).setting", source)
            self.assertNotIn("currentAccount", source)

    def test_duration_and_media_limits_are_independent(self) -> None:
        storage = load_storage_overlay()
        self.assertIsNone(storage.history_cutoff_ms("forever", 1_000_000))
        self.assertEqual(storage.history_cutoff_ms("days7", 1_000_000), 1_000_000 - 7 * 86_400_000)
        self.assertIsNone(storage.media_budget_bytes("unlimited"))
        self.assertEqual(storage.media_budget_bytes("gigabytes1"), 1_073_741_824)
        self.assertEqual(storage.media_budget_bytes("disabled"), 0)

    def test_media_eviction_removes_oldest_bytes_but_not_event_identity(self) -> None:
        storage = load_storage_overlay()
        records = [
            {"eventId": "old", "observedAtMs": 10, "byteCount": 600},
            {"eventId": "middle", "observedAtMs": 20, "byteCount": 500},
            {"eventId": "new", "observedAtMs": 30, "byteCount": 400},
        ]
        plan = storage.media_eviction_plan(records, 900)
        self.assertEqual(plan, ["old"])
        self.assertEqual([record["eventId"] for record in records], ["old", "middle", "new"])

    def test_secret_chat_requires_explicit_opt_in(self) -> None:
        storage = load_storage_overlay()
        self.assertFalse(storage.should_capture("days30", True, False))
        self.assertTrue(storage.should_capture("days30", True, True))
        self.assertFalse(storage.should_capture("disabled", False, True))


if __name__ == "__main__":
    unittest.main()
