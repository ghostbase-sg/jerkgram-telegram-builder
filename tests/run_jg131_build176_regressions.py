"""One terminal source/native gate before the single Build176 integration IPA."""
from pathlib import Path
import subprocess,sys,shutil
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from materialize_jg131_performance_wave1 import verify_wave1,baseline_source_view
verify_wave1(ROOT/'work/swiftgram-src')
failures=[]
def run(args):
 result=subprocess.run([sys.executable,*args],cwd=ROOT)
 if result.returncode:failures.append(args)
run(['-m','unittest','discover','-s','tests','-p','test_jg131_wave1*.py'])
run(['tests/run_jg131_wave1_projection.py'])
run(['-m','unittest','discover','-s','tests','-p','test_jg131_settings_animation.py'])
if shutil.which('xcrun'):run(['tests/run_jg131_final_syntax.py'])
else: print('SKIP Swift syntax/native compiler: unavailable on this host',flush=True)
# Verify immutable prior contracts through the exact reversed terminal stage.
with baseline_source_view(ROOT/'work/swiftgram-src') as prior:
 import verify_jg13_source as verifier
 verifier.SOURCE=prior
 verifier.main()
if failures:raise SystemExit('Build176 failed checks: '+repr(failures))
print('Build176 wave1 source gates PASS; runtime/device validation pending',flush=True)
