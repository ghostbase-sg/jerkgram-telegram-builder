import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

final class JerkgramAnalyticsV3Cancellation {
    private let lock = NSLock()
    private var action: (() -> Void)?
    init(_ action: @escaping () -> Void) { self.action = action }
    func cancel() {
        self.lock.lock(); let action = self.action; self.action = nil; self.lock.unlock()
        action?()
    }
}

// The core is confined to its owner's serial queue. Tests inject the real
// clock/scheduling/storage/transport boundaries and execute this same code.
final class JerkgramAnalyticsV3Core {
    enum InstallationEvidence: String, Codable, Equatable { case fresh, provenExisting, unknown }
    struct Metadata {
        let appVersion: String
        let build: String
        let osVersion: String
        let osMajor: Int
        let deviceRegion: String?
        let deviceModel: String?
        init(appVersion: String, build: String, osVersion: String, osMajor: Int,
             deviceRegion: String? = nil, deviceModel: String? = nil) {
            self.appVersion = appVersion; self.build = build; self.osVersion = osVersion
            self.osMajor = osMajor
            let region = deviceRegion?.uppercased()
            self.deviceRegion = region.flatMap { value in
                value.utf8.count == 2 && value.utf8.allSatisfy { (65...90).contains($0) } ? value : nil
            }
            self.deviceModel = deviceModel.flatMap { $0.utf8.count <= 64 && !$0.isEmpty ? $0 : nil }
        }
        var valid: Bool {
            (1...99).contains(self.osMajor) && [self.appVersion, self.build, self.osVersion].allSatisfy {
                !$0.isEmpty && $0.utf8.count <= 64
            }
        }
    }
    struct Response {
        let statusCode: Int?
        let retryAfter: TimeInterval?
        init(statusCode: Int?, retryAfter: TimeInterval? = nil) { self.statusCode = statusCode; self.retryAfter = retryAfter }
    }
    enum LoadResult { case absent, data(Data), unreadable }
    struct Dependencies {
        let now: () -> Date
        let uptime: () -> TimeInterval
        let makeUUID: () -> UUID
        let randomUnit: () -> Double
        let load: () -> LoadResult
        let save: (Data) -> Bool
        let loadRevocation: () -> Bool
        let saveRevocation: (Bool) -> Bool
        // Both callbacks must execute on the same serial owner as the core.
        let schedule: (TimeInterval, @escaping () -> Void) -> JerkgramAnalyticsV3Cancellation
        let send: (Data, @escaping (Response) -> Void) -> JerkgramAnalyticsV3Cancellation
    }
    private struct Event: Codable {
        let eventId: String
        let eventName: String
        let occurredAt: String
        let timestamp: Double
    }
    private struct Session: Codable {
        var lastSeenAt: Double
        var lastBackgroundAt: Double?
        var foregroundSeconds: Double
        var engaged: Bool
    }
    private struct State: Codable {
        let schema: Int
        let installationId: String
        let evidence: InstallationEvidence
        var events: [Event]
        var session: Session?
        var lastAttemptAt: Double?
        var retryNotBefore: Double?
        var retryAttempt: Int?
        var retryExhausted: Bool?
    }
    private struct WireEvent: Encodable {
        let eventId: String
        let eventName: String
        let occurredAt: String
    }
    private struct Envelope: Encodable {
        let schema = 3
        let platform = "ios"
        let installationId: String
        let appVersion: String
        let build: String
        let osVersion: String
        let osMajor: Int
        let deviceRegion: String?
        let deviceModel: String?
        let events: [WireEvent]
    }
    private struct Batch {
        let body: Data
        let ids: Set<String>
        var attempt: Int
    }
    private struct Flight {
        let token: UInt64
        let batch: Batch
        var cancellation: JerkgramAnalyticsV3Cancellation?
    }
    private enum Lifecycle { case notStarted, active, inactive, background }
    private let metadata: Metadata
    private let dependencies: Dependencies
    private let deliveryEnabled: Bool
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    private let formatter: ISO8601DateFormatter
    private var state: State?
    private var initialized = false
    private var enabled = false
    private var healthy = true
    private var lifecycle: Lifecycle = .notStarted
    private var foregroundStarted: TimeInterval?
    private var backgroundStarted: TimeInterval?
    private var flushTimer: JerkgramAnalyticsV3Cancellation?
    private var engagedTimer: JerkgramAnalyticsV3Cancellation?
    private var timeoutTimer: JerkgramAnalyticsV3Cancellation?
    private var flight: Flight?
    private var retryBatch: Batch?
    private var epoch: UInt64 = 0
    private var token: UInt64 = 0
    private var foreground: Bool { self.lifecycle == .active || self.lifecycle == .inactive }

