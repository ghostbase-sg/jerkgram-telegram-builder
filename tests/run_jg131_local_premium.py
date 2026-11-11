"""Hub source/native gates; recovery and historical gates see exact parents.

--require-native and --require-full-source are mandatory before an IPA build.
Portable proof snapshots and source tests never stand in for these gates.
"""
from pathlib import Path
import os
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG_LOCAL_PREMIUM_SOURCE', ROOT / 'work/swiftgram-src')).resolve()
sys.path.insert(0, str(ROOT / 'scripts'))
from materialize_jg131_local_premium import manifest, parent_source_view
from verify_jg131_local_premium import verify_source
from verify_jg131_botbridge1 import verify_full_checkout

required = '--require-native' in sys.argv
if required and (platform.system() != 'Darwin' or any(not shutil.which(tool) for tool in ('swiftc', 'swift', 'clang', 'xcrun'))):
    raise SystemExit('Local Premium requires macOS Swift, Clang and xcrun; native evidence unavailable')
if '--require-full-source' in sys.argv:
    count = verify_full_checkout(SOURCE, manifest()['upstream_sha'])
    print(f'Local Premium full pinned checkout presence verified: {count} tracked product inputs', flush=True)
verify_source(SOURCE)
failures = []


def run(args, env=None):
    if subprocess.run([sys.executable, *args], cwd=ROOT, env=env).returncode:
        failures.append(args)


for name in ('test_jg131_local_premium_stage.py', 'test_jg131_local_premium_integration.py'):
    run(['-m', 'unittest', 'discover', '-s', 'tests', '-p', name])
env = dict(os.environ, JG_LOCAL_PREMIUM_SOURCE=str(SOURCE))
if required:
    env['JG_LOCAL_PREMIUM_REQUIRE_NATIVE'] = '1'
run(['tests/test_jg131_local_premium.py'], env)
if shutil.which('xcrun'):
    for name in manifest()['owners']:
        if name.endswith('.swift') and subprocess.run(['xcrun', 'swiftc', '-frontend', '-parse', str(SOURCE / name)]).returncode:
            failures.append(name)
else:
    print('SKIP Hub owner native parsing: xcrun unavailable; macOS required', flush=True)
with parent_source_view(SOURCE) as parent:
    flags = [flag for flag in ('--require-native', '--require-full-source') if flag in sys.argv]
    run(['tests/run_jg131_beta2_recovery.py', *flags], dict(os.environ, JG_BETA2_SOURCE=str(parent)))
if failures:
    raise SystemExit('Local Premium failed: ' + repr(failures))
print('Local Premium composed source gates PASS; native evidence only when required, app/device separate', flush=True)
