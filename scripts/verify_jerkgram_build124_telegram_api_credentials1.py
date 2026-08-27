#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
import re


ASSIGN_RE = re.compile(r'(?m)^(telegram_api_id|telegram_api_hash)\s*=\s*"([^"]*)"\s*$')
OFFICIAL_API_ID = "8"
OFFICIAL_API_HASH = "7245de8e747a0d6fbe11f7cc14fcc0bb"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Jerkgram Telegram API verify] " + message)


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify injected Telegram API credentials without logging them")
    parser.add_argument(
        "--variables",
        default="build-input/configuration-repository/variables.bzl",
        help="Telegram build configuration variables.bzl",
    )
    args = parser.parse_args()

    expected_id = (os.environ.get("TELEGRAM_API_ID") or "").strip()
    expected_hash = (os.environ.get("TELEGRAM_API_HASH") or "").strip().lower()
    require(bool(expected_id), "TELEGRAM_API_ID is missing")
    require(bool(expected_hash), "TELEGRAM_API_HASH is missing")

    path = Path(args.variables)
    require(path.is_file(), "active variables.bzl is missing")
    values = dict(ASSIGN_RE.findall(path.read_text(encoding="utf-8")))
    require(set(values) == {"telegram_api_id", "telegram_api_hash"}, "API assignments are missing or duplicated")
    require(values["telegram_api_id"] == expected_id, "active telegram_api_id does not match the configured secret")
    require(values["telegram_api_hash"].lower() == expected_hash, "active telegram_api_hash does not match the configured secret")
    require(values["telegram_api_id"] != OFFICIAL_API_ID, "Official Telegram api_id is still active")
    require(values["telegram_api_hash"].lower() != OFFICIAL_API_HASH, "Official Telegram api_hash is still active")

    # Deliberately report only boolean state. Never echo values.
    print("[Jerkgram Telegram API verify] GREEN")
    print("[Jerkgram Telegram API verify] private credentials are active; secret values were not logged")


if __name__ == "__main__":
    main()
