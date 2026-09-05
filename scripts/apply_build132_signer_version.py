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


def main() -> int:
    root = source_root()
    path = root / TARGET
    if not path.is_file():
        raise SystemExit(f"[build132-signer-version] missing {TARGET}")

    original_text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(original_text)
    except Exception as exc:
        raise SystemExit(f"[build132-signer-version] invalid versions.json: {exc}")

    if not isinstance(data, dict) or "app" not in data:
        raise SystemExit("[build132-signer-version] versions.json must contain top-level 'app'")

    before_non_app = {k: v for k, v in data.items() if k != "app"}
    old = data["app"]
    data["app"] = EXPECTED_VERSION

    if {k: v for k, v in data.items() if k != "app"} != before_non_app:
        raise SystemExit("[build132-signer-version] internal scope failure: non-app version key changed")

    if old == EXPECTED_VERSION:
        print(f"[build132-signer-version] already correct: app={EXPECTED_VERSION}")
        return 0

    # Keep this patch deliberately narrow: only the app marketing version changes.
    # Telegram/BUILD consumes versions.json['app'] as CFBundleShortVersionString.
    path.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    print(f"[build132-signer-version] patched versions.json app: {old!r} -> {EXPECTED_VERSION!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
