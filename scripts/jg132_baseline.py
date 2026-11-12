"""Exact source-native historical32-stage baseline on genuine official13.2.

The baseline has frozen Build179 identity; Beta3/180 is an explicit later stage.
No native/full checkout compatibility is implied by this source contract.
"""
from pathlib import Path
import hashlib,json,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
TARGET='24638bc69bd083981b178dd1e7f921eebbf7fc46'
CHAIN=ROOT/'docs/migrations/telegram-13.2-stage-chain.json'
GUARDS=ROOT/'docs/migrations/telegram-13.2-guard-proof.json'
SELECTED=ROOT/'docs/migrations/telegram-13.2-selected-tree.json'

def enabled():return json.loads((ROOT/'jerkgram-migration.json').read_text())['upstream_new_sha']==TARGET

def digest(data):return hashlib.sha256(data).hexdigest() if data is not None else None

def path(source,name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts or not p.parts:raise RuntimeError('Unsafe baselineowner')
    return Path(source)/p

def read(source,name):
    p=path(source,name)
    return p.read_bytes() if p.is_file() else None

def chain():
    rows=json.loads(CHAIN.read_text())
    if len(rows)!=32 or [r['order'] for r in rows]!=list(range(1,33)):raise RuntimeError('Wrong132stagechain')
    return rows

def _git(source,*args):return subprocess.check_output(['git',*args],cwd=source)

def require_genuine(source):
    try:actual=_git(source,'rev-parse','HEAD').decode().strip()
    except subprocess.CalledProcessError as error:raise RuntimeError('Missing genuine official13.2HEAD') from error
    if actual!=TARGET:raise RuntimeError('Expected genuine official13.2HEAD')
    if _git(source,'cat-file','-t',TARGET).strip()!=b'commit':raise RuntimeError('Missing genuine13.2commitobject')

def states():
    rows=chain();state={}
    for r in rows:
        for n,v in r['owners'].items():state.setdefault(n,v['before'])
    result=[state.copy()]
    for r in rows:
        state.update({n:v['after'] for n,v in r['owners'].items()});result.append(state.copy())
    return result

def boundary(source):
    versions=states();names=versions[0];actual={n:digest(read(source,n)) for n in names}
    matches=[i for i,s in enumerate(versions) if actual==s]
    if len(matches)!=1:raise RuntimeError('Mixed/corrupt132baseline boundary; refusing source')
    # Every selected dependency outside stage ownership stays pristine.
    for n,expected in json.loads(SELECTED.read_text()).items():
        if n in names or expected is None:continue
        data=read(source,n)
        if data is None:raise RuntimeError('Missing selected132dependency '+n)
        actual_blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if actual_blob!=expected:raise RuntimeError('Changed selected132dependency '+n)
    return matches[0]

def patch(row):
    if row['stage']=='jg13-stable.product':
        from materialize_jg131_stable import reviewed_stable_patch
        p=reviewed_stable_patch()
    elif row['stage']=='identity':p=ROOT/'patches/jg132-baseline-identity.patch'
    else:p=ROOT/'patches'/(row['stage']+'.patch')
    if digest(p.read_bytes())!=row['regenerated_patch_sha256']:raise RuntimeError('Reviewed132patchchanged '+row['stage'])
    return p

def apply_stage(source,name,require_head=True):
    source=Path(source).resolve()
    if require_head:require_genuine(source)
    row=next(r for r in chain() if r['stage']==name)
    current=boundary(source)
    # Existing public stage APIs are idempotent on an already verified later
    # whole-prefix boundary. A raw repeated delta still fails git apply.
    if current>=row['order']:
        patch(row)
        return
    if current!=row['order']-1:raise RuntimeError('Wrong preceding132stage '+name)
    guards=[g for g in json.loads(GUARDS.read_text()) if g['stage']==name]
    for g in guards:
        if 'before' in g['timing'] and digest(read(source,g['target_path']))!=g['new_digest']:raise RuntimeError('132parentguardchanged '+g['target_path'])
    p=patch(row)
    subprocess.run(['git','apply','--check',str(p)],cwd=source,check=True)
    subprocess.run(['git','apply','--whitespace=nowarn',str(p)],cwd=source,check=True)
    if boundary(source)!=row['order']:raise RuntimeError('132stageoutputchanged '+name)

def apply_range(source,first,last,require_head=True):
    for row in chain()[first-1:last]:apply_stage(source,row['stage'],require_head=require_head)

def verify_stage(source,name):
    expected=next(r['order'] for r in chain() if r['stage']==name)
    if boundary(source)<expected:raise RuntimeError('132stage not yet applied '+name)
    return json.loads((ROOT/'patches'/(name+'.sha256.json')).read_text())

def verify_source(source):
    n=boundary(source)
    if n<18:raise RuntimeError('Incomplete132configuredbaseline')
    # All applied patches and source outputs are attributed to exact32chain.
    for row in chain()[:n]:patch(row)
    if read(source,'submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift') is not None:raise RuntimeError('Obsolete stateowner recreated')
    if read(source,'submodules/TelegramUI/Sources/CoreListChatHistoryBackend.swift') is not None:raise RuntimeError('Obsolete backendowner recreated')
    if n>=29:
        manager=read(source,'submodules/TelegramCore/Sources/State/AccountStateManager.swift').decode()
        if 'ghostBaseBotShadow' in manager or manager.count('let controller = BotBridgeHistoryController(')!=1:raise RuntimeError('Wrong132botimporter topology')
        if 'self.addOperation(.custom(self.getNextId(), signal), position: .last)' not in manager:raise RuntimeError('132nativecustomqueue boundarylost')
    if n>=32:
        replay=read(source,'submodules/TelegramCore/Sources/State/Sync/StateReplay+Messages.swift').decode()
        for hook in ('_internal_removeLocalSavedTagsGlobalIds','_internal_removeLocalSavedTagsMessages','_internal_removeLocalSavedTagsRange','updateLocalSavedTagsMetadata','transaction.recordMessageEdit(message)'):
            if hook not in replay:raise RuntimeError('132statehooklost '+hook)
    print('Genuine13.2baseline source boundary VERIFIED:',n,'stages; native/app/runtime evidence separate')
    return n


def stage_manifest(name):
    """Verify current materializer manifest against exact reviewed chain/guards."""
    row=next(r for r in chain() if r['stage']==name)
    m=json.loads((ROOT/'patches'/(name+'.sha256.json')).read_text())
    if m.get('upstream_sha')!=TARGET:raise RuntimeError('Wrong132manifestpin '+name)
    values=m.get('owners',{m['owner']:m} if 'owner' in m else {})
    if set(values)!=set(row['owners']):raise RuntimeError('132manifestownerschanged '+name)
    for n,v in row['owners'].items():
        if values[n]['before_sha256']!=v['before'] or values[n]['after_sha256']!=v['after']:raise RuntimeError('132manifestboundarychanged '+name+':'+n)
    if 'patch_sha256' in m and m['patch_sha256']!=row['regenerated_patch_sha256']:raise RuntimeError('132manifestpatchchanged')
    effective=patch(row)
    changed={line.split('\t',2)[2] for line in subprocess.check_output(['git','apply','--numstat',str(effective)],text=True).splitlines()}
    expected_changed={n for n,v in row['owners'].items() if v['before']!=v['after']}
    if changed!=expected_changed:raise RuntimeError('132patchscopechanged '+name)
    for g in json.loads(GUARDS.read_text()):
        if g['stage']==name and m[g['field']].get(g['target_path'])!=g['new_digest']:raise RuntimeError('132manifestguardchanged')
    return m


def source_boundary_view(source,order):
    """Disposable real13.2preceding view; preserve actual genuine Gitmetadata."""
    from contextlib import contextmanager
    from jg131_final_stages import source_view
    @contextmanager
    def context():
        current=boundary(source)
        if current<order:raise RuntimeError('Cannot fabricate a future132sourceboundary')
        replacements={}
        # Only changed owners are copied; untouched full-checkout inputs retain
        # their original links. No upstream commit or checkout is invented.
        with tempfile.TemporaryDirectory(prefix='jg132-boundary-') as td:
            temp=Path(td);reverse=temp/'reverse';reverse.mkdir()
            affected={n for row in chain()[order:current] for n in row['owners']}
            for n in affected:
                data=read(source,n)
                if data is not None:
                    p=path(reverse,n);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            for row in reversed(chain()[order:current]):
                p=patch(row)
                subprocess.run(['git','apply','--reverse','--check',str(p)],cwd=reverse,check=True)
                subprocess.run(['git','apply','--reverse','--whitespace=nowarn',str(p)],cwd=reverse,check=True)
            replacements={n:read(reverse,n) for n in affected}
            view=source_view(source,temp/'source',replacements)
            if boundary(view)!=order:raise RuntimeError('Restored132boundary mismatch')
            yield view
    return context()


def baseline_identity():
    """Identity of the frozen32stagechain, read from its verified stage18delta.

    Release config can already describe Beta3/180; it must not change historical
    stage parents used by feature restoration and early native fixtures.
    """
    import re
    text=patch(chain()[17]).read_text()
    values={}
    for key in ('displayVersion','technicalVersion','build','telegramBase'):
        matches=re.findall(r'^\+    public static let '+key+r' = "([^"\n]+)"$',text,re.M)
        if len(matches)!=1:raise RuntimeError('Frozen132identity patchseam changed '+key)
        values[key]=matches[0]
    bundle=re.findall(r'^\+    <string>([^<]+)</string>$',text,re.M)
    if len(bundle)!=1:raise RuntimeError('Frozen132bundle patchseam changed')
    return {'product_display_version':values['displayVersion'],'product_technical_version':values['technicalVersion'],'build_number':int(values['build']),'upstream_new_version':values['telegramBase'],'bundle_short_version':bundle[0]}
