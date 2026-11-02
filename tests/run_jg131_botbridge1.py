"""BOT terminal source/fixture gate, then historical contracts on restored C.

--require-native is mandatory in the macOS workflow; Linux skips never satisfy
that gate. --require-full-source rejects proof snapshots before collision scan.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('JERKGRAM_BOTBRIDGE_SOURCE',ROOT/'work/swiftgram-src')).resolve()
sys.path.insert(0,str(ROOT/'scripts'))
from materialize_jg131_botbridge1 import manifest, parent_source_view
from verify_jg131_botbridge1 import verify_source, task1_source_view, verify_full_checkout, PROVENANCE

if '--require-native' in sys.argv and (not shutil.which('swiftc') or not shutil.which('swift') or not shutil.which('xcrun')):
    raise SystemExit('BOTBRIDGE1 requires macOS Swift compiler and xcrun; native evidence unavailable')
if '--require-full-source' in sys.argv:
    tracked=verify_full_checkout(SOURCE,manifest()['upstream_sha'])
    print(f'BOT full checkout presence verified: {tracked} tracked product inputs',flush=True)

files=verify_source(SOURCE)
print(f'BOTBRIDGE1 collision scan scope: {"generated pinned checkout" if "--require-full-source" in sys.argv else "supplied source tree only"}; {files} files',flush=True)
failures=[]
def run(args,env=None):
    result=subprocess.run([sys.executable,*args],cwd=ROOT,env=env)
    if result.returncode: failures.append(args)

def suite(name,env):
    run(['-m','unittest','discover','-s','tests','-p',name],env)

for name in ('test_jg131_botbridge1_stage.py','test_jg131_botbridge1_integration.py'):
    suite(name,dict(os.environ))
with parent_source_view(SOURCE) as parent:
    with task1_source_view(parent) as history:
        env=dict(os.environ,JERKGRAM_BOTBRIDGE_SOURCE=str(history),JERKGRAM_BOTBRIDGE_C_SOURCE=str(parent))
        suite('test_jg131_botbridge1_history.py',env)
        env=dict(os.environ,JERKGRAM_BOTBRIDGE_SOURCE=str(SOURCE),JERKGRAM_BOTBRIDGE_TASK2_BEFORE=str(history),JERKGRAM_BOTBRIDGE_TASK2_ARTIFACTS=str(PROVENANCE))
        suite('test_jg131_botbridge1_diagnostics.py',env)
    # Earlier fixture/storage/policy contracts see their exact preceding source.
    if '--bot-only' not in sys.argv:
        env=dict(os.environ,JERKGRAM_SETTINGS_GLASS_SOURCE=str(parent))
        run(['tests/run_jg131_settings_glass_expansion.py'],env)
if shutil.which('xcrun'):
    for name in manifest()['owners']:
        if name.endswith('.swift'):
            result=subprocess.run(['xcrun','swiftc','-frontend','-parse',str(SOURCE/name)])
            if result.returncode: failures.append(name)
else:
    print('SKIP native final-owner Swift parsing: xcrun unavailable; macOS required',flush=True)
if failures: raise SystemExit('BOTBRIDGE1 failed: '+repr(failures))
print('BOTBRIDGE1 portable source gates PASS; native compilation/app/device evidence separate',flush=True)
