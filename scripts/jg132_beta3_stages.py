"""Exact, source-native successors to the verified Telegram 13.2 baseline.

This module owns no preference store or runtime wrappers. Every selected parent
is checked before mutation; historical contracts consume temporary reverse views.
"""
from contextlib import contextmanager, ExitStack
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = '24638bc69bd083981b178dd1e7f921eebbf7fc46'
STAGES = ('beta3-bot-recovery', 'beta3-settings-ui', 'beta3-native-tags')


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def _path(name):
    p = PurePosixPath(name)
    if p.is_absolute() or not p.parts or any(v in ('.', '..', '.git') for v in p.parts) or '\\' in name or str(p) != name:
        raise ValueError('Unsafe source owner path: ' + name)
    return p


def manifest(stage):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', stage):
        raise ValueError('Unsafe stage name')
    values = json.loads((ROOT / 'patches' / (stage + '.sha256.json')).read_text())
    if values['upstream_sha'] != UPSTREAM:
        raise RuntimeError('Beta3 upstream pin changed: ' + stage)
    patch = ROOT / 'patches' / (stage + '.patch')
    if digest(patch.read_bytes()) != values['patch_sha256']:
        raise RuntimeError('Beta3 patch changed: ' + stage)
    owners = values['owners']
    if not owners:
        raise RuntimeError('Beta3 stage has no owners: ' + stage)
    for name in [*owners, *values.get('parent_owners', {})]:
        _path(name)
    for row in owners.values():
        if row['before_sha256'] == row['after_sha256']:
            raise RuntimeError('Beta3 owner has no delta: ' + stage)
    names = {line.split('\t', 2)[2] for line in subprocess.check_output(['git', 'apply', '--numstat', str(patch)], text=True).splitlines()}
    if names != set(owners):
        raise RuntimeError('Beta3 patch scope changed: ' + stage)
    return values


def _actual(source, names):
    result = {}
    for name in names:
        path = Path(source) / name
        result[name] = digest(path.read_bytes()) if path.is_file() else None
    return result


def _guard(source, values):
    for name, expected in values.get('parent_owners', {}).items():
        if name not in values['owners'] and _actual(source, [name])[name] != expected:
            raise RuntimeError('Beta3 protected parent changed: ' + name)


def verify_stage(source, stage):
    values = manifest(stage)
    _guard(source, values)
    actual = _actual(source, values['owners'])
    for name, row in values['owners'].items():
        if actual[name] != row['after_sha256']:
            raise RuntimeError('Beta3 output changed: ' + stage + ':' + name)


def apply_stage(source, stage):
    source = Path(source).resolve()
    values = manifest(stage)
    _guard(source, values)
    actual = _actual(source, values['owners'])
    if all(actual[n] == v['after_sha256'] for n, v in values['owners'].items()):
        return
    for name, row in values['owners'].items():
        if actual[name] != row['before_sha256']:
            raise RuntimeError('Beta3 requires exact stage parent: ' + stage + ':' + name)
    patch = ROOT / 'patches' / (stage + '.patch')
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=source, check=True)
    subprocess.run(['git', 'apply', '--whitespace=nowarn', str(patch)], cwd=source, check=True)
    verify_stage(source, stage)


@contextmanager
def parent_source_view(source, stage):
    from jg131_final_stages import source_view
    source = Path(source).resolve()
    verify_stage(source, stage)
    values = manifest(stage)
    with tempfile.TemporaryDirectory(prefix='jg-beta3-parent-') as directory:
        root = Path(directory)
        reverse = root / 'reverse'
        reverse.mkdir()
        for name in values['owners']:
            p = reverse / name
            q = source / name
            if q.is_file():
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(q.read_bytes())
        subprocess.run(['git', 'apply', '--reverse', '--whitespace=nowarn', str(ROOT / 'patches' / (stage + '.patch'))], cwd=reverse, check=True)
        replacements = {}
        for name, row in values['owners'].items():
            p = reverse / name
            data = p.read_bytes() if p.is_file() else None
            if digest(data) != row['before_sha256']:
                raise RuntimeError('Beta3 reverse restoration failed: ' + name)
            replacements[name] = data
        yield source_view(source, root / 'source', replacements)


@contextmanager
def baseline_source_view(source):
    with ExitStack() as stack:
        view = Path(source).resolve()
        for stage in reversed(STAGES):
            view = stack.enter_context(parent_source_view(view, stage))
        yield view


def is_present(source):
    """A final-stage fragment routes corruption through this chain's verifier."""
    values = manifest(STAGES[-1])
    actual = _actual(source, values['owners'])
    return any(row['after_sha256'] is not None and actual[name] == row['after_sha256'] for name, row in values['owners'].items())


def apply_all(source):
    if is_present(source):
        with baseline_source_view(source):
            pass
        return
    for stage in STAGES:
        apply_stage(source, stage)


def verify_source(source):
    """Prove all successors and the restored current upstream baseline."""
    source = Path(source).resolve()
    from jg132_baseline import verify_source as verify_baseline
    with baseline_source_view(source) as before:
        if verify_baseline(before) != 32:
            raise RuntimeError('Beta3 requires all 32 accepted upstream stages')
    config = json.loads((ROOT / 'jerkgram-migration.json').read_text())
    if config['upstream_new_sha'] != UPSTREAM:
        raise RuntimeError('Beta3 configuration upstream mismatch')
    identity = (source / 'submodules/TelegramPresentationData/Sources/JerkgramStrings.swift').read_text()
    for key, value in [('displayVersion', config['product_display_version']), ('technicalVersion', config['product_technical_version']), ('build', str(config['build_number'])), ('telegramBase', config['upstream_new_version'])]:
        if f'public static let {key} = "{value}"' not in identity:
            raise RuntimeError('Beta3 identity mismatch: ' + key)
    if f'<string>{config["bundle_short_version"]}</string>' not in (source / 'Telegram/BUILD').read_text():
        raise RuntimeError('Beta3 bundle version mismatch')
    print('Beta3 source successors and restored32-stage13.2 baseline VERIFIED; native/app/device separate', flush=True)
