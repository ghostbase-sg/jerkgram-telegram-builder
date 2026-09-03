#!/usr/bin/env python3

import os
from pathlib import Path


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
TELEGRAM_UI_BUILD = ROOT / "submodules/TelegramUI/BUILD"
MARKER = "// MARK: Jerkgram v1.2S BUILD130_SIRI_RUNTIME_FAILCLOSED1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[verify Build130 Siri fail-closed] " + message)


def balanced_region(text: str, token: str) -> str:
    start = text.find(token)
    require(start >= 0, "missing owner: " + token)
    brace = text.find("{", start)
    require(brace >= 0, "missing opening brace: " + token)
    depth = 0
    for index in range(brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise RuntimeError("[verify Build130 Siri fail-closed] unbalanced owner: " + token)


def verify_app_delegate(text: str) -> None:
    require(text.count(MARKER) == 1, "Build130 helper marker count")
    require("import Security" not in text, "Security must not be imported for iOS Siri fail-closed")
    for forbidden in ("SecTaskCreateFromSelf", "SecTaskCopyValueForEntitlement", "CFBooleanGetValue", "INPreferences.requestSiriAuthorization", "INPreferences.siriAuthorizationStatus"):
        require(forbidden not in text, "unavailable or active Siri API remains: " + forbidden)

    request = balanced_region(text, "requestSiriAuthorization: { completion in")
    require(request.count("completion(false)") == 1, "request binding must complete false exactly once")
    status = balanced_region(text, "siriAuthorization: {")
    require(status.strip().endswith("return .denied\n        }"), "status binding must return denied")


def main() -> None:
    for path in (APP_DELEGATE, TELEGRAM_UI_BUILD):
        require(path.is_file(), "missing source owner: " + str(path))
    verify_app_delegate(APP_DELEGATE.read_text(encoding="utf-8"))
    build = TELEGRAM_UI_BUILD.read_text(encoding="utf-8")
    require("swift_library(" in build and 'name = "TelegramUI"' in build, "TelegramUI Bazel owner drifted")
    print("[verify Build130 Siri fail-closed] SOURCE VERIFIED")


if __name__ == "__main__":
    main()
