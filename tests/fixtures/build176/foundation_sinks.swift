// UI-only boundaries replaced for the standalone Foundation executable.
enum JerkgramWave1Instrumentation {
    static var counters: [String: Int] = [:]
    static func add(_ key: String, _ value: Int = 1) { counters[key, default: 0] += value }
    static func reset() { counters = [:]; GhostBaseGlassStyle.calls = 0; JerkgramBlockedReactionPolicy.calls = 0; JerkgramActivityGhostRuntime.calls = 0 }
}
enum GhostBaseGlassStyle {
    static var calls = 0
    static func setProfilePlaybackSettings(glassEnabled: Bool, animatedBackgroundEnabled: Bool,
        avatarBlurInProfile: Bool, tintEnabled: Bool, reducedBlur: Bool, hideOwnPhone: Bool,
        settingsTranslucencyEnabled: Bool? = nil, forceVisualChange: Bool = false) { calls += 1 }
}
enum JerkgramBlockedReactionPolicy { static var calls = 0; static func notifySettingsChanged() { calls += 1 } }
enum JerkgramActivityGhostRuntime { static var calls = 0; static func invalidate() { calls += 1 } }
struct JerkgramSettingsSnapshot {
    let accountPeerId: Int64
    let toggles: [String: Bool]
    let integerValues: [String: Int64]
    let stringValues: [String: String]
}
