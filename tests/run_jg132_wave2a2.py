from pathlib import Path
import os, platform, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from jg132_wave2a2 import green_view, OWNER
from jg132_beta3_stages import UPSTREAM
from verify_jg131_botbridge1 import verify_full_checkout
if __name__=='__main__':
    source=Path(os.environ.get('JG_WAVE2A2_SOURCE',ROOT/'work/swiftgram-src')).resolve()
    required='--require-native' in sys.argv
    if required and (platform.system()!='Darwin' or not shutil.which('xcrun')):raise SystemExit('Wave2A2 requires native macOS Swift/xcrun')
    if '--require-full-source' in sys.argv:verify_full_checkout(source,UPSTREAM)
    with green_view(source):pass
    env=dict(os.environ,JG_WAVE2A2_SOURCE=str(source))
    if required:env['JG_WAVE2A2_REQUIRE_NATIVE']='1'
    subprocess.run([sys.executable,str(ROOT/'tests/test_jg132_wave2a2.py')],env=env,check=True)
    if required:subprocess.run(['xcrun','swiftc','-frontend','-parse',str(source/OWNER)],check=True)
    print('Wave2A2 exact source gate PASS; native counts only if executed; device NOT VERIFIED',flush=True)
