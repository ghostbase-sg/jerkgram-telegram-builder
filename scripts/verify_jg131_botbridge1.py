"""BOT source guards and portable accepted Task1 source view.

The 16 whole modern owners are checked on the exact reversed C parent. The
final outputs remain pinned by the terminal manifest, including every permitted
observer/lifecycle edit. Native fixtures execute separately in the runner.
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from materialize_jg131_botbridge1 import verify_botbridge, parent_source_view, manifest

ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT/'tests/fixtures/botbridge1/provenance'
KEY = re.compile(rb'0x4a470002\b|\b'+str(0x4A470002).encode()+rb'\b', re.IGNORECASE)


def verify_preference_key_available(source):
    """Scan all files in the supplied product tree, following restored-view links."""
    count = 0
    visited = set()
    def fail(error):
        raise error
    for directory, dirs, files in os.walk(source, followlinks=True, onerror=fail):
        real = Path(directory).resolve(strict=True)
        if real in visited:
            # An alias or cycle contributes no new source bytes.
            dirs.clear()
            continue
        visited.add(real)
        dirs[:] = [name for name in dirs if name != '.git']
        for name in files:
            if name == '.git':
                continue
            path = Path(directory)/name
            if not path.is_file():
                raise RuntimeError('Unreadable product input: '+str(path))
            # Bound memory even when generated source includes large assets.
            with path.open('rb') as stream:
                tail = b''
                while chunk := stream.read(1024*1024):
                    data = tail+chunk
                    if KEY.search(data):
                        raise RuntimeError('BOT preference key collision: '+str(path.relative_to(source)))
                    tail = data[-32:]
            count += 1
    return count


def verify_provenance_files(root, expected):
    from jg131_final_stages import _parts
    for name, digest in expected.items():
        _parts(name)
        if hashlib.sha256((Path(root)/name).read_bytes()).hexdigest() != digest:
            raise RuntimeError('BOT portable provenance changed: '+name)


def verify_full_checkout(source, upstream):
    source=Path(source)
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
    tracked=subprocess.check_output(['git','ls-files','--stage','-z'],cwd=source).split(b'\0')
    regular=[]
    for entry in tracked:
        if not entry:
            continue
        metadata,name=entry.split(b'\t',1)
        mode=metadata.split()[0]
        if mode != b'160000':
            regular.append((mode,os.fsdecode(name)))
    if head != upstream or len(regular) < 1000:
        raise RuntimeError('BOT full generated source checkout/pin required; proof snapshot rejected')
    for mode,name in regular:
        present=(source/name).is_symlink() if mode == b'120000' else (source/name).is_file()
        if not present:
            raise RuntimeError('BOT full checkout missing tracked product input: '+name)
    return len(regular)


def verify_modern_parent(parent):
    from jg132_baseline import enabled, boundary, states, read, digest
    if enabled():
        if boundary(parent)!=28:raise RuntimeError('Protected modern132parent must be actual stage28')
        # Entire current prefix and untouched selected dependencies were proved;
        # this supersedes the historical16whole-owner13.1.2snapshot (retained).
        return len(states()[28])
    baseline = json.loads((PROVENANCE/'MODERN-WRITE-BASELINE.json').read_text())
    for row in baseline['files']:
        if hashlib.sha256((Path(parent)/row['path']).read_bytes()).hexdigest() != row['sha256']:
            raise RuntimeError('Protected whole modern owner changed: '+row['path'])
    return len(baseline['files'])


@contextmanager
def task1_source_view(parent):
    """Reconstruct the immutable accepted history draft for its original fixtures."""
    from jg131_final_stages import source_view
    from jg132_baseline import enabled, boundary, stage_manifest, patch as current_patch, chain, read, digest
    if enabled():
        if boundary(parent)!=28:raise RuntimeError('Expected real132stage28view')
        row=chain()[28];owners=stage_manifest('jg131-botbridge1')['owners']
        with tempfile.TemporaryDirectory(prefix='jg132-bot-accepted-') as directory:
            temp=Path(directory);changed=temp/'owners';changed.mkdir()
            for name,values in owners.items():
                data=read(parent,name)
                if digest(data)!=values['before_sha256']:raise RuntimeError('132BOTparent changed '+name)
                if data is not None:
                    p=changed/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            patch_path=current_patch(row)
            subprocess.run(['git','apply','--check',str(patch_path)],cwd=changed,check=True)
            subprocess.run(['git','apply','--whitespace=nowarn',str(patch_path)],cwd=changed,check=True)
            replacements={name:read(changed,name) for name in owners}
            for name,values in owners.items():
                if digest(replacements[name])!=values['after_sha256']:raise RuntimeError('132BOToutput changed '+name)
            view=source_view(parent,temp/'source',replacements)
            if boundary(view)!=29:raise RuntimeError('132BOTview boundary changed')
            yield view
        return
    import materialize_jg131_botbridge1 as stage
    # Reuse strict stage mechanics with a separate module instance and pinned patch.
    import importlib.util
    spec = importlib.util.spec_from_file_location('botbridge_task1_view_stage', stage.__file__)
    task1 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(task1)
    task1.PATCH = PROVENANCE/'task1.patch'
    task1.MANIFEST = PROVENANCE/'task1.sha256.json'
    owners = task1.manifest()['owners']
    with tempfile.TemporaryDirectory(prefix='jg-botbridge-task1-') as directory:
        temp=Path(directory); changed=temp/'owners'; changed.mkdir()
        for name, row in owners.items():
            path=changed/name
            if row['before_sha256'] is not None:
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes((Path(parent)/name).read_bytes())
        task1.apply_botbridge(changed)
        replacements={name:(changed/name).read_bytes() for name in owners}
        yield source_view(parent,temp/'source',replacements)


def verify_source(source):
    verify_botbridge(source)
    verify_provenance_files(ROOT, manifest()['portable_provenance'])
    with parent_source_view(source) as parent:
        modern = verify_modern_parent(parent)
        files = verify_preference_key_available(parent)
    text=(Path(source)/'submodules/TelegramCore/Sources/State/JerkgramBotBridgeHistory.swift').read_text()
    if set(re.findall(r'Api.functions.([\w.]+)\(',text)) != {'updates.getState','updates.getDifference'}:
        raise RuntimeError('BOT bridge RPC allowlist changed')
    for banned in ['setState(', 'finalStateWithDifference(', 'replayFinalState(', 'Logger.', 'getDialogs(', 'getHistory(']:
        if banned in text:
            raise RuntimeError('BOT bridge boundary violated: '+banned)
    print(f'BOTBRIDGE1 exact outputs, {modern} protected whole modern parents and preference-key scan of {files} product files PASS',flush=True)
    return files


if __name__ == '__main__':
    import sys
    verify_source(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'work/swiftgram-src')
