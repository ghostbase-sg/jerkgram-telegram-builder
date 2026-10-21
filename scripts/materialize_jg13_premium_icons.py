"""Three-owner App Icons capability after the reviewed Build163 About delta."""
import hashlib
import json
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'patches/jg13-premium-icons.sha256.json'
ITEM = 'submodules/SettingsUI/Sources/Themes/ThemeSettingsAppIconItem.swift'
THEME = 'submodules/SettingsUI/Sources/Themes/ThemeSettingsController.swift'
SETTINGS = 'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift'
BUILD = 'Telegram/BUILD'
APP = 'submodules/TelegramUI/Sources/AppDelegate.swift'
HELPER = '''// Jerkgram capability: App Icons only; never changes account Premium status.
enum JerkgramAppIconAccess {
    static let preferenceKey = "jerkgram.LocalPremium.AppIcons"

    static var unlockEnabled: Bool {
        return UserDefaults.standard.bool(forKey: self.preferenceKey)
    }

    static func isLocked(iconIsPremium: Bool, accountIsPremium: Bool) -> Bool {
        return iconIsPremium && !accountIsPremium && !self.unlockEnabled
    }

    static func title(languageCode: String) -> String {
        return languageCode == "ru" ? "Разблокировать Premium-иконки" : "Unlock Premium App Icons"
    }
}

'''
REPLACEMENTS = {
    ITEM: [
        ('private func generateBorderImage(', HELPER + 'private func generateBorderImage('),
        ('locked: !item.isPremium && icon.isPremium', 'locked: JerkgramAppIconAccess.isLocked(iconIsPremium: icon.isPremium, accountIsPremium: item.isPremium)'),
    ],
    THEME: [
        ('if premiumConfiguration.isPremiumDisabled || context.account.testingEnvironment {', 'if !JerkgramAppIconAccess.unlockEnabled && (premiumConfiguration.isPremiumDisabled || context.account.testingEnvironment) {'),
        ('if icon.isPremium && !isPremium {', 'if JerkgramAppIconAccess.isLocked(iconIsPremium: icon.isPremium, accountIsPremium: isPremium) {'),
    ],
    SETTINGS: [
        ('            .info(1, strings.hidePhoneHint)', '            .toggle(1, 8, JerkgramAppIconAccess.preferenceKey, JerkgramAppIconAccess.title(languageCode: strings.languageCode), JerkgramAppIconAccess.unlockEnabled),\n            .info(1, strings.hidePhoneHint)'),
        ('            case GhostBaseKey.profileEnabled:', '            case JerkgramAppIconAccess.preferenceKey:\n                UserDefaults.standard.set(value, forKey: JerkgramAppIconAccess.preferenceKey)\n            case GhostBaseKey.profileEnabled:'),
    ],
}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read_manifest():
    m = json.loads(MANIFEST.read_text())
    config = json.loads((ROOT / 'jerkgram-migration.json').read_text())
    stable = json.loads((ROOT / 'patches/jg13-stable.product.sha256.json').read_text())
    release = json.loads((ROOT / 'patches/jg13-release-ui.sha256.json').read_text())
    if m['upstream_sha'] != config['upstream_new_sha'] or set(m['owners']) != set(REPLACEMENTS):
        raise RuntimeError('App Icons scope/pin changed')
    for name, values in m['owners'].items():
        expected = release['after_sha256'] if name == SETTINGS else stable[name]
        if values['before_sha256'] != expected:
            raise RuntimeError('App Icons parent changed: ' + name)
    if APP not in m['locks'] or BUILD not in m['locks']:
        raise RuntimeError('App Icons branding/metadata locks missing')
    return m

def transform(name, text):
    for before, after in REPLACEMENTS[name]:
        if text.count(before) != 1:
            raise RuntimeError('App Icons replacement must have exactly one owner: ' + name)
        text = text.replace(before, after, 1)
    return text

def canonical_lock(name, data):
    if name == BUILD:
        # configure_jg13 substitutes only this generated bundle version.
        version = json.loads((ROOT / 'jerkgram-migration.json').read_text())['bundle_short_version']
        data = data.replace(('<key>CFBundleShortVersionString</key>\n    <string>' + version + '</string>').encode(), b'<key>CFBundleShortVersionString</key>\n    <string>$$version</string>')
    return data

def check_locks(source, manifest):
    for name, expected in manifest['locks'].items():
        if digest(canonical_lock(name, (Path(source) / name).read_bytes())) != expected:
            raise RuntimeError('App Icons resource/global status lock changed: ' + name)

def restore_owner(name, text):
    m = read_manifest()
    if digest(text.encode()) != m['owners'][name]['after_sha256']:
        raise RuntimeError('App Icons restoration requires exact final owner: ' + name)
    for before, after in reversed(REPLACEMENTS[name]):
        if text.count(after) != 1:
            raise RuntimeError('App Icons reverse replacement changed: ' + name)
        text = text.replace(after, before, 1)
    if digest(text.encode()) != m['owners'][name]['before_sha256']:
        raise RuntimeError('App Icons original owner was not preserved: ' + name)
    return text

def verify_icons(source):
    m = read_manifest()
    for name in m['owners']:
        restore_owner(name, (Path(source) / name).read_text())
    check_locks(source, m)
    config_tree = ast.parse((ROOT / 'scripts/configure_jg13.py').read_text())
    calls = [node for node in ast.walk(config_tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'apply_icons']
    if len(calls) != 1 or len(calls[0].args) != 1 or not isinstance(calls[0].args[0], ast.Name) or calls[0].args[0].id != 'SOURCE':
        raise RuntimeError('App Icons canonical configure call missing or duplicated')
    verifier = ast.parse((ROOT / 'scripts/verify_jg13_source.py').read_text())
    if not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'verify_icons' for node in ast.walk(verifier)):
        raise RuntimeError('App Icons canonical source verification missing')
    return {name: {'after_sha256': values['after_sha256']} for name, values in m['owners'].items()}

def apply_icons(source):
    source = Path(source)
    m = read_manifest()
    check_locks(source, m)
    outputs = {}
    for name, values in m['owners'].items():
        text = (source / name).read_text()
        if digest(text.encode()) != values['before_sha256']:
            raise RuntimeError('App Icons must follow exact parent; repeat refused: ' + name)
        updated = transform(name, text)
        if digest(updated.encode()) != values['after_sha256']:
            raise RuntimeError('App Icons reviewed output changed: ' + name)
        outputs[name] = updated
    for name, text in outputs.items():
        (source / name).write_text(text)
    verify_icons(source)
    print('App Icons: exact three-owner delta and resource/global status locks VERIFIED; NOT RUNTIME TESTED')
