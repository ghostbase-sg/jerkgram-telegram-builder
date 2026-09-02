#!/usr/bin/env python3

import verify_jerkgram_v12s_build128_final_ipa as base


base.base.EXPECTED_BUILD = "130"


def main() -> None:
    base.main()
    print("[Build130 final IPA verify] GREEN")


if __name__ == "__main__":
    main()
