#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
MENU = ROOT / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build125 single forward verify] " + message)


def validate(text: str) -> None:
    marker = "BUILD125_SINGLE_FORWARD_DIRECT_ACTION1"
    require(text.count(marker) == 1, "direct one-message forward owner missing")
    start = text.index(marker)
    end = text.find("if data.messageActions.options.contains", start)
    owner = text[start:] if end < 0 else text[start:end]
    require("let jerkgramForwardWithoutAuthorTargets = selectAll ? messages : [message]" in owner, "single target scope missing")
    require("jerkgramForwardWithoutAuthorTargets.allSatisfy" in owner, "safe target validation missing")
    executable_owner = re.sub(r"//[^\n]*", "", owner)
    require("data.messageActions.options.contains(.forward)" not in executable_owner, "direct action is still hidden by native forward permission")
    require("Namespaces.Peer.SecretChat" in owner and "TelegramMediaPaidContent" in owner and "TelegramMediaExpiredContent" in owner, "unsafe message exclusions missing")
    print("[Build125 single forward verify] GREEN")


def main() -> None:
    validate(MENU.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
