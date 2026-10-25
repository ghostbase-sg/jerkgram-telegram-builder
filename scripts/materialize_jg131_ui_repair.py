"""Restore stock shared cards/profile field masks and fix the Swift 27 weak capture."""
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / 'patches/jg131-ui-repair.patch'
MANIFEST = ROOT / 'patches/jg131-ui-repair.sha256.json'
CARD_OWNERS = (
    'submodules/TelegramUI/Components/ListSectionComponent/Sources/ListSectionComponent.swift',
    'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderMultiLineTextFieldNode.swift',
    'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderSingleLineTextFieldNode.swift',
)
DATA = 'submodules/SettingsUI/Sources/Jerkgram/JerkgramDataAndBackupController.swift'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read_manifest():
    m = json.loads(MANIFEST.read_text())
    config = json.loads((ROOT / 'jerkgram-migration.json').read_text())
    parent = json.loads((ROOT / 'patches/jg13-stable.product.sha256.json').read_text())
    if m['upstream_sha'] != config['upstream_new_sha'] or set(m['owners']) != {*CARD_OWNERS, DATA}:
        raise RuntimeError('UI repair scope or upstream changed')
    if digest(PATCH.read_bytes()) != m['patch_sha256']:
        raise RuntimeError('UI repair patch changed')
    for name, values in m['owners'].items():
        if values['before_sha256'] != parent[name]:
            raise RuntimeError('UI repair reviewed parent changed: ' + name)
    return m

def verify_ui_repair(source):
    for name, values in read_manifest()['owners'].items():
        if digest((Path(source) / name).read_bytes()) != values['after_sha256']:
            raise RuntimeError('UI repair final owner changed: ' + name)

def parent_bytes(name, data):
    values = read_manifest()['owners'][name]
    if digest(data) == values['before_sha256']:
        return data
    if digest(data) != values['after_sha256']:
        raise RuntimeError('UI repair owner changed: ' + name)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        target = root / name
        target.parent.mkdir(parents=True)
        target.write_bytes(data)
        subprocess.run(['git', 'init', '-q', str(root)], check=True)
        subprocess.run(['git', 'apply', '--reverse', '--include=' + name, str(PATCH)], cwd=root, check=True)
        result = target.read_bytes()
    if digest(result) != values['before_sha256']:
        raise RuntimeError('UI repair preceding bytes lost: ' + name)
    return result

def apply_ui_repair(source):
    source = Path(source).resolve()
    m = read_manifest()
    for name, values in m['owners'].items():
        if digest((source / name).read_bytes()) != values['before_sha256']:
            raise RuntimeError('UI repair requires exact preceding owner: ' + name)
    names = {line.split('\t', 2)[2] for line in subprocess.check_output(['git', 'apply', '--numstat', str(PATCH)], cwd=source, text=True).splitlines()}
    if names != set(m['owners']):
        raise RuntimeError('UI repair patch owner scope changed')
    subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=source, check=True)
    subprocess.run(['git', 'apply', str(PATCH)], cwd=source, check=True)
    verify_ui_repair(source)
