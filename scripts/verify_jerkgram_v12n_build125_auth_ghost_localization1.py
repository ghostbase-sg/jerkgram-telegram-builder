#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
PHONE = ROOT / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryControllerNode.swift"
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
MARKER = "// MARK: Jerkgram v1.2N BUILD125_AUTH_GHOST_LOCALIZATION1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build125 auth ghost localization verify] " + message)


def main() -> None:
    phone = PHONE.read_text(encoding="utf-8")
    strings = STRINGS.read_text(encoding="utf-8")
    require(MARKER in phone and MARKER in strings, "Build125 localization markers missing")
    require("BUILD125_AUTH_BOT_LOGIN_LOCALIZATION2" in phone, "bot-login localization marker missing")
    require("strings.jerkgram.authGhostModeStatus(enabled: enabled)" in phone, "Ghost Mode status is not wired to selected app language")
    require("strings.jerkgram.authGhostModeHint" in phone, "Ghost Mode hint is not wired to selected app language")
    require("strings.jerkgram.botLoginButton" in phone, "bot-login title is not wired to selected app language")
    require("strings.jerkgram.botLoginAccessibility" in phone, "bot-login accessibility is not wired to selected app language")
    require("Locale.current" not in phone, "login UI must not use the device locale")
    require("func authGhostModeStatus(enabled: Bool)" in strings, "state localizer missing")
    require("var authGhostModeHint: String" in strings, "hint localizer missing")
    require("self.languageCode == \"ru\"" in strings, "language selection missing")
    print("[Build125 auth ghost localization verify] GREEN")


if __name__ == "__main__":
    main()
