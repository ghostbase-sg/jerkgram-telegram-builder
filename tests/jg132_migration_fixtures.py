"""Hermetic fresh migration proofs from genuine pinned repository objects.

No personal workspace, cached success JSON, network request or invented HEAD.
Every CI input comes from tracked builder contracts or the genuine source repo.
"""
from pathlib import Path
import hashlib,io,json,subprocess,tarfile,tempfile
import sys
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'scripts/jg132_baseline.py').is_file())
sys.path.insert(0,str(ROOT/'scripts'))
import jg132_baseline as baseline

def selected():return {n:h for n,h in json.loads(baseline.SELECTED.read_text()).items() if h is not None}

def blob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def files(root):return {str(p.relative_to(root)):p.read_bytes() for p in Path(root).rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}

def hashes(root):return {n:baseline.digest(d) for n,d in files(root).items()}

def write(root,name,data):
    p=baseline.path(root,name)
    if data is None:
        if p.exists():p.unlink()
    else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)

def verify_pristine(root):
    expected=selected();actual=files(root)
    if set(actual)!=set(expected):raise RuntimeError('Pristine archive selected scope mismatch')
    for n,h in expected.items():
        if blob(actual[n])!=h:raise RuntimeError('Pristine selected blob changed '+n)
    if baseline.boundary(root)!=0:raise RuntimeError('Pristine projection is not boundary0')

class GenuinePristineFactory:
    """Fail closed unless real work/swiftgram-src contains the pinned commit."""
    def __init__(self,source=None):self.source=Path(source or ROOT/'work/swiftgram-src')
    def validate(self):
        baseline.require_genuine(self.source)
        from verify_jg131_botbridge1 import verify_full_checkout
        verify_full_checkout(self.source,baseline.TARGET)
        payload=subprocess.check_output(['git','cat-file','commit',baseline.TARGET],cwd=self.source)
        computed=hashlib.sha1(b'commit '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
        if computed!=baseline.TARGET:raise RuntimeError('Commit payload does not hash to genuine target')
        entries=subprocess.check_output(['git','ls-tree','-r','-z',baseline.TARGET,'--',*selected()],cwd=self.source).split(b'\0')
        rows={}
        for entry in entries:
            if not entry:continue
            meta,name=entry.split(b'\t',1);mode,kind,sha=meta.decode().split()
            if kind!='blob' or mode not in ('100644','100755'):raise RuntimeError('Unexpected selected object type')
            rows[name.decode()]=sha
        if rows!=selected():raise RuntimeError('Pinned selected paths do not match genuine target tree')
    def populate(self,destination):
        self.validate()
        destination=Path(destination);destination.mkdir()
        archive=subprocess.check_output(['git','archive','--format=tar',baseline.TARGET,'--',*selected()],cwd=self.source)
        with tarfile.open(fileobj=io.BytesIO(archive),mode='r:') as stream:
            for member in stream:
                if member.isdir():continue
                if not member.isfile() or member.name not in selected():raise RuntimeError('Unexpected archive member '+member.name)
                data=stream.extractfile(member).read()
                if blob(data)!=selected()[member.name]:raise RuntimeError('Archived blob changed '+member.name)
                write(destination,member.name,data)
        if (destination/'.git').exists():raise RuntimeError('Projection must not carry a fabricated HEAD')
        verify_pristine(destination)
        return destination

def apply(source,row):baseline.apply_stage(source,row['stage'],require_head=False)

def replay(factory,destination,prove_reversals):
    source=factory.populate(destination);pristine=hashes(source);records=[]
    for row in baseline.chain():
        before=hashes(source);apply(source,row);after=hashes(source);p=baseline.patch(row)
        repeated=subprocess.run(['git','apply','--check',str(p)],cwd=source,capture_output=True)
        if repeated.returncode==0:raise RuntimeError('Raw repeated delta accepted '+row['stage'])
        if hashes(source)!=after:raise RuntimeError('Raw repeat check wrote source')
        if prove_reversals:
            subprocess.run(['git','apply','--reverse','--check',str(p)],cwd=source,check=True,capture_output=True)
            subprocess.run(['git','apply','--reverse','--whitespace=nowarn',str(p)],cwd=source,check=True,capture_output=True)
            if hashes(source)!=before:raise RuntimeError('Reverse failed exact restoration '+row['stage'])
            n=next(n for n,v in row['owners'].items() if v['before']!=v['after']);original=baseline.read(source,n)
            write(source,n,b'corrupt independent parent fixture\n');damaged=hashes(source)
            try:apply(source,row)
            except RuntimeError:pass
            else:raise RuntimeError('Corrupt parent accepted '+row['stage'])
            if hashes(source)!=damaged:raise RuntimeError('Corrupt parent refusal wrote source')
            write(source,n,original);apply(source,row)
            if hashes(source)!=after:raise RuntimeError('Restored replay differs '+row['stage'])
        records.append({'stage':row['stage'],'raw_repeat_refused':True,'exact_reverse_and_corrupt_prewrite':prove_reversals})
    final=hashes(source);owners={n for row in baseline.chain() for n in row['owners']}
    changed={n for n in set(pristine)|set(final) if pristine.get(n)!=final.get(n)}
    if changed-owners:raise RuntimeError('Unattributed final change '+str(changed-owners))
    if baseline.verify_source(source)!=32:raise RuntimeError('Fresh replay did not reach32')
    return {'hashes':final,'source':source,'records':records,'changed':changed}

def two_fresh_replays(factory,directory):
    root=Path(directory)
    first=replay(factory,root/'first',True);second=replay(factory,root/'second',False)
    if first['hashes']!=second['hashes']:raise RuntimeError('Two fresh migration replays differ')
    return first,second
