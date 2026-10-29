"""Patch A source gate; run with --source-root pointing at builder output.

UIKit/ItemListUI cannot run on this Linux host. These are explicitly source
ownership regressions, not simulated ARC or device lifetime measurements.
"""
import argparse
import hashlib
from pathlib import Path
import re
import unittest

SOURCE_ROOT = Path(__file__).resolve().parents[1] / "work/swiftgram-src"
RELATIVE_PATH = Path("submodules/SettingsUI/Sources/Jerkgram/JerkgramDataAndBackupController.swift")
BASELINE_SHA256 = "176e0fde77815eee31aadb6c5af586085b156cf6e2e03ed32c68916462259c38"
LIFETIME_SUBCLASS = '''private final class JerkgramDataAndBackupListController: ItemListController {
    deinit {
        JerkgramWave1Instrumentation.add("liveDataBackupControllers", -1)
    }
}

'''


class DataBackupOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (SOURCE_ROOT / RELATIVE_PATH).read_text()
        cls.factory = cls.source.split("public func jerkgramDataAndBackupController", 1)[1].split(
            "private func jerkgramDataCoreRootURL", 1
        )[0]
        cls.actions = cls.factory.split("let arguments =", 1)[1].split("let signal =", 1)[0]

    def test_action_target_is_weak_and_never_rebound_strong_in_actions(self):
        self.assertRegex(self.factory, r"weak var actionTarget: ItemListController\?")
        self.assertNotRegex(self.actions, r"actionTarget\s*=")
        self.assertNotRegex(self.factory, r"(?m)^    var controller:")

    def test_factory_returns_strong_local_after_weak_handoff(self):
        self.assertRegex(self.factory, r'let controller = JerkgramDataAndBackupListController\(context: context, state: signal\)\s+JerkgramWave1Instrumentation.add\("liveDataBackupControllers"\)\s+actionTarget = controller\s+return controller\s+}')
        self.assertNotRegex(self.factory, r"weak var controller|return controller!")

    def test_lifetime_instrumentation_pairs_one_creation_with_one_deinit(self):
        self.assertIn(LIFETIME_SUBCLASS, self.source)
        self.assertEqual(self.source.count('JerkgramWave1Instrumentation.add("liveDataBackupControllers"'), 2)
        self.assertEqual(self.source.count('JerkgramDataAndBackupListController(context:'), 1)

    def test_export_import_and_picker_resolve_weak_action_target(self):
        for operation in ("Export", "Import"):
            self.assertIn("if let controller = actionTarget { jerkgramPresentArchive" + operation + "(context: context, controller: controller) }", self.actions)
        self.assertIn("[weak picker, weak controller = actionTarget]", self.actions)
        self.assertIn("actionTarget?.push(picker)", self.actions)
        self.assertEqual(len(re.findall(r"\bcontroller\b", self.actions)), 8,
                         "Unexpected controller reference may reintroduce an action capture")

    def test_cleanup_has_no_ui_controller_capture(self):
        cleanup = self.actions.split('case "cleanup":', 1)[1].split("default:", 1)[0]
        self.assertNotRegex(cleanup, r"\b(controller|actionTarget|context)\b")

    def test_only_ownership_edges_change_from_verified_build175(self):
        # Reversing the allowed edge changes must recover the exact baseline.
        # Catches accidental changes to cleanup, toggles, retention or archive calls.
        normalized = self.source.replace("weak var actionTarget: ItemListController?", "var controller: ItemListController?")
        normalized = normalized.replace(LIFETIME_SUBCLASS, "")
        normalized = normalized.replace("let controller = JerkgramDataAndBackupListController", "let controller = ItemListController")
        normalized = normalized.replace('    JerkgramWave1Instrumentation.add("liveDataBackupControllers")\n', "")
        normalized = normalized.replace("if let controller = actionTarget {", "if let controller {")
        normalized = normalized.replace("weak controller = actionTarget]", "weak controller = controller]")
        normalized = normalized.replace("actionTarget?.push(picker)", "controller?.push(picker)")
        normalized = normalized.replace("let controller = ItemListController(context: context, state: signal)\n    actionTarget = controller\n    return controller", "controller = ItemListController(context: context, state: signal)\n    return controller!")
        self.assertEqual(hashlib.sha256(normalized.encode()).hexdigest(), BASELINE_SHA256)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=SOURCE_ROOT)
    options, remaining = parser.parse_known_args()
    SOURCE_ROOT = options.source_root
    unittest.main(argv=[__file__, *remaining])
