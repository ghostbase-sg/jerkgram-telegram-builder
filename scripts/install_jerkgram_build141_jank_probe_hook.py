#!/usr/bin/env python3
from pathlib import Path
import os
import subprocess
import sys

import install_jerkgram_v12w_build133_probe_hook as base


SCRIPT_DIR = Path(__file__).resolve().parent
PROBE = Path(os.environ.get("JERKGRAM_PROBE_PATH", str(SCRIPT_DIR / "bazel_build_probe_official.sh"))).resolve()
UNIT_TEST_MODULE = "tests.test_jerkgram_build141_jank_probe1"
MARKER = "# JERKGRAM_BUILD141_JANK_PROBE1"
ANCHOR = "python3 ../../scripts/verify_jerkgram_build140_identity.py"
RUNTIME_REPAIR = "python3 ../../scripts/verify_jerkgram_v12w_build133_runtime_repair1.py"
BUILD141_ORDERED = (
    "apply_jerkgram_build141_jank_probe1.py",
    "verify_jerkgram_build141_jank_probe1.py",
)
_identity_index = base.SOURCE_ORDERED.index("verify_jerkgram_build140_identity.py") + 1
SOURCE_ORDERED = (
    base.SOURCE_ORDERED[:_identity_index]
    + BUILD141_ORDERED
    + base.SOURCE_ORDERED[_identity_index:]
)


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build141 probe hook] " + message)


def patch_probe(text: str) -> str:
    require(text.count(ANCHOR) == 1, "Build140 identity verifier anchor count")
    require(text.count(RUNTIME_REPAIR) == 1, "runtime repair verifier anchor count")
    payload = MARKER + "\n" + "\n".join("python3 ../../scripts/" + name for name in BUILD141_ORDERED)

    if MARKER in text:
        start = text.index(MARKER)
        end = text.find("\n" + RUNTIME_REPAIR, start)
        require(end > start, "existing Build141 block end")
        text = text[:start] + payload + text[end:]
    else:
        require(all(name not in text for name in BUILD141_ORDERED), "partial preexisting Build141 block")
        text = text.replace(ANCHOR, ANCHOR + "\n" + payload, 1)

    positions = [text.index(name) for name in BUILD141_ORDERED]
    require(positions == sorted(positions), "Build141 apply/verifier order")
    require(all(text.count(name) == 1 for name in BUILD141_ORDERED), "Build141 hook count")
    require(text.index(ANCHOR) < positions[0] < positions[-1] < text.index(RUNTIME_REPAIR), "Build141 must sit between identity140 and runtime repair")
    return text


def main() -> None:
    subprocess.check_call([sys.executable, "-m", "unittest", UNIT_TEST_MODULE], cwd=str(SCRIPT_DIR.parent))
    subprocess.check_call([sys.executable, str(SCRIPT_DIR / "install_jerkgram_v12w_build133_probe_hook.py")])
    require(PROBE.is_file(), "probe missing: " + str(PROBE))
    PROBE.write_text(patch_probe(PROBE.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build141 probe hook] GREEN")
    print("[Build141 probe hook] Build140 identity -> bounded jank probe -> runtime repair -> native Type1 -> Bazel")


if __name__ == "__main__":
    main()
