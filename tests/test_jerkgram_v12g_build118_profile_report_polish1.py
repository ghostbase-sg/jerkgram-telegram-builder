import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
OVERLAY = REPO / "scripts/apply_jerkgram_v12g_build118_profile_report_polish1.py"


class Build118ProfileReportPolishTests(unittest.TestCase):
    def test_patches_current_history_compile_username_form(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileReportPaneNode.swift"
            strings = root / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
            report.parent.mkdir(parents=True)
            strings.parent.mkdir(parents=True)
            report.write_text(
                '''            func value(_ value: String?) -> String {
                guard let value, !value.isEmpty else {
                    return "—"
                }
                return value
            }
            "Username: \\(value(previous.username)) → \\(value(current.username))"
            "BIO: \\(value(previous.about)) → \\(value(current.about))"
            "Emoji-status: \\(previous.emojiStatus) → \\(current.emojiStatus)"
            "Username: \\(oldValue) → \\(newValue)"
''',
                encoding="utf-8",
            )
            strings.write_text(
                '''        let prefixes: [(String, String)] = [
            ("Имя:", "Name:"),
        ]
''',
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["JERKGRAM_SOURCE_ROOT"] = str(root)
            result = subprocess.run(
                [sys.executable, str(OVERLAY)],
                cwd=REPO,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout)
            rendered_report = report.read_text(encoding="utf-8")
            rendered_strings = strings.read_text(encoding="utf-8")
            self.assertIn('"Юзернейм: \\(oldValue) → \\(newValue)"', rendered_report)
            self.assertIn("emojiStatusValue(previous.emojiStatus)", rendered_report)
            self.assertIn('("Эмодзи-статус:", "Emoji status:")', rendered_strings)


if __name__ == "__main__":
    unittest.main()
