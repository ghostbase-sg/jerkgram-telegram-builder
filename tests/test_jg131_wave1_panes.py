"""Builder source gates for coherent pane state. UIKit runtime is separate."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

SOURCE_ROOT = Path(__file__).resolve().parents[1] / "work/swiftgram-src"
BASE = Path("submodules/TelegramUI/Components/PeerInfo")


def read(relative):
    return (SOURCE_ROOT / BASE / relative).read_text()


class PaneVisualRevisionTests(unittest.TestCase):
    def test_protocol_declares_dynamic_hook_and_default_for_native_panes(self):
        source = read("PeerInfoPaneNode/Sources/PeerInfoPaneNode.swift")
        self.assertEqual(source.count("func updateJerkgramVisualState(glassEnabled: Bool, revision: UInt64)"), 2)

    def test_every_glass_owner_can_receive_new_revision(self):
        paths = ["PeerInfoScreen/Sources/PeerInfoPaneContainerNode.swift",
                 *["PeerInfoScreen/Sources/Panes/" + name for name in
                   ("PeerInfoMembersPane.swift", "PeerInfoGroupsInCommonPaneNode.swift", "PeerInfoListPaneNode.swift")],
                 *["PeerInfoVisualMediaPaneNode/Sources/" + name for name in
                   ("PeerInfoVisualMediaPaneNode.swift", "PeerInfoGiftsPaneNode.swift")]]
        for path in paths:
            with self.subTest(path=path):
                source = read(path)
                self.assertIn("private var ghostBaseGlassEnabled: Bool", source)
                self.assertIn("func updateJerkgramVisualState(glassEnabled: Bool, revision: UInt64)", source)
                self.assertIn("self.ghostBaseGlassEnabled = glassEnabled", source)

    def test_wrapper_invalidates_same_geometry_cache_before_node_update(self):
        source = read("PeerInfoScreen/Sources/PeerInfoPaneContainerNode.swift")
        wrapper = source.split("final class PeerInfoPaneWrapper", 1)[1].split("private final class GiftsTabItemComponent", 1)[0]
        self.assertIn("self.appliedParams = nil", wrapper)
        self.assertIn("self.node.updateJerkgramVisualState(glassEnabled: glassEnabled, revision: revision)", wrapper)
        self.assertIn("self.jerkgramVisualRevision == revision", wrapper)
        # Both iteration paths include newly constructed pending wrappers.
        self.assertRegex(source, r"pane\.pane\.updateJerkgramVisualState\(glassEnabled: self\.ghostBaseGlassEnabled, revision: self\.jerkgramVisualRevision\)\s+pane\.pane\.update\(")
        self.assertRegex(source, r"pane\.updateJerkgramVisualState\(glassEnabled: self\.ghostBaseGlassEnabled, revision: self\.jerkgramVisualRevision\)\s+pane\.update\(")
        lines = source.splitlines()
        for index, line in enumerate(lines):
            match = re.match(r"\s+(pane(?:\.pane)?)\.update\(size:", line)
            if match:
                self.assertEqual(lines[index - 1].strip(), match[1] + ".updateJerkgramVisualState(glassEnabled: self.ghostBaseGlassEnabled, revision: self.jerkgramVisualRevision)")
                self.assertEqual(len(lines[index - 1]) - len(lines[index - 1].lstrip()), len(line) - len(line.lstrip()))

    def test_groups_entry_equality_includes_revision_to_refresh_row_background(self):
        source = read("PeerInfoScreen/Sources/Panes/PeerInfoGroupsInCommonPaneNode.swift")
        self.assertIn("lhs.visualRevision == rhs.visualRevision", source)
        self.assertIn("lhs.glassEnabled == rhs.glassEnabled", source)
        self.assertIn("visualRevision: self.jerkgramVisualRevision", source)
        self.assertIn("isFirstLayout || self.jerkgramVisualStateDirty", source)

    def test_material_is_admitted_and_cleared_for_members_and_links(self):
        members = read("PeerInfoScreen/Sources/Panes/PeerInfoMembersPane.swift")
        links = read("PeerInfoScreen/Sources/Panes/PeerInfoListPaneNode.swift")
        self.assertIn("if GhostBaseGlassStyle.allowsMaterial {", members)
        self.assertIn("if GhostBaseGlassStyle.allowsMaterial {", links)
        self.assertIn("effectView.effect = nil", links)
        self.assertIn("self.ghostBaseGlassIsDark = nil", members)
        self.assertIn("self.ghostBaseGlassEnabled ? .clear : presentationData.theme.list.blocksBackgroundColor", links)
        for owner in (members, links):
            self.assertIn('JerkgramWave1Instrumentation.add("materialEffectCreations")', owner)

    def test_gifts_list_uses_propagated_state_and_accessible_fallback(self):
        pane = read("PeerInfoVisualMediaPaneNode/Sources/PeerInfoGiftsPaneNode.swift")
        gifts = read("PeerInfoVisualMediaPaneNode/Sources/GiftsListView.swift")
        self.assertIn("self.giftsListView.jerkgramGlassEnabled = self.ghostBaseGlassEnabled", pane)
        self.assertIn("self.jerkgramGlassEnabled ??", gifts)
        self.assertIn("GhostBaseGlassStyle.allowsTransparentSurfaces", gifts)

    @unittest.skipUnless(shutil.which("swift"), "Swift compiler unavailable; run on macOS builder")
    def test_native_production_wrapper_reconciles_revision_with_same_layout(self):
        source = read("PeerInfoScreen/Sources/PeerInfoPaneContainerNode.swift")
        wrapper = "final class PeerInfoPaneWrapper" + source.split("final class PeerInfoPaneWrapper", 1)[1].split("private final class GiftsTabItemComponent", 1)[0]
        fixture = Path(__file__).parent / "fixtures/build176/PaneWrapperRuntime.swift".read_text()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "main.swift"
            path.write_text(fixture.replace("// INSERT_PRODUCTION_WRAPPER", wrapper))
            result = subprocess.run([shutil.which("swift"), str(path)], capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("production wrapper revision runtime PASS", result.stdout)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=SOURCE_ROOT)
    options, remaining = parser.parse_known_args()
    SOURCE_ROOT = options.source_root
    unittest.main(argv=[__file__, *remaining])
