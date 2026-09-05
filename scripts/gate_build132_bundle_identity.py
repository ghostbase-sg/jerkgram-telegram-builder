#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
APPLY = SCRIPTS / "apply_build132_bundle_identity.py"
VERIFY = SCRIPTS / "verify_build132_active_bundle_identity.py"
SOURCE_ENV = "GHOSTBASE_SOURCE_ROOT"


def source_root() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    value = os.environ.get(SOURCE_ENV)
    if not value:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} <telegram-source-root> (or set {SOURCE_ENV})")
    return Path(value).resolve()


def run(script: Path, root: Path) -> None:
    if not script.is_file():
        raise SystemExit(f"[Build132 bundle identity gate] missing script: {script}")
    result = subprocess.run(
        [sys.executable, str(script), str(root)],
        text=True,
        capture_output=True,
        check=False,
        env=os.environ.copy(),
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        raise SystemExit(
            f"[Build132 bundle identity gate] FAIL: {script.name} exited {result.returncode}"
        )


def main() -> int:
    root = source_root()
    run(APPLY, root)
    run(VERIFY, root)
    print("[Build132 bundle identity gate] PASS: InstalledIdentity policy applied and verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
