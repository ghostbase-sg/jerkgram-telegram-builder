#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()


def require(value, message):
    if not value:
        raise RuntimeError("[Build117 extension boundary verification] " + message)


def main():
    owners = {
        "submodules/BuildConfig/Sources/BuildConfig.m": ("BUILD117_EXTENSION_BOUNDARY_CLASSIFIER1", "processLocal", "/Documents/AppGroup"),
        "Telegram/Share/ShareRootController.swift": ("BUILD117_SHARE_VISIBLE_DIAGNOSTIC1", "classification != \"shared\""),
        "Telegram/WidgetKitWidget/TodayViewController.swift": ("BUILD117_WIDGET_VISIBLE_DIAGNOSTIC1", "case diagnostic(String)"),
        "Telegram/BroadcastUpload/BroadcastUploadExtension.swift": ("BUILD117_BROADCAST_VISIBLE_DIAGNOSTIC1", "finishWithError(stage:"),
    }
    for relative, tokens in owners.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for token in tokens:
            require(token in text, f"{relative}: missing {token}")
    print("[Build117 extension boundary verification] GREEN")


if __name__ == "__main__":
    main()
