#!/usr/bin/env python3
from pathlib import Path
import os, subprocess, sys
SCRIPT_DIR=Path(__file__).resolve().parent
PROBE=Path(os.environ.get('JERKGRAM_PROBE_PATH',str(SCRIPT_DIR/'bazel_build_probe_official.sh'))).resolve()
APPLY='apply_jerkgram_v12t_build130_release_ui_telemetry1.py'
VERIFY='verify_jerkgram_v12t_build130_release_ui_telemetry1.py'
MARK='# JERKGRAM_V12T_BUILD130_PRE_BAZEL_GATE'
ANCHOR='python3 ../../scripts/apply_jerkgram_v12r_build129_protected_chat_forward1.py\n'
BAZEL='"$BAZEL_BIN" build'
def req(v,m):
    if not v: raise RuntimeError('[Build130 probe hook] '+m)
def patch(t):
    req(ANCHOR in t,'Build129 final source anchor missing')
    if MARK not in t:
        block=ANCHOR+'\n'+MARK+'\necho\necho "== Jerkgram Build130 release UI + telemetry =="\npython3 ../../scripts/'+APPLY+'\npython3 ../../scripts/'+VERIFY+'\necho "PRE-BUILD GATES: PASS"\n'
        t=t.replace(ANCHOR,block,1)
    req(t.count(MARK)==1,'gate marker count')
    req(t.count(APPLY)==1 and t.count(VERIFY)==1,'Build130 apply/verifier count')
    req(t.index(ANCHOR.strip()) < t.index(APPLY) < t.index(VERIFY) < t.index(BAZEL),'Build130 must apply+verify after Build129 and before Bazel')
    return t
def main():
    for name in (APPLY,VERIFY):
        path=SCRIPT_DIR/name;req(path.is_file(),'missing '+name);subprocess.check_call([sys.executable,'-m','py_compile',str(path)])
    req(PROBE.is_file(),'probe missing')
    PROBE.write_text(patch(PROBE.read_text(encoding='utf-8')),encoding='utf-8')
    print('[Build130 probe hook] GREEN: py_compile + final-source verifier wired before Bazel')
if __name__=='__main__':main()
