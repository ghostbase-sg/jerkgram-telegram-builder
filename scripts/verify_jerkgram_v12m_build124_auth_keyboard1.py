#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()
PHONE = ROOT / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryControllerNode.swift"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("[Build124 auth keyboard verifier] " + message)


def main() -> None:
    require(PHONE.is_file(), f"missing source: {PHONE}")
    text = PHONE.read_text(encoding="utf-8")

    require("Jerkgram v1.2M BUILD124_AUTH_KEYBOARD1" in text, "keyboard marker missing")

    require(
        text.count("Jerkgram v1.2M BUILD124_AUTH_RUNTIME_LAYOUT1") == 1,
        "final keyboard layout owner missing or duplicated",
    )
    require("self.ghostBaseBotLoginNode.isHidden = jerkgramKeyboardVisible" in text, "bot-login action still overlaps keyboard layout")
    require("self.ghostBaseSafeLoginNode.isHidden = jerkgramKeyboardVisible" in text, "Safe Login stack still overlaps keyboard layout")
    require("Режим призрака: ВКЛ" in text and "Включите до входа" in text, "Ghost-login localisation missing")

    # Regression gate: the phone input remains an input-height-aware Telegram
    # layout. This fix must not disable keyboard inset handling itself.
    require(
        "if let inputHeight = layout.inputHeight, !inputHeight.isZero" in text,
        "official input-height inset handling was lost",
    )

    print("[Build124 auth keyboard verifier] GREEN")
    print("[Build124 auth keyboard verifier] phone auth content stays above Safe Login stack while keyboard is visible")


if __name__ == "__main__":
    main()
