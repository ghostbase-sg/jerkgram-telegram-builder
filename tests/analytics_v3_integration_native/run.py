#!/usr/bin/env python3
"""Execute the real production pre-bootstrap evidence probe with the real v3 module."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SWIFT = shutil.which('swiftc')
if not SWIFT:
    raise SystemExit('BLOCKED: native Swift compiler unavailable; installation probe not executed')
payload = ROOT / 'scripts/jerkgram_analytics_v3_payload'
with tempfile.TemporaryDirectory(prefix='analytics-integration-native-') as scratch:
    binary = Path(scratch) / 'probe'
    subprocess.run([SWIFT, str(payload / 'JerkgramAnalyticsV3.swift'), str(payload / 'JerkgramAnalyticsV3InstallationProbe.swift'), str(Path(__file__).with_name('main.swift')), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
