#!/usr/bin/env python3
from pathlib import Path
import runpy

lite = Path(__file__).with_name("apply_ghostbase_history_channel_v09f3_lite.py")

if not lite.exists():
    raise SystemExit("ERROR: missing apply_ghostbase_history_channel_v09f3_lite.py")

print("[v0.9F.3] redirected to v0.9F.3-lite: no ghostBaseEditHistory enum")
runpy.run_path(str(lite), run_name="__main__")
