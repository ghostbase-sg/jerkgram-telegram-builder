"""Reversible successors to GREEN Build180; accepted historical patches stay frozen."""
from contextlib import contextmanager, ExitStack
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def stages():
    return tuple(json.loads((ROOT / 'jerkgram-migration.json').read_text()).get('post180_stages', []))


@contextmanager
def _restored(source):
    from jg132_beta3_stages import manifest, parent_source_view, digest
    present = []
    with ExitStack() as stack:
        view = Path(source).resolve()
        for stage in reversed(stages()):
            rows = manifest(stage)['owners']
            if any(row['after_sha256'] is not None and (view / name).is_file() and digest((view / name).read_bytes()) == row['after_sha256'] for name, row in rows.items()):
                view = stack.enter_context(parent_source_view(view, stage))
                present.insert(0, stage)
        if tuple(present) != stages()[:len(present)]:
            raise RuntimeError('Post180 requires an exact contiguous stage prefix')
        yield view, len(present)


@contextmanager
def build180_source_view(source):
    with _restored(source) as (view, _):
        yield view


def is_present(source):
    with _restored(source) as (_, count):
        return count != 0


def apply_all(source):
    from jg132_beta3_stages import apply_stage, verify_source as verify_build180, manifest
    from jg131_final_stages import source_view
    source = Path(source).resolve()
    with _restored(source) as (before, count):
        verify_build180(before)
    # Validate every remaining mutation on private owner copies before writing
    # anything to the real source, including when resuming an exact prefix.
    if count == len(stages()):
        verify_source(source)
        return
    names = {name for stage in stages() for name in manifest(stage)['owners']}
    replacements = {name: (source / name).read_bytes() if (source / name).is_file() else None for name in names}
    with tempfile.TemporaryDirectory(prefix='post180-preflight-') as directory:
        trial = source_view(source, Path(directory) / 'source', replacements)
        for stage in stages()[count:]:
            apply_stage(trial, stage)
        verify_source(trial)
    for stage in stages()[count:]:
        apply_stage(source, stage)
    verify_source(source)


def verify_source(source):
    from jg132_beta3_stages import verify_source as verify_build180
    with _restored(source) as (before, count):
        if count != len(stages()):
            raise RuntimeError('Post180 successor chain incomplete')
        verify_build180(before)
    config = json.loads((ROOT / 'jerkgram-migration.json').read_text())
    identity = (Path(source) / 'submodules/TelegramPresentationData/Sources/JerkgramStrings.swift').read_text()
    for key, value in [('displayVersion', config['product_display_version']), ('technicalVersion', config['product_technical_version']), ('build', str(config['build_number'])), ('telegramBase', config['upstream_new_version'])]:
        if f'public static let {key} = "{value}"' not in identity:
            raise RuntimeError('Post180 release identity mismatch: ' + key)
    print('Post180 exact successors and restored GREEN Build180 VERIFIED; device runtime separate', flush=True)