    init(metadata: Metadata, dependencies: Dependencies, deliveryEnabled: Bool) {
        self.metadata = metadata; self.dependencies = dependencies; self.deliveryEnabled = deliveryEnabled
        self.encoder.outputFormatting = [.sortedKeys]
        self.formatter = ISO8601DateFormatter()
        self.formatter.timeZone = TimeZone(secondsFromGMT: 0)
        self.formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
    }

    func initialize(enabled: Bool, evidence: InstallationEvidence) {
        guard !self.initialized else { self.setEnabled(enabled); return }
        self.initialized = true
        self.enabled = enabled
        let revoked = self.dependencies.loadRevocation()
        let markerSaved = enabled || self.dependencies.saveRevocation(true)
        switch self.dependencies.load() {
        case .unreadable:
            self.healthy = false
            return // no replacement identity or traffic on a storage read error
        case let .data(loaded):
            guard loaded.count <= 256 * 1024,
                  let decodedState = try? self.decoder.decode(State.self, from: loaded),
                  decodedState.schema == 3, Self.isV4(decodedState.installationId) else {
                self.healthy = false
                return // preserve corrupt state for recovery; never reset its receipt
            }
            var decoded = decodedState
            // Validate persisted strings once; steady-state events already came
            // through append(). Normal lifecycle work avoids hundreds of date parses.
            let allowed = Set(["install_registered", "app_opened", "session_started", "session_engaged"])
            decoded.events = decoded.events.suffix(500).filter { event in
                Self.isV4(event.eventId) && allowed.contains(event.eventName) && event.timestamp.isFinite
                    && self.formatter.date(from: event.occurredAt).map({ abs($0.timeIntervalSince1970 - event.timestamp) <= 0.01 }) == true
            }
            if let session = decoded.session,
               !session.foregroundSeconds.isFinite || session.foregroundSeconds < 0 || !session.lastSeenAt.isFinite {
                decoded.session = nil
            }
            self.state = decoded
        case .absent:
            let id = self.dependencies.makeUUID().uuidString.lowercased()
            guard Self.isV4(id) else { self.healthy = false; return }
            self.state = State(schema: 3, installationId: id, evidence: revoked ? .unknown : evidence, events: [], session: nil)
            if enabled && !revoked && evidence == .fresh { self.append("install_registered") }
        }
        if !enabled || revoked { self.clearConsentData() }
        self.prune()
        let saved = self.persist()
        if !markerSaved || (enabled && revoked && saved && !self.dependencies.saveRevocation(false)) {
            self.healthy = false
        }
    }

    func setEnabled(_ enabled: Bool) {
        guard self.initialized else { self.initialize(enabled: enabled, evidence: .unknown); return }
        guard self.enabled != enabled else { return }
        self.epoch &+= 1
        self.cancelWork()
        self.retryBatch = nil
        self.enabled = enabled
        let markerSaved = enabled || self.dependencies.saveRevocation(true)
        // Both consent transitions start with a clean queue. A persisted receipt
        // remains, so enabling analytics can never register another install.
        self.clearConsentData()
        self.foregroundStarted = nil
        guard self.persist() else { return }
        guard markerSaved && (!enabled || self.dependencies.saveRevocation(false)) else {
            self.healthy = false
            return
        }
        if enabled && self.foreground {
            self.ensureSession()
            self.startForegroundClock()
            _ = self.persist()
            self.scheduleDelivery()
        }
    }

    private func clearConsentData() {
        self.state?.events.removeAll()
        self.state?.session = nil
        self.state?.lastAttemptAt = nil
        self.state?.retryNotBefore = nil
        self.state?.retryAttempt = nil
        self.state?.retryExhausted = nil
        self.retryBatch = nil
    }

