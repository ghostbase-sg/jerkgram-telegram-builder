import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
func expect(_ condition: @autoclosure () -> Bool, _ message: String) { precondition(condition(), message) }
final class World {
    final class Task {
        let due: Double
        let run: () -> Void
        var cancelled = false
        init(_ due: Double, _ run: @escaping () -> Void) { self.due = due; self.run = run }
    }
    final class Request {
        let data: Data
        let completion: (JerkgramAnalyticsV3Core.Response) -> Void
        var cancelled = false
        init(_ data: Data, _ completion: @escaping (JerkgramAnalyticsV3Core.Response) -> Void) { self.data = data; self.completion = completion }
    }
    var time: Double = 0
    var wallOffset: Double = 0
    var bytes: Data?
    var failSave = false
    var revoked = false
    var failMarker = false
    var ids = 0
    var tasks: [Task] = []
    var requests: [Request] = []
    let epoch: Double = 1_795_000_000
    var now: Date { Date(timeIntervalSince1970: epoch + time + wallOffset) }
    func advance(_ seconds: Double) {
        let end = self.time + seconds
        while let next = self.tasks.filter({ !$0.cancelled && $0.due <= end }).min(by: { $0.due < $1.due }) {
            next.cancelled = true
            self.time = next.due
            next.run()
        }
        self.time = end
    }
    func core(delivery: Bool = true, storage: JerkgramAnalyticsV3FileStorage? = nil, markerDefaults: UserDefaults? = nil) -> JerkgramAnalyticsV3Core {
        let dependencies = JerkgramAnalyticsV3Core.Dependencies(
            now: { self.now }, uptime: { self.time },
            makeUUID: {
                self.ids += 1
                return UUID(uuidString: String(format: "00000000-0000-4000-8000-%012d", self.ids))!
            }, randomUnit: { 0 },
            load: { storage?.load() ?? self.bytes.map(JerkgramAnalyticsV3Core.LoadResult.data) ?? .absent },
            save: { data in
                if self.failSave { return false }
                if let storage, !storage.save(data) { return false }
                self.bytes = data; return true
            }, loadRevocation: { markerDefaults?.bool(forKey: "revoked") ?? self.revoked }, saveRevocation: { revoked in
                if self.failMarker { return false }
                if let markerDefaults {
                    markerDefaults.set(revoked, forKey: "revoked")
                    return markerDefaults.synchronize() && markerDefaults.bool(forKey: "revoked") == revoked
                }
                self.revoked = revoked; return true
            },
            schedule: { delay, action in
                let task = Task(self.time + delay, action); self.tasks.append(task)
                return JerkgramAnalyticsV3Cancellation { task.cancelled = true }
            }, send: { data, completion in
                let request = Request(data, completion); self.requests.append(request)
                return JerkgramAnalyticsV3Cancellation { request.cancelled = true }
            })
        return JerkgramAnalyticsV3Core(metadata: .init(appVersion: "1.2.1", build: "184", osVersion: "27.1", osMajor: 27, deviceRegion: "RU", deviceModel: "iPhone18,1"), dependencies: dependencies, deliveryEnabled: delivery)
    }
    var persisted: [String: Any] { (try! JSONSerialization.jsonObject(with: bytes!)) as! [String: Any] }
    var events: [[String: Any]] { persisted["events"] as! [[String: Any]] }
    func count(_ name: String) -> Int { events.filter { $0["eventName"] as? String == name }.count }
}

