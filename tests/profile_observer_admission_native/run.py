#!/usr/bin/env python3
"""Compile and execute the production admission core. No Python behavioral substitute."""
from pathlib import Path
import shutil, subprocess, tempfile
ROOT = Path(__file__).resolve().parents[2]
swift = shutil.which('swiftc')
if not swift:
    raise SystemExit('BLOCKED: swiftc unavailable; admission behavior NOT executed')
with tempfile.TemporaryDirectory() as directory:
    binary = Path(directory) / 'admission'
    subprocess.run([swift, '-O', str(ROOT/'scripts/jerkgram_profile_observer_v1_payload/JerkgramProfileObserverAdmission.swift'), str(Path(__file__).with_name('main.swift')), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
