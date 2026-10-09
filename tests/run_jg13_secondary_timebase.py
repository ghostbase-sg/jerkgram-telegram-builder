#!/usr/bin/env python3
"""Execute the real detach method with a strict AVFoundation boundary facade.

This verifies ownership/notification/idempotence, not UIKit/device playback.
"""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("JG13_SOURCE", ROOT / "work/swiftgram-src"))

def block(text, needle):
    assert text.count(needle) == 1, needle
    start = text.index(needle)
    brace = text.index("{", start)
    end, depth = brace + 1, 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[start:end] + "\n"

def fixture():
    text = (SOURCE / "submodules/MediaPlayer/Sources/MediaPlayerNode.swift").read_text()
    ownership = next(line.strip() for line in text.splitlines() if line.strip().startswith("var secondaryVideoLayersUseRenderSynchronizer ="))
    return r'''
import Foundation
final class Queue {
    static func mainQueue() -> Queue { Queue() }
    func isCurrent() -> Bool { Thread.isMainThread }
}
public final class AVSampleBufferDisplayLayer {
    var synchronizerAttached = false
    var writes = 0
    var flushes = 0
    var controlTimebase: Int? {
        get { 42 }
        set {
            precondition(!synchronizerAttached, "manual timebase while synchronizer attached")
            writes += 1
        }
    }
    func flushAndRemoveImage() { flushes += 1 }
}
final class Node {
    var secondaryVideoLayers: [ObjectIdentifier: AVSampleBufferDisplayLayer] = [:]
    var secondaryVideoLayersUpdated: (([AVSampleBufferDisplayLayer]) -> Void)?
''' + ownership + "\n" + block(text, "var currentSecondaryVideoLayers:") + block(text, "public func removeSecondaryVideoLayer(") + r'''
}
let native = Node()
native.secondaryVideoLayersUseRenderSynchronizer = true
let attached = AVSampleBufferDisplayLayer()
attached.synchronizerAttached = true
native.secondaryVideoLayers[ObjectIdentifier(attached)] = attached
var callbacks = 0
native.secondaryVideoLayersUpdated = { layers in
    precondition(layers.isEmpty)
    // Renderer removal is asynchronous; keep the facade attached here.
    callbacks += 1
}
native.removeSecondaryVideoLayer(attached)
native.removeSecondaryVideoLayer(attached)
precondition(attached.writes == 0 && attached.flushes == 1 && callbacks == 1)
precondition(native.currentSecondaryVideoLayers.isEmpty)
let legacy = Node()
let manual = AVSampleBufferDisplayLayer()
legacy.secondaryVideoLayers[ObjectIdentifier(manual)] = manual
legacy.removeSecondaryVideoLayer(manual)
legacy.removeSecondaryVideoLayer(manual)
precondition(manual.writes == 1 && manual.flushes == 1)
print("secondary-timebase component PASS: synchronizer ownership, legacy detach, idempotence")
'''

if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="jg13-timebase-") as tmp:
        file = Path(tmp) / "main.swift"
        file.write_text(fixture())
        subprocess.run(["xcrun", "swift", str(file)], check=True)
