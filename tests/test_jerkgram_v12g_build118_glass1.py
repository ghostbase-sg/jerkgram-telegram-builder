import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "work/swiftgram-src"
OVERLAY = REPO / "scripts/apply_jerkgram_v12g_build118_glass1.py"


class Build118GlassTests(unittest.TestCase):
    def test_glass_is_account_setting_gated_and_uses_reference_material(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative_paths = [
                "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenItemSectionContainerNode.swift",
                "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderSingleLineTextFieldNode.swift",
                "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderMultiLineTextFieldNode.swift",
                "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoPaneContainerNode.swift",
                "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoListPaneNode.swift",
                "submodules/TelegramUI/Components/PeerInfo/PeerInfoVisualMediaPaneNode/Sources/PeerInfoVisualMediaPaneNode.swift",
                "submodules/TelegramUI/Components/PeerInfo/PeerInfoVisualMediaPaneNode/BUILD",
            ]
            for relative in relative_paths:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(SOURCE / relative, target)
            env = os.environ.copy()
            env["JERKGRAM_SOURCE_ROOT"] = str(root)
            result = subprocess.run(
                [sys.executable, str(OVERLAY)], cwd=REPO, env=env,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            combined = "\n".join((root / relative).read_text() for relative in relative_paths)
            self.assertIn("BUILD118_GLASS1", combined)
            self.assertIn("ghostBaseGlassEnabled: Bool", combined)
            self.assertIn("UIColor.black.withAlphaComponent(0.075)", combined)
            self.assertIn("UIColor.white.withAlphaComponent(0.035)", combined)
            self.assertIn("cornerRadius: 16.0", combined)
            self.assertIn("ghostBaseGlassEnabled: ghostBaseGlassEnabled", combined)
            self.assertIn("//submodules/TelegramUI/Components/GlassBackgroundComponent", combined)
            list_source = (root / relative_paths[4]).read_text(encoding="utf-8")
            self.assertIn("import ComponentFlow\n", list_source)
            self.assertIn("else {", combined)


if __name__ == "__main__":
    unittest.main()
