let defaults = UserDefaults.standard
let allKeys = Set(jerkgramStateValues(GhostBaseSettingsState.readStored(accountPeerId: 1001, allowLegacyFallback: false)).keys)
assert(allKeys.count == 49)
let marker = "jerkgram.Settings.ActiveProjectionAccount.V176"
// Only fixture-owned executable-domain keys are touched.
for key in allKeys {
    defaults.removeObject(forKey: key)
    for id in [Int64(1001), Int64(1002)] { defaults.removeObject(forKey: jerkgramScopedSettingsKey(accountPeerId: id, key: key)) }
}
defaults.removeObject(forKey: marker)
let scheduledSuite = UserDefaults(suiteName: "group.com.jerkgram.ios")!
scheduledSuite.removeObject(forKey: GhostBaseKey.scheduledSend)
// Pure pre-activation page read cannot migrate or project anything.
JerkgramWave1Instrumentation.reset()
_ = GhostBaseSettingsState.load(accountPeerId: 1001)
assert(JerkgramWave1Instrumentation.counters.isEmpty)
assert(defaults.object(forKey: marker) == nil)
assert(defaults.object(forKey: jerkgramScopedSettingsKey(accountPeerId: 1001, key: GhostBaseKey.profileEnabled)) == nil)
// Migration precedence: scoped beats legacy, legacy beats default.
defaults.set(true, forKey: GhostBaseKey.messageSeconds)
defaults.set(false, forKey: jerkgramScopedSettingsKey(accountPeerId: 1001, key: GhostBaseKey.messageSeconds))
defaults.set(false, forKey: GhostBaseKey.showIds)
jerkgramActivateAccountSettings(accountPeerId: 1001)
var state = GhostBaseSettingsState.load(accountPeerId: 1001)
assert(!state.messageSeconds && !state.showIds)
assert(scheduledSuite.object(forKey: GhostBaseKey.scheduledSend) as? Bool == false)
// 100 ordinary opens, and repeated same-account activation, produce zero writes.
JerkgramWave1Instrumentation.reset()
for _ in 0..<100 { assert(GhostBaseSettingsState.load(accountPeerId: 1001) == state) }
jerkgramActivateAccountSettings(accountPeerId: 1001)
assert(JerkgramWave1Instrumentation.counters.isEmpty)
assert(GhostBaseGlassStyle.calls == 0 && JerkgramBlockedReactionPolicy.calls == 0)
// A nonvisual, nonhot change writes only its scoped+compatibility domains.
var next = state; next.saveEditHistory.toggle()
jerkgramPersistChangedSettings(accountPeerId: 1001, previous: state, current: next)
assert(JerkgramWave1Instrumentation.counters["projectionWrites"] == 2)
assert(JerkgramWave1Instrumentation.counters["hotInvalidations"] == nil)
assert(GhostBaseGlassStyle.calls == 0 && JerkgramBlockedReactionPolicy.calls == 0)
state = next
// Exact no-op does not call any setter or publisher.
JerkgramWave1Instrumentation.reset()
jerkgramPersistChangedSettings(accountPeerId: 1001, previous: state, current: state)
assert(JerkgramWave1Instrumentation.counters.isEmpty)
// A hot key invalidates once; cache observes the new value.
_ = JerkgramHotSettings.object(forKey: GhostBaseKey.messageSeconds)
next = state; next.messageSeconds.toggle()
jerkgramPersistChangedSettings(accountPeerId: 1001, previous: state, current: next)
assert(JerkgramWave1Instrumentation.counters["projectionWrites"] == 2)
assert(JerkgramWave1Instrumentation.counters["hotInvalidations"] == 1)
assert(JerkgramHotSettings.object(forKey: GhostBaseKey.messageSeconds) as? Bool == next.messageSeconds)
assert(GhostBaseGlassStyle.calls == 0)
state = next
// One visual batch calls the atomic publisher once.
JerkgramWave1Instrumentation.reset()
next = state; next.glassEnabled.toggle(); next.settingsTranslucency.toggle(); next.profileBlurTint.toggle()
jerkgramPersistChangedSettings(accountPeerId: 1001, previous: state, current: next)
assert(GhostBaseGlassStyle.calls == 1)
assert(JerkgramWave1Instrumentation.counters["projectionWrites"] == 6)
state = next
// Profile metadata participates in the same coherent visual revision.
JerkgramWave1Instrumentation.reset()
next = state; next.showDCs.toggle(); next.showRegistration.toggle()
jerkgramPersistChangedSettings(accountPeerId: 1001, previous: state, current: next)
assert(GhostBaseGlassStyle.calls == 1)
state = next
// Blocked policy publishes only for a real blocked-key delta.
JerkgramWave1Instrumentation.reset()
next = state; next.hideBlockedMessages.toggle()
jerkgramPersistChangedSettings(accountPeerId: 1001, previous: state, current: next)
assert(JerkgramBlockedReactionPolicy.calls == 1 && GhostBaseGlassStyle.calls == 0)
// New account does not inherit the prior account's runtime projection.
jerkgramActivateAccountSettings(accountPeerId: 1002)
let second = GhostBaseSettingsState.load(accountPeerId: 1002)
assert(!second.messageSeconds && second.showIds && second.glassEnabled)
jerkgramActivateAccountSettings(accountPeerId: 1001)
assert(GhostBaseSettingsState.load(accountPeerId: 1001) == next)
// Import retains extra integer catalog and legacy aliases, and invalidates hot once.
defaults.set(true, forKey: jerkgramScopedSettingsKey(accountPeerId: 1001, key: GhostBaseKey.scheduledSend))
let imported = JerkgramSettingsSnapshot(accountPeerId: 1001, toggles: [GhostBaseKey.scheduledSend: true],
    integerValues: [GhostBaseKey.deletedMediaCacheLimit: 123], stringValues: [:])
JerkgramWave1Instrumentation.reset()
jerkgramProjectImportedSettingsToActiveDefaults(imported)
assert(defaults.object(forKey: GhostBaseKey.deletedMediaCacheLimit) as? Int == 123)
assert(defaults.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool == true)
assert(scheduledSuite.object(forKey: GhostBaseKey.scheduledSend) as? Bool == true)
assert(scheduledSuite.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool == true)
assert(GhostBaseSettingsState.load(accountPeerId: 1001).scheduledSend)
JerkgramWave1Instrumentation.reset()
jerkgramProjectImportedSettingsToActiveDefaults(imported)
assert(JerkgramWave1Instrumentation.counters.isEmpty)
assert(GhostBaseGlassStyle.calls == 0 && JerkgramBlockedReactionPolicy.calls == 0)
print("PASS: production Foundation projection/migration/account/import/cache fixtures")