    func didBecomeActive() {
        let opened = self.lifecycle == .notStarted || self.lifecycle == .background
        self.lifecycle = .active
        guard self.initialized, self.enabled, self.healthy, self.state != nil else { return }
        if opened {
            self.ensureSession()
            self.append("app_opened")
            self.startForegroundClock()
            self.prune()
            guard self.persist() else { return }
            self.scheduleDelivery()
        }
    }

    func didResignActive() {
        if self.lifecycle == .active { self.lifecycle = .inactive }
        // Inactive (e.g. Control Center) is still foreground. It neither opens
        // the app again nor breaks foreground engagement into a new session.
    }

    func didEnterBackground() {
        guard self.lifecycle != .background else { return }
        _ = self.recordEngagementIfDue()
        self.accumulateForeground()
        self.backgroundStarted = self.dependencies.uptime()
        self.lifecycle = .background
        self.epoch &+= 1
        if self.enabled {
            self.state?.session?.lastBackgroundAt = self.dependencies.now().timeIntervalSince1970
            self.state?.session?.lastSeenAt = self.dependencies.now().timeIntervalSince1970
            _ = self.persist()
        }
        if let flight = self.flight { self.retryBatch = flight.batch }
        self.cancelWork()
    }

    private func ensureSession() {
        let now = self.dependencies.now().timeIntervalSince1970
        let previous = self.state?.session
        let end = previous?.lastBackgroundAt ?? previous?.lastSeenAt
        // Monotonic time wins within this process. Across an ungraceful process
        // death only the last persisted observation is available; the actual
        // termination time cannot be reconstructed without a background event.
        let pause = self.backgroundStarted.map { max(0, self.dependencies.uptime() - $0) }
            ?? end.map { now - $0 }
        self.backgroundStarted = nil
        if previous == nil || pause.map({ $0 >= 1800 }) == true {
            self.state?.session = Session(lastSeenAt: now, lastBackgroundAt: nil, foregroundSeconds: 0, engaged: false)
            self.append("session_started")
        } else {
            self.state?.session?.lastBackgroundAt = nil
            self.state?.session?.lastSeenAt = now
        }
    }

    private func startForegroundClock() {
        guard self.foregroundStarted == nil else { return }
        self.foregroundStarted = self.dependencies.uptime()
        self.scheduleEngagement()
    }

    private func foregroundSeconds() -> Double {
        let current = self.foregroundStarted.map { max(0, self.dependencies.uptime() - $0) } ?? 0
        return (self.state?.session?.foregroundSeconds ?? 0) + current
    }

    private func accumulateForeground() {
        guard let start = self.foregroundStarted else { return }
        self.state?.session?.foregroundSeconds += max(0, self.dependencies.uptime() - start)
        self.foregroundStarted = nil
    }

    private func scheduleEngagement() {
        self.engagedTimer?.cancel(); self.engagedTimer = nil
        guard self.enabled, self.healthy, self.foreground, self.state?.session?.engaged == false else { return }
        let epoch = self.epoch
        self.engagedTimer = self.dependencies.schedule(max(0, 10 - self.foregroundSeconds())) { [weak self] in
            guard let self, self.epoch == epoch, self.enabled, self.foreground, self.healthy else { return }
            self.engagedTimer = nil
            if self.recordEngagementIfDue() {
                if self.persist() { self.scheduleDelivery() }
            } else { self.scheduleEngagement() }
        }
    }

    @discardableResult private func recordEngagementIfDue() -> Bool {
        guard self.enabled, self.healthy, self.foreground, self.state?.session?.engaged == false,
              self.foregroundSeconds() >= 10 else { return false }
        self.state?.session?.engaged = true
        self.state?.session?.lastSeenAt = self.dependencies.now().timeIntervalSince1970
        self.append("session_engaged")
        return true
    }

    private func append(_ name: String) {
        guard self.enabled, self.metadata.valid else { return }
        let now = self.dependencies.now()
        guard now.timeIntervalSince1970.isFinite else { return }
        let id = self.dependencies.makeUUID().uuidString.lowercased()
        guard Self.isV4(id) else { self.healthy = false; return }
        self.state?.events.append(Event(eventId: id, eventName: name, occurredAt: self.formatter.string(from: now), timestamp: now.timeIntervalSince1970))
        self.prune()
    }

