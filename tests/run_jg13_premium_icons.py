"""Compile the actual App Icons capability and test its persisted toggle on macOS."""
import os
from pathlib import Path
import subprocess
import tempfile
from run_jg13_deleted_reply import block

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/swiftgram-src'))
owner = (SOURCE / 'submodules/SettingsUI/Sources/Themes/ThemeSettingsAppIconItem.swift').read_text()
helper = block(owner, 'enum JerkgramAppIconAccess')
fixture = '''
let key = JerkgramAppIconAccess.preferenceKey
let defaults = UserDefaults.standard
let previous = defaults.object(forKey: key)
defer {
    if let previous { defaults.set(previous, forKey: key) }
    else { defaults.removeObject(forKey: key) }
}
defaults.removeObject(forKey: key)
precondition(!JerkgramAppIconAccess.unlockEnabled)
for enabled in [false, true] {
    defaults.set(enabled, forKey: key)
    for iconPremium in [false, true] {
        for accountPremium in [false, true] {
            precondition(JerkgramAppIconAccess.isLocked(iconIsPremium: iconPremium, accountIsPremium: accountPremium) == (iconPremium && !accountPremium && !enabled))
        }
    }
}
precondition(JerkgramAppIconAccess.title(languageCode: "ru") == "Разблокировать Premium-иконки")
precondition(JerkgramAppIconAccess.title(languageCode: "en") == "Unlock Premium App Icons")
precondition(JerkgramAppIconAccess.title(languageCode: "fr") == "Unlock Premium App Icons")
print("PASS: actual App Icons capability, default off, persisted switch, all eight Premium combinations, RU/EN fallback")
'''
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / 'main.swift'
    path.write_text('import Foundation\n' + helper + '\n' + fixture)
    subprocess.run(['xcrun', 'swift', str(path)], check=True)
