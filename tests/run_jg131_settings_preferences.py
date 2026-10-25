"""Extend the real snapshot-owner fixture with settings and account projection checks."""
from pathlib import Path
import importlib.util
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'tests/run_jg13_profile_preferences.py'
spec=importlib.util.spec_from_file_location('previous_preferences',p)
previous=importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
s=previous.fixture()
s=s.replace('let warmReads = defaults.reads','precondition(!GhostBaseGlassStyle.settingsTranslucencyEnabled)\nlet warmReads = defaults.reads',1)
s=s.replace('for _ in 0..<10000 {','for _ in 0..<10000 {\n    _ = GhostBaseGlassStyle.settingsTranslucencyEnabled')
s=s.replace('func set(_ value: Bool, forKey key: String) { writes += 1; values[key] = value }','func set(_ value: Any, forKey key: String) { writes += 1; values[key] = value as? Bool }\n    func removeObject(forKey key: String) { values.removeValue(forKey: key) }')
projection=previous.block((previous.SOURCE/'submodules/TelegramUI/Sources/SharedAccountContext.swift').read_text(),'private func jerkgramBuild135ProjectAccountSettings(')
projection=projection.replace('UserDefaults.standard','CountedDefaults.standard').replace('UserDefaults(suiteName:', 'CountedDefaults(suiteName:')
s=s.replace('static let standard = CountedDefaults()', 'static let standard = CountedDefaults()\n    init() {}\n    convenience init?(suiteName: String) { self.init() }')
s+='''
enum JerkgramHotSettings { static func invalidate() {} }
enum JerkgramActivityGhostRuntime { static func invalidate() {} }
enum JerkgramBlockedReactionPolicy { static func notifySettingsChanged() {} }
enum Queue { static func mainQueue() -> DispatchQueue { return .main } }
'''+projection+'''
GhostBaseGlassStyle.setSettingsTranslucencyEnabled(true)
precondition(GhostBaseGlassStyle.settingsTranslucencyEnabled)
defaults.values["jerkgram.Settings.Translucency"] = false
defaults.afterReadKey = "jerkgram.Settings.Translucency"
defaults.afterRead = { GhostBaseGlassStyle.setSettingsTranslucencyEnabled(true) }
GhostBaseGlassStyle.reloadFromDefaults()
precondition(GhostBaseGlassStyle.settingsTranslucencyEnabled, "stale refresh overwrote live settings toggle")
defaults.afterReadKey = nil
defaults.values["jerkgram.account.10.setting.jerkgram.Settings.Translucency"] = true
defaults.values["jerkgram.account.20.setting.jerkgram.Settings.Translucency"] = false
jerkgramBuild135ProjectAccountSettings(accountPeerId: 10)
precondition(GhostBaseGlassStyle.settingsTranslucencyEnabled)
jerkgramBuild135ProjectAccountSettings(accountPeerId: 20)
precondition(!GhostBaseGlassStyle.settingsTranslucencyEnabled)
jerkgramBuild135ProjectAccountSettings(accountPeerId: 30)
precondition(!GhostBaseGlassStyle.settingsTranslucencyEnabled)
precondition(defaults.values["jerkgram.Settings.Translucency"] == nil)
print("settings snapshot/account projection PASS")
'''
with tempfile.TemporaryDirectory(prefix='jg170-settings-') as d:
    path=Path(d)/'main.swift';path.write_text(s)
    subprocess.run(['xcrun','swift',str(path)],check=True)