    private func prune() {
        guard var state = self.state else { return }
        let now = self.dependencies.now().timeIntervalSince1970
        state.events.removeAll {
            now - $0.timestamp > 7 * 86400 || $0.timestamp - now > 300
        }
        if state.events.count > 500 { state.events.removeFirst(state.events.count - 500) }
        self.state = state
    }

    @discardableResult private func persist() -> Bool {
        guard let state = self.state, let bytes = try? self.encoder.encode(state), self.dependencies.save(bytes) else {
            self.healthy = false
            self.cancelWork()
            return false
        }
        self.healthy = true
        return true
    }

    private func scheduleDelivery(delay: Double? = nil) {
        guard self.enabled, self.healthy, self.deliveryEnabled, self.foreground,
              self.flight == nil, self.flushTimer == nil, self.state?.events.isEmpty == false else { return }
        let now = self.dependencies.now().timeIntervalSince1970
        let lastAttempt = self.state?.lastAttemptAt ?? (now - 60)
        let retryNotBefore = self.state?.retryNotBefore ?? 0
        let retrying = self.retryBatch != nil || ((self.state?.retryAttempt ?? 0) > 0 && self.state?.retryExhausted != true)
        let oldestDue = (self.state?.events.first?.timestamp ?? now) + 60
        let requestedDue = delay.map { now + $0 } ?? (retrying ? retryNotBefore : oldestDue)
        // Queue age survives short foreground visits and process restarts.
        // Even overdue work is coalesced for two seconds, never sent by an open hook.
        let due = max(max(requestedDue, lastAttempt + (retrying ? 0 : 60)), retryNotBefore)
        let wait = max(2, due - now)
        let epoch = self.epoch
        self.flushTimer = self.dependencies.schedule(max(0, wait)) { [weak self] in
            guard let self, self.epoch == epoch else { return }
            self.flushTimer = nil
            self.sendBatch()
        }
    }

    private func makeBatch() -> Batch? {
        guard let state, self.metadata.valid else { return nil }
        var events = Array(state.events.prefix(20))
        while !events.isEmpty {
            let envelope = Envelope(installationId: state.installationId, appVersion: self.metadata.appVersion,
                build: self.metadata.build, osVersion: self.metadata.osVersion, osMajor: self.metadata.osMajor,
                deviceRegion: self.metadata.deviceRegion, deviceModel: self.metadata.deviceModel,
                events: events.map { WireEvent(eventId: $0.eventId, eventName: $0.eventName, occurredAt: $0.occurredAt) })
            if let body = try? self.encoder.encode(envelope), body.count <= 16 * 1024 {
                return Batch(body: body, ids: Set(events.map { $0.eventId }), attempt: min(4, max(0, state.retryAttempt ?? 0)))
            }
            events.removeLast()
        }
        return nil
    }

    private func sendBatch() {
        guard self.enabled, self.healthy, self.deliveryEnabled, self.foreground, self.flight == nil else { return }
        self.prune()
        if self.state?.retryExhausted == true {
            guard self.dependencies.now().timeIntervalSince1970 >= (self.state?.retryNotBefore ?? 0) else { return }
            self.state?.retryAttempt = 0
            self.state?.retryExhausted = false
        }
        // A retry may have expired, been evicted by the cap, or moved into the
        // future after a clock change. Rebuild rather than sending stale data.
        if let batch = self.retryBatch {
            let valid = Set(self.state?.events.map { $0.eventId } ?? [])
            if !batch.ids.isSubset(of: valid) { self.retryBatch = nil }
        }
        guard let batch = self.retryBatch ?? self.makeBatch() else { _ = self.persist(); return }
        self.state?.lastAttemptAt = self.dependencies.now().timeIntervalSince1970
        guard self.persist() else { return }
        self.token &+= 1
        let token = self.token, epoch = self.epoch
        self.flight = Flight(token: token, batch: batch)
        let cancellation = self.dependencies.send(batch.body) { [weak self] response in
            self?.complete(token: token, epoch: epoch, response: response)
        }
        if self.flight?.token == token {
            self.flight?.cancellation = cancellation
            self.timeoutTimer = self.dependencies.schedule(8) { [weak self] in
                self?.complete(token: token, epoch: epoch, response: Response(statusCode: nil))
            }
        } else { cancellation.cancel() }
    }

