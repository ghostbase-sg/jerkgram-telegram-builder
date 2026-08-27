#!/usr/bin/env python3

from pathlib import Path
import subprocess
import sys

import jerkgram_publish_build122_artifact as base


base.EXPECTED_BUILD = "124"
base.OUTPUT_IPA = Path("artifacts/Jerkgram-Build124-canary.ipa")
base.OUTPUT_INFO = Path("artifacts/Jerkgram-Build124-canary-info.txt")
FINAL_VERIFY = Path("scripts/verify_jerkgram_v12m_build124_final_ipa.py")


def main() -> None:
    source = next((path for path in base.SOURCE_CANDIDATES if path.is_file()), None)
    base.require(source is not None, "final IPA source missing")

    # The canary is not publishable even as a private Actions artifact until
    # its compiled API identity and ordinary Build124 IPA topology both pass.
    subprocess.run(
        [sys.executable, str(FINAL_VERIFY), str(source)],
        check=True,
    )

    base.main()
    text = base.OUTPUT_INFO.read_text(encoding="utf-8")
    base.OUTPUT_INFO.write_text(
        text.replace("Build=122", "Build=124-canary"),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
