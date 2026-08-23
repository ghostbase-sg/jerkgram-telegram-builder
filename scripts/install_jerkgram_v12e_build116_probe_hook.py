#!/usr/bin/env python3

from pathlib import Path


PROBE = Path(__file__).resolve().parent / "bazel_build_probe_official.sh"

ORDERED_SCRIPTS = (
    "apply_jerkgram_v12e_build116_ui1.py",
    "verify_jerkgram_v12e_build116_ui1.py",
    "apply_jerkgram_v12e_build116_extensions1.py",
    "verify_jerkgram_v12e_build116_extensions1.py",
    "apply_jerkgram_v12e_build116_foundation1.py",
    "verify_jerkgram_v12e_build116_foundation1.py",
)

ANCHOR = '''python3 ../../scripts/apply_jerkgram_v12d_build115_numeric_links1.py
python3 ../../scripts/verify_jerkgram_v12d_build115_numeric_links1.py
# END MARK: GhostBase v1.1G unified recovery'''

BLOCK = '''python3 ../../scripts/apply_jerkgram_v12d_build115_numeric_links1.py
python3 ../../scripts/verify_jerkgram_v12d_build115_numeric_links1.py

echo
echo "== Jerkgram v1.2E Build116 user-facing fixes =="
python3 ../../scripts/apply_jerkgram_v12e_build116_ui1.py
python3 ../../scripts/verify_jerkgram_v12e_build116_ui1.py

echo
echo "== Jerkgram v1.2E Build116 extension diagnostics =="
python3 ../../scripts/apply_jerkgram_v12e_build116_extensions1.py
python3 ../../scripts/verify_jerkgram_v12e_build116_extensions1.py

echo
echo "== Jerkgram v1.2E Build116 typed foundations =="
python3 ../../scripts/apply_jerkgram_v12e_build116_foundation1.py
python3 ../../scripts/verify_jerkgram_v12e_build116_foundation1.py
# END MARK: GhostBase v1.1G unified recovery'''


def require(value, message):
    if not value:
        raise RuntimeError("[Build116 probe hook] " + message)


def patch_probe(text):
    counts = {name: text.count(name) for name in ORDERED_SCRIPTS}
    if all(value == 1 for value in counts.values()):
        result = text
    else:
        require(all(value == 0 for value in counts.values()), "partial Build116 wiring: " + repr(counts))
        require(text.count(ANCHOR) == 1, "Build115 numeric anchor count != 1")
        result = text.replace(ANCHOR, BLOCK, 1)
    positions = [result.index("verify_jerkgram_v12d_build115_numeric_links1.py")]
    positions.extend(result.index(name) for name in ORDERED_SCRIPTS)
    positions.append(result.index('"$BAZEL_BIN" build'))
    require(positions == sorted(positions), "Build115 -> Build116 -> Bazel order invalid")
    return result


def main():
    require(PROBE.is_file(), "probe missing: " + str(PROBE))
    PROBE.write_text(patch_probe(PROBE.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build116 probe hook] GREEN: Build115 -> UI -> extensions -> foundation -> Bazel")


if __name__ == "__main__":
    main()
