#!/usr/bin/env python3

from pathlib import Path

PROBE = Path(__file__).resolve().parent / "bazel_build_probe_official.sh"

APPGROUP_APPLY = "apply_jerkgram_v12d_build115_appgroup1.py"
APPGROUP_VERIFY = "verify_jerkgram_v12d_build115_appgroup1.py"
PROFILE_APPLY = "apply_jerkgram_v12d_build115_profile_ui1.py"
PROFILE_VERIFY = "verify_jerkgram_v12d_build115_profile_ui1.py"
LOCALIZATION_APPLY = "apply_jerkgram_v12d_build115_localization1.py"
LOCALIZATION_VERIFY = "verify_jerkgram_v12d_build115_localization1.py"
RESEARCH_APPLY = "apply_jerkgram_v12d_build115_research_settings1.py"
RESEARCH_VERIFY = "verify_jerkgram_v12d_build115_research_settings1.py"
SETTINGS_LOCALIZATION_APPLY = "apply_jerkgram_v12d_build115_settings_localization1.py"
SETTINGS_LOCALIZATION_VERIFY = "verify_jerkgram_v12d_build115_settings_localization1.py"
RECOVERY_APPLY = "apply_jerkgram_v12d_build115_recovery_english1.py"
RECOVERY_VERIFY = "verify_jerkgram_v12d_build115_recovery_english1.py"
NUMERIC_APPLY = "apply_jerkgram_v12d_build115_numeric_links1.py"
NUMERIC_VERIFY = "verify_jerkgram_v12d_build115_numeric_links1.py"

ANCHOR = '''echo
echo "== Jerkgram v1.2C Build114 source/runtime/UI =="
python3 ../../scripts/apply_jerkgram_v12c_build114_core1.py
python3 ../../scripts/verify_jerkgram_v12c_build114_core1.py
# END MARK: GhostBase v1.1G unified recovery
'''

REPLACEMENT = '''echo
echo "== Jerkgram v1.2C Build114 source/runtime/UI =="
python3 ../../scripts/apply_jerkgram_v12c_build114_core1.py
python3 ../../scripts/verify_jerkgram_v12c_build114_core1.py

echo
echo "== Jerkgram v1.2D Build115 AppGroup selection =="
python3 ../../scripts/apply_jerkgram_v12d_build115_appgroup1.py
python3 ../../scripts/verify_jerkgram_v12d_build115_appgroup1.py

echo
echo "== Jerkgram v1.2D Build115 profile UI =="
python3 ../../scripts/apply_jerkgram_v12d_build115_profile_ui1.py
python3 ../../scripts/verify_jerkgram_v12d_build115_profile_ui1.py

echo
echo "== Jerkgram v1.2D Build115 localization foundation =="
python3 ../../scripts/apply_jerkgram_v12d_build115_localization1.py
python3 ../../scripts/verify_jerkgram_v12d_build115_localization1.py

echo
echo "== Jerkgram v1.2D Build115 research Settings canonicalization =="
python3 ../../scripts/apply_jerkgram_v12d_build115_research_settings1.py --phase canonical

echo
echo "== Jerkgram v1.2D Build115 Settings localization =="
python3 ../../scripts/apply_jerkgram_v12d_build115_settings_localization1.py
python3 ../../scripts/verify_jerkgram_v12d_build115_settings_localization1.py

echo
echo "== Jerkgram v1.2D Build115 research Settings localization =="
python3 ../../scripts/apply_jerkgram_v12d_build115_research_settings1.py --phase localized
python3 ../../scripts/verify_jerkgram_v12d_build115_research_settings1.py

echo
echo "== Jerkgram v1.2D Build115 recovery English baseline =="
python3 ../../scripts/apply_jerkgram_v12d_build115_recovery_english1.py
python3 ../../scripts/verify_jerkgram_v12d_build115_recovery_english1.py

echo
echo "== Jerkgram v1.2D Build115 numeric links =="
python3 ../../scripts/apply_jerkgram_v12d_build115_numeric_links1.py
python3 ../../scripts/verify_jerkgram_v12d_build115_numeric_links1.py
# END MARK: GhostBase v1.1G unified recovery
'''


def require(value, message):
    if not value:
        raise RuntimeError("[Build115 probe hook] " + message)


def main():
    require(PROBE.is_file(), "probe missing: " + str(PROBE))
    text = PROBE.read_text(encoding="utf-8")

    expected_counts = {
        APPGROUP_APPLY: 1,
        APPGROUP_VERIFY: 1,
        PROFILE_APPLY: 1,
        PROFILE_VERIFY: 1,
        LOCALIZATION_APPLY: 1,
        LOCALIZATION_VERIFY: 1,
        RESEARCH_APPLY: 2,
        RESEARCH_VERIFY: 1,
        SETTINGS_LOCALIZATION_APPLY: 1,
        SETTINGS_LOCALIZATION_VERIFY: 1,
        RECOVERY_APPLY: 1,
        RECOVERY_VERIFY: 1,
        NUMERIC_APPLY: 1,
        NUMERIC_VERIFY: 1,
    }
    counts = {name: text.count(name) for name in expected_counts}

    if all(counts[name] == expected for name, expected in expected_counts.items()):
        print("[Build115 probe hook] already installed")
    else:
        require(
            all(value == 0 for value in counts.values()),
            "partial Build115 wiring: " + repr(counts)
        )
        require(text.count(ANCHOR) == 1, "Build114 probe anchor count != 1")
        text = text.replace(ANCHOR, REPLACEMENT, 1)
        PROBE.write_text(text, encoding="utf-8")

    check = PROBE.read_text(encoding="utf-8")
    for name, expected in expected_counts.items():
        require(check.count(name) == expected, "wiring count mismatch: " + name)

    research_first = check.index(RESEARCH_APPLY)
    research_second = check.index(RESEARCH_APPLY, research_first + len(RESEARCH_APPLY))

    order = [
        check.index("apply_jerkgram_v12c_build114_core1.py"),
        check.index("verify_jerkgram_v12c_build114_core1.py"),
        check.index(APPGROUP_APPLY),
        check.index(APPGROUP_VERIFY),
        check.index(PROFILE_APPLY),
        check.index(PROFILE_VERIFY),
        check.index(LOCALIZATION_APPLY),
        check.index(LOCALIZATION_VERIFY),
        research_first,
        check.index(SETTINGS_LOCALIZATION_APPLY),
        check.index(SETTINGS_LOCALIZATION_VERIFY),
        research_second,
        check.index(RESEARCH_VERIFY),
        check.index(RECOVERY_APPLY),
        check.index(RECOVERY_VERIFY),
        check.index(NUMERIC_APPLY),
        check.index(NUMERIC_VERIFY),
        check.index('"$BAZEL_BIN" build'),
    ]
    require(order == sorted(order), "Build114 -> Build115 -> Bazel order invalid")

    print(
        "[Build115 probe hook] GREEN: Build114 -> "
        "AppGroup -> profile UI -> localization -> research canonical -> "
        "Settings localization -> research localization -> recovery English -> "
        "numeric links -> Bazel"
    )


if __name__ == "__main__":
    main()
