#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
PHONE = ROOT / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryControllerNode.swift"
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
MARKER = "// MARK: Jerkgram v1.2N BUILD125_AUTH_GHOST_LOCALIZATION1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build125 auth ghost localization] " + message)


EXTENSION = r'''

// MARK: Jerkgram v1.2N BUILD125_AUTH_GHOST_LOCALIZATION1
// Login controls must follow the app language before an account session exists.
public extension JerkgramStrings {
    private var authGhostIsRussian: Bool { self.languageCode == "ru" }

    func authGhostModeStatus(enabled: Bool) -> String {
        if self.authGhostIsRussian {
            return enabled ? "👻 Режим призрака: ВКЛ" : "👻 Режим призрака: ВЫКЛ"
        } else {
            return enabled ? "👻 Ghost Mode: ON" : "👻 Ghost Mode: OFF"
        }
    }

    var authGhostModeHint: String {
        return self.authGhostIsRussian
            ? "Включите до входа, чтобы оставаться невидимым с первой сессии."
            : "Enable before login to stay invisible from the first session."
    }
}
'''


def patch_phone(text: str) -> str:
    if MARKER in text:
        return text
    replacements = {
        'return enabled ? "👻 Режим призрака: ВКЛ" : "👻 Режим призрака: ВЫКЛ"': 'return strings.jerkgram.authGhostModeStatus(enabled: enabled)',
        'return enabled ? "👻 Ghost Mode: ON" : "👻 Ghost Mode: OFF"': 'return strings.jerkgram.authGhostModeStatus(enabled: enabled)',
        'string: "Включите до входа, чтобы оставаться невидимым с первой сессии."': 'string: strings.jerkgram.authGhostModeHint',
        'string: "Enable before login to stay invisible from the first session."': 'string: strings.jerkgram.authGhostModeHint',
    }
    changed = 0
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new, 1)
            changed += 1
    require(changed == 2, f"expected Ghost Mode title and hint owners, patched {changed}")
    return text + "\n" + MARKER + "\n"


def patch_strings(text: str) -> str:
    if MARKER in text:
        return text
    require("public struct JerkgramStrings" in text, "JerkgramStrings owner missing")
    return text.rstrip() + EXTENSION + "\n"


def main() -> None:
    require(PHONE.is_file(), f"missing phone entry owner: {PHONE}")
    require(STRINGS.is_file(), f"missing JerkgramStrings owner: {STRINGS}")
    PHONE.write_text(patch_phone(PHONE.read_text(encoding="utf-8")), encoding="utf-8")
    STRINGS.write_text(patch_strings(STRINGS.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build125 auth ghost localization] GREEN")


if __name__ == "__main__":
    main()
