"""Exact successors to GREEN181; frozen predecessor provenance is mandatory."""
from contextlib import contextmanager, ExitStack
import json
from pathlib import Path
import tempfile
ROOT=Path(__file__).resolve().parents[1]

def stages():
    return tuple(json.loads((ROOT/'jerkgram-migration.json').read_text()).get('post181_stages', []))

@contextmanager
def _restored(source):
    from jg132_beta3_stages import manifest,parent_source_view,digest
    present=[]
    with ExitStack() as stack:
        view=Path(source).resolve()
        for stage in reversed(stages()):
            rows=manifest(stage)['owners']
            if any(row['after_sha256'] is not None and (view/name).is_file() and digest((view/name).read_bytes())==row['after_sha256'] for name,row in rows.items()):
                view=stack.enter_context(parent_source_view(view,stage));present.insert(0,stage)
        if tuple(present)!=stages()[:len(present)]:raise RuntimeError('Post181 requires exact contiguous stage prefix')
        yield view,len(present)

@contextmanager
def build181_source_view(source):
    with _restored(source) as (view,_):yield view

@contextmanager
def stage_source_view(source,stage):
    """Expose an exact historical boundary without mutating current source."""
    from jg132_beta3_stages import parent_source_view,verify_stage
    if stage not in stages():raise RuntimeError('Unknown Post181 stage')
    with ExitStack() as stack:
        view=Path(source).resolve()
        for later in reversed(stages()[stages().index(stage)+1:]):
            view=stack.enter_context(parent_source_view(view,later))
        verify_stage(view,stage)
        yield view

def apply_all(source):
    from jg132_beta3_stages import apply_stage,manifest
    from jg132_post180 import verify_source as verify_green
    from jg131_final_stages import source_view
    source=Path(source).resolve()
    with _restored(source) as (before,count):verify_green(before)
    if count==len(stages()):verify_source(source);return
    names={name for stage in stages() for name in manifest(stage)['owners']}
    replacements={name:(source/name).read_bytes() if (source/name).is_file() else None for name in names}
    with tempfile.TemporaryDirectory(prefix='post181-preflight-') as directory:
        trial=source_view(source,Path(directory)/'source',replacements)
        for stage in stages()[count:]:apply_stage(trial,stage)
        verify_source(trial)
    for stage in stages()[count:]:apply_stage(source,stage)
    verify_source(source)

def verify_source(source):
    from jg132_post180 import verify_source as verify_green
    with _restored(source) as (before,count):
        if count!=len(stages()):raise RuntimeError('Post181 chain incomplete')
        verify_green(before)
    config=json.loads((ROOT/'jerkgram-migration.json').read_text())
    identity=(Path(source)/'submodules/TelegramPresentationData/Sources/JerkgramStrings.swift').read_text()
    for key,value in [('displayVersion',config['product_display_version']),('technicalVersion',config['product_technical_version']),('build',str(config['build_number'])),('telegramBase',config['upstream_new_version'])]:
        if f'public static let {key} = "{value}"' not in identity:raise RuntimeError('Post181 identity mismatch: '+key)
    print('Post181 exact successor chain and restored GREEN181 VERIFIED; device runtime separate',flush=True)
