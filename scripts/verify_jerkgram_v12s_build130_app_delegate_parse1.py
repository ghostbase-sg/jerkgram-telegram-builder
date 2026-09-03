#!/usr/bin/env python3

import os
from pathlib import Path
import shutil
import subprocess


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[verify Build130 AppDelegate parse] " + message)


def swiftc_path() -> str:
    direct = shutil.which("swiftc")
    if direct:
        return direct
    result = subprocess.run(["xcrun", "--find", "swiftc"], text=True, capture_output=True)
    require(result.returncode == 0 and result.stdout.strip(), "swiftc not found through xcrun: " + result.stderr.strip())
    return result.stdout.strip()


def main() -> None:
    require(APP_DELEGATE.is_file(), "missing AppDelegate: " + str(APP_DELEGATE))
    result = subprocess.run([swiftc_path(), "-parse", str(APP_DELEGATE)], text=True, capture_output=True)
    require(result.returncode == 0, "Swift parser rejected materialized AppDelegate:\n" + result.stderr[-4000:])
    print("[verify Build130 AppDelegate parse] GREEN")


if __name__ == "__main__":
    main()
