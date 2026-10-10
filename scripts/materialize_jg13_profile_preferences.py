#!/usr/bin/env python3
"""Hash-gated four-owner delta: memory-only profile and header preferences."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "patches/jg13-profile-preferences.sha256.json"
GLASS = "submodules/Display/Source/GhostBaseGlass.swift"
AVATAR = "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoAvatarTransformContainerNode.swift"
SETTINGS = "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
HEADER = "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderNode.swift"

def replace_once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError("Profile preference parent context changed")
    return text.replace(old, new, 1)

def transform(name, text):
    if name == GLASS:
        text = replace_once(text, "    public static func reloadFromDefaults() {\n        self.enabledLock.lock()\n        defer { self.enabledLock.unlock() }\n        self.enabledValue = UserDefaults.standard.object(forKey: self.enabledKey) as? Bool ?? true\n    }", '''    private static var profileAnimatedValue: Bool = {
        return UserDefaults.standard.object(forKey: "jerkgram.ProfileBlur.Animated") as? Bool ?? true
    }()

    private static var profileAvatarValue = UserDefaults.standard.object(forKey: "jerkgram.ProfileBlur.Avatar") as? Bool ?? true
    private static var profileTintValue = UserDefaults.standard.object(forKey: "jerkgram.ProfileBlur.Tint") as? Bool ?? true
    private static var profileReducedValue = UserDefaults.standard.object(forKey: "jerkgram.ProfileBlur.Reduced") as? Bool ?? false
    private static var profileHideOwnPhoneValue = UserDefaults.standard.object(forKey: "jerkgram.Appearance.HideOwnPhone") as? Bool ?? false

    private static var preferenceGeneration: UInt64 = 0

    public static func reloadFromDefaults() {
        // Account projection/import calls this after updating active defaults.
        // Explicit refresh I/O is outside the hot lock; lazy bootstrap is once.
        self.enabledLock.lock()
        self.preferenceGeneration &+= 1
        let generation = self.preferenceGeneration
        self.enabledLock.unlock()
        let defaults = UserDefaults.standard
        let enabled = defaults.object(forKey: self.enabledKey) as? Bool ?? true
        let animated = defaults.object(forKey: "jerkgram.ProfileBlur.Animated") as? Bool ?? true
        let avatar = defaults.object(forKey: "jerkgram.ProfileBlur.Avatar") as? Bool ?? true
        let tint = defaults.object(forKey: "jerkgram.ProfileBlur.Tint") as? Bool ?? true
        let reduced = defaults.object(forKey: "jerkgram.ProfileBlur.Reduced") as? Bool ?? false
        let hideOwnPhone = defaults.object(forKey: "jerkgram.Appearance.HideOwnPhone") as? Bool ?? false
        self.enabledLock.lock()
        defer { self.enabledLock.unlock() }
        guard self.preferenceGeneration == generation else { return }
        self.enabledValue = enabled
        self.profileAnimatedValue = animated
        self.profileAvatarValue = avatar
        self.profileTintValue = tint
        self.profileReducedValue = reduced
        self.profileHideOwnPhoneValue = hideOwnPhone
    }

    public static var profileBlurSettings: GhostBaseProfileBlurSettings? {
        self.enabledLock.lock()
        defer { self.enabledLock.unlock() }
        guard self.enabledValue else { return nil }
        return GhostBaseProfileBlurSettings(
            avatarBlurInProfile: self.profileAvatarValue,
            animatedBackgroundEnabled: self.profileAnimatedValue,
            tintEnabled: self.profileTintValue,
            reducedBlur: self.profileReducedValue
        )
    }

    public static var profileAnimatedBackgroundEnabled: Bool {
        self.enabledLock.lock()
        defer { self.enabledLock.unlock() }
        return self.enabledValue && self.profileAnimatedValue
    }

    public static var profileHideOwnPhone: Bool {
        self.enabledLock.lock()
        defer { self.enabledLock.unlock() }
        return self.profileHideOwnPhoneValue
    }

    public static func setProfilePlaybackSettings(glassEnabled: Bool, animatedBackgroundEnabled: Bool, avatarBlurInProfile: Bool? = nil, tintEnabled: Bool? = nil, reducedBlur: Bool? = nil, hideOwnPhone: Bool? = nil) {
        // Controller projects profile and phone keys before atomic publication.
        self.enabledLock.lock()
        self.enabledValue = glassEnabled
        self.profileAnimatedValue = animatedBackgroundEnabled
        if let avatarBlurInProfile { self.profileAvatarValue = avatarBlurInProfile }
        if let tintEnabled { self.profileTintValue = tintEnabled }
        if let reducedBlur { self.profileReducedValue = reducedBlur }
        if let hideOwnPhone { self.profileHideOwnPhoneValue = hideOwnPhone }
        self.preferenceGeneration &+= 1
        self.enabledLock.unlock()
    }''')
        text = replace_once(text, '''    public static func setEnabled(_ value: Bool) {
        self.enabledLock.lock()
        self.enabledValue = value
        self.enabledLock.unlock()
        UserDefaults.standard.set(value, forKey: self.enabledKey)
    }''', '''    public static func setEnabled(_ value: Bool) {
        UserDefaults.standard.set(value, forKey: self.enabledKey)
        self.enabledLock.lock()
        self.enabledValue = value
        self.preferenceGeneration &+= 1
        self.enabledLock.unlock()
    }''')
        text = replace_once(text, '''    // Reads the master key first. Child settings are not read and no profile
    // object is created when the effect is disabled.
    public static func loadEnabled() -> GhostBaseProfileBlurSettings? {
        guard GhostBaseGlassStyle.isEnabled else {
            return nil
        }
        let defaults = UserDefaults.standard
        return GhostBaseProfileBlurSettings(
            avatarBlurInProfile: defaults.object(forKey: self.avatarBlurKey) as? Bool ?? true,
            animatedBackgroundEnabled: defaults.object(forKey: self.animatedKey) as? Bool ?? true,
            tintEnabled: defaults.object(forKey: self.tintKey) as? Bool ?? true,
            reducedBlur: defaults.object(forKey: self.reducedKey) as? Bool ?? false
        )
    }''', '''    // Master gate and all child values are read atomically from the snapshot.
    // Defaults bootstrap is once; explicit account/import refresh stays supported.
    public static func loadEnabled() -> GhostBaseProfileBlurSettings? {
        return GhostBaseGlassStyle.profileBlurSettings
    }''')
    elif name == AVATAR:
        text = replace_once(text, '''            let keepVideoAlive =
                GhostBaseProfileBlurSettings
                    .loadEnabled()?
                    .animatedBackgroundEnabled
                == true''', '''            let animatedBackgroundEnabled = GhostBaseGlassStyle.profileAnimatedBackgroundEnabled
            let keepVideoAlive = animatedBackgroundEnabled''')
    elif name == SETTINGS:
        publication = '''    GhostBaseGlassStyle.setProfilePlaybackSettings(
        glassEnabled: current.glassEnabled,
        animatedBackgroundEnabled: current.profileAnimatedBackground,
        avatarBlurInProfile: current.profileAvatarBlur,
        tintEnabled: current.profileBlurTint,
        reducedBlur: current.profileBlurReduced,
        hideOwnPhone: current.hideOwnPhone
    )'''
        text = replace_once(text, "    guard !changes.isEmpty else { return }", '''    guard !changes.isEmpty else {
''' + publication + '''
        return
    }''')
        text = replace_once(text, '''    let jerkgramSynchronousRuntimeSettingKeys: Set<String> = Set<String>([
        GhostBaseKey.scheduledSend,''', '''    let jerkgramSynchronousRuntimeSettingKeys: Set<String> = Set<String>([
        // Only preference changes project here, never avatar transition ticks.
        GhostBaseKey.glassEnabled,
        GhostBaseKey.profileAnimatedBackground,
        GhostBaseKey.profileAvatarBlur,
        GhostBaseKey.profileBlurTint,
        GhostBaseKey.profileBlurReduced,
        GhostBaseKey.hideOwnPhone,
        GhostBaseKey.scheduledSend,''')
        text = replace_once(text, '''    }
    JerkgramActivityGhostRuntime.invalidate()''', '''    }
''' + publication + '''
    JerkgramActivityGhostRuntime.invalidate()''')
    elif name == HEADER:
        text = replace_once(text, '''                let hideOwnPhone =
                    (
                        UserDefaults.standard
                            .object(
                                forKey:
                                    "jerkgram.Appearance.HideOwnPhone"
                            )
                        as? Bool
                    )
                    ?? false''', '''                let hideOwnPhone = GhostBaseGlassStyle.profileHideOwnPhone''')
    else:
        raise RuntimeError("Unreviewed profile preferences owner")
    return text

def check(source, stage, final_owners=None):
    manifest = json.loads(MANIFEST.read_text())
    if final_owners:
        if stage != "after": raise RuntimeError("Final owner override is only valid after materialization")
        for name in set(manifest["owners"]) & set(final_owners):
            manifest["owners"][name]["after_sha256"] = final_owners[name]["after_sha256"]
    config = json.loads((ROOT / "jerkgram-migration.json").read_text())
    if config["upstream_new_sha"] != manifest["upstream_sha"]:
        raise RuntimeError("Profile preferences upstream pin changed")
    if set(manifest["owners"]) != {GLASS, AVATAR, SETTINGS, HEADER}:
        raise RuntimeError("Profile preferences owner scope changed")
    for name, hashes in manifest["owners"].items():
        data = (source / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != hashes[stage + "_sha256"]:
            raise RuntimeError(f"Profile preferences {stage} hash mismatch: {name}")
        declarations = set(re.findall(r"(?m)^\s*(?:(?:public|private|fileprivate|internal|override|static|class|final|@objc)\s+)*func\s+(\w+)", data.decode()))
        if not set(hashes["survival_functions"]) <= declarations:
            raise RuntimeError(f"Profile preferences lost function: {name}")
    for name, expected in manifest["regression_locks"].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Profile preferences regression lock changed: {name}")
    return manifest

def verify_preferences(source, final_owners=None):
    source = Path(source).resolve()
    manifest = check(source, "after", final_owners=final_owners)
    from materialize_jg13_profile_p0 import verify_p0
    verify_p0(source, final_owners={**manifest["owners"], **(final_owners or {})})
    env = dict(os.environ, JG13_SOURCE=str(source))
    subprocess.run([sys.executable, str(ROOT / "tests/test_jg13_profile_preferences.py")], cwd=ROOT, env=env, check=True)

def apply_preferences(source):
    source = Path(source).resolve()
    git_root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=source, text=True).strip()).resolve()
    if git_root != source:
        raise RuntimeError("Profile preferences source must be its own Git root")
    check(source, "before")
    # Validate every exact replacement before writing any owner.
    outputs = {name: transform(name, (source / name).read_text()) for name in (GLASS, AVATAR, SETTINGS, HEADER)}
    manifest = json.loads(MANIFEST.read_text())
    for name, value in outputs.items():
        if hashlib.sha256(value.encode()).hexdigest() != manifest["owners"][name]["after_sha256"]:
            raise RuntimeError(f"Profile preferences generated hash mismatch: {name}")
    for name, value in outputs.items():
        (source / name).write_text(value)
    verify_preferences(source)
    print("Profile preferences memory snapshot PATCHED / VERIFIED; NOT COMPILED / NOT RUNTIME TESTED")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "work/swiftgram-src")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    (apply_preferences if args.apply else verify_preferences)(args.source)
