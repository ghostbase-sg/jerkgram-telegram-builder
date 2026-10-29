// Runs the extracted production policy/admission against pinned SwiftSignalKit,
// with only the unrelated Telegram entity value represented by a minimal shape.
struct MessageTextEntity: Encodable {
    enum Kind: Encodable { case Url, Mention, TextUrl(url: String) }
    let range: Range<Int>; let type: Kind
    init(range: Range<Int>, type: Kind = .Url) { self.range = range; self.type = type }
}
public enum TranslationError { case generic, limitExceeded }
func require(_ value: @autoclosure () -> Bool, _ message: String) { if !value() { fatalError(message) } }
func eventually(_ predicate: () -> Bool) {
    let deadline = Date().addingTimeInterval(3)
    while !predicate() && Date() < deadline { Thread.sleep(forTimeInterval: 0.005) }
    require(predicate(), "asynchronous assertion timed out")
}
let counter = Atomic(value: [String: Int]())
func increment(_ key: String) { _ = counter.modify { value in var value = value; value[key, default: 0] += 1; return value } }
func count(_ key: String) -> Int { counter.with { $0[key, default: 0] } }
private func held(_ name: String) -> Signal<JerkgramTranslatedTexts, TranslationError> {
    Signal { _ in increment(name); return ActionDisposable { increment(name + " disposed") } }
}
let a: Int64 = 42
require(JerkgramTranslationSettings.enabled(accountPeerId: a), "default on")
let initial = JerkgramTranslationSettings.generation(accountPeerId: a)
JerkgramTranslationSettings.update(accountPeerId: a, enabled: false)
require(!JerkgramTranslationSettings.enabled(accountPeerId: a), "off")
require(JerkgramTranslationSettings.enabled(accountPeerId: 43), "account isolation")
require(JerkgramTranslationSettings.generation(accountPeerId: a) != initial, "off invalidates generation")
let off = JerkgramTranslationSettings.generation(accountPeerId: a)
JerkgramTranslationSettings.update(accountPeerId: a, enabled: false)
require(JerkgramTranslationSettings.generation(accountPeerId: a) == off, "idempotent update")
require(JerkgramTranslationSettings.scopedKey(accountPeerId: a) == "jerkgram.account.42.setting.jerkgram.EnhancedTranslation", "canonical key")

// The method body below is extracted verbatim from TranslationMessageAttribute.
private let message = Message("source-v2:fixture")
private let valid = TranslationValidityFixture(message.fingerprint, 2)
JerkgramTranslationSettings.update(accountPeerId: a, enabled: true)
require(valid.isValidForMessage(message, accountPeerId: a), "current fingerprint")
JerkgramTranslationSettings.update(accountPeerId: a, enabled: false)
require(!valid.isValidForMessage(message, accountPeerId: a), "OFF must invalidate cached immutable-message validity")
require(!valid.isValidForMessage(message), "tagged result fails without account")
require(!TranslationValidityFixture("apple-v1:fixture", 0).isValidForMessage(message, accountPeerId: 43), "legacy provenance rejected")
require(TranslationValidityFixture(nil, 0).isValidForMessage(message), "stock untagged attr retained")
let persistedAccount: Int64 = -990042
let persistedKey = JerkgramTranslationSettings.scopedKey(accountPeerId: persistedAccount)
UserDefaults.standard.set(false, forKey: persistedKey)
require(!JerkgramTranslationSettings.enabled(accountPeerId: persistedAccount), "canonical OFF read")
for id in 1000...1020 { _ = JerkgramTranslationSettings.enabled(accountPeerId: Int64(id)) }
require(!JerkgramTranslationSettings.enabled(accountPeerId: persistedAccount), "evicted OFF must reload canonical preference")
UserDefaults.standard.removeObject(forKey: persistedKey)
require(!jerkgramValidTranslatedEntities("😀x", [MessageTextEntity(range: 1..<2)]), "reject split surrogate")
require(jerkgramValidTranslatedEntities("😀x", [MessageTextEntity(range: 0..<2)]), "accept valid UTF16 boundaries")
require(jerkgramLocalTranslatedEntities(source: ("name", [MessageTextEntity(range: 0..<4, type: .TextUrl(url: "https://example.com"))]), translated: "hello name")?.last?.range == 6..<10, "hidden link uses translated offsets")
require(jerkgramLocalTranslatedEntities(source: ("name", [MessageTextEntity(range: 0..<4, type: .TextUrl(url: "https://example.com"))]), translated: "name name") == nil, "ambiguous hidden link fails")
JerkgramTranslationSettings.update(accountPeerId: a, enabled: false)

