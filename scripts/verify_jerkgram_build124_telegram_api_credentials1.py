#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
import re


ASSIGN_RE = re.compile(r'(?m)^(telegram_api_id|telegram_api_hash)\s*=\s*"([^"]*)"\s*$')
API_HASH_FORMAT_RE = re.compile(r'^[0-9a-fA-F]{32}$')
EXPECTED_API_ID = "22732185"
OFFICIAL_API_ID = "8"
OFFICIAL_API_HASH = "7245de8e747a0d6fbe11f7cc14fcc0bb"
DEFAULT_BUILD_CONFIG_OWNER = "submodules/BuildConfig/Sources/BuildConfig.m"
SOURCE_OWNER_MARKER = "// MARK: Jerkgram Build124 API identity proof"
SOURCE_OWNER_PROOF = '"JERKGRAM_BUILD124_API_ID=" JERKGRAM_BUILD124_STRINGIFY(APP_CONFIG_API_ID)'


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
    parser.add_argument(
        "--build-config-owner",
        default=DEFAULT_BUILD_CONFIG_OWNER,
        help="Official Telegram BuildConfig source owner",
    )
    args = parser.parse_args()

    expected_id = (os.environ.get("JERKGRAM_TELEGRAM_API_ID") or "").strip()
    expected_hash = (os.environ.get("JERKGRAM_TELEGRAM_API_HASH") or "").strip().lower()
    require(bool(expected_id), "JERKGRAM_TELEGRAM_API_ID is missing")
    require(bool(expected_hash), "JERKGRAM_TELEGRAM_API_HASH is missing")
    require(expected_id == EXPECTED_API_ID, "configured API ID is not the approved Build124 canary identity")
    require(API_HASH_FORMAT_RE.fullmatch(expected_hash) is not None, "configured API hash has an invalid shape")

    variables_path = Path(args.variables)
    owner_path = Path(args.build_config_owner)
    require(variables_path.is_file(), "active variables.bzl is missing")
    require(owner_path.is_file(), "active BuildConfig source owner is missing")

    values = dict(ASSIGN_RE.findall(variables_path.read_text(encoding="utf-8")))
    require(set(values) == {"telegram_api_id", "telegram_api_hash"}, "API assignments are missing or duplicated")
    require(values["telegram_api_id"] == expected_id, "active telegram_api_id does not match the configured secret")
    require(values["telegram_api_hash"].lower() == expected_hash, "active telegram_api_hash does not match the configured secret")
    require(values["telegram_api_id"] == EXPECTED_API_ID, "active telegram_api_id is not the approved Build124 canary identity")
    require(values["telegram_api_id"] != OFFICIAL_API_ID, "Official Telegram api_id is still active")
    require(values["telegram_api_hash"].lower() != OFFICIAL_API_HASH, "Official Telegram api_hash is still active")

    owner = owner_path.read_text(encoding="utf-8")
    require(owner.count(SOURCE_OWNER_MARKER) == 1, "BuildConfig API identity proof is missing or duplicated")
    require(owner.count(SOURCE_OWNER_PROOF) == 1, "BuildConfig API identity proof is not derived from APP_CONFIG_API_ID")
    require(owner.count("_apiId = APP_CONFIG_API_ID;") == 1, "Official BuildConfig API ID owner changed")
    require(owner.count("_apiHash = @(APP_CONFIG_API_HASH);") == 1, "Official BuildConfig API hash owner changed")
    require(expected_hash not in owner.lower(), "private API hash leaked into BuildConfig source")

    print("[Jerkgram Telegram API verify] GREEN")
    print("[Jerkgram Telegram API verify] approved canary credentials and compiled source owner are active; secret values were not logged")


if __name__ == "__main__":
    main()
