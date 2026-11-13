"""Single mandatory combined gate after frozen GREEN181; native skips forbidden in CI."""
from pathlib import Path
import os,platform,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from jg132_post181 import verify_source,stages
from jg132_beta3_stages import manifest,UPSTREAM
from verify_jg131_botbridge1 import verify_full_checkout
def run_required_checks(commands, *, env=None, execute=subprocess.run):
    """Report independent failures together; any nonzero result blocks the gate."""
    failures=[]
    for name, command in commands:
        result=execute(command,env=env,check=False)
        if result.returncode:
            failures.append((name,result.returncode))
    if failures:
        raise RuntimeError('Stable182 mandatory checks failed: '+', '.join(f'{name} (exit {code})' for name,code in failures))

if __name__=='__main__':
    required='--require-native' in sys.argv
    if required and (platform.system()!='Darwin' or any(not shutil.which(t) for t in ('xcrun','swiftc','clang'))):
        raise SystemExit('Stable182 requires native macOS Swift/Clang/xcrun')
    source=Path(os.environ.get('JG_STABLE182_SOURCE',ROOT/'work/swiftgram-src')).resolve()
    if '--require-full-source' in sys.argv:verify_full_checkout(source,UPSTREAM)
    verify_source(source)
    env=dict(os.environ,JG_STABLE182_SOURCE=str(source),JERKGRAM_STABLE_BOT_SOURCE=str(source),JG_STABLE182_PREMIUM_SOURCE=str(source))
    if required:env['JG_STABLE182_REQUIRE_NATIVE']='1'
    commands=[]
    for name in ['test_jg132_post181_runner.py','test_jg132_post181_stages.py','test_jg132_post181_performance.py','test_jg132_stable_bot_history.py','test_jg132_stable_premium_master.py','test_jg132_stable_gram_balance.py','test_jg132_stable_gram_presentations.py']:
        commands.append((name,[sys.executable,str(ROOT/'tests'/name)]))
    if shutil.which('xcrun'):
        for name in sorted({n for stage in stages() for n in manifest(stage)['owners'] if n.endswith('.swift')}):
            commands.append(('parse '+name,['xcrun','swiftc','-frontend','-parse',str(source/name)]))
    elif required:raise SystemExit('Native parser unavailable')
    run_required_checks(commands,env=env)
    print('Stable182 source/component gate PASS; app and device separate',flush=True)
