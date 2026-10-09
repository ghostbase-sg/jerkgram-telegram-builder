"""Bounded diagnostic contracts, not performance or UIKit runtime proof."""
import os
import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("JG13_SOURCE", ROOT / "work/swiftgram-src"))
P = "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/"

def read(path):
    return (SOURCE / path).read_text()

class ProfileP0Tests(unittest.TestCase):
    def test_chain_order_and_bounded_owner_set(self):
        tree = ast.parse((ROOT / "scripts/materialize_jg13.py").read_text())
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        calls = [node.value.func.id for node in main.body if isinstance(node, ast.Expr)
                 and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)]
        self.assertEqual(calls.count("apply_cleanup"), 1)
        self.assertEqual(calls.count("apply_p0"), 1)
        self.assertLess(calls.index("apply_cleanup"), calls.index("apply_p0"))
        manifest = json.loads((ROOT / "patches/jg13-profile-p0-diagnostics.sha256.json").read_text())
        self.assertEqual(set(manifest["owners"]), {
            P + "GhostBaseProfileFullscreenBackground.swift", P + "PeerInfoScreen.swift",
            P + "PeerInfoAvatarTransformContainerNode.swift",
            "submodules/TelegramCore/Sources/Utils/JerkgramPerformanceDiagnostics.swift",
            "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift",
            "submodules/MediaPlayer/Sources/ChunkMediaPlayerV2.swift",
            "submodules/MediaPlayer/Sources/MediaPlayerNode.swift"})
        self.assertEqual(len(manifest["regression_locks"]), 5)
        self.assertFalse(set(manifest["owners"]) & set(manifest["regression_locks"]))

    def test_summary_not_frame_logging_or_new_workers(self):
        text = read(P + "GhostBaseProfileFullscreenBackground.swift")
        self.assertTrue("final class JerkgramProfilePerformanceProbe" in text, "Missing bounded probe")
        probe = text.split("final class JerkgramProfilePerformanceProbe", 1)[1].split("enum GhostBaseProfileGlassRuntime", 1)[0]
        self.assertEqual(probe.count("Logger.shared.log"), 1)
        for token in ("Timer(", "CADisplayLink", "addObserver", "DispatchQueue", "FileManager", "UserDefaults"):
            self.assertFalse(token in probe, f"Probe creates work: {token}")
        self.assertIn("enum Stage: String, CaseIterable", probe)
        self.assertIn("maxMs", probe)
        self.assertIn("liveInstances", probe)

    def test_expensive_boundaries_measured(self):
        screen = read(P + "PeerInfoScreen.swift")
        for stage in (".layout", ".data"):
            self.assertTrue("beginPerformanceSpan(" + stage in screen)
            self.assertTrue("endPerformanceSpan(" + stage in screen)
        avatar = read(P + "PeerInfoAvatarTransformContainerNode.swift")
        self.assertIn("performanceProbe?.begin(.transition)", avatar)
        self.assertIn("performanceProbe?.begin(.play)", avatar)
        self.assertIn("performanceProbe?.end(.play", avatar)
        self.assertTrue("performanceProbe?.begin(.preferences)" in avatar, "Preferences cost is not separated from transition")
        self.assertTrue("performanceProbe?.begin(.alpha)" in avatar, "Layer transition cost is not separated from play")
        text = read(P + "GhostBaseProfileFullscreenBackground.swift")
        for stage in (".background", ".attach", ".detach"):
            self.assertIn("beginPerformanceSpan(" + stage, text)

    def test_source_slot_accounting_and_cleanup(self):
        text = read(P + "GhostBaseProfileFullscreenBackground.swift")
        self.assertEqual(text.count("self.sourceDisposable.set("), 1)
        self.assertTrue("private func setSourceSubscription" in text)
        self.assertIn("performanceProbe.disposals += 1", text)
        self.assertIn("performanceProbe.subscriptions += 1", text)
        self.assertIn('summary("inactive"', text)
        self.assertIn('summary("deinit"', text)
        self.assertIn("self.sourceDisposable.dispose()", text)

    def test_native_playback_untouched_diagnostics_gated(self):
        text = read("submodules/MediaPlayer/Sources/ChunkMediaPlayerV2.swift")
        self.assertIn("ghostBaseHadSecondaryOutput", text)
        self.assertIn("ghostBaseDetachedPlayingTicks == 60", text)
        self.assertIn("self.resetMediaDataStarvation()", text)
        self.assertIn("1.0 / 60.0 : 1.0 / 5.0", text)
        self.assertIn("self.updateTimer?.invalidate()", text)
        for name in ("GhostBaseProfileFullscreenBackground.swift", "PeerInfoAvatarTransformContainerNode.swift"):
            text = read(P + name)
            self.assertNotIn("AVPlayer(", text)
            self.assertNotIn(".sleep(", text)
        avatar = read(P + "PeerInfoAvatarTransformContainerNode.swift")
        self.assertIn("videoNode.play()", avatar)
        self.assertIn("animatedBackgroundEnabled", avatar)

if __name__ == "__main__":
    unittest.main()
