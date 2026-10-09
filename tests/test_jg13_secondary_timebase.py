"""Ownership contracts for the Build145 AVFoundation exception path.

These inspect actual materialized methods; they are not device crash proof.
"""
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("JG13_SOURCE", ROOT / "work/swiftgram-src"))

def block(text, needle):
    start = text.index(needle)
    brace = text.index("{", start)
    depth, end = 1, brace + 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[start:end]

class SecondaryTimebaseTests(unittest.TestCase):
    def setUp(self):
        self.node = (SOURCE / "submodules/MediaPlayer/Sources/MediaPlayerNode.swift").read_text()
        self.v2 = (SOURCE / "submodules/MediaPlayer/Sources/ChunkMediaPlayerV2.swift").read_text()

    def test_v2_declares_synchronizer_ownership_before_callbacks_or_attach(self):
        self.assertTrue("var secondaryVideoLayersUseRenderSynchronizer = false" in self.node, "Missing explicit timebase ownership")
        claim = "playerNode.secondaryVideoLayersUseRenderSynchronizer = true"
        self.assertTrue(claim in self.v2, "V2 does not claim synchronizer ownership")
        self.assertLess(self.v2.index(claim), self.v2.index("self.partsStateDisposable ="))
        self.assertLess(self.v2.index(claim), self.v2.index("self.renderSynchronizer.addRenderer(self.videoRenderer"))

    def test_detach_cannot_write_synchronizer_owned_timebase(self):
        method = block(self.node, "public func removeSecondaryVideoLayer(")
        self.assertTrue("if !self.secondaryVideoLayersUseRenderSynchronizer" in method, "Detach writes synchronizer-owned timebase")
        guard = block(method, "if !self.secondaryVideoLayersUseRenderSynchronizer")
        self.assertIn("layer.controlTimebase = nil", guard)
        self.assertEqual(method.count("layer.controlTimebase = nil"), 1)
        self.assertIn("self.secondaryVideoLayersUpdated?(self.currentSecondaryVideoLayers)", method)
        self.assertIn("removeValue(forKey: key)", method)

    def test_updates_cannot_queue_manual_timebase_for_synchronizer_outputs(self):
        method = block(self.node, "private func updateState()")
        loop = block(method, "for secondaryLayer in self.secondaryVideoLayers.values")
        self.assertTrue("if !self.secondaryVideoLayersUseRenderSynchronizer" in loop, "Update queues manual timebase on synchronizer output")
        guard = block(loop, "if !self.secondaryVideoLayersUseRenderSynchronizer")
        self.assertIn("videoQueue.async", guard)
        self.assertIn("secondaryLayer.controlTimebase = timebase", guard)
        self.assertEqual(loop.count("secondaryLayer.controlTimebase = timebase"), 1)
        self.assertIn("secondaryLayer.setAffineTransform(transform)", loop)
        # Preserve stock primary and the legacy manual-timebase backend.
        self.assertIn("videoLayer.controlTimebase = timebase", method)
        self.assertIn("videoLayer.setAffineTransform(transform)", method)

if __name__ == "__main__":
    unittest.main()
