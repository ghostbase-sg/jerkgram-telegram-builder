"""Explicit bounded source fixtures. They never supply or fabricate upstream HEAD."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1]

def digest(data):return hashlib.sha256(data).hexdigest() if data is not None else None

def official_bytes(source,name):
    if os.environ.get('JG132_PRISTINE_SOURCE'):
        selected=json.loads((ROOT/'docs/migrations/telegram-13.2-selected-tree.json').read_text())
        if name not in selected or selected[name] is None:
            from jg132_baseline import states
            initial=states()[0]
            if name in initial and initial[name] is None:return b''
            raise RuntimeError('Missing official selected fixture '+name)
        data=(Path(os.environ['JG132_PRISTINE_SOURCE'])/name).read_bytes()
        expected=selected[name]
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if blob!=expected:raise RuntimeError('Explicit pristine fixtureblob changed '+name)
        return data
    return subprocess.check_output(['git','show','HEAD:'+name],cwd=source)

def apply_exact_delta_fixture(stage,source):
    """Exercise current reviewed delta algebra on owner-only fixture bytes.

    Production APIs independently require genuine HEAD and a whole sourceprefix;
    this helper is exclusively a unit fixture and provides neither claim.
    """
    m=stage.read_manifest() if hasattr(stage,'read_manifest') else stage.manifest()
    owners=m.get('owners',{m['owner']:m} if 'owner' in m else {})
    for n,v in owners.items():
        p=Path(source)/n;actual=p.read_bytes() if p.exists() else None
        if digest(actual)!=v['before_sha256']:raise RuntimeError('Fixture parent changed '+n)
    if hasattr(stage,'check_locks') and 'locks' in m:stage.check_locks(source,m)
    for field in ('regression_locks','locks','parent_owners'):
        if field=='locks' and hasattr(stage,'check_locks'):continue
        for n,expected in m.get(field,{}).items():
            if n not in owners and digest((Path(source)/n).read_bytes())!=expected:raise RuntimeError('Fixture guard changed '+n)
    from jg132_baseline import enabled,chain,patch as reviewed_patch
    if enabled():
        name=Path(stage.MANIFEST).name.removesuffix('.sha256.json')
        patch=reviewed_patch(next(row for row in chain() if row['stage']==name))
    else:patch=stage.PATCH
    if 'patch_sha256' in m and digest(patch.read_bytes())!=m['patch_sha256']:raise RuntimeError('Fixture patch changed')
    subprocess.run(['git','apply','--check',str(patch)],cwd=source,check=True)
    subprocess.run(['git','apply','--whitespace=nowarn',str(patch)],cwd=source,check=True)
    for n,v in owners.items():
        p=Path(source)/n;actual=p.read_bytes() if p.exists() else None
        if digest(actual)!=v['after_sha256']:raise RuntimeError('Fixture output changed '+n)
