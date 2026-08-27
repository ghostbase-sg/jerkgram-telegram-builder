#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
import re


API_ID_RE = re.compile(r'(?m)^telegram_api_id\s*=\s*"[^"]*"\s*$')
API_HASH_RE = re.compile(r'(?m)^telegram_api_hash\s*=\s*"[^"]*"\s*$')
API_HASH_FORMAT_RE = re.compile(r'^[0-9a-fA-F]{32}$')
EXPECTED_API_ID = "22732185"


def validate_credentials(api_id: str, api_hash: str) -> tuple[str, str]:
    api_id = (api_id or "").strip()
    api_hash = (api_hash or "").strip()
    if not api_id or not api_hash:
        raise ValueError("JERKGRAM_TELEGRAM_API_ID and JERKGRAM_TELEGRAM_API_HASH must both be present")
    if not api_id.isdigit() or int(api_id) <= 0:
        raise ValueError("JERKGRAM_TELEGRAM_API_ID must be a positive decimal integer")
    if api_id != EXPECTED_API_ID:
        raise ValueError("JERKGRAM_TELEGRAM_API_ID does not match the approved Build124 canary identity")
    if not API_HASH_FORMAT_RE.fullmatch(api_hash):
        raise ValueError("JERKGRAM_TELEGRAM_API_HASH must be exactly 32 hexadecimal characters")
    return api_id, api_hash.lower()


def patch_variables(text: str, api_id: str, api_hash: str) -> str:
    api_id, api_hash = validate_credentials(api_id, api_hash)
    if len(API_ID_RE.findall(text)) != 1:
        raise RuntimeError("expected exactly one telegram_api_id assignment")
    if len(API_HASH_RE.findall(text)) != 1:
        raise RuntimeError("expected exactly one telegram_api_hash assignment")
    text = API_ID_RE.sub(f'telegram_api_id = "{api_id}"', text, count=1)
    text = API_HASH_RE.sub(f'telegram_api_hash = "{api_hash}"', text, count=1)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Inject Jerkgram Telegram API credentials without logging them")
    parser.add_argument(
        "--variables",
        default="build-input/configuration-repository/variables.bzl",
        help="Telegram build configuration variables.bzl",
    )
    args = parser.parse_args()

    api_id, api_hash = validate_credentials(
        os.environ.get("JERKGRAM_TELEGRAM_API_ID", ""),
        os.environ.get("JERKGRAM_TELEGRAM_API_HASH", ""),
    )
    path = Path(args.variables)
    if not path.is_file():
        raise RuntimeError(f"Telegram build variables file not found: {path}")

    original = path.read_text(encoding="utf-8")
    updated = patch_variables(original, api_id, api_hash)
    path.write_text(updated, encoding="utf-8")

    print("[Jerkgram Telegram API] credentials injected into active build configuration")


if __name__ == "__main__":
    main()
