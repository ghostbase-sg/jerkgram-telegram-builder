#!/usr/bin/env python3
"""Execute actual preference snapshot owner with a counted defaults facade.

Checks freshness and zero repeated defaults reads, NOT iOS/UI performance.
"""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("JG13_SOURCE", ROOT / "work/swiftgram-src"))

def block(text, needle):
    assert text.count(needle) == 1, needle
    start = text.index(needle)
    brace = text.index("{", start)
    end, depth = brace + 1, 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[start:end] + "\n"

def fixture():
    text = (SOURCE / "submodules/Display/Source/GhostBaseGlass.swift").read_text()
    # Extract the real owner, excluding only unrelated UIKit color/style methods.
    owner = text.split("public enum GhostBaseGlassStyle {", 1)[1].split("    public static var usesReducedEffects:", 1)[0]
    owner += block(text, "    public static func setEnabled(")
    owner = "enum GhostBaseGlassStyle {" + owner + "}\n"
    # UserDefaults is the counted dependency boundary; snapshot code is unchanged.
    owner += "public struct GhostBaseProfileBlurSettings" + text.split("public struct GhostBaseProfileBlurSettings", 1)[1]
    owner = owner.replace("UserDefaults.standard", "CountedDefaults.standard")
    return r'''
import Foundation
import Dispatch
final class CountedDefaults {
    static let standard = CountedDefaults()
    var values: [String: Bool] = [:]
    var reads = 0
    var writes = 0
    var afterRead: (() -> Void)?
    var afterReadKey: String?
    private let boundaryLock = NSLock()
    func object(forKey key: String) -> Any? {
        boundaryLock.lock()
        reads += 1
        let captured = values[key]
        let matches = afterReadKey == nil || afterReadKey == key
        let callback = matches ? afterRead : nil
        if matches { afterRead = nil }
        boundaryLock.unlock()
        callback?()
        return captured
    }
    func set(_ value: Bool, forKey key: String) { writes += 1; values[key] = value }
}
''' + owner + r'''
let defaults = CountedDefaults.standard
// Missing keys retain the existing true defaults.
precondition(GhostBaseGlassStyle.profileAnimatedBackgroundEnabled)
let initialBackground = GhostBaseProfileBlurSettings.loadEnabled()!
precondition(initialBackground.avatarBlurInProfile && initialBackground.animatedBackgroundEnabled && initialBackground.tintEnabled && !initialBackground.reducedBlur)
precondition(!GhostBaseGlassStyle.profileHideOwnPhone)
let warmReads = defaults.reads
for _ in 0..<10000 {
    precondition(GhostBaseGlassStyle.profileAnimatedBackgroundEnabled)
    precondition(!GhostBaseGlassStyle.profileHideOwnPhone)
    precondition(GhostBaseProfileBlurSettings.loadEnabled() == initialBackground)
}
precondition(defaults.reads == warmReads, "transition reread defaults")
// Controller state must apply immediately, before its deferred disk projection.
GhostBaseGlassStyle.setProfilePlaybackSettings(glassEnabled: true, animatedBackgroundEnabled: false)
precondition(!GhostBaseGlassStyle.profileAnimatedBackgroundEnabled)
precondition(defaults.reads == warmReads && defaults.writes == 0)
GhostBaseGlassStyle.setProfilePlaybackSettings(glassEnabled: false, animatedBackgroundEnabled: true)
precondition(!GhostBaseGlassStyle.profileAnimatedBackgroundEnabled)
GhostBaseGlassStyle.setEnabled(true)
precondition(GhostBaseGlassStyle.profileAnimatedBackgroundEnabled)
// Full controller state publishes in one locked generation, before persistence.
GhostBaseGlassStyle.setProfilePlaybackSettings(glassEnabled: true, animatedBackgroundEnabled: false, avatarBlurInProfile: false, tintEnabled: false, reducedBlur: true)
let toggled = GhostBaseProfileBlurSettings.loadEnabled()!
precondition(!toggled.avatarBlurInProfile && !toggled.animatedBackgroundEnabled && !toggled.tintEnabled && toggled.reducedBlur)
precondition(defaults.reads == warmReads)
GhostBaseGlassStyle.setEnabled(false)
precondition(GhostBaseProfileBlurSettings.loadEnabled() == nil)
GhostBaseGlassStyle.setEnabled(true)
precondition(GhostBaseProfileBlurSettings.loadEnabled() == toggled)
// Phone privacy is independent of glass; legacy publishers preserve its value.
GhostBaseGlassStyle.setProfilePlaybackSettings(glassEnabled: false, animatedBackgroundEnabled: true, hideOwnPhone: true)
precondition(GhostBaseGlassStyle.profileHideOwnPhone)
GhostBaseGlassStyle.setProfilePlaybackSettings(glassEnabled: true, animatedBackgroundEnabled: false)
precondition(GhostBaseGlassStyle.profileHideOwnPhone)
GhostBaseGlassStyle.setEnabled(false)
precondition(GhostBaseGlassStyle.profileHideOwnPhone)
GhostBaseGlassStyle.setEnabled(true)
GhostBaseGlassStyle.setProfilePlaybackSettings(glassEnabled: true, animatedBackgroundEnabled: false, hideOwnPhone: false)
precondition(!GhostBaseGlassStyle.profileHideOwnPhone)
precondition(defaults.reads == warmReads)
// Existing account/import hooks reload all projected defaults.
defaults.values["jerkgram.ProfileBlur.Avatar"] = true
defaults.values["jerkgram.ProfileBlur.Tint"] = true
defaults.values["jerkgram.ProfileBlur.Reduced"] = false
defaults.values["jerkgram.Glass.Enabled"] = true
defaults.values["jerkgram.ProfileBlur.Animated"] = false
defaults.values["jerkgram.Appearance.HideOwnPhone"] = true
GhostBaseGlassStyle.reloadFromDefaults()
precondition(GhostBaseGlassStyle.profileHideOwnPhone)
precondition(!GhostBaseGlassStyle.profileAnimatedBackgroundEnabled)
let imported = GhostBaseProfileBlurSettings.loadEnabled()!
precondition(imported.avatarBlurInProfile && imported.tintEnabled && !imported.reducedBlur && !imported.animatedBackgroundEnabled)
defaults.values["jerkgram.Glass.Enabled"] = false
defaults.values["jerkgram.ProfileBlur.Animated"] = true
GhostBaseGlassStyle.reloadFromDefaults()
precondition(!GhostBaseGlassStyle.profileAnimatedBackgroundEnabled)
defaults.values.removeAll()
GhostBaseGlassStyle.reloadFromDefaults()
precondition(!GhostBaseGlassStyle.profileHideOwnPhone)
precondition(GhostBaseGlassStyle.profileAnimatedBackgroundEnabled)
let reloadedReads = defaults.reads
for _ in 0..<10000 {
    precondition(GhostBaseGlassStyle.profileAnimatedBackgroundEnabled)
    precondition(!GhostBaseGlassStyle.profileHideOwnPhone)
    precondition(GhostBaseProfileBlurSettings.loadEnabled() == initialBackground)
}
precondition(defaults.reads == reloadedReads)
// A concurrent import refresh must not overwrite a newer live publication.
defaults.values["jerkgram.ProfileBlur.Animated"] = false
defaults.afterRead = {
    GhostBaseGlassStyle.setProfilePlaybackSettings(glassEnabled: true, animatedBackgroundEnabled: true, avatarBlurInProfile: false, tintEnabled: false, reducedBlur: true)
}
GhostBaseGlassStyle.reloadFromDefaults()
precondition(GhostBaseGlassStyle.profileAnimatedBackgroundEnabled, "stale import refresh overwrote live setting")
let fresh = GhostBaseProfileBlurSettings.loadEnabled()!
precondition(!fresh.avatarBlurInProfile && !fresh.tintEnabled && fresh.reducedBlur, "stale refresh overwrote child snapshot")
// Capture an old phone value, then publish a new one before refresh completes.
defaults.afterReadKey = "jerkgram.Appearance.HideOwnPhone"
defaults.afterRead = {
    GhostBaseGlassStyle.setProfilePlaybackSettings(glassEnabled: true, animatedBackgroundEnabled: true, hideOwnPhone: true)
}
GhostBaseGlassStyle.reloadFromDefaults()
precondition(GhostBaseGlassStyle.profileHideOwnPhone, "stale import overwrote live phone privacy")
defaults.afterReadKey = nil
// Older import captures OFF, newer account refresh captures ON; deliberately
// allow the older refresh to finish first. Only the newest refresh may publish.
let oldCaptured = DispatchSemaphore(value: 0)
let releaseOld = DispatchSemaphore(value: 0)
let oldDone = DispatchSemaphore(value: 0)
let newCaptured = DispatchSemaphore(value: 0)
let releaseNew = DispatchSemaphore(value: 0)
let newDone = DispatchSemaphore(value: 0)
func awaitSignal(_ semaphore: DispatchSemaphore) {
    precondition(semaphore.wait(timeout: .now() + 10) == .success, "component interleaving timed out")
}
defaults.values["jerkgram.Glass.Enabled"] = false
defaults.values["jerkgram.ProfileBlur.Animated"] = false
defaults.afterReadKey = "jerkgram.ProfileBlur.Animated"
defaults.afterRead = { oldCaptured.signal(); awaitSignal(releaseOld) }
DispatchQueue.global().async { GhostBaseGlassStyle.reloadFromDefaults(); oldDone.signal() }
awaitSignal(oldCaptured)
defaults.values["jerkgram.Glass.Enabled"] = true
defaults.values["jerkgram.ProfileBlur.Animated"] = true
defaults.afterRead = { newCaptured.signal(); awaitSignal(releaseNew) }
DispatchQueue.global().async { GhostBaseGlassStyle.reloadFromDefaults(); newDone.signal() }
awaitSignal(newCaptured)
releaseOld.signal()
awaitSignal(oldDone)
releaseNew.signal()
awaitSignal(newDone)
precondition(GhostBaseGlassStyle.profileAnimatedBackgroundEnabled, "older refresh rejected newer account snapshot")
precondition(GhostBaseProfileBlurSettings.loadEnabled() == initialBackground, "newer account child settings were not restored")
precondition(!GhostBaseGlassStyle.profileHideOwnPhone, "account refresh did not restore missing phone key")
print("profile-phone-preference component PASS: memory-only repeated reads, immediate toggles, independent master, legacy publisher preservation, account/import freshness, stale refresh rejection")
print("profile-preferences component PASS: background and transition memory-only repeated reads, immediate toggles, master gate, account/import reload, missing keys")
'''

if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="jg13-profile-preferences-") as tmp:
        source = Path(tmp) / "main.swift"
        source.write_text(fixture())
        subprocess.run(["xcrun", "swift", str(source)], check=True)