    private func complete(token: UInt64, epoch: UInt64, response: Response) {
        guard self.epoch == epoch, self.enabled, let flight = self.flight, flight.token == token else { return }
        self.timeoutTimer?.cancel(); self.timeoutTimer = nil
        flight.cancellation?.cancel(); self.flight = nil
        let status = response.statusCode
        if status.map({ (200..<300).contains($0) }) == true || status.map({ (400..<500).contains($0) && $0 != 408 && $0 != 429 }) == true {
            // Server counters (including newEvents) never determine delivery.
            self.state?.events.removeAll { flight.batch.ids.contains($0.eventId) }
            self.retryBatch = nil
            self.state?.retryNotBefore = nil
            self.state?.retryAttempt = nil
            self.state?.retryExhausted = nil
            if self.persist() { self.scheduleDelivery() }
        } else if flight.batch.attempt < 4 {
            var batch = flight.batch; batch.attempt += 1; self.retryBatch = batch
            let random = max(0, min(1, self.dependencies.randomUnit()))
            let backoff = Double(5 << flight.batch.attempt) * (1 + 0.25 * random)
            let retryAfter = response.retryAfter.flatMap { $0.isFinite && $0 >= 0 ? min(3600, $0) : nil } ?? 0
            let delay = max(backoff, retryAfter)
            self.state?.retryNotBefore = self.dependencies.now().timeIntervalSince1970 + delay
            self.state?.retryAttempt = batch.attempt
            self.state?.retryExhausted = false
            if self.persist() { self.scheduleDelivery(delay: delay) }
        } else {
            self.retryBatch = nil
            self.state?.retryNotBefore = self.dependencies.now().timeIntervalSince1970 + 3600
            self.state?.retryAttempt = 4
            self.state?.retryExhausted = true
            _ = self.persist()
            // Retry budget exhausted. A later real foreground transition may
            // schedule another bounded attempt; there is no permanent poller.
        }
    }

    private func cancelWork() {
        self.flushTimer?.cancel(); self.flushTimer = nil
        self.engagedTimer?.cancel(); self.engagedTimer = nil
        self.timeoutTimer?.cancel(); self.timeoutTimer = nil
        self.flight?.cancellation?.cancel(); self.flight = nil
    }

    private static func isV4(_ value: String) -> Bool {
        let bytes = Array(value.lowercased().utf8)
        return UUID(uuidString: value) != nil && bytes.count == 36 && bytes[14] == 52 && [56, 57, 97, 98].contains(bytes[19])
    }
}

