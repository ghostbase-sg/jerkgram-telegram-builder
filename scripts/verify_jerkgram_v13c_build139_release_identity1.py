#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build139 release identity verify] " + message)


def main() -> None:
    require(STRINGS.is_file(), "JerkgramStrings missing")
    text = STRINGS.read_text(encoding="utf-8")
    require('public static let displayVersion = "1.0.2"' in text, "display version is not 1.0.2")
    require('public static let technicalVersion = "1.0.2"' in text, "technical version is not 1.0.2")
    require('public static let build = "139"' in text, "Jerkgram build is not 139")
    require('public static let build = "138"' not in text, "stale Build138 release identity survived")
    require('public static let telegramBase = "12.9.2"' in text, "Telegram base is not 12.9.2")
    print("[Build139 release identity verify] GREEN")


if __name__ == "__main__":
    main()
