#!/usr/bin/env python3
"""Exact bounded Build153 diagnostic delta after the preference snapshot."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from materialize_jg13_profile_preferences import verify_preferences
ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / 'patches/jg13-expanded-diagnostics.patch'
MANIFEST = ROOT / 'patches/jg13-expanded-diagnostics.sha256.json'
OWNERS = {
    'submodules/TelegramCore/Sources/Utils/JerkgramPerformanceDiagnostics.swift',
    'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift',
    'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreen.swift',
    'submodules/TelegramUI/Sources/ChatController.swift',
    'submodules/ChatListUI/Sources/ChatListController.swift',
}
def check(source, stage):
    manifest = json.loads(MANIFEST.read_text())
    config = json.loads((ROOT / 'jerkgram-migration.json').read_text())
    if config['upstream_new_sha'] != manifest['upstream_sha'] or set(manifest['owners']) != OWNERS:
        raise RuntimeError('Expanded diagnostics pin/owner scope changed')
    for name, values in manifest['owners'].items():
        data = (source / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != values[stage + '_sha256']:
            raise RuntimeError('Expanded diagnostics ' + stage + ' hash mismatch: ' + name)
        declarations = set(re.findall(r'(?m)^\s*(?:(?:public|private|fileprivate|internal|override|static|class|final|@objc)\s+)*func\s+(\w+)', data.decode()))
        if not set(values['survival_functions']) <= declarations:
            raise RuntimeError('Expanded diagnostics function lost: ' + name)
    for name, expected in manifest['regression_locks'].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('Expanded diagnostics regression lock changed: ' + name)
    return manifest

def verify_expanded(source):
    source = Path(source).resolve()
    manifest = check(source, 'after')
    verify_preferences(source, final_owners=manifest['owners'])
    subprocess.run([sys.executable, str(ROOT / 'tests/test_jg13_expanded_diagnostics.py')], env=dict(os.environ, JG13_SOURCE=str(source)), cwd=ROOT, check=True)

def apply_expanded(source):
    source = Path(source).resolve()
    git_root = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=source, text=True).strip()).resolve()
    if git_root != source: raise RuntimeError('Expanded diagnostic source must be its own Git root')
    manifest = check(source, 'before')
    names = {line.split('\t', 2)[2] for line in subprocess.check_output(['git', 'apply', '--numstat', str(PATCH)], cwd=source, text=True).splitlines()}
    if names != set(manifest['owners']): raise RuntimeError('Expanded patch owner set changed')
    subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=source, check=True)
    subprocess.run(['git', 'apply', str(PATCH)], cwd=source, check=True)
    verify_expanded(source)
    print('Expanded diagnostics PATCHED / VERIFIED; NOT COMPILED / NOT RUNTIME TESTED')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'work/swiftgram-src')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    (apply_expanded if args.apply else verify_expanded)(args.source)
