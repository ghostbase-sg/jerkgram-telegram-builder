#!/usr/bin/env python3

from pathlib import Path
import subprocess
import sys

import jerkgram_publish_build122_artifact as base


base.EXPECTED_BUILD = "126"
base.OUTPUT_IPA = Path("artifacts/Jerkgram-Build126-canary.ipa")
base.OUTPUT_INFO = Path("artifacts/Jerkgram-Build126-canary-info.txt")
FINAL_VERIFY = Path("scripts/verify_jerkgram_v12o_build126_final_ipa.py")


def main() -> None:
    source = next((path for path in base.SOURCE_CANDIDATES if path.is_file()), None)
    base.require(source is not None, "final IPA source missing")
    subprocess.run([sys.executable, str(FINAL_VERIFY), str(source)], check=True)
    base.main()
    base.OUTPUT_INFO.write_text(
        base.OUTPUT_INFO.read_text(encoding="utf-8").replace("Build=122", "Build=126-canary"),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
