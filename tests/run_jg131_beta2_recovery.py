"""Final recovery native/source gates and historical gates on exact reversed BOT.

--require-native and --require-full-source are mandatory in source/app CI.
Portable runs never substitute for those requirements or retained-device launch.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG_BETA2_SOURCE', ROOT/'work/swiftgram-src')).resolve()
sys.path.insert(0, str(ROOT/'scripts'))
from materialize_jg131_beta2_recovery import manifest, parent_source_view
from verify_jg131_beta2_recovery import verify_source
from verify_jg131_botbridge1 import verify_full_checkout

required = '--require-native' in sys.argv
if required and any(not shutil.which(tool) for tool in ('swiftc', 'swift', 'clang', 'xcrun')):
    raise SystemExit('Beta2 recovery requires macOS Swift, Clang and xcrun; native evidence unavailable')
if '--require-full-source' in sys.argv:
    count = verify_full_checkout(SOURCE, manifest()['upstream_sha'])
    print(f'Beta2 full pinned checkout presence verified: {count} tracked product inputs', flush=True)
verify_source(SOURCE)
failures = []
def run(args, env=None):
    if subprocess.run([sys.executable, *args], cwd=ROOT, env=env).returncode:
        failures.append(args)

for name in ('test_jg131_beta2_recovery_stage.py', 'test_jg131_beta2_recovery_integration.py'):
    run(['-m', 'unittest', 'discover', '-s', 'tests', '-p', name])
env = dict(os.environ, JG_BETA2_CODEC_OWNER=str(SOURCE/'submodules/TelegramCore/Sources/State/JerkgramBotBridgeHistory.swift'), JG_BETA2_UI_SOURCE=str(SOURCE))
if required:
    env.update(JG_BETA2_REQUIRE_NATIVE='1', JG_BETA2_UI_REQUIRE_NATIVE='1')
for name in ('test_jg131_beta2_bot_codec.py', 'test_jg131_beta2_recovery_ui.py'):
    run(['tests/'+name], env)
if shutil.which('xcrun'):
    for name in manifest()['owners']:
        if name.endswith('.swift') and subprocess.run(['xcrun', 'swiftc', '-frontend', '-parse', str(SOURCE/name)]).returncode:
            failures.append(name)
else:
    print('SKIP native recovery owner parsing: xcrun unavailable; macOS required', flush=True)
with parent_source_view(SOURCE) as parent:
    args = ['tests/run_jg131_botbridge1.py']
    args += [flag for flag in ('--require-native', '--require-full-source') if flag in sys.argv]
    # A restored view preserves .git links but full-checkout proof is checked on
    # the real final source above; historical BOT also retains its strict check.
    run(args, dict(os.environ, JERKGRAM_BOTBRIDGE_SOURCE=str(parent)))
if failures:
    raise SystemExit('Beta2 recovery failed: '+repr(failures))
print('Beta2 recovery composed source gates PASS; native evidence only when required, app/device separate', flush=True)
