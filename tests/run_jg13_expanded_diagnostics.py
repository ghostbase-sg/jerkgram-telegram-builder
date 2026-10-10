#!/usr/bin/env python3
"""Execute actual capture + actual refresh owner with a strict display-link facade.

UIKit layout/rendering remains device-only; these test session/aggregate contracts.
"""
import os
from pathlib import Path
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/swiftgram-src'))
FACADE = r'''
// CADisplayLink is the sole UIKit boundary. It never draws or schedules a timer.
final class CADisplayLink: NSObject {
    static var created = 0
    static var invalidated = 0
    static var latest: CADisplayLink?
    private var target: NSObject?
    private let selector: Selector
    var timestamp: Double = 0
    var targetTimestamp: Double = 0
    var added = false
    init(target: NSObject, selector: Selector) {
        self.target = target; self.selector = selector
        super.init()
        Self.created += 1; Self.latest = self
    }
    func add(to loop: RunLoop, forMode mode: RunLoop.Mode) {
        precondition(loop == RunLoop.main && mode == .common)
        precondition(!self.added); self.added = true
    }
    func invalidate() {
        precondition(self.added)
        self.added = false; self.target = nil; Self.invalidated += 1
    }
    func fire(_ timestamp: Double, _ targetTimestamp: Double) {
        precondition(self.added)
        self.timestamp = timestamp; self.targetTimestamp = targetTimestamp
        _ = self.target?.perform(self.selector, with: self)
    }
}
'''
FIXTURE = r'''
let capture = JerkgramPerformanceDiagnostics.shared
private let probe = JerkgramRefreshIntervalProbe.shared
probe.start()
precondition(CADisplayLink.created == 0, "refresh owner exists while capture is off")
capture.setVisibleRoute("settings")
capture.start(); probe.start(); probe.start(); capture.start()
precondition(CADisplayLink.created == 1)
let link = CADisplayLink.latest!
link.fire(1.0, 1.0 + 1.0/60.0)
link.fire(1.0 + 1.0/60.0, 1.0 + 2.0/60.0)
link.fire(1.1, 1.1 + 1.0/60.0)
let sections = ["sectionsBuild", "sectionsRegularUpdate", "sectionsRegularPlacement", "sectionsRegularRemoval", "sectionsEditingBuild", "sectionsEditingUpdate", "sectionsEditingPlacement", "sectionsEditingRemoval"]
for key in sections { capture.measure("settings." + key, milliseconds: 20, startedAt: ProcessInfo.processInfo.systemUptime - 0.02, owner: 0) }
let measured = capture.report()
precondition(measured.contains("refresh route=settings samples=3"))
precondition(measured.contains("maxGapMs=83.33"))
precondition(measured.contains("missedOpportunitiesEstimated=4"))
for key in sections { precondition(measured.contains("settings." + key + ": calls=1")) }
// Route transitions must not bridge their intervals. Adaptive 120Hz/60Hz
// target spacing must not be forced by diagnostics.
capture.setVisibleRoute("chatList")
link.fire(2, 2 + 1.0/120.0)
link.fire(2 + 1.0/120.0, 2 + 2.0/120.0)
capture.setVisibleRoute("chat")
link.fire(3, 3 + 1.0/60.0)
capture.setVisibleRoute("unrecognized/private label")
link.fire(4, 4 + 1.0/60.0)
precondition(!capture.report().contains("unrecognized/private label"))
precondition(capture.report().contains("refresh route=chatList samples=2 maxGapMs=8.33"))
precondition(capture.report().contains("refresh route=chat samples=1 maxGapMs=0.00"))
precondition(capture.report().contains("refresh route=unclassified samples=1"))
// Refresh owner reserves client.work before UI/profile keys can fill the table.
precondition(capture.report().contains("client.work: calls=0"))
for index in 0..<23 { capture.measure("bounded" + String(index), milliseconds: 0) }
precondition(capture.report().components(separatedBy: "\n").filter { $0.contains(": calls=") }.count == 32)
capture.measure("rejected-extra", milliseconds: 100)
precondition(capture.report().contains("timingKeysRejected=1"))
precondition(!capture.report().contains("rejected-extra:"))
capture.stop()
precondition(CADisplayLink.invalidated == 1)
let stopped = capture.report()
capture.sampleRefreshOpportunity(timestamp: 5, targetTimestamp: 5.02)
precondition(capture.report() == stopped)
capture.start(); probe.start()
precondition(CADisplayLink.created == 2)
precondition(!capture.report().contains("refresh route="))
precondition(capture.report().contains("timingKeysRejected=0"))
NotificationCenter.default.post(name: Notification.Name("UIApplicationDidEnterBackgroundNotification"), object: nil)
precondition(!capture.isRecording && CADisplayLink.invalidated == 2)
print("expanded-diagnostics component PASS: actual refresh owner lifetime, common-mode boundary, adaptive interval aggregates, fixed private route labels, section keys, strict 32 timing cap, stop/restart/background invalidation")
'''
OWNERSHIP_FIXTURE = r'''
let capture = JerkgramPerformanceDiagnostics.shared
precondition(capture.beginOperation(.inputText) == nil)
capture.start()
let outgoing = NSObject()
let incoming = NSObject()
capture.setVisibleRoute("settings", owner: outgoing)
capture.setVisibleRoute("chat", owner: incoming)
capture.clearVisibleRoute(owner: outgoing)
precondition(capture.report().contains("route=chat timingKeysRejected=0 routeReleasesIgnored=1"))
capture.setVisibleRoute("chat", owner: outgoing)
capture.clearVisibleRoute(owner: incoming)
precondition(capture.report().contains("route=chat timingKeysRejected=0 routeReleasesIgnored=2"))
capture.clearVisibleRoute(owner: outgoing)
precondition(capture.report().contains("route=transition timingKeysRejected=0"))
capture.setVisibleRoute("private customer text", owner: incoming)
precondition(!capture.report().contains("private customer text"))
precondition(capture.report().contains("route=unclassified timingKeysRejected=0"))
capture.setVisibleRoute("chat", owner: incoming)
let real = capture.beginOperation(.inputText)
RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.025))
capture.endOperation(real)
let realReport = capture.report()
precondition(realReport.contains("client.work: calls=1"))
precondition(realReport.contains("operation=inputText route=chat"))
precondition(realReport.contains("operation=inputText route=chat thread=main"))
// All fixed details share one timing key, one slow-event pool, bounded labels.
capture.stop(); capture.start()
RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.025))
for operation in JerkgramPerformanceDiagnostics.Operation.allCases {
    capture.measure("client.work", milliseconds: 20, startedAt: ProcessInfo.processInfo.systemUptime - 0.02, owner: 0, detail: operation)
    precondition(capture.report().contains("operation=" + operation.rawValue + " route=chat"))
}
precondition(capture.report().contains("client.work: calls=" + String(JerkgramPerformanceDiagnostics.Operation.allCases.count)))
for index in 0..<31 { capture.measure("bounded" + String(index), milliseconds: 0) }
capture.measure("overflow", milliseconds: 20)
precondition(capture.report().contains("timingKeysRejected=1"))
precondition(!capture.report().contains("overflow:"))
let stale = capture.beginOperation(.mediaFill)
capture.stop()
let stopped = capture.report()
capture.endOperation(stale)
precondition(capture.report() == stopped)
capture.start(); capture.endOperation(stale)
precondition(!capture.report().contains("client.work:"))
precondition(capture.report().contains("routeReleasesIgnored=0"))
capture.stop()
// Entered-operation bitmap proves even fast hooks ran; it is not another table.
capture.start()
let fast = capture.beginOperation(.inputText)
capture.endOperation(fast)
precondition(capture.report().contains("operationsEntered=inputText (entry coverage only; inclusive spans overlap)"))
capture.stop()
let frozen = capture.report()
capture.endOperation(capture.beginOperation(.inputSend))
precondition(capture.report() == frozen)
capture.start()
precondition(capture.report().contains("operationsEntered= (entry coverage only; inclusive spans overlap)"))
let all = JerkgramPerformanceDiagnostics.Operation.allCases
precondition(all.count == 24 && all.count <= 64)
for operation in all { capture.endOperation(capture.beginOperation(operation)) }
let enteredReport = capture.report()
for operation in all { precondition(enteredReport.contains(operation.rawValue)) }
capture.stop()
capture.start()
RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.025))
// sync may execute inline on the calling main thread. This fixture must
// actually cross the thread boundary while retaining the worker assertion.
let workerDone = DispatchSemaphore(value: 0)
DispatchQueue.global().async {
    precondition(!Thread.isMainThread)
    capture.measure("client.work", milliseconds: 20, startedAt: ProcessInfo.processInfo.systemUptime - 0.02, owner: 0, detail: .mediaFill)
    workerDone.signal()
}
precondition(workerDone.wait(timeout: .now() + 5) == .success)
precondition(capture.report().contains("operation=mediaFill route=chat thread=worker"))
capture.stop()
print("client-operations component PASS: actual owner-checked release, safe labels, real begin/end, all24 fixed details sharing one timing slot/slow budget, entered-operation bitmap including fast calls, strict32 cap, stale-token/stop/restart guards")
'''
if __name__ == '__main__':
    core=(SOURCE / 'submodules/TelegramCore/Sources/Utils/JerkgramPerformanceDiagnostics.swift').read_text()
    settings=(SOURCE / 'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift').read_text()
    owner='private final class JerkgramRefreshIntervalProbe' + settings.split('private final class JerkgramRefreshIntervalProbe',1)[1].split('private enum GhostBaseKey',1)[0]
    with tempfile.TemporaryDirectory(prefix='jg13-expanded-') as directory:
        target=Path(directory)/'main.swift';target.write_text(core+'\n'+FACADE+'\n'+owner+'\n'+FIXTURE)
        subprocess.run(['xcrun','swift',str(target)],check=True)
        target.write_text(core+'\n'+OWNERSHIP_FIXTURE)
        subprocess.run(['xcrun','swift',str(target)],check=True)
        # Only the session-duration configuration is shortened. Real utility
        # expiry, generation guard, snapshot notification and owner cleanup run.
        expiry = core.replace('maxCaptureSeconds = 600.0', 'maxCaptureSeconds = 0.05')
        target.write_text(expiry+'\n'+FACADE+'\n'+owner+\
            '\nlet capture = JerkgramPerformanceDiagnostics.shared\n'+\
            'capture.start(); JerkgramRefreshIntervalProbe.shared.start()\n'+\
            'RunLoop.main.run(until: Date(timeIntervalSinceNow: 1.3))\n'+\
            'precondition(!capture.isRecording && CADisplayLink.invalidated == 1)\n'+\
            'let stopped = capture.report()\n'+\
            'RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.2))\n'+\
            'precondition(stopped == capture.report())\n'+\
            'print("expanded-diagnostics expiry PASS: actual utility cutoff invalidates refresh owner and freezes report")\n')
        subprocess.run(['xcrun','swift',str(target)],check=True)