if CommandLine.arguments.count == 3 {
    let url = URL(string: CommandLine.arguments[1])!
    expect(url.host == "127.0.0.1" && url.path == "/v3/events", "mock endpoint must be loopback")
    let scenario = CommandLine.arguments[2]
    let world = World()
    let received = DispatchSemaphore(value: 0)
    var response: JerkgramAnalyticsV3Core.Response?
    var callback: ((JerkgramAnalyticsV3Core.Response) -> Void)?
    var networkTask: URLSessionDataTask?
    var attempts = 0
    let dependencies = JerkgramAnalyticsV3Core.Dependencies(
        now: { world.now }, uptime: { world.time }, makeUUID: { UUID() }, randomUnit: { 0 },
        load: { world.bytes.map(JerkgramAnalyticsV3Core.LoadResult.data) ?? .absent }, save: { world.bytes = $0; return true },
        loadRevocation: { world.revoked }, saveRevocation: { world.revoked = $0; return true },
        schedule: { delay, action in
            let task = World.Task(world.time + delay, action); world.tasks.append(task)
            return JerkgramAnalyticsV3Cancellation { task.cancelled = true }
        }, send: { data, completion in
            callback = completion
            attempts += 1
            var request = URLRequest(url: url); request.httpMethod = "POST"; request.httpBody = data
            request.setValue("application/json", forHTTPHeaderField: "Content-Type"); request.timeoutInterval = 3
            request.setValue(scenario, forHTTPHeaderField: "X-Jerkgram-Test-Scenario")
            let task = URLSession.shared.dataTask(with: request) { _, http, _ in
                response = .init(statusCode: (http as? HTTPURLResponse)?.statusCode)
                received.signal()
            }
            networkTask = task
            task.resume()
            return JerkgramAnalyticsV3Cancellation { task.cancel() }
        })
    let core = JerkgramAnalyticsV3Core(metadata: .init(appVersion: "1.2.1", build: "184", osVersion: "27.1", osMajor: 27), dependencies: dependencies, deliveryEnabled: scenario == "disabled" ? JerkgramAnalyticsV3.productionTransportEnabled : true)
    core.initialize(enabled: true, evidence: .fresh); core.didBecomeActive(); world.advance(60)
    if scenario == "disabled" {
        world.advance(600)
        expect(attempts == 0, "production-style disabled gate produces no transport request")
    } else if scenario == "off" {
        let oldIds = Set(world.events.compactMap { $0["eventId"] as? String })
        Thread.sleep(forTimeInterval: 0.1) // allow loopback server to receive the pending request
        core.setEnabled(false)
        expect(networkTask?.state != .running && world.events.isEmpty, "OFF cancels actual URLSession task and persistent queue")
        expect(received.wait(timeout: .now() + 5) == .success, "URLSession cancellation completion timed out")
        core.setEnabled(true)
        callback?(response!)
        expect(world.events.allSatisfy { !oldIds.contains($0["eventId"] as! String) }, "old HTTP completion cannot restore old consent events")
        core.setEnabled(false); world.advance(600)
        expect(attempts == 1, "OFF prevents further actual HTTP requests")
    } else {
        expect(received.wait(timeout: .now() + 5) == .success, "local HTTP response timed out")
        callback?(response!)
        if scenario == "retry" {
            expect(!world.events.isEmpty, "HTTP503 retains durable batch")
            world.advance(5)
            expect(received.wait(timeout: .now() + 5) == .success, "retry HTTP response timed out")
            callback?(response!)
            expect(attempts == 2 && world.events.isEmpty, "HTTP retry succeeds with stable IDs")
        } else {
            world.advance(600)
            expect(attempts == 1 && world.events.isEmpty, "HTTP2xx acknowledges; HTTP400 drops without retry")
        }
    }
    print("Analytics v3 loopback HTTP mock: " + scenario + " passed")
    exit(0)
}

