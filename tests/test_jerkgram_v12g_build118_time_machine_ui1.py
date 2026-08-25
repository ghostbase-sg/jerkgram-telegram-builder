import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
OVERLAY = REPO / "scripts/apply_jerkgram_v12g_build118_time_machine_ui1.py"


class Build118TimeMachineUITests(unittest.TestCase):
    def test_search_route_filters_diff_and_local_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            node = root / "submodules/TelegramUI/Components/Chat/ChatSearchNavigationContentNode/Sources/ChatSearchNavigationContentNode.swift"
            build = root / "submodules/TelegramUI/Components/Chat/ChatSearchNavigationContentNode/BUILD"
            strings = root / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
            node.parent.mkdir(parents=True)
            strings.parent.mkdir(parents=True)
            node.write_text('''public final class ChatSearchNavigationContentNode {\n    private let interaction: ChatPanelInterfaceInteraction\n    public init(context: AccountContext, chatLocation: ChatLocation, interaction: ChatPanelInterfaceInteraction) {\n        self.interaction = interaction\n        super.init()\n        self.view.addSubview(self.backgroundContainer)\n    }\n    override public var nominalHeight: CGFloat {\n        return 60.0\n    }\n    override public func updateLayout(size: CGSize, leftInset: CGFloat, rightInset: CGFloat, transition: ContainedViewLayoutTransition) -> CGSize {\n        return size\n    }\n}\n''')
            build.write_text('deps = [\n]')
            strings.write_text('public struct JerkgramStrings { public let languageCode: String }')
            env = os.environ.copy()
            env["JERKGRAM_SOURCE_ROOT"] = str(root)
            result = subprocess.run([sys.executable, str(OVERLAY)], cwd=REPO, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.assertEqual(result.returncode, 0, result.stdout)
            rendered = node.read_text()
            controller = (node.parent / "JerkgramTimeMachineController.swift").read_text()
            self.assertIn("jerkgramTimeMachineController", rendered)
            self.assertIn("interaction.presentController", rendered)
            self.assertLess(
                rendered.index("self.view.addSubview(self.backgroundContainer)"),
                rendered.index("self.view.addSubview(self.jerkgramTimeMachineBackground)"),
                "Time Machine control must be above the full-size background container",
            )
            for token in ("deletedMessage", "editedMessage", "recoveredMedia", "senderPeerId", "JerkgramTextDiff.diff", "navigateToMessage", "localDetail"):
                self.assertIn(token, controller)
            self.assertIn("loadNextPage", controller)
            self.assertIn("timeMachineLoadMore", strings.read_text())
            self.assertIn("event.eventId", controller)
            self.assertNotIn("deduplicat", controller.lower())


if __name__ == "__main__":
    unittest.main()