private final class LifetimeProbe {}
private final class WeakProbe { weak var value: LifetimeProbe? }
private func lifetimeRequest(_ admission: JerkgramTranslationAdmission, key: String, success: Bool, error: @escaping () -> Void = {}) -> (Disposable, WeakProbe) {
    let probe = LifetimeProbe()
    let weak = WeakProbe(); weak.value = probe
    let disposable = admission.request(key: key, count: 1, bytes: 1, start: { [probe] in
        withExtendedLifetime(probe) {
            if success { return Signal<JerkgramTranslatedTexts, TranslationError>.single([("done", [])]) }
            return Signal<JerkgramTranslatedTexts, TranslationError> { _ in
                increment(key)
                return ActionDisposable { withExtendedLifetime(probe) { increment(key + " disposed") } }
            }
        }
    }).start(error: { _ in error() })
    return (disposable, weak)
}

private let admission = JerkgramTranslationAdmission()
private let successLifetime = lifetimeRequest(admission, key: "lifetime-success", success: true)
eventually { successLifetime.1.value == nil }
successLifetime.0.dispose()
private let cancelledLifetime = lifetimeRequest(admission, key: "lifetime-cancel", success: false)
eventually { count("lifetime-cancel") == 1 }
cancelledLifetime.0.dispose()
eventually { cancelledLifetime.1.value == nil }
require(count("lifetime-cancel disposed") == 1, "cancel lifetime transport once")

let hugeURL = "https://example.com/" + String(repeating: "x", count: 17000)
private let giantInput: JerkgramTranslatedTexts = [("name", [MessageTextEntity(range: 0..<4, type: .TextUrl(url: hugeURL))])]
require((jerkgramTranslationPayloadBytes(giantInput) ?? 0) > 16 * 1024, "short label must not hide 16 KiB entity input")
let giantInputRejected = DispatchSemaphore(value: 0)
let giantInputRequest = admission.request(key: "giant-input", count: giantInput.count, bytes: jerkgramTranslationPayloadBytes(giantInput)!, start: { held("giant-input") }).start(error: { _ in giantInputRejected.signal() })
require(giantInputRejected.wait(timeout: .now() + 3) == .success && count("giant-input") == 0, "full encoded TextUrl budget rejects before transport")
giantInputRequest.dispose()
private let giantOutput: JerkgramTranslatedTexts = [("name", [MessageTextEntity(range: 0..<4, type: .TextUrl(url: String(repeating: "x", count: 1024 * 1024 + 1)))])]
require((jerkgramTranslationPayloadBytes(giantOutput) ?? 0) > 1024 * 1024, "cache accounts full hidden URL")
for attempt in 0..<2 {
    let done = DispatchSemaphore(value: 0)
    let d = admission.request(key: "giant-cache", count: 1, bytes: 1, start: {
        increment("giant-cache starts"); return .single(giantOutput)
    }).start(completed: { done.signal() })
    require(done.wait(timeout: .now() + 3) == .success, "giant output delivered")
    d.dispose()
    require(count("giant-cache starts") == attempt + 1, "oversized entity result must not enter cache")
}

let one = admission.request(key: "dedup", count: 1, bytes: 1, start: { held("dedup") }).start()
let two = admission.request(key: "dedup", count: 1, bytes: 1, start: { held("dedup") }).start()
eventually { count("dedup") == 1 }
one.dispose(); Thread.sleep(forTimeInterval: 0.03)
require(count("dedup disposed") == 0, "one dedup subscriber must preserve physical request")
two.dispose(); eventually { count("dedup disposed") == 1 }
two.dispose(); require(count("dedup disposed") == 1, "dispose exactly once")

