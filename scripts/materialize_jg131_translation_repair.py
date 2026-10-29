"""Dependent, idempotent TASK A stage after the exact Build176 source.

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
PATCH = ROOT / 'patches/jg131-translation-repair.patch'
MANIFEST = ROOT / 'patches/jg131-translation-repair.sha256.json'
UPSTREAM = 'fb0e62ba8a147f0821da6aa63c09da7d79a10111'


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def manifest():
    values = json.loads(MANIFEST.read_text())
    if values['upstream_sha'] != UPSTREAM:
        raise RuntimeError('Translation repair upstream pin changed')
    if digest(PATCH.read_bytes()) != values['patch_sha256']:
        raise RuntimeError('Translation repair patch changed')
    if not values['owners']:
        raise RuntimeError('Translation repair has no owners')
    from jg131_final_stages import _parts
    for name in values['owners']:
        _parts(name)
    names = {line.split('\t', 2)[2] for line in subprocess.check_output(['git', 'apply', '--numstat', str(PATCH)], text=True).splitlines()}
    if names != set(values['owners']):
        raise RuntimeError('Translation repair patch scope changed')
    return values


def _actual(source, owners):
    return {n: digest((Path(source) / n).read_bytes()) if (Path(source) / n).exists() else None for n in owners}


def verify_repair(source):
    owners = manifest()['owners']
    actual = _actual(source, owners)
    for n, v in owners.items():
        if actual[n] != v['after_sha256']:
            raise RuntimeError('Translation repair output changed: ' + n)


def is_applied(source):
    owners = manifest()['owners']
    return all(v['after_sha256'] == a for v, a in zip(owners.values(), _actual(source, owners).values()))


def apply_repair(source):
    source = Path(source).resolve()
    owners = manifest()['owners']
    actual = _actual(source, owners)
    if all(actual[n] == v['after_sha256'] for n, v in owners.items()):
        return
    for n, v in owners.items():
        if actual[n] != v['before_sha256']:
            raise RuntimeError('Translation repair requires exact Build176 parent: ' + n)
    subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=source, check=True)
    subprocess.run(['git', 'apply', '--whitespace=nowarn', str(PATCH)], cwd=source, check=True)
    verify_repair(source)


@contextmanager
def parent_source_view(source):
    from jg131_final_stages import source_view
    source = Path(source).resolve()
    verify_repair(source)
    owners = manifest()['owners']
    with tempfile.TemporaryDirectory(prefix='jg-translation-parent-') as directory:
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
                raise RuntimeError('Translation parent restoration failed: ' + n)
            replacements[n] = data
        yield source_view(source, temp / 'source', replacements)


if __name__ == '__main__':
    apply_repair(ROOT / 'work/swiftgram-src')
