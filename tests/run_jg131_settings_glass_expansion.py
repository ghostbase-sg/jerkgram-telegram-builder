"""TASK C gate followed by TASK B's gate on its exact restored source view."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JERKGRAM_SETTINGS_GLASS_SOURCE', ROOT / 'work/swiftgram-src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from materialize_jg131_settings_glass_expansion import verify_glass, parent_source_view, manifest

verify_glass(SOURCE)
failures = []
for name in ('test_jg131_settings_glass_expansion_stage.py', 'test_jg131_settings_glass_expansion.py'):
    result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', name], cwd=ROOT)
    if result.returncode:
        failures.append(name)
if shutil.which('xcrun'):
    for name in manifest()['owners']:
        if name.endswith('.swift'):
            result = subprocess.run(['xcrun', 'swiftc', '-frontend', '-parse', str(SOURCE / name)])
            if result.returncode:
                failures.append(name)
else:
    print('SKIP native Swift parsing: xcrun unavailable on this host', flush=True)
with parent_source_view(SOURCE) as parent:
    env = dict(os.environ, JERKGRAM_DEFAULT_FOLDER_SOURCE=str(parent))
    result = subprocess.run([sys.executable, 'tests/run_jg131_default_folder.py'], cwd=ROOT, env=env)
    if result.returncode:
        failures.append('TASK B exact parent gate')
if failures:
    raise SystemExit('Settings glass failed: ' + repr(failures))
print('TASK C source gates PASS; app/device navigation still requires runtime', flush=True)
