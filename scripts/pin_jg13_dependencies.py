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
    if config["upstream_new_sha"] == "24638bc69bd083981b178dd1e7f921eebbf7fc46":
        assert git("rev-parse", "HEAD") == config["upstream_new_sha"], "Wrong genuine13.2head"
        assert not git("ls-tree", "HEAD", "submodules/rlottie"), "Obsolete rlottie unexpectedly present"
        assert PATH not in config.get("dependency_overrides", {}), "Obsolete rlottie override"
        assert git("ls-tree", "HEAD", "submodules/tlottie/tlottie").split()[:3] == ["160000", "commit", "92df98dc209bc39b1e567ec74a8c86a0af5239de"]
        print("Official13.2dependency contract VERIFIED; rlottie removed upstream, tlottie unchanged; runtime separate")
        return
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
