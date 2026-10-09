#!/usr/bin/env python3
"""Hash-gated three-owner delta: memory-only profile playback preference."""
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

def replace_once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError("Profile preference parent context changed")
    return text.replace(old, new, 1)

def transform(name, text):
    if name == GLASS:
        text = replace_once(text, "    public static func reloadFromDefaults() {\n        self.enabledLock.lock()\n        defer { self.enabledLock.unlock() }\n        self.enabledValue = UserDefaults.standard.object(forKey: self.enabledKey) as? Bool ?? true\n    }", '''    private static var profileAnimatedValue: Bool = {
        return UserDefaults.standard.object(forKey: "jerkgram.ProfileBlur.Animated") as? Bool ?? true
    }()

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
        self.enabledLock.lock()
        defer { self.enabledLock.unlock() }
        guard self.preferenceGeneration == generation else { return }
        self.enabledValue = enabled
        self.profileAnimatedValue = animated
    }

    public static var profileAnimatedBackgroundEnabled: Bool {
        self.enabledLock.lock()
        defer { self.enabledLock.unlock() }
        return self.enabledValue && self.profileAnimatedValue
    }

    public static func setProfilePlaybackSettings(glassEnabled: Bool, animatedBackgroundEnabled: Bool) {
        // Controller projects these two keys before publishing; other keys defer.
        self.enabledLock.lock()
        self.enabledValue = glassEnabled
        self.profileAnimatedValue = animatedBackgroundEnabled
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
        animatedBackgroundEnabled: current.profileAnimatedBackground
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
        GhostBaseKey.scheduledSend,''')
        text = replace_once(text, '''    }
    JerkgramActivityGhostRuntime.invalidate()''', '''    }
''' + publication + '''
    JerkgramActivityGhostRuntime.invalidate()''')
    else:
        raise RuntimeError("Unreviewed profile preferences owner")
    return text

def check(source, stage):
    manifest = json.loads(MANIFEST.read_text())
    config = json.loads((ROOT / "jerkgram-migration.json").read_text())
    if config["upstream_new_sha"] != manifest["upstream_sha"]:
        raise RuntimeError("Profile preferences upstream pin changed")
    if set(manifest["owners"]) != {GLASS, AVATAR, SETTINGS}:
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

def verify_preferences(source):
    source = Path(source).resolve()
    manifest = check(source, "after")
    from materialize_jg13_profile_p0 import verify_p0
    verify_p0(source, final_owners=manifest["owners"])
    env = dict(os.environ, JG13_SOURCE=str(source))
    subprocess.run([sys.executable, str(ROOT / "tests/test_jg13_profile_preferences.py")], cwd=ROOT, env=env, check=True)

def apply_preferences(source):
    source = Path(source).resolve()
    git_root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=source, text=True).strip()).resolve()
    if git_root != source:
        raise RuntimeError("Profile preferences source must be its own Git root")
    check(source, "before")
    # Validate every exact replacement before writing any owner.
    outputs = {name: transform(name, (source / name).read_text()) for name in (GLASS, AVATAR, SETTINGS)}
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
