"""Bounded source contracts. Device measurements and Swift compilation are separate."""
import os
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("JG13_SOURCE", ROOT / "work/target-src"))
CORE = "submodules/TelegramCore/Sources/Utils/JerkgramPerformanceDiagnostics.swift"
SETTINGS = "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
def read(path):
    file = SOURCE / path
    return file.read_text() if file.exists() else ""
class CaptureTests(unittest.TestCase):
    def test_visible_about_controls_and_export(self):
        text = read(SETTINGS)
        about = text.split("if page == .about {", 1)[1].split("if page == .debugResearch", 1)[0]
        for token in ("performanceStart", "performanceStop", "performanceShare", "performanceCopy", "JerkgramPerformanceDiagnostics.shared.status"):
            self.assertTrue(token in about, token)
        self.assertTrue("UIActivityViewController(activityItems:" in text)
        self.assertTrue("popoverPresentationController" in text)
    def test_bounded_session_and_shutdown(self):
        text = read(CORE)
        for token in ("capacity = 512", "pendingPulse", "generation", "timer?.cancel()", "expiredTimer?.cancel()", "removeObserver", "ru_utime", "ru_stime", "ru_maxrss", "thermalState", "mainQueueWaitMs", "snapshotChanged", "maxCaptureSeconds = 600"):
            self.assertTrue(token in text, token)
        for token in ("UserDefaults", "FileManager", "URLSession", "CADisplayLink", "AVPlayer"):
            self.assertFalse(token in text, token)
    def test_timing_and_native_output_routed_into_capture(self):
        p = "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/"
        helper = read(p + "GhostBaseProfileFullscreenBackground.swift")
        self.assertTrue("JerkgramPerformanceDiagnostics.shared.measure(" in helper)
        self.assertTrue("JerkgramPerformanceDiagnostics.shared.record(" in helper)
        native = read("submodules/MediaPlayer/Sources/ChunkMediaPlayerV2.swift")
        self.assertGreaterEqual(native.count("JerkgramPerformanceDiagnostics.shared.record("), 3)
if __name__ == "__main__": unittest.main()
