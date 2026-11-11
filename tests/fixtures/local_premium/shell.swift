// Only native list/controller/signal publication boundaries are replaced.
// Defaults, canonical state, policies, setters and appearance callback are real.
public struct PresentationStrings { public let baseLanguageCode: String }
private class ItemListController {
    func viewWillAppear(_ animated: Bool) {}
    func viewDidAppear(_ animated: Bool) {}
    func viewWillDisappear(_ animated: Bool) {}
}
private final class JerkgramPerformanceDiagnostics {
    static let shared = JerkgramPerformanceDiagnostics()
    func setVisibleRoute(_ route: String, owner: AnyObject) {}
    func clearVisibleRoute(owner: AnyObject) {}
}
private final class Atomic<Value> {
    var value: Value
    init(value: Value) { self.value = value }
    func modify(_ f: (Value) -> Value) -> Value { self.value = f(self.value); return self.value }
    func with<Result>(_ f: (Value) -> Result) -> Result { return f(self.value) }
}
private final class ValuePromise<Value> {
    var value: Value
    var publications = 0
    init(_ value: Value, ignoreRepeated: Bool) { self.value = value }
    func set(_ value: Value) { self.value = value; self.publications += 1 }
}
private struct FixturePeerId { let value: Int64; func toInt64() -> Int64 { self.value } }
private struct FixtureAccount { let peerId: FixturePeerId }
private struct FixtureContext {
    let account: FixtureAccount
    init(_ value: Int64) { self.account = FixtureAccount(peerId: FixturePeerId(value: value)) }
}
private struct FixturePage {
    let controller: JerkgramDiagnosticSettingsController
    let current: () -> GhostBaseSettingsState
    let update: ((GhostBaseSettingsState) -> GhostBaseSettingsState) -> Void
    let promise: ValuePromise<GhostBaseSettingsState>
}
// Translation admission is external to settings state. No translation/network
// operation is exercised by this fixture.
private final class JerkgramTranslationAdmission {
    static let shared = JerkgramTranslationAdmission()
    func cancel(accountPeerId: Int64) {}
}
