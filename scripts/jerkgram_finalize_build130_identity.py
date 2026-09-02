#!/usr/bin/env python3

import jerkgram_finalize_build128_identity as base


base.base.BUILD = "130"


def main() -> None:
    base.main()
    print("[Build130 identity] GREEN")
    print("[Build130 identity] CFBundleVersion=130; Build128 package topology preserved")


if __name__ == "__main__":
    main()
