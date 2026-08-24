import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
CORE = REPO / "scripts/apply_jerkgram_v12g_build118_core1.py"
OVERLAY = REPO / "scripts/apply_jerkgram_v12g_build118_archive1.py"


def load_overlay():
    spec = importlib.util.spec_from_file_location("build118_archive", OVERLAY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Build118ArchiveTests(unittest.TestCase):
    def test_materializes_v2_and_transaction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = os.environ.copy()
            env["JERKGRAM_SOURCE_ROOT"] = str(root)
            subprocess.run([sys.executable, str(CORE)], cwd=REPO, env=env, check=True)
            result = subprocess.run([sys.executable, str(OVERLAY)], cwd=REPO, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.assertEqual(result.returncode, 0, result.stdout)
            source = (root / "submodules/JerkgramCore/Sources/JerkgramArchiveV2.swift").read_text()
            transaction = (root / "submodules/JerkgramCore/Sources/JerkgramArchiveTransaction.swift").read_text()
            self.assertIn("schemaVersion = 2", source)
            self.assertIn("accountPeerId", source)
            self.assertIn("settingsSnapshot", source)
            self.assertIn("sha256", source)
            self.assertNotIn("authKey", source)
            self.assertNotIn("sessionToken", source)
            self.assertIn("rollback", transaction.lower())
            self.assertIn("confirmSettingsChanges", transaction)

    def test_exact_identity_never_deduplicates_by_text(self):
        archive = load_overlay()
        existing = [{"accountPeerId": 1, "eventId": "a", "text": "same"}]
        incoming = [
            {"accountPeerId": 1, "eventId": "a", "text": "same"},
            {"accountPeerId": 1, "eventId": "b", "text": "same"},
            {"accountPeerId": 2, "eventId": "a", "text": "same"},
        ]
        preview = archive.classify(existing, incoming)
        self.assertEqual(preview, {"duplicate": 1, "new": 2, "conflict": 0})

    def test_conflict_and_unavailable_account_write_nothing(self):
        archive = load_overlay()
        existing = [{"accountPeerId": 1, "eventId": "a", "text": "old"}]
        incoming = [{"accountPeerId": 1, "eventId": "a", "text": "new"}]
        self.assertEqual(archive.classify(existing, incoming)["conflict"], 1)
        self.assertFalse(archive.accounts_available({1, 2}, {1}))

    def test_rejects_traversal_and_bad_checksum(self):
        archive = load_overlay()
        self.assertFalse(archive.safe_relative_path("../events.jsonl"))
        self.assertFalse(archive.safe_relative_path("/tmp/events.jsonl"))
        self.assertTrue(archive.safe_relative_path("accounts/1/events.jsonl"))
        self.assertNotEqual(archive.sha256_hex(b"a"), archive.sha256_hex(b"b"))


if __name__ == "__main__":
    unittest.main()
