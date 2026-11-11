"""Focused final gate after the existing required Build179 baseline gate."""
from pathlib import Path
import os
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from materialize_jg131_wave2a1 import parent_source_view, manifest
from verify_jg131_wave2a1 import verify_source
from verify_jg131_botbridge1 import verify_full_checkout


def main():
    flags = sys.argv[1:]
    required = '--require-native' in flags
    if required and (platform.system() != 'Darwin' or any(not shutil.which(t) for t in ('swiftc', 'xcrun'))):
        raise SystemExit('Wave2A1 requires macOS Swift/xcrun; native behavior evidence unavailable')
    source = Path(os.environ.get('JG_WAVE2A1_SOURCE', ROOT / 'work/swiftgram-src')).resolve()
    if '--require-full-source' in flags:
        verify_full_checkout(source, manifest()['upstream_sha'])
    verify_source(source)
    with parent_source_view(source) as before:
        env = dict(os.environ, JG_WAVE2A1_SOURCE=str(source), JG_WAVE2A1_BEFORE=str(before))
        if required:
            env['JG_WAVE2A1_REQUIRE_NATIVE'] = '1'
        for name in ('test_jg131_wave2a1.py', 'test_jg131_wave2a1_stage.py', 'test_jg131_wave2a1_integration.py'):
            subprocess.run([sys.executable, str(ROOT / 'tests' / name)], cwd=ROOT, env=env, check=True)
    print('Wave2A1 focused gate PASS; baseline native gate remains separately required before materialization; full app/device performance unverified', flush=True)


if __name__ == '__main__':
    main()
