"""Exact final profile metadata stage, applied after the Build169 UI repair."""
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / 'patches/jg131-profile-metadata.patch'
MANIFEST = ROOT / 'patches/jg131-profile-metadata.sha256.json'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def manifest():
    m = json.loads(MANIFEST.read_text())
    if digest(PATCH.read_bytes()) != m['patch_sha256']:
        raise RuntimeError('Profile metadata patch changed')
    return m

def verify_profile_metadata(source):
    for n, v in manifest()['owners'].items():
        if digest((Path(source)/n).read_bytes()) != v['after_sha256']:
            raise RuntimeError('Profile metadata output changed: ' + n)

def parent_bytes(name, data):
    values = manifest()['owners'].get(name)
    if values is None or digest(data) == values['before_sha256']:
        return data
    if digest(data) != values['after_sha256']:
        raise RuntimeError('Unknown profile metadata owner: ' + name)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        subprocess.run(['git', 'apply', '--reverse', '--whitespace=nowarn', '--include=' + name, str(PATCH)], cwd=root, check=True)
        result = p.read_bytes()
    if digest(result) != values['before_sha256']:
        raise RuntimeError('Profile metadata parent restoration failed: ' + name)
    return result

def apply_profile_metadata(source):
    source = Path(source).resolve()
    m = manifest()
    for n,v in m['owners'].items():
        if digest((source/n).read_bytes()) != v['before_sha256']:
            raise RuntimeError('Profile metadata requires exact preceding owner: ' + n)
    names = {line.split('\t', 2)[2] for line in subprocess.check_output(['git', 'apply', '--numstat', str(PATCH)], cwd=source, text=True).splitlines()}
    if names != set(m['owners']):
        raise RuntimeError('Profile metadata patch scope changed')
    subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=source, check=True)
    subprocess.run(['git', 'apply', str(PATCH)], cwd=source, check=True)
    verify_profile_metadata(source)
