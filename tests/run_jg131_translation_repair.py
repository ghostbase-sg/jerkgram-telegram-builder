"""TASK A terminal source gates; compilation and device results are separate."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JERKGRAM_TRANSLATION_REPAIR_SOURCE', ROOT / 'work/swiftgram-src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from materialize_jg131_translation_repair import verify_repair, parent_source_view, manifest

verify_repair(SOURCE)
failures = []
for name in ('test_jg131_translation_repair_stage.py', 'test_jg131_translation_core.py',
             'test_jg131_translation_ui_repair.py', 'test_jg131_translation_corpus.py'):
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
    import verify_jg13_source as verifier
    verifier.SOURCE = parent
    verifier.main()
if failures:
    raise SystemExit('Translation repair failed: ' + repr(failures))
print('Translation TASK A source gates PASS; backend/device quality unverified', flush=True)
