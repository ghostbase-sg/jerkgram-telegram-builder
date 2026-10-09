#!/usr/bin/env python3
"""Execute actual Foundation owners; network stub never contacts production.

These are component tests, NOT device/UI runtime validation or benchmarks.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work/swiftgram-src"


def owner(path):
    return (SOURCE / path).read_text()


def block(text, needle):
    assert text.count(needle) == 1, needle
    start = text.index(needle)
    brace = text.index("{", start)
    end, depth = brace + 1, 1
    while depth:
        if text[end] == "{":
            depth += 1
        elif text[end] == "}":
            depth -= 1
        end += 1
    return text[start:end] + "\n"


def run(name, text, args=()):
    with tempfile.TemporaryDirectory(prefix="jg13-" + name + "-") as tmp:
        p = Path(tmp) / "main.swift"
        p.write_text(text)
        subprocess.run(["xcrun", "swift", str(p), *args], check=True)


models = owner("submodules/JerkgramCore/Sources/JerkgramModels.swift")
controller = owner("submodules/TelegramUI/Components/Chat/ChatSearchNavigationContentNode/Sources/JerkgramTimeMachineController.swift")
cases = controller.split("private enum JerkgramTimeMachineUIEntry: ItemListNodeEntry {", 1)[1].split("    var section:", 1)[0]
equality = block(controller, "    static func == (lhs: Self, rhs: Self)")
date_text = block(controller, "private func jerkgramTimeMachineDateText(")
formatter = controller.split("        let dateFormatter = DateFormatter()", 1)[1].split("        for (index, event)", 1)[0]

run("entries", models + "\nenum JerkgramTimeMachineUIEntry: Equatable {" + cases + equality + "\n}\n" + date_text + r'''
func event(_ payload: JerkgramEventPayload = JerkgramEventPayload(text: "same")) -> JerkgramCanonicalEvent {
    return JerkgramCanonicalEvent(accountPeerId: 1, chatPeerId: 10, eventId: JerkgramEventId(rawValue: "a"), sequence: 5, kind: .editedMessage, senderPeerId: 2, messageNamespace: 0, messageId: 1, observedAtMs: 1700000000000, payload: payload)
}
let values: [JerkgramTimeMachineUIEntry] = [.header(1, "a"), .summary(1, 1, "a", "b"), .filter(1, 2, "a", "✓", .editedMessage), .result(1, 3, "a", "b", event()), .info(3, "a"), .loadMore(3, "a")]
for i in values.indices {
    for j in values.indices { precondition((values[i] == values[j]) == (i == j)) }
}
precondition(JerkgramTimeMachineUIEntry.header(1, "a") != .header(2, "a"))
precondition(JerkgramTimeMachineUIEntry.summary(1, 1, "a", "b") != .summary(1, 2, "a", "b"))
precondition(JerkgramTimeMachineUIEntry.filter(1, 1, "a", "✓", .editedMessage) != .filter(1, 1, "a", "✓", .deletedMessage))
precondition(JerkgramTimeMachineUIEntry.result(1, 1, "same", "same", event()) != .result(1, 1, "same", "same", event(JerkgramEventPayload(text: "same", metadata: ["media": "changed"]))))
precondition(JerkgramTimeMachineUIEntry.info(1, "a") != .info(1, "b"))
precondition(JerkgramTimeMachineUIEntry.loadMore(1, "a") != .loadMore(1, "b"))
let dateFormatter = DateFormatter()
''' + formatter + r'''
let reference = DateFormatter()
reference.locale = Locale.current
reference.dateStyle = .medium
reference.timeStyle = .short
precondition(dateFormatter.timeZone == reference.timeZone)
for ms in [Int64(0), -1, 1700000000000, 1735689600000] {
    let expected = ms > 0 ? reference.string(from: Date(timeIntervalSince1970: Double(ms) / 1000.0)) : ""
    precondition(jerkgramTimeMachineDateText(ms, formatter: dateFormatter) == expected)
}
print("PASS: actual typed entries/payload equality and unchanged date formatting")
''')

store = owner("submodules/JerkgramCore/Sources/JerkgramStore.swift").split("public enum JerkgramCaptureRecorder {", 1)[0]
run("store", models + owner("submodules/JerkgramCore/Sources/JerkgramIndex.swift") + store + r'''
let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
defer { try? FileManager.default.removeItem(at: root) }
let store = JerkgramJSONLEventStore(rootURL: root)
func make(_ account: Int64, _ chat: Int64, _ id: String, _ sequence: Int64) -> JerkgramCanonicalEvent {
    return JerkgramCanonicalEvent(accountPeerId: account, chatPeerId: chat, eventId: JerkgramEventId(rawValue: id), sequence: sequence, kind: .deletedMessage, senderPeerId: nil, messageNamespace: 0, messageId: Int32(sequence), observedAtMs: 1700000000000, payload: JerkgramEventPayload(text: id))
}
try store.appendBatch([make(1, 10, "b", 2), make(1, 20, "other", 3), make(1, 10, "a", 2), make(1, 10, "c", 5), make(2, 10, "foreign", 4)])
func ids(_ records: [JerkgramTimeMachineIndexRecord]) -> [String] { records.map { $0.eventId.rawValue } }
func check(_ condition: Bool) { precondition(condition) }
check(try ids(store.indexRecords(accountPeerId: 1, chatPeerId: 10)) == ["a", "b", "c"])
check(try ids(store.readyIndexRecords(accountPeerId: 1, chatPeerId: 10, afterSequence: 2, throughSequence: 5)) == ["c"])
check(try ids(store.indexRecords(accountPeerId: 1, chatPeerId: 10, throughSequence: 2)) == ["a", "b"])
check(try store.indexRecords(accountPeerId: 1, chatPeerId: 99).isEmpty)
check(try ids(store.indexRecords(accountPeerId: 2, chatPeerId: 10)) == ["foreign"])
check(try store.eventPage(accountPeerId: 1, chatPeerId: 10, limit: 2).map { $0.eventId.rawValue } == ["c", "b"])
check(try store.eventPage(accountPeerId: 1, chatPeerId: 10, beforeSequence: 2, beforeEventId: JerkgramEventId(rawValue: "b"), limit: 2).map { $0.eventId.rawValue } == ["a"])
try store.append(make(1, 10, "late", 1))
check(try ids(store.readyIndexRecords(accountPeerId: 1, chatPeerId: 10)) == ["late", "a", "b", "c"])
let reopened = JerkgramJSONLEventStore(rootURL: root)
check(try ids(reopened.indexRecords(accountPeerId: 1, chatPeerId: 10)) == ["late", "a", "b", "c"])
print("PASS: actual JSONL store/chat partitions, account isolation, strict bounds, ties, paging, late append")
''')

avatar = owner("submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift")
cache_store = block(avatar, "    private static func ghostBaseStoreAvatarDiskCache(")
cache_match = block(avatar, "    private static func ghostBaseTouchMatchingAvatarDiskCache(")
# UIKit is unavailable to the macOS command-line fixture. This explicit image facade
# tests the ACTUAL cache filesystem/locking code, not UIKit's JPEG decoder/rendering.
run("avatar-cache", r'''import Foundation
struct FixtureCGImage { let width: Int; let height: Int }
final class UIImage {
    let cgImage: FixtureCGImage?
    static let lock = NSLock()
    static var encodings = 0
    init(_ width: Int, _ height: Int) { cgImage = FixtureCGImage(width: width, height: height) }
    init?(contentsOfFile path: String) {
        guard let text = try? String(contentsOfFile: path, encoding: .utf8) else { return nil }
        let parts = text.split(separator: ",").compactMap { Int($0) }
        guard parts.count == 2, parts.allSatisfy({ $0 > 0 }) else { return nil }
        cgImage = FixtureCGImage(width: parts[0], height: parts[1])
    }
    func jpegData(compressionQuality: Double) -> Data? {
        precondition(compressionQuality == 0.88)
        Self.lock.lock(); Self.encodings += 1; Self.lock.unlock()
        guard let image = cgImage else { return nil }
        return Data("\(image.width),\(image.height)".utf8)
    }
}
enum Cache {
    static let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    static let ghostBaseAvatarDiskCacheLock = NSLock()
    static let ghostBaseAvatarDiskCacheLimit = 48
    static func ghostBaseAvatarDiskCacheRoot() -> URL? { root }
    static func ghostBaseAvatarDiskCacheURL(identity: String) -> URL? { root.appendingPathComponent(identity + ".jpg") }
    static func store(_ image: UIImage, _ identity: String) { ghostBaseStoreAvatarDiskCache(image, identity: identity) }
''' + cache_store + cache_match + r'''
}
defer { try? FileManager.default.removeItem(at: Cache.root) }
let image = UIImage(360, 360)
Cache.store(image, "same")
precondition(UIImage.encodings == 1)
let same = Cache.root.appendingPathComponent("same.jpg")
try FileManager.default.setAttributes([.modificationDate: Date(timeIntervalSince1970: 1)], ofItemAtPath: same.path)
Cache.store(image, "same")
precondition(UIImage.encodings == 1)
let touchedDate = try same.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate!
precondition(touchedDate > Date(timeIntervalSince1970: 1))
try Data("corrupt".utf8).write(to: same)
Cache.store(image, "same")
precondition(UIImage.encodings == 2 && UIImage(contentsOfFile: same.path)?.cgImage?.width == 360)
Cache.store(UIImage(180, 180), "same")
precondition(UIImage.encodings == 3 && UIImage(contentsOfFile: same.path)?.cgImage?.width == 180)
try FileManager.default.removeItem(at: same)
Cache.store(image, "same")
precondition(UIImage.encodings == 4)
DispatchQueue.concurrentPerform(iterations: 50) { _ in Cache.store(image, "same") }
precondition(UIImage.encodings == 4)
for i in 0..<47 {
    Cache.store(image, "old-\(i)")
    try FileManager.default.setAttributes([.modificationDate: Date(timeIntervalSince1970: Double(i + 100))], ofItemAtPath: Cache.root.appendingPathComponent("old-\(i).jpg").path)
}
Cache.store(image, "same")
Cache.store(image, "new-1")
Cache.store(image, "new-2")
let files = try FileManager.default.contentsOfDirectory(atPath: Cache.root.path)
precondition(files.count == 48 && files.contains("same.jpg"))
precondition(!files.contains("old-0.jpg") && !files.contains("old-1.jpg"))
print("PASS: actual avatar cache filesystem policy; matching/invalid/missing/different-size/concurrent/LRU48 (image facade, NOT UIKit runtime)")
''')

app = owner("submodules/TelegramUI/Sources/AppDelegate.swift")
preferences = block(app, "private extension Notification.Name {") + block(app, "private enum JerkgramTelemetryPreferences {")
sender = block(app, "private final class JerkgramTelemetry {")
telemetry_fixture = r'''import Foundation
import Darwin
struct UIDevice { static let current = UIDevice(); let systemVersion = "26.0" }
enum JerkgramReleaseIdentity { static let technicalVersion = "1.1.0-beta.1"; static let build = "143" }
final class Logger {
    static let shared = Logger()
    private let lock = NSLock()
    private var lines: [String] = []
    func log(_ tag: String, _ line: String) { lock.lock(); lines.append(line); lock.unlock() }
    func contains(_ value: String) -> Bool { lock.lock(); defer { lock.unlock() }; return lines.contains { $0.contains(value) } }
}
final class StubProtocol: URLProtocol {
    static let lock = NSLock()
    static var requests: [URLRequest] = []
    static var status = 204
    override class func canInit(with request: URLRequest) -> Bool { return true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { return request }
    override func startLoading() {
        precondition(request.url?.absoluteString == "https://jerkgram-telemetry.cronusk1809.workers.dev/v1/activity")
        var captured = request
        if captured.httpBody == nil, let stream = request.httpBodyStream {
            stream.open(); defer { stream.close() }
            var bytes = [UInt8](repeating: 0, count: 4096), data = Data()
            while stream.hasBytesAvailable { let count = stream.read(&bytes, maxLength: bytes.count); if count <= 0 { break }; data.append(contentsOf: bytes.prefix(count)) }
            captured.httpBody = data
        }
        Self.lock.lock(); Self.requests.append(captured); Self.lock.unlock()
        if Self.status == -1009 {
            client?.urlProtocol(self, didFailWithError: NSError(domain: NSURLErrorDomain, code: -1009)); return
        }
        client?.urlProtocol(self, didReceive: HTTPURLResponse(url: request.url!, statusCode: Self.status, httpVersion: "HTTP/1.1", headerFields: nil)!, cacheStoragePolicy: .notAllowed)
        client?.urlProtocolDidFinishLoading(self)
    }
    override func stopLoading() {}
    static func snapshot() -> [URLRequest] { lock.lock(); defer { lock.unlock() }; return requests }
}
func wait(_ condition: () -> Bool) {
    let deadline = Date().addingTimeInterval(5)
    while !condition() { precondition(Date() < deadline, "async fixture timeout"); Thread.sleep(forTimeInterval: 0.01) }
}
'''
telemetry_cases = r'''
let defaults = UserDefaults.standard
for key in defaults.dictionaryRepresentation().keys where key.hasPrefix("jerkgram.telemetry.") { defaults.removeObject(forKey: key) }
StubProtocol.status = Int(CommandLine.arguments[1])!
precondition(URLProtocol.registerClass(StubProtocol.self))
JerkgramTelemetry.shared.applicationDidBecomeActive()
wait { !StubProtocol.snapshot().isEmpty }
let request = StubProtocol.snapshot()[0]
precondition(request.httpMethod == "POST" && request.timeoutInterval == 8)
precondition(request.value(forHTTPHeaderField: "Content-Type") == "application/json")
let payload = try JSONSerialization.jsonObject(with: request.httpBody!) as! [String: Any]
precondition(payload["schema"] as? Int == 1)
precondition(payload["appVersion"] as? String == "1.1.0-beta.1")
precondition(payload["build"] as? String == "143")
precondition(payload["event"] as? String == "app_active")
precondition(payload["openCountToday"] as? Int == 1)
precondition(payload["installReceiptId"] as? String != nil)
if StubProtocol.status == 204 {
    wait { defaults.object(forKey: "jerkgram.telemetry.lastSuccess.v1") != nil }
    precondition(defaults.bool(forKey: "jerkgram.telemetry.installReported.v1"))
    precondition(defaults.string(forKey: "jerkgram.telemetry.installReceipt.v1") == nil)
} else {
    wait { Logger.shared.contains(StubProtocol.status == -1009 ? "transport failure code=-1009" : "activity HTTP status=422") }
    precondition(defaults.object(forKey: "jerkgram.telemetry.lastSuccess.v1") == nil)
    precondition(!defaults.bool(forKey: "jerkgram.telemetry.installReported.v1"))
}
JerkgramTelemetry.shared.applicationDidBecomeActive()
JerkgramTelemetry.shared.applicationDidEnterBackground()
JerkgramTelemetry.shared.applicationDidBecomeActive()
wait { defaults.integer(forKey: "jerkgram.telemetry.opens.count") == 2 }
Thread.sleep(forTimeInterval: 0.1)
precondition(StubProtocol.snapshot().count == 1, "4h throttle must remain unchanged")
JerkgramTelemetryPreferences.isEnabled = false
JerkgramTelemetry.shared.applicationDidEnterBackground()
JerkgramTelemetry.shared.applicationDidBecomeActive()
Thread.sleep(forTimeInterval: 0.1)
precondition(defaults.integer(forKey: "jerkgram.telemetry.opens.count") == 2)
precondition(StubProtocol.snapshot().count == 1)
print("PASS: actual telemetry sender, stub status \(StubProtocol.status), payload/version/lifecycle/opt-out/throttle")
'''
for status in (204, 422, -1009):
    run("telemetry", telemetry_fixture + preferences + sender + telemetry_cases, [str(status)])
