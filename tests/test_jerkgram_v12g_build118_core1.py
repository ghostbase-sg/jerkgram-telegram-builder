import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
OVERLAY = REPO / "scripts/apply_jerkgram_v12g_build118_core1.py"


class Build118CoreOverlayTests(unittest.TestCase):
    def run_overlay(self, root: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["JERKGRAM_SOURCE_ROOT"] = str(root)
        return subprocess.run(
            [sys.executable, str(OVERLAY)],
            cwd=REPO,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

    def test_materializes_account_scoped_core_without_payload_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.run_overlay(root)
            self.assertEqual(result.returncode, 0, result.stdout)

            module = root / "submodules/JerkgramCore"
            models = (module / "Sources/JerkgramModels.swift").read_text(encoding="utf-8")
            index = (module / "Sources/JerkgramIndex.swift").read_text(encoding="utf-8")
            build = (module / "BUILD").read_text(encoding="utf-8")

            self.assertIn("public struct JerkgramEventId", models)
            self.assertIn("public let accountPeerId: Int64", models)
            self.assertIn("public let eventId: JerkgramEventId", models)
            self.assertIn("public let chatPeerId: Int64", models)
            self.assertNotIn("messageText", index)
            self.assertNotIn("mediaBytes", index)
            self.assertIn('name = "JerkgramCore"', build)

    def test_overlay_rejects_second_materialization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self.run_overlay(root)
            self.assertEqual(first.returncode, 0, first.stdout)
            second = self.run_overlay(root)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("owner already exists", second.stdout)


if __name__ == "__main__":
    unittest.main()
