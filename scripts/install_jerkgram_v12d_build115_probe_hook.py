#!/usr/bin/env python3

from pathlib import Path


PROBE = (
    Path(__file__)
    .resolve()
    .parent
    / "bazel_build_probe_official.sh"
)

APPLY = (
    "apply_jerkgram_v12d_build115_appgroup1.py"
)

VERIFY = (
    "verify_jerkgram_v12d_build115_appgroup1.py"
)

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
# END MARK: GhostBase v1.1G unified recovery
'''


def require(value, message):
    if not value:
        raise RuntimeError(
            "[Build115 probe hook] "
            + message
        )


def main():
    require(
        PROBE.is_file(),
        "probe missing: "
        + str(PROBE)
    )

    text = PROBE.read_text(
        encoding="utf-8"
    )

    apply_count = text.count(
        APPLY
    )

    verify_count = text.count(
        VERIFY
    )

    if (
        apply_count == 1
        and verify_count == 1
    ):
        print(
            "[Build115 probe hook] "
            "already installed"
        )
    else:
        require(
            apply_count == 0
            and verify_count == 0,
            (
                "partial Build115 wiring: "
                f"apply={apply_count} "
                f"verify={verify_count}"
            )
        )

        require(
            text.count(ANCHOR) == 1,
            (
                "Build114 probe anchor count != 1: "
                f"{text.count(ANCHOR)}"
            )
        )

        text = text.replace(
            ANCHOR,
            REPLACEMENT,
            1
        )

        PROBE.write_text(
            text,
            encoding="utf-8"
        )

    check = PROBE.read_text(
        encoding="utf-8"
    )

    require(
        check.count(APPLY) == 1,
        "Build115 apply wiring count != 1"
    )

    require(
        check.count(VERIFY) == 1,
        "Build115 verify wiring count != 1"
    )

    build114_apply = check.index(
        "apply_jerkgram_v12c_build114_core1.py"
    )

    build114_verify = check.index(
        "verify_jerkgram_v12c_build114_core1.py"
    )

    build115_apply = check.index(
        APPLY
    )

    build115_verify = check.index(
        VERIFY
    )

    bazel = check.index(
        '"$BAZEL_BIN" build'
    )

    require(
        (
            build114_apply
            < build114_verify
            < build115_apply
            < build115_verify
            < bazel
        ),
        "Build114 -> Build115 -> Bazel order invalid"
    )

    print(
        "[Build115 probe hook] GREEN: "
        "Build114 -> Build115 -> Bazel"
    )


if __name__ == "__main__":
    main()
