"""Run every new Build175 native/source fixture before returning a failure."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
TESTS=(
 'test_jg131_typing_echo.py',
 'test_jg131_profile_metadata_copy.py',
 'test_jg131_settings_animation.py',
 'test_jg131_bot_persistence.py',
 'test_jg131_translation.py',
 'test_jg131_translation_stage.py',
 'test_jg131_localization.py',
 'test_jg131_translation_175.py',
 'test_jg131_bot_ui_175.py',
 'test_jg131_surfaces_175.py',
 'test_jg131_performance_175.py',
)
failures=[]
for name in TESTS:
    result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p',name],cwd=ROOT)
    if result.returncode: failures.append(name)
syntax=subprocess.run([sys.executable,str(ROOT/'tests/run_jg131_final_syntax.py')],cwd=ROOT)
if syntax.returncode: failures.append('run_jg131_final_syntax.py')
if failures:
    print('Build175 failed checks: '+', '.join(failures), flush=True)
    raise SystemExit(1)
print('All Build175 native/source fixtures and Swift syntax checks PASS',flush=True)
