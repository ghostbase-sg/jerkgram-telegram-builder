#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
MARKER = "// MARK: Jerkgram v1.3A0 BUILD139_APPDELEGATE_IMPORT_COMPAT"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build139 AppDelegate import compat] " + message)


def patch_app_delegate_text(text: str) -> str:
    if "import Foundation\n" in text:
        return text

    # The fully materialized Build138 chain starts AppDelegate with UIKit rather
    # than Foundation. Build139's notification bridge needs a stable Foundation
    # import anchor for URLComponents/Data and for the following JerkgramCore
    # insertion. Normalize only the import list; do not touch runtime behavior.
    anchor = "import UIKit\n"
    require(text.count(anchor) == 1, "expected exactly one UIKit import anchor")
    text = text.replace(anchor, anchor + "import Foundation\n", 1)
    require(text.count("import Foundation\n") == 1, "Foundation import normalization failed")
    return text


def main() -> None:
    require(APP_DELEGATE.is_file(), "AppDelegate missing: " + str(APP_DELEGATE))
    source = APP_DELEGATE.read_text(encoding="utf-8")
    patched = patch_app_delegate_text(source)
    APP_DELEGATE.write_text(patched, encoding="utf-8")
    print("[Build139 AppDelegate import compat] SOURCE NORMALIZED")


if __name__ == "__main__":
    main()
