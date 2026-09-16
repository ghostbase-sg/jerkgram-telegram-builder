#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"

GUARD = "        guard url.absoluteString.utf8.count <= 3072,\n"
DUPLICATE_GUARD = GUARD + GUARD
AUTHORIZE = "private func handleJerkgramNotificationsAuthorizeUrl(_ url: URL) -> Bool"
RECONCILE = "private func handleJerkgramNotificationsReconcileUrl(_ url: URL) -> Bool"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build139 reconcile compile fix] " + message)


def normalize_text(text: str) -> str:
    require(AUTHORIZE in text, "authorize helper missing")
    require(RECONCILE in text, "reconcile helper missing")

    # The Build139 materialization chain can encounter a previously patched
    # reconcile helper before the canonical v13A patch is replayed. The old
    # incremental path left the size guard twice in succession, which parses
    # but fails Swift type checking as `guard ..., guard ...`.
    while DUPLICATE_GUARD in text:
        text = text.replace(DUPLICATE_GUARD, GUARD, 1)

    # Exactly one URL-size guard belongs to /authorize and one to /reconcile.
    require(text.count(GUARD) == 2, f"expected exactly two URL size guards, found {text.count(GUARD)}")
    require(DUPLICATE_GUARD not in text, "duplicate guard survived normalization")
    return text


def main() -> None:
    require(APP_DELEGATE.is_file(), "AppDelegate missing: " + str(APP_DELEGATE))
    text = APP_DELEGATE.read_text(encoding="utf-8")
    normalized = normalize_text(text)
    APP_DELEGATE.write_text(normalized, encoding="utf-8")
    print("[Build139 reconcile compile fix] GREEN")
    print("[Build139 reconcile compile fix] /authorize and /reconcile each contain exactly one URL-size guard")


if __name__ == "__main__":
    main()
