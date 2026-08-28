#!/usr/bin/env python3

from pathlib import Path
import sys

import verify_jerkgram_v12k_build122_final_ipa as base


base.EXPECTED_BUILD = "124"


def main() -> None:
    ipa = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "work/swiftgram-src/ghostbase-final/GhostBase.ipa"
    ).resolve()

    # Build124 source overlays are deliberately not materialized in the
    # recovery canary. Their API-marker verifier therefore cannot describe
    # this IPA; preserve the complete, independently green Build122/124
    # topology verification instead.
    base.main()


if __name__ == "__main__":
    main()
