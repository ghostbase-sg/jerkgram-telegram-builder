#!/usr/bin/env python3
"""Execute actual Foundation/Darwin capture owner on CI. NOT iPhone/UI profiling."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work/swiftgram-src/submodules/TelegramCore/Sources/Utils/JerkgramPerformanceDiagnostics.swift"
FIXTURE = r'''
let capture = JerkgramPerformanceDiagnostics.shared
precondition(!capture.isRecording)
capture.start()
capture.start() // Duplicate start must not reset or add another owner.
capture.measure("fixture", milliseconds: 20.0)
RunLoop.main.run(until: Date(timeIntervalSinceNow: 1.3))
capture.stop()
let report = capture.report()
precondition(report.contains("fixture: calls=1 maxMs=20 slow>=16.7ms=1"))
precondition(report.contains("cpuPct="))
precondition(report.contains("peakRSSBytes="))
precondition(report.contains("mainQueueWaitMs="))
precondition(!capture.isRecording)
capture.record("must-not-appear")
precondition(!capture.report().contains("must-not-appear"))
capture.start()
precondition(!capture.report().contains("fixture:"))
for _ in 0..<600 { capture.record("bounded-event") }
precondition(capture.status.contains("512/512"))
NotificationCenter.default.post(name: Notification.Name("UIApplicationDidEnterBackgroundNotification"), object: nil)
precondition(!capture.isRecording)
let stopped = capture.report()
RunLoop.main.run(until: Date(timeIntervalSinceNow: 1.2))
precondition(capture.report() == stopped) // Canceled/in-flight old timer cannot append.
print("PASS: actual capture CPU/memory/main queue, bounded ring, duplicate start, stop, restart and background shutdown")
'''

with tempfile.TemporaryDirectory(prefix="jg13-performance-") as directory:
    target = Path(directory) / "main.swift"
    target.write_text(SOURCE.read_text() + "\n" + FIXTURE)
    subprocess.run(["xcrun", "swift", str(target)], check=True)
