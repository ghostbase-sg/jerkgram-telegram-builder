#!/usr/bin/env python3
"""Apply only the explicitly approved, exact source-dependency exception."""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work/swiftgram-src"
PATH = "submodules/rlottie/rlottie"
ORIGINAL = "53c9679069eb6b6513ccc3c892ef4f4a760658da"
FALLBACK = "67f103bc8b625f2a4a9e94f1d8c7bd84c5a08d1d"


def git(*args, cwd=None):
    return subprocess.check_output(["git", *args], cwd=cwd or SOURCE, text=True).strip()


def main(verify=False):
    config = json.loads((ROOT / "jerkgram-migration.json").read_text())
    assert git("rev-parse", "HEAD") == config["upstream_new_sha"], "Upstream pin changed"
    assert git("ls-tree", "HEAD", PATH).split()[2] == ORIGINAL, "Original gitlink changed"
    exception = config["dependency_overrides"][PATH]
    assert exception["original_sha"] == ORIGINAL and exception["source_sha"] == FALLBACK
    assert exception["repository"] == "TelegramMessenger/rlottie"
    if verify:
        assert git("rev-parse", "HEAD", cwd=SOURCE / PATH) == FALLBACK, "Wrong rlottie source"
        print("Approved rlottie source SHA VERIFIED; runtime compatibility NOT TESTED")
    else:
        entry = git("ls-files", "--stage", PATH).split()
        assert entry[0] == "160000" and entry[1] in (ORIGINAL, FALLBACK)
        subprocess.run(["git", "update-index", "--cacheinfo", "160000," + FALLBACK + "," + PATH], cwd=SOURCE, check=True)
        print(f"Approved source fallback: {PATH} {ORIGINAL} -> {FALLBACK}")


if __name__ == "__main__":
    main(verify="--verify" in sys.argv)
