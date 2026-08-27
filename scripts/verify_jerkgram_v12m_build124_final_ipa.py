#!/usr/bin/env python3

import os
from pathlib import Path
import sys

import verify_jerkgram_build124_telegram_api_ipa1 as api_verify
import verify_jerkgram_v12k_build122_final_ipa as base


base.EXPECTED_BUILD = "124"


def main() -> None:
    ipa = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "work/swiftgram-src/ghostbase-final/GhostBase.ipa"
    ).resolve()
    api_verify.verify_ipa_credentials(
        ipa,
        os.environ.get("JERKGRAM_TELEGRAM_API_HASH", ""),
    )
    base.main()


if __name__ == "__main__":
    main()
