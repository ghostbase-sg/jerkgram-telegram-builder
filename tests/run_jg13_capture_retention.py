#!/usr/bin/env python3
"""Execute real storage/aggregation for 600 simulated seconds, not a UI benchmark.

Only the monotonic clock and timer scheduling are controlled. A same-file test
extension feeds the same locked sample methods used by the real 1Hz timer.
Existing native capture/expiry/ownership tests run unmodified alongside this gate.
"""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/swiftgram-src'))
CORE = SOURCE / 'submodules/TelegramCore/Sources/Utils/JerkgramPerformanceDiagnostics.swift'
CLOCK = r'''
enum FixtureClock {
    private static let lock = NSLock()
    private static var value = 10000.0
    static var now: Double {
        get { lock.lock(); defer { lock.unlock() }; return value }
        set { lock.lock(); defer { lock.unlock() }; value = newValue }
    }
}
extension JerkgramPerformanceDiagnostics {
    func fixtureSample(cpu: Double, rss: Int64, thermal: Int, wait: Double) {
        self.lock.lock(); defer { self.lock.unlock() }
        guard self.running else { return }
        let now = FixtureClock.now
        self.recordUtilitySampleLocked(now: now, cpuPercent: cpu, peakRSS: rss, thermal: thermal)
        self.recordMainWaitLocked(submittedAt: now, finishedAt: now + wait / 1000, route: self.visibleRoute)
    }
    func fixtureBounds() {
        self.lock.lock(); defer { self.lock.unlock() }
        precondition(self.telemetryBlocks.count <= 120)
        precondition(self.operationSummaries.count <= 29)
        precondition(self.operationWorst.count <= 29 && self.windowWorst.count <= 60)
        precondition(self.retainedSamples.count <= 89)
        precondition(self.sampleReferences.count == self.retainedSamples.count)
        precondition(self.sampleReferences.values.allSatisfy { $0 >= 1 && $0 <= 2 })
        precondition(self.timings.count <= 32)
        precondition(self.fixedOverflow.count <= 63)
        precondition(self.retainedDetailLinesLocked().count <= 96)
        precondition(self.lines.count + self.telemetryBlocks.count + self.retainedDetailLinesLocked().count + self.captureBoundaries.count <= 512)
    }
}
'''
FIXTURE = r'''
let capture = JerkgramPerformanceDiagnostics.shared
let operations = JerkgramPerformanceDiagnostics.Operation.allCases
precondition(operations.count == 29)
func span(_ operation: JerkgramPerformanceDiagnostics.Operation, _ ms: Double) {
    let token = capture.beginOperation(operation)
    FixtureClock.now += ms / 1000
    capture.endOperation(token)
}
func stored(_ text: String) -> Int {
    let status = capture.status
    return Int(status.components(separatedBy: "/512")[0].components(separatedBy: " · ").last!)!
}
let profileStages = ["layout", "data", "background", "transition", "play", "attach", "detach", "preferences", "alpha", "bgPreferences", "bgResolve", "bgApply", "header", "sections", "panesAndTail", "navigation", "scrollHeader", "scrollPanes", "headerPhonePreference", "headerAvatar", "headerCover"]
let sectionStages = ["sectionsBuild", "sectionsRegularUpdate", "sectionsRegularPlacement", "sectionsRegularRemoval", "sectionsEditingBuild", "sectionsEditingUpdate", "sectionsEditingPlacement", "sectionsEditingRemoval"]
// Exercise both the three-minute report and the entire permitted ten minutes.
for seconds in [180, 600] {
    FixtureClock.now = 10000
    capture.start()
    capture.reserveClientWork()
    for stage in profileStages + sectionStages { capture.measure("settings." + stage, milliseconds: 1) }
    capture.measure("fixture-reserve-first", milliseconds: 0)
    capture.measure("fixture-reserve-second", milliseconds: 0)
    for second in 0..<seconds {
        FixtureClock.now = 10000 + Double(second) + 0.01
        capture.setVisibleRoute(second < 30 || second >= seconds - 30 ? "settings" : "chat")
        let late = second == seconds - 11
        capture.fixtureSample(cpu: late ? 299.9 : 10, rss: late ? 2000000000 : 100, thermal: late ? 3 : 0, wait: late ? 431 : 1)
        for operation in operations { span(operation, 0.01) }
        span(.historyNodeCompute, 100)
        capture.measure("chat.layout", milliseconds: 22)
        capture.measure("peer.layout", milliseconds: 23)
        capture.measure("worker.avatarDiskLoad", milliseconds: 24)
        if second == seconds - 10 { capture.setVisibleRoute("chat"); span(.keyboardLayout, 207); span(.sendCurrent, 208); span(.sendEnqueue, 209) }
        precondition(stored(capture.status) <= 512)
        capture.fixtureBounds()
    }
    FixtureClock.now = 10000 + Double(seconds)
    capture.stop()
    let result = capture.report()
    precondition(result.contains("telemetryBlocks=" + String(seconds / 5)))
    precondition(result.contains("durationSeconds=" + String(seconds)))
    precondition(result.contains("auxiliaryDropped=0"))
    precondition(result.contains("cpuMaxPct=299.9"))
    precondition(result.contains("peakRSSBytes=2000000000"))
    precondition(result.contains("thermalMax=3"))
    precondition(result.contains("mainQueueWaitMs=431"))
    for operation in operations { precondition(result.contains("operationSummary operation=" + operation.rawValue + " samples=")) }
    precondition(result.contains("operationSummary operation=historyNodeCompute samples=" + String(seconds * 2)))
    precondition(result.contains("fixedStageOverflow stage=peer.layout samples=" + String(seconds)))
    precondition(result.contains("unsupportedTimingSamplesDropped=0"))
    precondition(result.contains("operation=keyboardLayout route=chat thread=main"))
    precondition(result.contains("operation=sendCurrent route=chat thread=main"))
    precondition(result.contains("operation=sendEnqueue route=chat thread=main"))
    let detailLines = result.components(separatedBy: "\n").filter { $0.hasPrefix("slow stage=") }
    precondition(detailLines.count <= 96)
    let lateAt = (seconds - 10) * 1000
    precondition(detailLines.contains { line in
        guard line.contains("operation=sendCurrent"), let start = line.components(separatedBy: "startMs=").last?.components(separatedBy: " ").first, let time = Int(start) else { return false }
        return time >= lateAt
    }, "late send detail was starved by history")
    precondition(detailLines.contains { line in
        guard line.contains("operation=historyNodeCompute"), let start = line.components(separatedBy: "startMs=").last?.components(separatedBy: " ").first, let time = Int(start) else { return false }
        return time >= (seconds - 20) * 1000
    }, "end-of-session history detail was not retained")
    let frozen = capture.report()
    capture.fixtureSample(cpu: 999, rss: 9, thermal: 9, wait: 999)
    precondition(capture.report() == frozen)
    print("capture-retention PASS: actual " + String(seconds) + "s storage, full operation totals, late keyboard/send details, peak-preserving 5s blocks, fixed overflow stages, total512/detail96 bounds")
}
// Auxiliary flood cannot evict telemetry, operation details or session boundaries.
FixtureClock.now = 20000
capture.start(); capture.setVisibleRoute("chat")
capture.fixtureSample(cpu: 333, rss: 444, thermal: 2, wait: 555)
span(.inputText, 120)
for _ in 0..<5000 { capture.record("auxiliary-owner-event") }
precondition(stored(capture.status) == 512)
let flooded = capture.report()
precondition(flooded.contains("cpuMaxPct=333.0") && flooded.contains("mainQueueWaitMs=555"))
precondition(flooded.contains("operation=inputText route=chat thread=main"))
precondition(flooded.contains("capture start;"))
capture.stop()
precondition(capture.report().contains("capture stop: user"))
// Real worker spans remain separate from main-thread totals.
FixtureClock.now = 30000
capture.start()
let done = DispatchSemaphore(value: 0)
DispatchQueue.global().async {
    precondition(!Thread.isMainThread)
    span(.mediaFill, 250)
    done.signal()
}
precondition(done.wait(timeout: .now() + 5) == .success)
precondition(capture.report().contains("operationSummary operation=mediaFill samples=1 mainSamples=0 workerSamples=1"))
precondition(capture.report().contains("operation=mediaFill route=chat thread=worker"))
let stale = capture.beginOperation(.inputText)
capture.stop(); capture.start(); capture.endOperation(stale)
precondition(!capture.report().contains("operationSummary operation="))
precondition(capture.report().contains("auxiliaryDropped=0"))
capture.stop()
print("capture-retention PASS: auxiliary saturation preserves critical evidence, real worker attribution, stop freezes storage, restart clears summaries, stale tokens rejected")
// All29 slow operations every second, legacy detail saturation BEFORE late
// input, and a filled32-key table. The real bounded reservoirs must retain
// late events without increasing either the96-detail or512-total bound.
FixtureClock.now = 40000
capture.start(); capture.reserveClientWork(); capture.setVisibleRoute("chat")
FixtureClock.now += 0.1
capture.fixtureSample(cpu: 1, rss: 1, thermal: 0, wait: 1)
for _ in 0..<4 {
    for index in 0..<31 {
        capture.measure("legacy" + String(index), milliseconds: 20, startedAt: FixtureClock.now - 0.02, owner: 0)
    }
    FixtureClock.now += 1.01
}
precondition(capture.report().contains("slowEvents=96 "))
for second in 5..<600 {
    FixtureClock.now = 40000 + Double(second) + 0.1
    capture.fixtureSample(cpu: 1, rss: 1, thermal: 0, wait: 1)
    for operation in operations {
        capture.measure("client.work", milliseconds: 20, startedAt: FixtureClock.now - 0.02, owner: 0, detail: operation)
    }
    if second == 590 { span(.inputText, 250.5); span(.sendCurrent, 251.5) }
    capture.fixtureBounds()
}
FixtureClock.now = 40600
capture.stop()
let pressure = capture.report()
precondition(pressure.contains("telemetryBlocks=120") && pressure.contains("auxiliaryDropped=0"))
precondition(pressure.contains("durationMs=251 operation=sendCurrent route=chat thread=main"))
precondition(pressure.contains("durationMs=250 operation=inputText route=chat thread=main"))
precondition(!pressure.contains("legacyDetailsEvicted=0"))
print("capture-retention PASS: 600s all29 slow operations, full32 timing table and prefilled96 legacy details cannot starve late input/send or exceed critical storage bounds")
// This MUST fail if the window reservoir is removed: neither late span can
// replace its earlier, larger per-operation maximum. Input and history share
// the same20s window and must not compete with each other for its example.
FixtureClock.now = 50000
capture.start(); capture.setVisibleRoute("chat")
span(.historyNodeCompute, 300.5)
span(.inputText, 350.5)
FixtureClock.now = 50590
span(.historyNodeCompute, 80.5)
span(.inputText, 40.5)
let competed = DispatchSemaphore(value: 0)
DispatchQueue.global().async { span(.mediaFill, 500); competed.signal() }
precondition(competed.wait(timeout: .now() + 5) == .success)
capture.fixtureBounds()
capture.stop()
let windows = capture.report()
precondition(windows.contains("durationMs=300 operation=historyNodeCompute route=chat thread=main"))
precondition(windows.contains("durationMs=80 operation=historyNodeCompute route=chat thread=main"))
precondition(windows.contains("durationMs=350 operation=inputText route=chat thread=main"))
precondition(windows.contains("durationMs=40 operation=inputText route=chat thread=main"))
precondition(windows.contains("durationMs=500 operation=mediaFill route=chat thread=worker"))
print("capture-retention PASS: early larger maxima do not hide later smaller history/input in separate20s pools; longer worker cannot displace main-window evidence")
// Gross-overhead guard, NOT an iPhone performance claim: repeated unselected
// slow spans must update counts without rebuilding/sorting the reservoir.
FixtureClock.now = 60000
capture.start(); FixtureClock.now += 0.1
let benchmarkStarted = ProcessInfo.processInfo.systemUptime
for _ in 0..<100000 {
    capture.measure("client.work", milliseconds: 20, startedAt: FixtureClock.now - 0.02, owner: 0, detail: .inputLayout)
}
let overhead = ProcessInfo.processInfo.systemUptime - benchmarkStarted
precondition(overhead < 10, "100000 repeated spans exceeded the generous10s CI overhead ceiling")
capture.fixtureBounds(); capture.stop()
precondition(capture.report().contains("operationSummary operation=inputLayout samples=100000"))
precondition(capture.report().components(separatedBy: "\n").filter { $0.hasPrefix("slow stage=") }.count == 1)
print("capture-retention PASS: 100000 repeated spans retain exact totals/one example in " + String(overhead) + "s (CI only, NOT device profiling)")
'''

if __name__ == '__main__':
    original = CORE.read_text()
    controlled = original.replace('ProcessInfo.processInfo.systemUptime', 'FixtureClock.now')
    assert original.count('timer.resume()') == 1
    controlled = controlled.replace('timer.resume()', 'timer.cancel(); timer.resume()')
    with tempfile.TemporaryDirectory(prefix='jg13-retention-') as directory:
        target = Path(directory) / 'main.swift'
        target.write_text(controlled + '\n' + CLOCK + '\n' + FIXTURE)
        subprocess.run(['xcrun', 'swift', str(target)], check=True)
