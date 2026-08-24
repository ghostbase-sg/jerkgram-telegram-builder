#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
REPORT = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileReportPaneNode.swift"
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"

def require(value, message):
    if not value: raise RuntimeError("[verify Build118 profile report polish] " + message)

def main():
    report, strings = REPORT.read_text(), STRINGS.read_text()
    for token in ("BUILD118_PROFILE_REPORT_SEMANTICS1", "emojiStatusValue", '"Юзернейм:', '"Описание:', '"Эмодзи-статус:'):
        require(token in report, "missing " + token)
    require("suffix.prefix(while:" in report, "Swift Sequence.prefix label is not compile-safe")
    require("suffix.prefix(where:" not in report, "invalid Swift Sequence.prefix label remains")
    require('("Эмодзи-статус:", "Emoji status:")' in strings, "English semantic label missing")
    require('"Emoji-status: \\(previous.emojiStatus)' not in report, "raw Swift dump remains")
    print("[verify Build118 profile report polish] GREEN: no raw emoji object dump; RU/EN labels complete")

if __name__ == "__main__": main()
