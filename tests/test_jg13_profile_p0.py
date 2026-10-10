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
            P + "PeerInfoHeaderNode.swift",
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

    def test_settings_sub_boundaries_and_correlated_slow_spans(self):
        screen = read(P + "PeerInfoScreen.swift")
        background = read(P + "GhostBaseProfileFullscreenBackground.swift")
        for stage in ("header", "sections", "panesAndTail"):
            self.assertIn("beginPerformanceSpan(." + stage + ")", screen)
            self.assertIn("endPerformanceSpan(." + stage + ",", screen)
        for stage in ("bgPreferences", "bgResolve", "bgApply"):
            self.assertIn("beginPerformanceSpan(." + stage + ")", background)
            self.assertIn("endPerformanceSpan(." + stage + ",", background)
        self.assertLess(background.index("endPerformanceSpan(.bgPreferences"), background.index("guard let liveSettings = loadedSettings"))
        self.assertLess(background.index("endPerformanceSpan(.bgResolve"), background.index("guard self.currentStateKey != stateKey"))
        self.assertIn('if !stage.settingsDetail || self.context == "settings"', background)
        core = read("submodules/TelegramCore/Sources/Utils/JerkgramPerformanceDiagnostics.swift")
        for token in ("slowEventLimit = 96", "timings.count < 32", "capacity = 512", "startedAt >= self.started", "now - $0 >= 1.0", "submittedAtMs=", "finishedAtMs=", "startMs=", "endMs=", "suppressedSlowEvents"):
            self.assertIn(token, core)

    def test_scroll_navigation_boundaries_are_measured(self):
        screen = read(P + "PeerInfoScreen.swift")
        navigation = screen.split("fileprivate func updateNavigation(", 1)[1].split("func scrollViewWillBeginDragging", 1)[0]
        self.assertIn("beginPerformanceSpan(.navigation)", navigation)
        self.assertIn("endPerformanceSpan(.navigation,", navigation)
        for stage, call in (("scrollHeader", "self.headerNode.update("), ("scrollPanes", "self.paneContainerNode.update(")):
            begin = navigation.index("beginPerformanceSpan(." + stage + ")")
            end = navigation.index("endPerformanceSpan(." + stage + ",")
            self.assertLess(begin, navigation.index(call))
            self.assertLess(navigation.index(call), end)
        background = read(P + "GhostBaseProfileFullscreenBackground.swift")
        detail = background.split("var settingsDetail: Bool", 1)[1].split("private struct Sample", 1)[0]
        for stage in ("navigation", "scrollHeader", "scrollPanes"):
            self.assertIn("." + stage, detail)

    def test_header_inner_boundaries_and_weak_probe_binding(self):
        header = read(P + "PeerInfoHeaderNode.swift")
        self.assertIn("weak var ghostBasePerformanceProbe: JerkgramProfilePerformanceProbe?", header)
        screen = read(P + "PeerInfoScreen.swift")
        self.assertEqual(screen.count("self.headerNode.ghostBasePerformanceProbe = ghostBaseProfileBackgroundView.performanceProbe"), 1)
        for stage, operation in (("headerPhonePreference", "let hideOwnPhone ="), ("headerAvatar", "self.avatarListNode.update(size: CGSize()"), ("headerCover", "let backgroundCoverSize = self.backgroundCover.update(")):
            begin = header.index("ghostBasePerformanceProbe?.begin(." + stage + ")")
            end = header.index("ghostBasePerformanceProbe?.end(." + stage + ",")
            self.assertLess(begin, header.index(operation))
            self.assertLess(header.index(operation), end)
        detail = read(P + "GhostBaseProfileFullscreenBackground.swift").split("var settingsDetail: Bool", 1)[1].split("private struct Sample", 1)[0]
        for stage in ("headerPhonePreference", "headerAvatar", "headerCover"):
            self.assertIn("." + stage, detail)

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
