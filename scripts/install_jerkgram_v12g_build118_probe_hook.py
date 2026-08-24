#!/usr/bin/env python3
from pathlib import Path

PROBE = Path(__file__).resolve().parent / "bazel_build_probe_official.sh"
ORDERED = (
    "apply_jerkgram_v12g_build118_core1.py", "verify_jerkgram_v12g_build118_core1.py",
    "apply_jerkgram_v12g_build118_storage1.py", "verify_jerkgram_v12g_build118_storage1.py",
    "apply_jerkgram_v12g_build118_time_machine1.py", "verify_jerkgram_v12g_build118_time_machine1.py",
    "apply_jerkgram_v12g_build118_archive1.py", "verify_jerkgram_v12g_build118_archive1.py",
    "apply_jerkgram_v12g_build118_about_cards1.py", "verify_jerkgram_v12g_build118_about_cards1.py",
    "apply_jerkgram_v12g_build118_profile_report_polish1.py", "verify_jerkgram_v12g_build118_profile_report_polish1.py",
    "apply_jerkgram_v12g_build118_integration1.py",
    "apply_jerkgram_v12g_build118_data_ui1.py", "verify_jerkgram_v12g_build118_data_ui1.py",
    "apply_jerkgram_v12g_build118_time_machine_ui1.py", "verify_jerkgram_v12g_build118_time_machine_ui1.py",
    "apply_jerkgram_v12g_build118_glass1.py", "verify_jerkgram_v12g_build118_glass1.py",
    "apply_jerkgram_v12g_build118_since_last_open1.py", "verify_jerkgram_v12g_build118_since_last_open1.py",
    "verify_jerkgram_v12g_build118_release_readiness1.py",
)
ANCHOR = "python3 ../../scripts/verify_jerkgram_v12f_build117_release_readiness1.py\n"

def require(value, message):
    if not value: raise RuntimeError("[Build118 probe hook] " + message)

def main():
    require(PROBE.is_file(), "probe missing")
    text = PROBE.read_text()
    counts = [text.count(name) for name in ORDERED]
    if all(count == 0 for count in counts):
        require(text.count(ANCHOR) == 1, "Build117 release anchor count != 1")
        block = ANCHOR + '\necho\necho "== Jerkgram v1.2G Build118 =="\n' + "\n".join("python3 ../../scripts/" + name for name in ORDERED) + "\n"
        text = text.replace(ANCHOR, block, 1)
    else:
        require(all(count == 1 for count in counts), "partial Build118 wiring")
    positions = [text.index(name) for name in ORDERED]
    require(positions == sorted(positions), "Build118 overlay order invalid")
    require(positions[-1] < text.index('"$BAZEL_BIN" build'), "Build118 runs after Bazel")
    PROBE.write_text(text)
    print("[Build118 probe hook] GREEN: Build118 overlays precede Bazel")

if __name__ == "__main__": main()
