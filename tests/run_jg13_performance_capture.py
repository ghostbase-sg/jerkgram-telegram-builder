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
// Exercise actual slow-span emission, repeated-call suppression and total cap.
capture.start()
RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.05))
for index in 0..<30 {
    for _ in 0..<100 {
        capture.measure("detail" + String(index), milliseconds: 20.0, startedAt: ProcessInfo.processInfo.systemUptime - 0.02, owner: 7)
    }
}
let correlated = capture.report()
precondition(correlated.contains("slowEvents=30 suppressedSlowEvents=2970 limit=96"))
precondition(correlated.contains("slow stage=detail0 owner=7 startMs="))
precondition(correlated.contains("endMs=") && correlated.contains("durationMs=20"))
for _ in 0..<3 {
    RunLoop.main.run(until: Date(timeIntervalSinceNow: 1.05))
    for index in 0..<30 {
        capture.measure("detail" + String(index), milliseconds: 20.0, startedAt: ProcessInfo.processInfo.systemUptime - 0.02, owner: 7)
    }
}
precondition(capture.report().contains("slowEvents=96 suppressedSlowEvents=2994 limit=96"))
let lines = capture.report().components(separatedBy: "\n").filter { $0.hasPrefix("slow stage=") }
precondition(lines.count == 96, "slow events exceeded budget or were dropped")
capture.measure("detail0", milliseconds: 0.1, startedAt: ProcessInfo.processInfo.systemUptime, owner: 7)
precondition(capture.report().contains("slowEvents=96"))
capture.stop()
let finalSlowReport = capture.report()
capture.measure("detail0", milliseconds: 100.0, startedAt: ProcessInfo.processInfo.systemUptime, owner: 7)
precondition(capture.report() == finalSlowReport)
capture.start()
precondition(capture.report().contains("slowEvents=0 suppressedSlowEvents=0 limit=96"))
capture.stop()
capture.start()
RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.05))
let settingsProbe = JerkgramProfilePerformanceProbe()
settingsProbe.context = "settings"
let peerProbe = JerkgramProfilePerformanceProbe()
peerProbe.context = "peer"
for stage in JerkgramProfilePerformanceProbe.Stage.allCases where stage.settingsDetail {
    let settingsStart = settingsProbe.begin(stage)
    settingsProbe.end(stage, settingsStart - 0.02)
    let peerStart = peerProbe.begin(stage)
    peerProbe.end(stage, peerStart - 0.02)
    precondition(capture.report().contains("settings." + stage.rawValue + ": calls=1"))
    precondition(!capture.report().contains("peer." + stage.rawValue + ":"))
}
precondition(capture.report().contains("slowEvents=9"))
// Cover all profile context keys plus existing worker keys within the 32-key limit.
for probe in [settingsProbe, peerProbe] {
    for stage in JerkgramProfilePerformanceProbe.Stage.allCases where !stage.settingsDetail {
        let started = probe.begin(stage)
        probe.end(stage, started)
    }
}
capture.measure("worker.first", milliseconds: 0)
capture.measure("worker.second", milliseconds: 0)
precondition(capture.report().contains("worker.second: calls=1"))
precondition(capture.report().components(separatedBy: "\n").filter { $0.contains(": calls=") }.count == 29)
capture.stop()
print("PASS: actual capture Settings navigation keys, peer filtering and 29-key budget")
print("PASS: actual capture correlated slow spans, per-stage throttling, 96-event budget and reset")
print("PASS: actual capture CPU/memory/main queue, bounded ring, duplicate start, stop, restart and background shutdown")
'''

with tempfile.TemporaryDirectory(prefix="jg13-performance-") as directory:
    target = Path(directory) / "main.swift"
    background = (ROOT / "work/swiftgram-src/submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift").read_text()
    probe = "final class JerkgramProfilePerformanceProbe" + background.split("final class JerkgramProfilePerformanceProbe", 1)[1].split("enum GhostBaseProfileGlassRuntime", 1)[0]
    logger = "final class Logger { static let shared = Logger(); func log(_ category: String, _ text: String) {} }\n"
    target.write_text(SOURCE.read_text() + "\n" + logger + probe + "\n" + FIXTURE)
    subprocess.run(["xcrun", "swift", str(target)], check=True)
