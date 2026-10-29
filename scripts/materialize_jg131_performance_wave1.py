"""Exact dependent Performance Remediation Wave 1, after every Build175 stage."""
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / 'patches/jg131-performance-wave1.patch'
MANIFEST = ROOT / 'patches/jg131-performance-wave1.sha256.json'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def manifest():
    m = json.loads(MANIFEST.read_text())
    if digest(PATCH.read_bytes()) != m['patch_sha256']:
        raise RuntimeError('Performance wave1 patch changed')
    return m

def verify_wave1(source):
    for n, v in manifest()['owners'].items():
        if digest((Path(source)/n).read_bytes()) != v['after_sha256']:
            raise RuntimeError('Performance wave1 output changed: ' + n)

def parent_bytes(name, data):
    values = manifest()['owners'].get(name)
    if values is None or digest(data) == values['before_sha256']:
        return data
    if digest(data) != values['after_sha256']:
        raise RuntimeError('Unknown performance wave1 owner: ' + name)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        subprocess.run(['git', 'apply', '--reverse', '--whitespace=nowarn', '--include=' + name, str(PATCH)], cwd=root, check=True)
        result = p.read_bytes()
    if digest(result) != values['before_sha256']:
        raise RuntimeError('Performance wave1 parent restoration failed: ' + name)
    return result

def apply_wave1(source):
    source = Path(source).resolve()
    m = manifest()
    for n,v in m['owners'].items():
        if digest((source/n).read_bytes()) != v['before_sha256']:
            raise RuntimeError('Performance wave1 requires exact preceding owner: ' + n)
    names = {line.split('\t', 2)[2] for line in subprocess.check_output(['git', 'apply', '--numstat', str(PATCH)], cwd=source, text=True).splitlines()}
    if names != set(m['owners']):
        raise RuntimeError('Performance wave1 patch scope changed')
    subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=source, check=True)
    subprocess.run(['git', 'apply', str(PATCH)], cwd=source, check=True)
    verify_wave1(source)


def is_applied(source):
    name, values = next(iter(manifest()['owners'].items()))
    path = Path(source)/name
    return path.exists() and digest(path.read_bytes()) == values['after_sha256']

from contextlib import contextmanager
@contextmanager
def baseline_source_view(source):
    from jg131_final_stages import source_view
    verify_wave1(source)
    replacements = {name: parent_bytes(name, (Path(source)/name).read_bytes()) for name in manifest()['owners']}
    with tempfile.TemporaryDirectory(prefix='jg176-baseline-') as directory:
        yield source_view(source, Path(directory)/'source', replacements)

if __name__ == '__main__':
    apply_wave1(ROOT/'work/swiftgram-src')
