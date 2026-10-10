"""Hot-path and freshness contracts; not device performance proof."""
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("JG13_SOURCE", ROOT / "work/swiftgram-src"))
AVATAR = "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoAvatarTransformContainerNode.swift"
GLASS = "submodules/Display/Source/GhostBaseGlass.swift"
SETTINGS = "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

def block(text, needle):
    start = text.index(needle)
    brace = text.index("{", start)
    end, depth = brace + 1, 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[start:end]

class ProfilePreferencesTests(unittest.TestCase):
    def test_header_phone_preference_is_memory_only_and_fresh(self):
        header = (SOURCE / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderNode.swift").read_text()
        update = block(header, "func update(width: CGFloat, containerHeight:")
        self.assertIn("let hideOwnPhone = GhostBaseGlassStyle.profileHideOwnPhone", update)
        self.assertNotIn("UserDefaults", update)
        glass = (SOURCE / GLASS).read_text()
        getter = block(glass, "public static var profileHideOwnPhone: Bool")
        self.assertIn("return self.profileHideOwnPhoneValue", getter)
        self.assertNotIn("UserDefaults", getter)
        self.assertNotIn("enabledValue", getter)
        reload = block(glass, "public static func reloadFromDefaults()")
        self.assertIn('defaults.object(forKey: "jerkgram.Appearance.HideOwnPhone") as? Bool ?? false', reload)
        self.assertIn("self.profileHideOwnPhoneValue = hideOwnPhone", reload)
        settings = block((SOURCE / SETTINGS).read_text(), "private func jerkgramPersistChangedSettings(")
        self.assertIn("GhostBaseKey.hideOwnPhone,", settings)
        self.assertEqual(settings.count("hideOwnPhone: current.hideOwnPhone"), 2)

    def test_transition_uses_memory_not_defaults(self):
        text = block((SOURCE / AVATAR).read_text(), "func updateTransitionFraction(")
        self.assertNotIn("loadEnabled()", text)
        self.assertNotIn("UserDefaults", text)
        self.assertIn("GhostBaseGlassStyle.profileAnimatedBackgroundEnabled", text)
        self.assertIn("performanceProbe?.begin(.preferences)", text)

    def test_background_settings_are_memory_only_and_publish_all_children(self):
        text = (SOURCE / GLASS).read_text()
        loader = block(text, "public static func loadEnabled()")
        self.assertNotIn("UserDefaults", loader)
        self.assertIn("GhostBaseGlassStyle.profileBlurSettings", loader)
        getter = block(text, "public static var profileBlurSettings:")
        self.assertNotIn("UserDefaults", getter)
        self.assertIn("guard self.enabledValue else", getter)
        for field in ("profileAvatarValue", "profileAnimatedValue", "profileTintValue", "profileReducedValue"):
            self.assertIn("self." + field, getter)
        settings = block((SOURCE / SETTINGS).read_text(), "private func jerkgramPersistChangedSettings(")
        for field in ("profileAvatarBlur", "profileBlurTint", "profileBlurReduced"):
            self.assertIn("current." + field, settings)
            self.assertIn("GhostBaseKey." + field + ",", settings)

    def test_playback_branches_remain_identical(self):
        text = block((SOURCE / AVATAR).read_text(), "func updateTransitionFraction(")
        policy = text.split("if keepVideoAlive {", 1)[1].split("let alphaTiming", 1)[0]
        self.assertIn("} else if fraction > 0.0 {\n                videoNode.pause()", policy)
        self.assertEqual(policy.count("videoNode.play()"), 2)
        self.assertEqual(policy.count("videoNode.pause()"), 1)

    def test_memory_getter_checks_master_and_animation_without_io(self):
        text = (SOURCE / GLASS).read_text()
        self.assertIn("public static var profileAnimatedBackgroundEnabled: Bool", text)
        getter = block(text, "public static var profileAnimatedBackgroundEnabled: Bool")
        self.assertIn("return self.enabledValue && self.profileAnimatedValue", getter)
        for token in ("UserDefaults", "loadEnabled", "reloadFromDefaults", "DispatchQueue"):
            self.assertNotIn(token, getter)
        self.assertIn("self.enabledLock.lock()", getter)
        self.assertIn("self.enabledLock.unlock()", getter)

    def test_reload_reads_outside_snapshot_lock(self):
        text = (SOURCE / GLASS).read_text()
        reload = block(text, "public static func reloadFromDefaults()")
        self.assertIn('defaults.object(forKey: "jerkgram.ProfileBlur.Animated")', reload)
        self.assertLess(reload.rindex("defaults.object"), reload.rindex("self.enabledLock.lock()"))
        self.assertIn("self.profileAnimatedValue = animated", reload)
        self.assertIn("guard self.preferenceGeneration == generation else { return }", reload)
        self.assertLess(reload.index("self.preferenceGeneration &+= 1"), reload.index("let generation ="))

    def test_settings_publish_before_deferred_persistence(self):
        text = block((SOURCE / SETTINGS).read_text(), "private func jerkgramPersistChangedSettings(")
        self.assertIn("GhostBaseGlassStyle.setProfilePlaybackSettings(", text)
        self.assertIn("glassEnabled: current.glassEnabled", text)
        self.assertIn("animatedBackgroundEnabled: current.profileAnimatedBackground", text)
        self.assertLess(text.index("setProfilePlaybackSettings("), text.index("JerkgramSettingsCommitQueue.enqueue"))
        self.assertIn("GhostBaseKey.glassEnabled,", text)
        self.assertIn("GhostBaseKey.profileAnimatedBackground,", text)
        self.assertLess(text.index("value.write(to: defaults, key: key)"), text.rindex("setProfilePlaybackSettings("))

    def test_runtime_setter_has_no_defaults_or_workers(self):
        text = (SOURCE / GLASS).read_text()
        self.assertIn("public static func setProfilePlaybackSettings(", text)
        setter = block(text, "public static func setProfilePlaybackSettings(")
        self.assertIn("self.enabledValue = glassEnabled", setter)
        self.assertIn("self.profileAnimatedValue = animatedBackgroundEnabled", setter)
        self.assertIn("self.preferenceGeneration &+= 1", setter)
        for token in ("UserDefaults", "DispatchQueue", "addObserver", "Timer("):
            self.assertNotIn(token, setter)

    def test_frozen_import_and_account_hooks_reload_snapshot(self):
        # The Display owner changes reload semantics; both existing callers
        # remain in the immutable, hash-checked Stable delta.
        patch = (ROOT / "patches/jg13-stable.product.patch").read_text()
        imported = block(patch, "private func jerkgramProjectImportedSettingsToActiveDefaults(")
        account = block(patch, "private func jerkgramBuild135ProjectAccountSettings(")
        for hook in (imported, account):
            self.assertIn("GhostBaseGlassStyle.reloadFromDefaults()", hook)
            self.assertIn("defer {", hook)

    def test_chain_applies_snapshot_after_p0_once(self):
        import ast
        tree = ast.parse((ROOT / "scripts/materialize_jg13.py").read_text())
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        calls = [n.value.func.id for n in main.body if isinstance(n, ast.Expr)
                 and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name)]
        self.assertEqual(calls.count("apply_preferences"), 1)
        self.assertLess(calls.index("apply_p0"), calls.index("apply_preferences"))

if __name__ == "__main__":
    unittest.main()