do {
    let w = World(); let core = w.core()
    core.initialize(enabled: true, evidence: .fresh)
    core.didBecomeActive(); core.didBecomeActive()
    w.advance(3); core.didResignActive(); w.advance(1); core.didBecomeActive()
    expect(w.count("install_registered") == 1 && w.count("app_opened") == 1, "fresh install and one real opening")
    expect(w.count("session_started") == 1, "one session")
    core.didEnterBackground(); w.advance(2); core.didBecomeActive()
    expect(w.count("app_opened") == 2, "background to active counts")
    w.advance(6)
    expect(w.count("session_engaged") == 1, "engagement uses cumulative foreground, excludes background")
    expect(w.requests.isEmpty, "opening does not perform HTTP")
    w.advance(54)
    expect(w.requests.count == 1, "bounded scheduler sends later")
    let first = w.requests[0]
    let body = try! JSONSerialization.jsonObject(with: first.data) as! [String: Any]
    expect(body["schema"] as? Int == 3 && body["platform"] as? String == "ios", "contract envelope")
    expect(body["appVersion"] as? String == "1.2.1", "Jerkgram release identity")
    expect(first.data.count <= 16 * 1024 && (body["events"] as! [Any]).count <= 20, "wire bounds")
    let expectedKeys = Set(["schema", "platform", "installationId", "appVersion", "build", "osVersion", "osMajor", "deviceRegion", "deviceModel", "events"])
    expect(Set(body.keys) == expectedKeys, "only contract fields are transmitted")
    expect(UUID(uuidString: body["installationId"] as! String) != nil, "installation ID is random UUID")
    expect((body["events"] as! [[String: Any]]).allSatisfy { ($0["occurredAt"] as! String).hasSuffix("Z") }, "wire timestamps are UTC")
    first.completion(.init(statusCode: nil))
    w.advance(5)
    expect(w.requests.count == 2 && w.requests[1].data == first.data, "retry preserves event IDs/body")
    // Ignore newEvents entirely: a 2xx status is sufficient.
    w.requests[1].completion(.init(statusCode: 204))
    expect(w.events.isEmpty, "successful batch removed")
    print(String(data: first.data, encoding: .utf8)!)
}
for evidence in [JerkgramAnalyticsV3Core.InstallationEvidence.provenExisting, .unknown] {
    let w = World(); let core = w.core(delivery: false)
    core.initialize(enabled: true, evidence: evidence); core.didBecomeActive()
    expect(w.count("install_registered") == 0, "update and ambiguous old installs are never new")
}
do {
    let w = World(); let core = w.core()
    core.initialize(enabled: false, evidence: .fresh); core.didBecomeActive()
    expect(w.events.isEmpty, "OFF fresh install has no events")
    core.setEnabled(true)
    expect(w.count("install_registered") == 0, "re-enabling is never an install")
    core.didEnterBackground(); core.didBecomeActive(); w.advance(60)
    expect(w.requests.count == 1, "enabled collection eventually sends")
    let stale = w.requests[0]
    core.setEnabled(false)
    expect(stale.cancelled && w.events.isEmpty, "OFF cancels and clears persisted queue")
    core.setEnabled(true); core.didEnterBackground(); core.didBecomeActive()
    let nextIds = w.events.compactMap { $0["eventId"] as? String }
    stale.completion(.init(statusCode: 200)); w.advance(1)
    expect(w.events.compactMap { $0["eventId"] as? String } == nextIds, "old response cannot remove new-consent events")
}
do {
    let w = World(); let core = w.core(delivery: false)
    core.initialize(enabled: true, evidence: .fresh); core.didBecomeActive(); w.advance(10)
    core.didEnterBackground(); w.advance(1799); core.didBecomeActive()
    expect(w.count("session_started") == 1, "29:59 pause keeps session")
    core.didEnterBackground(); w.advance(1800); core.didBecomeActive(); w.advance(10)
    expect(w.count("session_started") == 2 && w.count("session_engaged") == 2, "30 minute boundary starts a new engaged session")
    let ids = w.events.compactMap { $0["eventId"] as? String }
    core.didEnterBackground()
    let reloaded = w.core(delivery: false)
    reloaded.initialize(enabled: true, evidence: .fresh)
    expect(w.events.compactMap { $0["eventId"] as? String } == ids, "queue IDs survive process restart and evidence cannot reclassify existing installation")
    reloaded.didBecomeActive()
    expect(w.count("install_registered") == 1, "existing v3 receipt wins over fresh evidence")
    for _ in 0..<600 { reloaded.didEnterBackground(); reloaded.didBecomeActive() }
    expect(w.events.count <= 500, "persistent queue bounded")
    w.advance(7 * 86400 + 1); reloaded.didEnterBackground(); reloaded.didBecomeActive()
    expect(w.events.count < 10, "expired events pruned")
}
do {
    let w = World(); let core = w.core()
    core.initialize(enabled: true, evidence: .provenExisting); core.didBecomeActive(); w.advance(60)
    w.requests[0].completion(.init(statusCode: 400)); w.advance(600)
    expect(w.requests.count == 1 && w.events.isEmpty, "invalid 400 batch is dropped, never retried")
}
do {
    let w = World(); let core = w.core()
    core.initialize(enabled: true, evidence: .unknown); core.didBecomeActive(); w.advance(60)
    for i in 0..<5 {
        expect(w.requests.count == i + 1, "one in-flight request")
        w.requests[i].completion(.init(statusCode: 503))
        if i < 4 { w.advance(Double(5 << i)) }
    }
    w.advance(3600)
    expect(w.requests.count == 5, "automatic retries bounded; no permanent polling")
    expect(!w.events.isEmpty, "retry exhaustion retains queue until expiry or later lifecycle")
}
do {
    let w = World(); let core = w.core(delivery: false)
    core.initialize(enabled: true, evidence: .fresh); core.didBecomeActive()
    let opens = w.count("app_opened")
    w.wallOffset += 86400; core.didResignActive(); core.didBecomeActive()
    expect(w.count("app_opened") == opens, "calendar boundary alone never opens app")
    core.didEnterBackground(); core.didBecomeActive()
    expect(w.count("app_opened") == opens + 1, "next real opening across day still counts")
    expect(w.requests.isEmpty, "disabled production-style delivery never sends")
}
do {
    let w = World(); let core = w.core()
    core.initialize(enabled: true, evidence: .unknown); core.didBecomeActive(); w.advance(60)
    let stalled = w.requests[0]
    w.advance(8)
    expect(stalled.cancelled, "deadline cancels stalled transport")
    w.advance(5)
    expect(w.requests.count == 2, "deadline uses the same bounded retry scheduler")
    core.setEnabled(false)
    w.advance(100)
    expect(w.requests.count == 2 && w.events.isEmpty, "OFF cancels deadlines and all scheduled retries")
}
do {
    let w = World(); let core = w.core()
    core.initialize(enabled: true, evidence: .unknown)
    w.failSave = true
    core.didBecomeActive(); w.advance(300)
    expect(w.requests.isEmpty, "unpersisted IDs cannot be sent")
    core.setEnabled(false); w.failSave = false; core.setEnabled(true)
    expect(w.events.allSatisfy { $0["eventName"] as? String != "app_opened" }, "consent transition clears failed old collection before re-enable")
}
do {
    let w = World()
    var collector: JerkgramAnalyticsV3Core? = w.core(delivery: false)
    collector!.initialize(enabled: true, evidence: .unknown)
    for _ in 0..<40 { collector!.didBecomeActive(); collector!.didEnterBackground() }
    collector = nil
    let sender = w.core()
    sender.initialize(enabled: true, evidence: .unknown); sender.didBecomeActive(); w.advance(60)
    let body = try! JSONSerialization.jsonObject(with: w.requests[0].data) as! [String: Any]
    expect((body["events"] as! [Any]).count == 20, "large persistent queue splits at exactly 20 events")
    w.requests[0].completion(.init(statusCode: 200))
    expect(!w.events.isEmpty, "acknowledgement removes only the sent IDs")
    w.advance(60)
    expect(w.requests.count == 2, "subsequent batch respects scheduler spacing")
}
do {
    let w = World(); let core = w.core(delivery: false)
    core.initialize(enabled: true, evidence: .fresh); core.didBecomeActive()
    w.wallOffset -= 600
    core.didEnterBackground(); core.didBecomeActive()
    expect(w.events.allSatisfy { ($0["timestamp"] as! Double) <= w.now.timeIntervalSince1970 + 300 }, "events over five minutes in future never remain sendable")
}
do {
    let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    let store = JerkgramAnalyticsV3FileStorage(directory: directory)
    defer { try? FileManager.default.removeItem(at: directory) }
    for code in [CocoaError.fileNoSuchFile.rawValue, CocoaError.fileReadNoSuchFile.rawValue] {
        expect(JerkgramAnalyticsV3FileStorage.isMissingFile(NSError(domain: NSCocoaErrorDomain, code: code)), "Cocoa missing-file variants")
        let denied = NSError(domain: NSPOSIXErrorDomain, code: 13)
        expect(!JerkgramAnalyticsV3FileStorage.isMissingFile(NSError(domain: NSCocoaErrorDomain, code: code, userInfo: [NSUnderlyingErrorKey: denied])), "wrapped permission error is not missing")
    }
    expect(JerkgramAnalyticsV3FileStorage.isMissingFile(NSError(domain: NSPOSIXErrorDomain, code: 2)), "direct ENOENT")
    for code in [13, 20, 5] {
        expect(!JerkgramAnalyticsV3FileStorage.isMissingFile(NSError(domain: NSPOSIXErrorDomain, code: code)), "access, not-directory and I/O errors fail closed")
    }
    if case .absent = store.load() {} else { preconditionFailure("fresh persistent store") }
    let bytes = Data("durable-state".utf8)
    expect(store.save(bytes), "atomic file write")
    if case let .data(reloaded) = JerkgramAnalyticsV3FileStorage(directory: directory).load() {
        expect(reloaded == bytes, "file persistence survives owner restart")
    } else { preconditionFailure("existing file must load") }
    let blocked = directory.appendingPathComponent("blocked")
    try! Data([0]).write(to: blocked)
    let failed = JerkgramAnalyticsV3FileStorage(directory: blocked)
    expect(!failed.save(bytes), "real file failure is surfaced to the fail-closed core")
    if case .unreadable = failed.load() {} else { preconditionFailure("unreadable is not absent") }
    // Corruption must not mint/send a replacement installation identity.
    let w = World(); let corrupt = w.core(storage: store)
    corrupt.initialize(enabled: true, evidence: .fresh); corrupt.didBecomeActive(); w.advance(300)
    expect(w.ids == 0 && w.requests.isEmpty, "corrupt receipt fails closed")
    try! Data(repeating: 65, count: 256 * 1024 + 1).write(to: directory.appendingPathComponent("v3-state.json"))
    if case .unreadable = store.load() {} else { preconditionFailure("read size cap") }
}
do {
    let w = World(); let core = w.core(delivery: false)
    core.initialize(enabled: true, evidence: .unknown); core.didBecomeActive()
    w.time = 10 // a busy queue delays the due engagement timer
    core.didEnterBackground()
    expect(w.count("session_engaged") == 1, "background boundary observes engagement even if due timer was delayed")
    w.advance(0); core.didEnterBackground()
    expect(w.count("session_engaged") == 1, "late timer/background callbacks cannot duplicate engagement")
}
do {
    let w = World(); let core = w.core(delivery: false)
    core.initialize(enabled: true, evidence: .unknown); core.didBecomeActive(); core.didEnterBackground()
    w.wallOffset += 7200; w.advance(10); core.didBecomeActive()
    expect(w.count("session_started") == 1, "wall clock jump cannot fabricate a 30-minute pause in this process")
}
do {
    let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    defer { try? FileManager.default.removeItem(at: directory) }
    let store = JerkgramAnalyticsV3FileStorage(directory: directory)
    let w = World(); let core = w.core(storage: store)
    core.initialize(enabled: true, evidence: .fresh); core.didBecomeActive()
    let identity = w.persisted["installationId"] as! String
    core.setEnabled(false)
    if case let .data(bytes) = store.load() {
        let saved = try! JSONSerialization.jsonObject(with: bytes) as! [String: Any]
        expect((saved["events"] as! [Any]).isEmpty && saved["session"] == nil, "OFF clears durable file events/session")
        expect(saved["installationId"] as? String == identity, "OFF preserves install receipt")
    } else { preconditionFailure("OFF state must be persisted") }
    let restarted = w.core(storage: store)
    restarted.initialize(enabled: true, evidence: .fresh); restarted.didBecomeActive()
    expect(w.count("install_registered") == 0, "restart after OFF does not register another install")
}
do {
    let w = World(); var core: JerkgramAnalyticsV3Core? = w.core()
    core!.initialize(enabled: true, evidence: .unknown); core!.didBecomeActive(); w.advance(60)
    w.requests[0].completion(.init(statusCode: 429, retryAfter: 3600))
    w.advance(1); core!.didEnterBackground(); w.advance(1); core!.didBecomeActive()
    expect(w.persisted["retryAttempt"] as? Int == 1, "retry budget is persistent")
    core!.didEnterBackground(); core = nil
    let reloaded = w.core(); reloaded.initialize(enabled: true, evidence: .unknown); reloaded.didBecomeActive()
    w.advance(3597)
    expect(w.requests.count == 1, "429 cooldown survives background/foreground and process restart")
    w.advance(1)
    expect(w.requests.count == 2, "retry allowed exactly at persisted deadline 3660")
}
do {
    let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    let backup = directory.appendingPathExtension("held")
    let suite = "JerkgramAnalyticsV3Tests." + UUID().uuidString
    let defaults = UserDefaults(suiteName: suite)!
    defer {
        try? FileManager.default.removeItem(at: directory); try? FileManager.default.removeItem(at: backup)
        defaults.removePersistentDomain(forName: suite); _ = defaults.synchronize()
    }
    let storage = JerkgramAnalyticsV3FileStorage(directory: directory)
    let w = World(); let core = w.core(storage: storage, markerDefaults: defaults)
    core.initialize(enabled: true, evidence: .fresh); core.didBecomeActive()
    let originalId = w.persisted["installationId"] as! String
    let oldIds = Set(w.events.compactMap { $0["eventId"] as? String })
    // Keep a genuinely old durable state, but make its queue-file path unwritable.
    // The independent existing-defaults marker remains writable.
    try! FileManager.default.moveItem(at: directory, to: backup)
    try! Data([0]).write(to: directory)
    core.setEnabled(false); core.setEnabled(true)
    expect(defaults.bool(forKey: "revoked"), "failed OFF/ON file writes retain durable revocation")
    try! FileManager.default.removeItem(at: directory)
    try! FileManager.default.moveItem(at: backup, to: directory)
    let reloaded = w.core(storage: storage, markerDefaults: UserDefaults(suiteName: suite)!)
    reloaded.initialize(enabled: true, evidence: .fresh)
    expect(w.events.isEmpty && w.persisted["installationId"] as? String == originalId, "recovery drops pre-OFF events while preserving receipt")
    expect(!defaults.bool(forKey: "revoked"), "marker clears only after clean queue commit")
    reloaded.didBecomeActive(); w.advance(60)
    let body = try! JSONSerialization.jsonObject(with: w.requests[0].data) as! [String: Any]
    expect((body["events"] as! [[String: Any]]).allSatisfy { !oldIds.contains($0["eventId"] as! String) }, "no pre-OFF event can be sent after disk recovery/restart")
    core.setEnabled(false) // cancel the original owner's already disabled work
}
do {
    let w = World(); let core = w.core()
    core.initialize(enabled: true, evidence: .unknown); core.didBecomeActive()
    w.failMarker = true
    core.setEnabled(false); core.setEnabled(true); w.advance(600)
    expect(w.requests.isEmpty, "revocation marker write failure blocks delivery")
}
do {
    let w = World(); let core = w.core()
    core.initialize(enabled: true, evidence: .unknown); core.didBecomeActive()
    w.advance(10); core.didEnterBackground(); w.advance(60)
    core.didBecomeActive()
    expect(w.requests.isEmpty, "overdue queue does not send directly from opening")
    w.advance(2)
    expect(w.requests.count == 1, "short foreground visits eventually deliver aged queued events")
    w.requests[0].completion(.init(statusCode: 200))
    for _ in 0..<10 {
        core.didEnterBackground(); core.didBecomeActive(); w.advance(1)
    }
    expect(w.requests.count == 1, "rapid repeated openings do not trigger one HTTP per open")
}
print("Analytics v3 native core: all checks passed")
