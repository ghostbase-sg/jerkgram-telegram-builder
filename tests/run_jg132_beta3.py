"""Required source/native successor gate before the common Beta3 app build."""
from pathlib import Path
import os
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from jg132_beta3_stages import UPSTREAM, STAGES, baseline_source_view, manifest
from verify_jg131_botbridge1 import verify_full_checkout


def main():
    required = '--require-native' in sys.argv[1:]
    if required and (platform.system() != 'Darwin' or any(not shutil.which(t) for t in ('swiftc', 'clang', 'xcrun'))):
        raise SystemExit('Beta3 requires macOS Swift/Clang/xcrun; native verification unavailable')
    source = Path(os.environ.get('JG_BETA3_SOURCE', ROOT / 'work/swiftgram-src')).resolve()
    if '--require-full-source' in sys.argv[1:]:
        verify_full_checkout(source, UPSTREAM)
    failures = []
    with baseline_source_view(source) as before:
        # Check the accepted baseline's current genuine target contracts.
        from verify_jg131_saved_tags import verify_source
        verify_source(before)
        env = dict(os.environ, JG_BETA3_SOURCE=str(source), JG_BETA3_BEFORE=str(before), JG13_SOURCE=str(source), JG_BETA3_BOT_CORE=str(source / 'submodules/TelegramCore/Sources'))
        if required:
            env['JG_BETA3_REQUIRE_NATIVE'] = '1'
        for name in ('test_jg132_beta3_stages.py', 'test_jg132_beta3_integration.py', 'test_jg132_backend_fixture.py', 'test_jg132_bot_reset_recovery.py', 'test_jg132_settings_followup.py', 'test_jg132_wallet_surface.py', 'test_jg132_beta3_native_tags.py'):
            path = ROOT / 'tests' / name
            if not path.is_file():
                failures.append('required suite absent: ' + name)
            elif subprocess.run([sys.executable, str(path)], cwd=ROOT, env=env).returncode:
                failures.append(name)
    if shutil.which('xcrun'):
        owners = {n for stage in STAGES for n in manifest(stage)['owners'] if n.endswith('.swift')}
        for name in sorted(owners):
            if subprocess.run(['xcrun', 'swiftc', '-frontend', '-parse', str(source / name)]).returncode:
                failures.append('parse: ' + name)
    elif required:
        failures.append('xcrun absent')
    else:
        print('SKIP native owner parsing: macOS xcrun unavailable', flush=True)
    if failures:
        raise SystemExit('Beta3 gate failed: ' + repr(failures))
    print('Beta3 exact successor/source gates PASS; native execution only when required, whole app and device separate', flush=True)


if __name__ == '__main__':
    main()
