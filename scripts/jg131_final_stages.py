"""Final Build170 stages and a disposable preceding-source view for old hash gates.

The view links unchanged inputs for reading and copies only changed owners. It
must only be handed to read-only verifiers, never to materializers or builders.
"""
from contextlib import contextmanager
from pathlib import Path
import tempfile
import json
import materialize_jg131_profile_polish as polish
import materialize_jg131_profile_metadata as metadata
import materialize_jg131_excluded_history as excluded
import materialize_jg131_settings_transparency as settings
import materialize_jg131_performance_followup as performance

STAGES = (
    (polish, polish.apply_profile_polish, polish.verify_profile_polish),
    (metadata, metadata.apply_profile_metadata, metadata.verify_profile_metadata),
    (excluded, excluded.apply_excluded_history, excluded.verify_excluded_history),
    (settings, settings.apply_settings_transparency, settings.verify_settings_transparency),
    (performance, performance.apply_performance_followup, performance.verify_performance_followup),
)

def _check_pins():
    config = json.loads((Path(__file__).resolve().parents[1]/'jerkgram-migration.json').read_text())
    for stage, _, _ in STAGES:
        if stage.manifest()['upstream_sha'] != config['upstream_new_sha']:
            raise RuntimeError('Final-stage upstream pin changed')

def apply_final_stages(source):
    _check_pins()
    # Validate every independent parent before the first stage mutates a file.
    seen = set()
    for stage, _, _ in STAGES:
        for name, values in stage.manifest()['owners'].items():
            _parts(name)
            if name in seen: raise RuntimeError('Overlapping final-stage owner: ' + name)
            seen.add(name)
            p = Path(source)/name
            actual = stage.digest(p.read_bytes()) if p.exists() else None
            if actual != values['before_sha256']:
                raise RuntimeError('Unexpected final-stage parent: ' + name)
    for _, apply, _ in STAGES: apply(source)

def verify_final_stages(source):
    _check_pins()
    for _, _, verify in STAGES: verify(source)

def _parts(name):
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError('Unsafe source owner: ' + name)
    return path.parts

def source_view(source, target, replacements):
    source, target = Path(source).resolve(), Path(target)
    if target.exists(): raise ValueError('Source view target must not exist')
    tree = {}
    for name, data in replacements.items():
        parts = _parts(name)
        branch = tree
        for part in parts[:-1]:
            branch = branch.setdefault(part, {})
            if not isinstance(branch, dict): raise ValueError('Overlapping source owner')
        if parts[-1] in branch: raise ValueError('Overlapping source owner')
        if data is not None and not isinstance(data, bytes): raise TypeError('Expected source bytes')
        branch[parts[-1]] = data
    def build(original, destination, branch):
        destination.mkdir()
        children = {p.name: p for p in original.iterdir()} if original.exists() else {}
        for name in children.keys() | branch.keys():
            if name not in branch:
                p = children[name]
                (destination/name).symlink_to(p, target_is_directory=p.is_dir())
            elif isinstance(branch[name], dict):
                build(original/name, destination/name, branch[name])
            elif branch[name] is not None:
                (destination/name).write_bytes(branch[name])
    build(source, target, tree)
    return target

@contextmanager
def preceding_source_view(source):
    verify_final_stages(source)
    preceding = {}
    for stage, _, _ in STAGES:
        for name in stage.manifest()['owners']:
            if name in preceding: raise RuntimeError('Overlapping final-stage owner: ' + name)
            preceding[name] = stage.parent_bytes(name, (Path(source)/name).read_bytes())
    with tempfile.TemporaryDirectory(prefix='jg170-preceding-') as directory:
        yield source_view(source, Path(directory)/'source', preceding)
