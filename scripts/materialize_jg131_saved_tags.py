"""Dependent, idempotent Local Saved Tags after exact Hub source.

All parents are checked before mutation. All immutable historical contracts use a
disposable reversed view, including removal of owners introduced by this stage.
"""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / 'patches/jg131-saved-tags.patch'
MANIFEST = ROOT / 'patches/jg131-saved-tags.sha256.json'
UPSTREAM = '24638bc69bd083981b178dd1e7f921eebbf7fc46'


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def manifest():
    values = json.loads(MANIFEST.read_text())
    if values['upstream_sha'] != UPSTREAM:
        raise RuntimeError('Saved Tags upstream pin changed')
    if digest(PATCH.read_bytes()) != values['patch_sha256']:
        raise RuntimeError('Saved Tags patch changed')
    if not values['owners']:
        raise RuntimeError('Saved Tags has no owners')
    from jg131_final_stages import _parts
    for name in [*values['owners'], *values.get('parent_owners', {})]:
        _parts(name)
    names = {line.split('\t', 2)[2] for line in subprocess.check_output(['git', 'apply', '--numstat', str(PATCH)], text=True).splitlines()}
    if names != set(values['owners']):
        raise RuntimeError('Saved Tags patch scope changed')
    return values


def _actual(source, owners):
    return {n: digest((Path(source) / n).read_bytes()) if (Path(source) / n).exists() else None for n in owners}


def _verify_parent_context(source, values):
    for name, expected in values.get('parent_owners', {}).items():
        if name not in values['owners'] and _actual(source, [name])[name] != expected:
            raise RuntimeError('Saved Tags requires exact Hub parent: ' + name)


def verify_tags(source):
    values = manifest()
    _verify_parent_context(source, values)
    owners = values['owners']
    actual = _actual(source, owners)
    for n, v in owners.items():
        if actual[n] != v['after_sha256']:
            raise RuntimeError('Saved Tags output changed: ' + n)


def is_applied(source):
    owners = manifest()['owners']
    return all(v['after_sha256'] == a for v, a in zip(owners.values(), _actual(source, owners).values()))


def is_present(source):
    """Recognize mixed/corrupt Tags before any historical fallback."""
    owners = manifest()['owners']
    actual = _actual(source, owners)
    return any((row['before_sha256'] is None and (Path(source) / n).exists()) or actual[n] == row['after_sha256'] for n, row in owners.items())


def apply_tags(source):
    from jg132_baseline import enabled, apply_stage
    if enabled() and Path(MANIFEST).resolve().parent == (ROOT / "patches").resolve():
        return apply_stage(source, 'jg131-saved-tags')
    source = Path(source).resolve()
    values = manifest()
    _verify_parent_context(source, values)
    owners = values['owners']
    actual = _actual(source, owners)
    if all(actual[n] == v['after_sha256'] for n, v in owners.items()):
        return
    for n, v in owners.items():
        if actual[n] != v['before_sha256']:
            raise RuntimeError('Saved Tags requires exact Hub parent: ' + n)
    subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=source, check=True)
    subprocess.run(['git', 'apply', '--whitespace=nowarn', str(PATCH)], cwd=source, check=True)
    verify_tags(source)


@contextmanager
def parent_source_view(source):
    from jg131_final_stages import source_view
    source = Path(source).resolve()
    verify_tags(source)
    owners = manifest()['owners']
    with tempfile.TemporaryDirectory(prefix='jg-saved-tags-parent-') as directory:
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
                raise RuntimeError('Saved Tags parent restoration failed: ' + n)
            replacements[n] = data
        yield source_view(source, temp / 'source', replacements)


if __name__ == '__main__':
    apply_tags(ROOT / 'work/swiftgram-src')
