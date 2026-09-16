#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"

MARKER = "// MARK: Jerkgram v1.3C BUILD139_RELEASE_IDENTITY1"
OLD_BUILD = 'public static let build = "138"'
NEW_BUILD = 'public static let build = "139"'


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build139 release identity] " + message)


def patch_strings_text(text: str) -> str:
    if MARKER in text:
        require(text.count(MARKER) == 1, "release identity marker is ambiguous")
        require(NEW_BUILD in text, "Build139 identity marker exists without build=139")
        return text

    require(text.count(OLD_BUILD) == 1, "expected exactly one Build138 release identity owner")
    require('public static let displayVersion = "1.0.2"' in text, "Jerkgram display version changed")
    require('public static let technicalVersion = "1.0.2"' in text, "Jerkgram technical version changed")
    require('public static let telegramBase = "12.9.2"' in text, "Telegram base changed")
    text = text.replace(OLD_BUILD, NEW_BUILD, 1)
    enum_anchor = "public enum JerkgramReleaseIdentity {"
    require(text.count(enum_anchor) == 1, "JerkgramReleaseIdentity owner mismatch")
    text = text.replace(enum_anchor, MARKER + "\n" + enum_anchor, 1)
    return text


def main() -> None:
    require(STRINGS.is_file(), "JerkgramStrings missing: " + str(STRINGS))
    STRINGS.write_text(patch_strings_text(STRINGS.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build139 release identity] SOURCE PATCHED")
    print("[Build139 release identity] Jerkgram 1.0.2 / Build 139 / Telegram Base 12.9.2")


if __name__ == "__main__":
    main()
