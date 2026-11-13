"""One required final successor gate after every accepted Build180 check."""
from pathlib import Path
import os, platform, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from jg132_post180 import verify_source, stages
from jg132_beta3_stages import manifest, UPSTREAM
from verify_jg131_botbridge1 import verify_full_checkout

if __name__=='__main__':
    required='--require-native' in sys.argv
    if required and (platform.system()!='Darwin' or any(not shutil.which(t) for t in ('xcrun','swiftc','clang'))):
        raise SystemExit('Post180 requires macOS native Swift/Clang/xcrun')
    source=Path(os.environ.get('JG_POST180_SOURCE',ROOT/'work/swiftgram-src')).resolve()
    if '--require-full-source' in sys.argv:verify_full_checkout(source,UPSTREAM)
    verify_source(source)
    env=dict(os.environ,JG_POST180_SOURCE=str(source))
    if required:env['JG_BETA3_REQUIRE_NATIVE']='1'
    for name in ('test_jg132_post180_stages.py','test_jg132_post180_history.py'):
        subprocess.run([sys.executable,str(ROOT/'tests'/name)],env=env,check=True)
    if shutil.which('xcrun'):
        for name in sorted({n for stage in stages() for n in manifest(stage)['owners'] if n.endswith('.swift')}):
            subprocess.run(['xcrun','swiftc','-frontend','-parse',str(source/name)],check=True)
    elif required:raise SystemExit('Native parser unavailable')
    print('Post180 source/component gates PASS; whole app and device separate',flush=True)
