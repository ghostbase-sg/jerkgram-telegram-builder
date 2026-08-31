#!/usr/bin/env python3
from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent
BASE = HERE / "verify_jerkgram_v12t_build130_release_ui_telemetry1.py"
spec = importlib.util.spec_from_file_location("build130_verify_base", BASE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.PROFILE = module.ROOT / "submodules/TelegramUI/Sources/PeerInfoHeaderNode.swift"

if __name__ == "__main__":
    module.main()
