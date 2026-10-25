"""Exact final excluded history stage, applied after the Build169 UI repair."""
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / 'patches/jg131-excluded-history.patch'
MANIFEST = ROOT / 'patches/jg131-excluded-history.sha256.json'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def manifest():
    m = json.loads(MANIFEST.read_text())
    if digest(PATCH.read_bytes()) != m['patch_sha256']:
        raise RuntimeError('Excluded history patch changed')
    return m

def verify_excluded_history(source):
    for n, v in manifest()['owners'].items():
        if digest((Path(source)/n).read_bytes()) != v['after_sha256']:
            raise RuntimeError('Excluded history output changed: ' + n)

def parent_bytes(name, data):
    values = manifest()['owners'].get(name)
    if values is None or (data is None and values['before_sha256'] is None) or (data is not None and digest(data) == values['before_sha256']):
        return data
    if data is None or digest(data) != values['after_sha256']:
        raise RuntimeError('Unknown excluded history owner: ' + name)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        subprocess.run(['git', 'apply', '--reverse', '--whitespace=nowarn', '--include=' + name, str(PATCH)], cwd=root, check=True)
        result = p.read_bytes() if p.exists() else None
    if (digest(result) if result is not None else None) != values['before_sha256']:
        raise RuntimeError('Excluded history parent restoration failed: ' + name)
    return result

def apply_excluded_history(source):
    source = Path(source).resolve()
    m = manifest()
    for n,v in m['owners'].items():
        path = source/n
        actual = digest(path.read_bytes()) if path.exists() else None
        if actual != v['before_sha256']:
            raise RuntimeError('Excluded history requires exact preceding owner: ' + n)
    names = {line.split('\t', 2)[2] for line in subprocess.check_output(['git', 'apply', '--numstat', str(PATCH)], cwd=source, text=True).splitlines()}
    if names != set(m['owners']):
        raise RuntimeError('Excluded history patch scope changed')
    subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=source, check=True)
    subprocess.run(['git', 'apply', str(PATCH)], cwd=source, check=True)
    verify_excluded_history(source)
