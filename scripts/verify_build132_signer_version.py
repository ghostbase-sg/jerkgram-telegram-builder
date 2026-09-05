#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SOURCE_ENV = "GHOSTBASE_SOURCE_ROOT"
TARGET = Path("versions.json")
EXPECTED_VERSION = "12.9.2"


def source_root() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    value = os.environ.get(SOURCE_ENV)
    if not value:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} <telegram-source-root> (or set {SOURCE_ENV})")
    return Path(value).resolve()


def fail(message: str) -> None:
    raise SystemExit(f"[build132-signer-version-verify] FAIL: {message}")


def main() -> int:
    path = source_root() / TARGET
    if not path.is_file():
        fail(f"missing {TARGET}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid versions.json: {exc}")
    if not isinstance(data, dict):
        fail("versions.json root is not an object")
    if data.get("app") != EXPECTED_VERSION:
        fail(f"versions.json['app'] must be {EXPECTED_VERSION!r}, got {data.get('app')!r}")
    for required in ("xcode", "deploy_xcode", "bazel", "macos"):
        if required not in data:
            fail(f"required upstream version key missing: {required}")
    forbidden = {"1.0.0", "1.0.2", "1.0.2-beta.1", "1.0.2 Beta 1"}
    if data["app"] in forbidden:
        fail("Jerkgram product version leaked into signer-visible Telegram app version")
    print("[build132-signer-version-verify] PASS: signer-visible CFBundleShortVersionString source is 12.9.2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
