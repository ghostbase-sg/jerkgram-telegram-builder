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


def payload_files():
    return {
        Path("BUILD"): PAYLOAD / "BUILD",
        **{
            Path("Sources") / source.name: source
            for source in sorted(PAYLOAD.glob("*.swift"))
        },
    }


def destination_is_recognized_core() -> bool:
    expected = payload_files()
    if not DESTINATION.is_dir():
        return False
    # Later Build119+ overlays extend JerkgramStore.swift. The immutable BUILD,
    # model and index owners still identify the Build118 foundation, while the
    # Store declaration proves it is the same core rather than an arbitrary
    # pre-existing directory.
    for relative in (Path("BUILD"), Path("Sources/JerkgramModels.swift"), Path("Sources/JerkgramIndex.swift")):
        target = DESTINATION / relative
        source = expected[relative]
        if not target.is_file() or target.read_bytes() != source.read_bytes():
            return False
    store = DESTINATION / "Sources/JerkgramStore.swift"
    if not store.is_file():
        return False
    return "public enum JerkgramCaptureRecorder" in store.read_text(encoding="utf-8")


def main():
    require(PAYLOAD.is_dir(), "payload missing")
    if DESTINATION.exists():
        require(
            destination_is_recognized_core(),
            "foundation owner exists with different content: submodules/JerkgramCore",
        )
        print("[Build118 core] account-scoped canonical store and reference index already materialized")
        return
    DESTINATION.mkdir(parents=True)
    for relative, source in payload_files().items():
        target = DESTINATION / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    print("[Build118 core] account-scoped canonical store and reference index materialized")


if __name__ == "__main__":
    main()
