"""Use the public TelegramCore peer-ID alias after upstream removed the UI Postbox import."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'patches/jg131-ui-type-compat.sha256.json'
REPLACEMENTS = (
    ('private func ghostBaseV10NSaveSourcePeerId(_ peerId: PeerId, source: String)', 'private func ghostBaseV10NSaveSourcePeerId(_ peerId: EnginePeer.Id, source: String)'),
    ('    peerId: PeerId?,\n    stockCount: Int', '    peerId: EnginePeer.Id?,\n    stockCount: Int'),
)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def manifest():
    m = json.loads(MANIFEST.read_text())
    config = json.loads((ROOT / 'jerkgram-migration.json').read_text())
    parent = json.loads((ROOT / 'patches/jg13-stable.product.sha256.json').read_text())
    if m['upstream_sha'] != config['upstream_new_sha'] or m['before_sha256'] != parent[m['owner']]:
        raise RuntimeError('UI peer-ID compatibility parent/pin changed')
    return m

def verify_ui_types(source):
    m = manifest()
    if digest((Path(source) / m['owner']).read_bytes()) != m['after_sha256']:
        raise RuntimeError('UI peer-ID compatibility final owner changed')

def apply_ui_types(source):
    m = manifest()
    target = Path(source) / m['owner']
    before = target.read_bytes()
    if digest(before) != m['before_sha256']:
        raise RuntimeError('UI peer-ID compatibility requires exact preceding owner')
    text = before.decode()
    for old, new in REPLACEMENTS:
        if text.count(old) != 1:
            raise RuntimeError('UI peer-ID compatibility anchor changed')
        text = text.replace(old, new, 1)
    if digest(text.encode()) != m['after_sha256']:
        raise RuntimeError('UI peer-ID compatibility output changed')
    target.write_text(text)
    verify_ui_types(source)