// One bounded blob, atomically replaced off the UI queue. Failed writes are
// reported to the core so unpersisted event IDs are never transmitted.
final class JerkgramAnalyticsV3FileStorage {
    private let directory: URL
    private let legacyDefaults: UserDefaults?
    private var file: URL { self.directory.appendingPathComponent("v3-state.json") }
    init(directory: URL, legacyDefaults: UserDefaults? = nil) {
        self.directory = directory; self.legacyDefaults = legacyDefaults
    }
    static func isMissingFile(_ error: NSError) -> Bool {
        // Foundation uses both Cocoa missing-file codes and direct ENOENT.
        // A conflicting underlying error must never mint a replacement receipt.
        let missing: (NSError) -> Bool = { value in
            (value.domain == NSPOSIXErrorDomain && value.code == 2)
                || (value.domain == NSCocoaErrorDomain
                    && (value.code == CocoaError.fileNoSuchFile.rawValue
                        || value.code == CocoaError.fileReadNoSuchFile.rawValue))
        }
        guard missing(error) else { return false }
        if let underlying = error.userInfo[NSUnderlyingErrorKey] as? NSError {
            guard missing(underlying), underlying.userInfo[NSUnderlyingErrorKey] == nil else { return false }
        }
        return true
    }
    func load() -> JerkgramAnalyticsV3Core.LoadResult {
        var isDirectory = ObjCBool(false)
        if FileManager.default.fileExists(atPath: self.directory.path, isDirectory: &isDirectory), !isDirectory.boolValue {
            return .unreadable
        }
        do {
            let handle = try FileHandle(forReadingFrom: self.file)
            defer { try? handle.close() }
            let bytes = try handle.read(upToCount: 256 * 1024 + 1) ?? Data()
            guard bytes.count <= 256 * 1024 else { return .unreadable }
            return .data(bytes)
        } catch {
            let error = error as NSError
            guard Self.isMissingFile(error) else {
                return .unreadable
            }
            if let legacy = self.legacyDefaults?.data(forKey: "jerkgram.analytics.v3.state") {
                return legacy.count <= 256 * 1024 ? .data(legacy) : .unreadable
            }
            return .absent
        }
    }
    func save(_ data: Data) -> Bool {
        do {
            #if os(iOS)
            try FileManager.default.createDirectory(at: self.directory, withIntermediateDirectories: true,
                attributes: [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication])
            try FileManager.default.setAttributes([.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication], ofItemAtPath: self.directory.path)
            #else
            try FileManager.default.createDirectory(at: self.directory, withIntermediateDirectories: true)
            #endif
            var excluded = URLResourceValues(); excluded.isExcludedFromBackup = true
            var directory = self.directory
            try? directory.setResourceValues(excluded)
            try data.write(to: self.file, options: .atomic)
            var file = self.file
            try? file.setResourceValues(excluded)
            #if os(iOS)
            try FileManager.default.setAttributes([.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication], ofItemAtPath: self.file.path)
            #endif
            // Only a previous v3-development blob is migrated. v1 is untouched.
            self.legacyDefaults?.removeObject(forKey: "jerkgram.analytics.v3.state")
            return true
        } catch { return false }
    }
}

// The application bridge provides actual Jerkgram release/device metadata.
// Production delivery requires an explicit reviewed source change after the
// server is deployed. Mock tests inject their own transport into the core.
final class JerkgramAnalyticsV3 {
    typealias Metadata = JerkgramAnalyticsV3Core.Metadata
    typealias InstallationEvidence = JerkgramAnalyticsV3Core.InstallationEvidence
    static let productionTransportEnabled = false
    static let shared = JerkgramAnalyticsV3()
    private let queue = DispatchQueue(label: "org.jerkgram.analytics.v3", qos: .utility)
    private let gate = JerkgramAnalyticsV3TransportGate()
    private var core: JerkgramAnalyticsV3Core?
    private init() {}

    func configure(metadata: Metadata) {
        self.queue.async {
            guard self.core == nil else { return }
            let queue = self.queue, gate = self.gate
            let directory = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first?
                .appendingPathComponent("Jerkgram/Analytics", isDirectory: true)
            let storage = directory.map { JerkgramAnalyticsV3FileStorage(directory: $0, legacyDefaults: .standard) }
            let dependencies = JerkgramAnalyticsV3Core.Dependencies(
                now: Date.init, uptime: { ProcessInfo.processInfo.systemUptime },
                makeUUID: Self.randomUUID, randomUnit: { Double.random(in: 0...1) },
                load: { storage?.load() ?? .unreadable },
                save: { data in storage?.save(data) ?? false },
                loadRevocation: { UserDefaults.standard.bool(forKey: "jerkgram.analytics.v3.revoked") },
                saveRevocation: { revoked in
                    let defaults = UserDefaults.standard
                    defaults.set(revoked, forKey: "jerkgram.analytics.v3.revoked")
                    // Rare consent transition; flush on this utility queue.
                    // Foundation cannot promise durability after total OS/storage failure.
                    let saved = defaults.synchronize() && defaults.bool(forKey: "jerkgram.analytics.v3.revoked") == revoked
                    if !saved && !revoked {
                        defaults.set(true, forKey: "jerkgram.analytics.v3.revoked")
                        _ = defaults.synchronize()
                    }
                    return saved
                },
                schedule: { delay, action in
                    let item = DispatchWorkItem(block: action)
                    queue.asyncAfter(deadline: .now() + delay, execute: item)
                    return JerkgramAnalyticsV3Cancellation { item.cancel() }
                }, send: { data, completion in
                    gate.send(data: data) { response in queue.async { completion(response) } }
                })
            self.core = JerkgramAnalyticsV3Core(metadata: metadata, dependencies: dependencies,
                deliveryEnabled: Self.productionTransportEnabled)
        }
    }
    func initialize(enabled: Bool, evidence: InstallationEvidence) {
        let consent = self.gate.beginConsentChange()
        if !enabled { UserDefaults.standard.set(true, forKey: "jerkgram.analytics.v3.revoked") }
        self.queue.async {
            self.core?.initialize(enabled: enabled, evidence: evidence)
            self.gate.finishConsentChange(enabled: enabled, generation: consent)
        }
    }
    func setEnabled(_ enabled: Bool) {
        // Gate and task cancellation are immediate, before the queued clear.
        let consent = self.gate.beginConsentChange()
        // This scalar joins the same app-defaults transaction as the existing
        // setting. The potentially blocking flush stays on the utility queue.
        if !enabled { UserDefaults.standard.set(true, forKey: "jerkgram.analytics.v3.revoked") }
        self.queue.async {
            self.core?.setEnabled(enabled)
            self.gate.finishConsentChange(enabled: enabled, generation: consent)
        }
    }
    func didBecomeActive() { self.queue.async { self.core?.didBecomeActive() } }
    func didResignActive() { self.queue.async { self.core?.didResignActive() } }
    func didEnterBackground() { self.queue.async { self.core?.didEnterBackground() } }