var handles: [Disposable] = []
for i in 0..<4 { handles.append(admission.request(key: "saturation\(i)", count: 16, bytes: 16384, start: { held("saturation\(i)") }).start()) }
let rejected = DispatchSemaphore(value: 0)
let overflow = admission.request(key: "overflow", count: 1, bytes: 1, start: { held("overflow") }).start(error: { _ in rejected.signal() })
require(rejected.wait(timeout: .now() + 3) == .success, "64-item admission bound")
require(count("saturation0") + count("saturation1") + count("saturation2") + count("saturation3") == 2, "two physical requests")
handles[2].dispose(); handles[3].dispose(); handles[0].dispose(); handles[1].dispose()
eventually { count("saturation0 disposed") == 1 && count("saturation1 disposed") == 1 }
require(count("saturation2") == 0 && count("saturation3") == 0 && count("overflow") == 0, "queued cancellations must never start")
overflow.dispose()

var byteHandles: [Disposable] = []
for i in 0..<8 { byteHandles.append(admission.request(key: "bytes\(i)", count: 1, bytes: 16384, start: { held("bytes\(i)") }).start()) }
let byteRejected = DispatchSemaphore(value: 0)
let byteOverflow = admission.request(key: "byte-overflow", count: 1, bytes: 1, start: { held("byte-overflow") }).start(error: { _ in byteRejected.signal() })
require(byteRejected.wait(timeout: .now() + 3) == .success, "128 KiB input bound")
for i in (2..<8).reversed() { byteHandles[i].dispose() }
byteHandles[0].dispose(); byteHandles[1].dispose(); byteOverflow.dispose()
eventually { count("bytes0 disposed") == 1 && count("bytes1 disposed") == 1 }
require(count("bytes2") == 0 && count("byte-overflow") == 0, "byte-bound cancellation")
let oversized = DispatchSemaphore(value: 0)
let hugeJob = admission.request(key: "huge", count: 1, bytes: 16385, start: { held("huge") }).start(error: { _ in oversized.signal() })
require(oversized.wait(timeout: .now() + 3) == .success && count("huge") == 0, "16 KiB job bound")
hugeJob.dispose()

func cachedRequest(_ key: String) {
    let done = DispatchSemaphore(value: 0)
    let d = admission.request(key: key, count: 1, bytes: 1, start: {
        increment("cache starts \(key)"); return .single([("translated", [])])
    }).start(next: { value in require(value.first?.0 == "translated", "cache result") }, completed: { done.signal() })
    require(done.wait(timeout: .now() + 3) == .success, "completion")
    d.dispose()
}
cachedRequest("cache0"); cachedRequest("cache0")
require(count("cache starts cache0") == 1, "cache replay")
for i in 1...256 { cachedRequest("cache\(i)") }
cachedRequest("cache0")
require(count("cache starts cache0") == 2, "LRU bounded at 256")

let policyCancelled = DispatchSemaphore(value: 0)
let stale = JerkgramTranslationAdmission.shared.request(key: "42:old-generation", count: 1, bytes: 1, start: { held("policy") }).start(error: { _ in policyCancelled.signal() })
eventually { count("policy") == 1 }
JerkgramTranslationSettings.update(accountPeerId: a, enabled: true)
require(policyCancelled.wait(timeout: .now() + 3) == .success, "policy update cancels request")
eventually { count("policy disposed") == 1 }; stale.dispose()

let timedOut = DispatchSemaphore(value: 0)
let timeoutStart = Date()
private let timeoutLifetime = lifetimeRequest(admission, key: "timeout", success: false, error: { timedOut.signal() })
let timeout = timeoutLifetime.0
require(timedOut.wait(timeout: .now() + 33) == .success, "30 second timeout")
require(Date().timeIntervalSince(timeoutStart) >= 29, "deadline must be real")
require(count("timeout disposed") == 1, "timeout cancels physical transport exactly once")
timeout.dispose()
eventually { timeoutLifetime.1.value == nil }
print("production policy/admission cases passed")
