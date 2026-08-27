#!/usr/bin/env python3
import jerkgram_publish_build122_artifact as base
from pathlib import Path

base.EXPECTED_BUILD = "123"
base.OUTPUT_IPA = Path("artifacts/Jerkgram-build123.ipa")
base.OUTPUT_INFO = Path("artifacts/Jerkgram-build123-info.txt")

if __name__ == "__main__":
    base.main()
    text = base.OUTPUT_INFO.read_text(encoding="utf-8")
    base.OUTPUT_INFO.write_text(text.replace("Build=122", "Build=123"), encoding="utf-8")