    private static func randomUUID() -> UUID {
        var random = SystemRandomNumberGenerator()
        var bytes = (0..<16).map { _ in UInt8.random(in: .min ... .max, using: &random) }
        bytes[6] = (bytes[6] & 0x0f) | 0x40; bytes[8] = (bytes[8] & 0x3f) | 0x80
        return UUID(uuid: (bytes[0], bytes[1], bytes[2], bytes[3], bytes[4], bytes[5], bytes[6], bytes[7],
            bytes[8], bytes[9], bytes[10], bytes[11], bytes[12], bytes[13], bytes[14], bytes[15]))
    }
}

private final class JerkgramAnalyticsV3TransportGate {
    private let lock = NSLock()
    private var enabled = false
    private var task: URLSessionDataTask?
    private lazy var session: URLSession = {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.httpCookieStorage = nil
        configuration.httpShouldSetCookies = false
        configuration.urlCache = nil
        configuration.requestCachePolicy = .reloadIgnoringLocalCacheData
        configuration.timeoutIntervalForRequest = 8
        configuration.timeoutIntervalForResource = 8
        return URLSession(configuration: configuration)
    }()
    private var generation: UInt64 = 0
    func beginConsentChange() -> UInt64 {
        self.lock.lock(); defer { self.lock.unlock() }
        self.generation &+= 1
        self.enabled = false
        self.task?.cancel(); self.task = nil
        return self.generation
    }
    func finishConsentChange(enabled: Bool, generation: UInt64) {
        self.lock.lock(); defer { self.lock.unlock() }
        if self.generation == generation { self.enabled = enabled }
    }
    func send(data: Data, completion: @escaping (JerkgramAnalyticsV3Core.Response) -> Void) -> JerkgramAnalyticsV3Cancellation {
        self.lock.lock(); defer { self.lock.unlock() }
        guard self.enabled, JerkgramAnalyticsV3.productionTransportEnabled else {
            return JerkgramAnalyticsV3Cancellation {}
        }
        var request = URLRequest(url: URL(string: "https://jerkgram-telemetry.cronusk1809.workers.dev/v3/events")!)
        request.httpMethod = "POST"; request.httpBody = data; request.timeoutInterval = 8
        request.httpShouldHandleCookies = false
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let task = self.session.dataTask(with: request) { _, response, _ in
            let http = response as? HTTPURLResponse
            let retry = http?.value(forHTTPHeaderField: "Retry-After").flatMap(Double.init)
            completion(.init(statusCode: http?.statusCode, retryAfter: retry))
        }
        self.task = task; task.resume()
        return JerkgramAnalyticsV3Cancellation { task.cancel() }
    }
}
