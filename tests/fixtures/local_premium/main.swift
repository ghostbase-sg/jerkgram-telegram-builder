func check(_ condition: @autoclosure () -> Bool, _ message: String) { precondition(condition(), message) }
let defaults = UserDefaults.standard
let a: Int64 = 91823734561
let b = a + 1
let keys = [JerkgramSponsoredContentPolicy.preferenceKey, JerkgramDownloadBoostSettings.preferenceKey, JerkgramTranslationSettings.preferenceKey]
let savedKeys = keys + keys.flatMap { key in [a, b].map { jerkgramScopedSettingsKey(accountPeerId: $0, key: key) } } + [JerkgramAppIconAccess.preferenceKey]
let previous = savedKeys.map { defaults.object(forKey: $0) }
defer {
    for (key, value) in zip(savedKeys, previous) {
        if let value { defaults.set(value, forKey: key) } else { defaults.removeObject(forKey: key) }
    }
}
for key in savedKeys { defaults.removeObject(forKey: key) }
let beforeOpen = savedKeys.map { defaults.object(forKey: $0) }
private let hub = makePage(a)
private let home = makePage(a)
private let messages = makePage(a)
private let media = makePage(a)
for page in [hub, home, messages, media] { page.controller.viewWillAppear(false) }
check(!hub.current().removeSponsored && hub.current().downloadBoost == "off" && hub.current().enhancedTranslation, "canonical defaults must remain false/off/true")
check(!JerkgramAppIconAccess.unlockEnabled, "global App Icons default must remain false")
for (before, key) in zip(beforeOpen, savedKeys) { check(JerkgramSettingsProjection.equal(before, defaults.object(forKey: key)), "opening/appearing writes no setting") }
JerkgramWave1Instrumentation.reset()
hub.update { current in var next = current; next.removeSponsored = true; next.downloadBoost = "maximum"; next.enhancedTranslation = false; return next }
check(JerkgramSponsoredContentPolicy.removeSponsored(accountPeerId: a), "existing ad cache setter receives change")
check(JerkgramDownloadBoostSettings.mode(accountPeerId: a) == .maximum, "existing boost cache setter receives change")
check(!JerkgramTranslationSettings.enabled(accountPeerId: a), "existing translation cache setter receives change")
for page in [home, messages, media] {
    page.controller.viewWillAppear(false)
    check(page.current().removeSponsored && page.current().downloadBoost == "maximum" && !page.current().enhancedTranslation, "returning aliases reload same current state")
    check(page.promise.value == page.current(), "refreshed values must be published to native list signal")
}
// An unrelated mutation from the formerly stale parent must retain Hub edits.
home.update { current in var next = current; next.showIds = !current.showIds; return next }
hub.controller.viewWillAppear(false)
check(hub.current().removeSponsored && hub.current().downloadBoost == "maximum" && !hub.current().enhancedTranslation, "back navigation may not revert unrelated Hub changes")
private let reopened = makePage(a)
check(reopened.current().downloadBoost == "maximum", "reopening reads committed state")
media.update { current in var next = current; next.downloadBoost = "medium"; return next }
hub.controller.viewWillAppear(false)
check(hub.current().downloadBoost == "medium", "alias edit refreshes Hub on return")
let writesBeforeAppearance = JerkgramWave1Instrumentation.counters["projectionWrites", default: 0]
hub.controller.viewWillAppear(false)
check(JerkgramWave1Instrumentation.counters["projectionWrites", default: 0] == writesBeforeAppearance, "appearance itself must not project settings")
// Global icon preference is intentionally outside the account state projection.
defaults.set(true, forKey: JerkgramAppIconAccess.preferenceKey)
check(JerkgramAppIconAccess.unlockEnabled && !JerkgramAppIconAccess.isLocked(iconIsPremium: true, accountIsPremium: false), "icon access remains device global")
private let other = makePage(b)
other.controller.viewWillAppear(false)
check(!other.current().removeSponsored && other.current().downloadBoost == "off" && other.current().enhancedTranslation, "second account must not inherit active projection")
check(JerkgramAppIconAccess.unlockEnabled, "account switch must preserve global icon value")
for key in keys { check(defaults.object(forKey: jerkgramScopedSettingsKey(accountPeerId: b, key: key)) == nil, "account reads do not create values") }
defaults.set("invalid", forKey: JerkgramDownloadBoostSettings.scopedKey(accountPeerId: b))
other.controller.viewWillAppear(false)
check(other.current().downloadBoost == "off", "invalid Boost must fall back to off without writing")
check(defaults.string(forKey: JerkgramDownloadBoostSettings.scopedKey(accountPeerId: b)) == "invalid", "invalid value read remains pure")
for language in ["en", "ru", "ru-RU", "fr"] {
    let strings = JerkgramStrings(baseLanguageCode: language)
    let russian = language.hasPrefix("ru")
    check(strings.localPremium == (russian ? "Локальный Premium" : "Local Premium"), "Hub title follows selected language/fallback")
    check(strings.translationNeedsWork.contains(russian ? "Требует доработки" : "Needs work"), "Translation status is truthful in both languages")
    check(strings.localPremiumScopeHint.contains(russian ? "не предоставляют Telegram Premium" : "do not grant Telegram Premium"), "local scope is explained")
}
print("Local Premium production state/lifecycle/defaults/alias/scope fixture PASS")
