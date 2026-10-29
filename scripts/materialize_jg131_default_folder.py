"""Dependent, idempotent TASK B stage after the exact TASK A source.

All parents are checked before mutation. Previous immutable contracts use a
disposable reversed view, including removal of owners introduced by this stage.
"""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / 'patches/jg131-default-folder.patch'
MANIFEST = ROOT / 'patches/jg131-default-folder.sha256.json'
UPSTREAM = 'fb0e62ba8a147f0821da6aa63c09da7d79a10111'


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def manifest():
    values = json.loads(MANIFEST.read_text())
    if values['upstream_sha'] != UPSTREAM:
        raise RuntimeError('Default folder upstream pin changed')
    if digest(PATCH.read_bytes()) != values['patch_sha256']:
        raise RuntimeError('Default folder patch changed')
    if not values['owners']:
        raise RuntimeError('Default folder has no owners')
    from jg131_final_stages import _parts
    for name in values['owners']:
        _parts(name)
    names = {line.split('\t', 2)[2] for line in subprocess.check_output(['git', 'apply', '--numstat', str(PATCH)], text=True).splitlines()}
    if names != set(values['owners']):
        raise RuntimeError('Default folder patch scope changed')
    return values


def _actual(source, owners):
    return {n: digest((Path(source) / n).read_bytes()) if (Path(source) / n).exists() else None for n in owners}


def verify_folder(source):
    owners = manifest()['owners']
    actual = _actual(source, owners)
    for n, v in owners.items():
        if actual[n] != v['after_sha256']:
            raise RuntimeError('Default folder output changed: ' + n)


def is_applied(source):
    owners = manifest()['owners']
    return all(v['after_sha256'] == a for v, a in zip(owners.values(), _actual(source, owners).values()))


def apply_folder(source):
    source = Path(source).resolve()
    owners = manifest()['owners']
    actual = _actual(source, owners)
    if all(actual[n] == v['after_sha256'] for n, v in owners.items()):
        return
    for n, v in owners.items():
        if actual[n] != v['before_sha256']:
            raise RuntimeError('Default folder requires exact TASK A parent: ' + n)
    subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=source, check=True)
    subprocess.run(['git', 'apply', '--whitespace=nowarn', str(PATCH)], cwd=source, check=True)
    verify_folder(source)


@contextmanager
def parent_source_view(source):
    from jg131_final_stages import source_view
    source = Path(source).resolve()
    verify_folder(source)
    owners = manifest()['owners']
    with tempfile.TemporaryDirectory(prefix='jg-folder-parent-') as directory:
        temp = Path(directory)
        reverse = temp / 'reverse'
        reverse.mkdir()
        for n in owners:
            p = reverse / n
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes((source / n).read_bytes())
        subprocess.run(['git', 'apply', '--reverse', '--whitespace=nowarn', str(PATCH)], cwd=reverse, check=True)
        replacements = {}
        for n, v in owners.items():
            p = reverse / n
            data = p.read_bytes() if p.exists() else None
            if digest(data) != v['before_sha256']:
                raise RuntimeError('Default folder parent restoration failed: ' + n)
            replacements[n] = data
        yield source_view(source, temp / 'source', replacements)


if __name__ == '__main__':
    apply_folder(ROOT / 'work/swiftgram-src')
