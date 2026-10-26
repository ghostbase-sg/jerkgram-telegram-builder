"""Chat-navigation cancellation contracts and actual Foundation scheduling fixture."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('JG_PERFORMANCE_SOURCE',ROOT/'work/swiftgram-src'))
STORE='submodules/JerkgramCore/Sources/JerkgramStore.swift'
CHAT='submodules/TelegramUI/Sources/ChatController.swift'
FIXTURE=r'''
let queue = DispatchQueue(label: "fixture.visit")
let gate = DispatchSemaphore(value: 0)
let entered = DispatchSemaphore(value: 0)
queue.async { entered.signal(); gate.wait() }
precondition(entered.wait(timeout: .now()+2) == .success)
var reads = 0
var callbacks = 0
var requests: [JerkgramArchiveVisitRequest] = []
let expected = JerkgramChangesSinceLastOpening(upperSequence: 7, deletedCount: 1, editedCount: 2, recoveredMediaCount: 3, eventIds: [JerkgramEventId(rawValue: "event")])
for _ in 0..<200 {
    let request = JerkgramArchiveVisitRequest.schedule(on: queue, work: { _ in reads += 1; return expected }, completion: { _ in callbacks += 1 })
    request.cancel()
    requests.append(request)
}
final class Owner { var request: JerkgramArchiveVisitRequest? }
var owner: Owner? = Owner()
weak var oldOwner = owner
owner?.request = JerkgramArchiveVisitRequest.schedule(on: queue, work: { _ in reads += 1; return expected }, completion: { [weak owner] _ in _ = owner })
weak var droppedRequest = owner?.request
owner = nil
precondition(oldOwner == nil && droppedRequest == nil, "queued work retained departed screen/request")
gate.signal()
queue.sync {}
RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.03))
precondition(reads == 0 && callbacks == 0, "canceled queued visits still queried archive")
let started = DispatchSemaphore(value: 0)
let finish = DispatchSemaphore(value: 0)
let inFlight = JerkgramArchiveVisitRequest.schedule(on: queue, work: { request in
    started.signal(); finish.wait()
    precondition(request.isCancelled)
    return expected
}, completion: { _ in callbacks += 1 })
precondition(started.wait(timeout: .now()+2) == .success)
inFlight.cancel() // Must return without waiting for the archive queue.
finish.signal()
queue.sync {}
RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.03))
precondition(callbacks == 0, "stale in-flight result reached departed screen")
var delivered = false
let successful = JerkgramArchiveVisitRequest.schedule(on: queue, work: { request in
    precondition(!Thread.isMainThread && !request.isCancelled)
    reads += 1
    return expected
}, completion: { result in
    precondition(Thread.isMainThread && result == expected)
    callbacks += 1; delivered = true
})
let deadline = Date(timeIntervalSinceNow: 2)
while !delivered && Date() < deadline { RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.01)) }
precondition(delivered && reads == 1 && callbacks == 1)
withExtendedLifetime(successful) {}
print("PASS: 200 queued cancellations, screen/request release, in-flight cancellation, main completion")
'''
class ChatVisitTests(unittest.TestCase):
    def test_chat_exit_cancels_visit_and_does_not_wait_for_archive(self):
        text=(SOURCE/CHAT).read_text()
        appearance=text.split('override public func viewDidAppear(',1)[1].split('self.chatDisplayNode.historyNode.experimentalSnapScrollToItem',1)[0]
        self.assertIn('JerkgramCaptureRecorder.requestChangesSinceLastOpening(',appearance)
        self.assertNotIn('Queue.concurrentDefaultQueue().async',appearance)
        self.assertNotIn('readyIndexRecords(',appearance)
        disappearance=text.split('override public func viewWillDisappear(',1)[1].split('func saveInterfaceState(',1)[0]
        self.assertIn('self.jerkgramArchiveVisitRequest?.cancel()',disappearance)
        self.assertIn('self.jerkgramArchiveVisitRequest = nil',disappearance)
        self.assertIn('completion: { [weak self] changes in',appearance)
    def test_archive_request_has_cooperative_cancellation_boundaries(self):
        text=(SOURCE/STORE).read_text()
        request=text.split('public static func requestChangesSinceLastOpening(',1)[1].split('public static func record(',1)[0]
        self.assertNotIn('queue.sync',request)
        self.assertIn('JerkgramArchiveVisitRequest.schedule(on: self.queue',request)
        self.assertGreaterEqual(request.count('!request.isCancelled'),2)
    @unittest.skipUnless(shutil.which('swiftc'),'Swift unavailable: actual scheduling fixture runs in macOS CI')
    def test_actual_request_scheduling_and_lifetime(self):
        # Compile the complete actual Foundation module, with Store in main.swift
        # so the fixture can exercise its fileprivate scheduling boundary.
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'main.swift';exe=Path(directory)/'check'
            p.write_text((SOURCE/STORE).read_text()+'\n'+FIXTURE)
            others=sorted(str(x) for x in (SOURCE/'submodules/JerkgramCore/Sources').glob('*.swift') if x.name != 'JerkgramStore.swift')
            subprocess.run(['swiftc','-swift-version','5','-warnings-as-errors',*others,str(p),'-o',str(exe)],check=True)
            subprocess.run([str(exe)],check=True,timeout=15)
if __name__=='__main__':unittest.main()
