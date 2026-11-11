"""One composed final gate: Tags → exact Hub → exact recovery → exact BOT.

--require-native and --require-full-source are mandatory in each source/app
checkout. Portable proofs never substitute for native or full-app evidence.
"""
from pathlib import Path
import os
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from materialize_jg131_saved_tags import manifest, parent_source_view
from verify_jg131_saved_tags import verify_source
from verify_jg131_botbridge1 import verify_full_checkout


def main(flags=None, source=None):
    flags = sys.argv[1:] if flags is None else flags
    source = Path(source if source is not None else os.environ.get('JG_SAVED_TAGS_SOURCE', ROOT / 'work/swiftgram-src')).resolve()
    required = '--require-native' in flags
    if required and (platform.system() != 'Darwin' or any(not shutil.which(tool) for tool in ('swiftc', 'swift', 'clang', 'xcrun'))):
        raise SystemExit('Saved Tags requires macOS Swift, Clang and xcrun; native evidence unavailable')
    if '--require-full-source' in flags:
        count = verify_full_checkout(source, manifest()['upstream_sha'])
        print(f'Saved Tags full pinned checkout presence verified: {count} tracked product inputs', flush=True)
    verify_source(source)
    failures = []

    def run(args, env=None):
        if subprocess.run([sys.executable, *args], cwd=ROOT, env=env).returncode:
            failures.append(args)

    for name in ('test_jg131_saved_tags_stage.py', 'test_jg131_saved_tags_integration.py'):
        run(['-m', 'unittest', 'discover', '-s', 'tests', '-p', name])
    # Never materialize or compile into the disposable parent. Native fixtures
    # compile in their own temporary directories; the view supplies read-only inputs.
    with parent_source_view(source) as parent:
        env = dict(os.environ, JG_SAVED_TAGS_SOURCE=str(source), JG_SAVED_TAGS_BEFORE=str(parent))
        if required:
            env['JG_SAVED_TAGS_REQUIRE_NATIVE'] = '1'
        for name in ('store', 'core', 'ui'):
            run(['tests/test_jg131_beta2_saved_tags_' + name + '.py'], env)
        forwarded = [flag for flag in ('--require-native', '--require-full-source') if flag in flags]
        run(['tests/run_jg131_local_premium.py', *forwarded], dict(os.environ, JG_LOCAL_PREMIUM_SOURCE=str(parent)))
    if shutil.which('xcrun'):
        for name in manifest()['owners']:
            if name.endswith('.swift') and subprocess.run(['xcrun', 'swiftc', '-frontend', '-parse', str(source / name)]).returncode:
                failures.append(name)
    else:
        print('SKIP Saved Tags owner native parsing: xcrun unavailable; macOS required', flush=True)
    if failures:
        raise SystemExit('Saved Tags failed: ' + repr(failures))
    print('Saved Tags composed source gates PASS; native evidence only when required, app/device separate', flush=True)


if __name__ == '__main__':
    main()
