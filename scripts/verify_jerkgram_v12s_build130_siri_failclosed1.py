#!/usr/bin/env python3

import os
from pathlib import Path


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
MARKER = "// MARK: Jerkgram v1.2S BUILD130_SIRI_RUNTIME_FAILCLOSED1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[verify Build130 Siri fail-closed] " + message)


def balanced_region(text: str, token: str) -> str:
    start = text.find(token)
    require(start >= 0, "missing owner: " + token)
    token_brace = token.rfind("{")
    brace = start + token_brace if token_brace >= 0 else text.find("{", start + len(token))
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
    require(text.count(MARKER) == 1, "Build130 marker count")
    request = balanced_region(text, "requestSiriAuthorization: { completion in")
    status = balanced_region(text, "siriAuthorization: {")
    require("completion(false)" in request, "request binding lacks fail-closed completion")
    require("return .denied" in status, "status binding lacks fail-closed denied result")
    for region, name in ((request, "request"), (status, "status")):
        require("INPreferences" not in region, name + " binding still calls Siri API")
        require("buildConfig.isSiriEnabled" not in region, name + " binding still treats build configuration as entitlement")
        require("jerkgramHasRuntimeSiriEntitlement" not in region, name + " binding retains obsolete entitlement helper")
    for forbidden in ("import Security", "import JerkgramSiriEntitlement", "SecTask", "JerkgramSiriEntitlement"):
        require(forbidden not in text, "obsolete Siri entitlement bridge remains: " + forbidden)


def main() -> None:
    require(APP_DELEGATE.is_file(), "missing source owner: " + str(APP_DELEGATE))
    verify_app_delegate(APP_DELEGATE.read_text(encoding="utf-8"))
    print("[verify Build130 Siri fail-closed] SOURCE VERIFIED")


if __name__ == "__main__":
    main()
