"""Remove the temporary capture controls from About, retaining internal diagnostics."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OWNER = 'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift'
MANIFEST = ROOT / 'patches/jg13-release-ui.sha256.json'
ANCHOR = '            .info(3, strings.anonymousAnalyticsDescription),\n'
def read_manifest():
    m = json.loads(MANIFEST.read_text())
    parent = json.loads((ROOT / 'patches/jg13-expanded-diagnostics.sha256.json').read_text())
    config = json.loads((ROOT / 'jerkgram-migration.json').read_text())
    if m['owner'] != OWNER or m['upstream_sha'] != config['upstream_new_sha'] or m['before_sha256'] != parent['owners'][OWNER]['after_sha256']:
        raise RuntimeError('Release About parent/pin changed')
    return m

def verify_release_ui(source):
    m = read_manifest()
    text = (Path(source) / OWNER).read_text()
    actual = hashlib.sha256(text.encode()).hexdigest()
    if hashlib.sha256(without_app_icons(text).encode()).hexdigest() != m['after_sha256']:
        raise RuntimeError('Release About final owner changed')
    return {OWNER: {'after_sha256': actual}}

def without_app_icons(text):
    from materialize_jg13_download_boost import without_boost
    text = without_boost(OWNER, text)
    from materialize_jg13_premium_icons import read_manifest as icons_manifest, restore_owner
    m = icons_manifest()
    if hashlib.sha256(text.encode()).hexdigest() == m['owners'][OWNER]['after_sha256']:
        return restore_owner(OWNER, text)
    return text

def apply_release_ui(source):
    m = read_manifest()
    target = Path(source) / OWNER
    text = target.read_text()
    if hashlib.sha256(text.encode()).hexdigest() != m['before_sha256'] or text.count(m['removed_about_block']) != 1:
        raise RuntimeError('Release About must follow the exact reviewed parent')
    updated = text.replace(m['removed_about_block'], '', 1)
    if hashlib.sha256(updated.encode()).hexdigest() != m['after_sha256']:
        raise RuntimeError('Release About transformation changed')
    target.write_text(updated)
    verify_release_ui(source)

def restore_parent(text):
    m = read_manifest()
    text = without_app_icons(text)
    if hashlib.sha256(text.encode()).hexdigest() != m['after_sha256'] or text.count(ANCHOR) != 1:
        raise RuntimeError('Release About restoration requires the exact final owner')
    restored = text.replace(ANCHOR, ANCHOR + m['removed_about_block'], 1)
    if hashlib.sha256(restored.encode()).hexdigest() != m['before_sha256']:
        raise RuntimeError('Release About restored parent changed')
    return restored
