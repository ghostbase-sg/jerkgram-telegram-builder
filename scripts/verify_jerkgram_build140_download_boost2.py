#!/usr/bin/env python3

from pathlib import Path
import os
import runpy


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_VERIFY = SCRIPT_DIR / "verify_jerkgram_build140_download_boost1.py"
ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
FETCH = ROOT / "submodules/TelegramCore/Sources/Network/FetchV2.swift"

RAW_PENDING = "maxPendingParts: 6,"
PATCHED_PENDING = "maxPendingParts: jerkgramDownloadMaxPendingParts(6),"
EXPECTED_PENDING_OWNERS = 4


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build140 Download Boost2 verify] " + message)


require(BASE_VERIFY.is_file(), "base verifier missing: " + str(BASE_VERIFY))
runpy.run_path(str(BASE_VERIFY), run_name="__main__")

require(FETCH.is_file(), "FetchV2 missing: " + str(FETCH))
fetch = FETCH.read_text(encoding="utf-8")
require(
    fetch.count(PATCHED_PENDING) == EXPECTED_PENDING_OWNERS,
    f"expected {EXPECTED_PENDING_OWNERS} patched pending owners, found {fetch.count(PATCHED_PENDING)}",
)
require(RAW_PENDING not in fetch, "stock maxPendingParts: 6 owner survived")
require("self.cdnPartSize = 128 * 1024" in fetch, "CDN chunk size no longer stock 128 KiB")

print("[Build140 Download Boost2 verify] GREEN")
print("[Build140 Download Boost2 verify] exact FetchV2 topology: 4 pending owners patched; no stock owner survived")
