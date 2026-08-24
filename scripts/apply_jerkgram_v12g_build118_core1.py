#!/usr/bin/env python3

from pathlib import Path
import os
import shutil


REPO = Path(__file__).resolve().parents[1]
PAYLOAD = REPO / "scripts/jerkgram_v12g_build118_core1_payload"
ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()
DESTINATION = ROOT / "submodules/JerkgramCore"


def require(value, message):
    if not value:
        raise RuntimeError("[Build118 core] " + message)


def main():
    require(PAYLOAD.is_dir(), "payload missing")
    require(not DESTINATION.exists(), "foundation owner already exists: submodules/JerkgramCore")
    DESTINATION.mkdir(parents=True)
    shutil.copy2(PAYLOAD / "BUILD", DESTINATION / "BUILD")
    sources = DESTINATION / "Sources"
    sources.mkdir()
    for source in sorted(PAYLOAD.glob("*.swift")):
        shutil.copy2(source, sources / source.name)
    print("[Build118 core] account-scoped canonical store and reference index materialized")


if __name__ == "__main__":
    main()
