#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
import re


API_ID_RE = re.compile(r'(?m)^telegram_api_id\s*=\s*"[^"]*"\s*$')
API_HASH_RE = re.compile(r'(?m)^telegram_api_hash\s*=\s*"[^"]*"\s*$')
API_HASH_FORMAT_RE = re.compile(r'^[0-9a-fA-F]{32}$')
EXPECTED_API_ID = "22732185"
DEFAULT_BUILD_CONFIG_OWNER = "submodules/BuildConfig/Sources/BuildConfig.m"
BUILD_CONFIG_OWNER_MARKER = "// MARK: Jerkgram Build124 API identity proof"
BUILD_CONFIG_OWNER_ANCHOR = "@implementation BuildConfig"
BUILD_CONFIG_API_ID_ANCHOR = "_apiId = APP_CONFIG_API_ID;"


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


def patch_build_config_owner(text: str) -> str:
    if BUILD_CONFIG_OWNER_MARKER in text:
        return text
    if text.count(BUILD_CONFIG_OWNER_ANCHOR) != 1:
        raise RuntimeError("expected exactly one BuildConfig implementation owner")
    if text.count(BUILD_CONFIG_API_ID_ANCHOR) != 1:
        raise RuntimeError("expected exactly one APP_CONFIG_API_ID owner")
    proof = '''// MARK: Jerkgram Build124 API identity proof
#define JERKGRAM_BUILD124_STRINGIFY_INNER(value) #value
#define JERKGRAM_BUILD124_STRINGIFY(value) JERKGRAM_BUILD124_STRINGIFY_INNER(value)
__attribute__((used))
static const char jerkgramBuild124ApiIdOwner[] =
    "JERKGRAM_BUILD124_API_ID=" JERKGRAM_BUILD124_STRINGIFY(APP_CONFIG_API_ID);

'''
    return text.replace(BUILD_CONFIG_OWNER_ANCHOR, proof + BUILD_CONFIG_OWNER_ANCHOR, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inject Jerkgram Telegram API credentials without logging them")
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

    api_id, api_hash = validate_credentials(
        os.environ.get("JERKGRAM_TELEGRAM_API_ID", ""),
        os.environ.get("JERKGRAM_TELEGRAM_API_HASH", ""),
    )
    variables_path = Path(args.variables)
    owner_path = Path(args.build_config_owner)
    if not variables_path.is_file():
        raise RuntimeError(f"Telegram build variables file not found: {variables_path}")
    if not owner_path.is_file():
        raise RuntimeError(f"Telegram BuildConfig owner not found: {owner_path}")

    original_variables = variables_path.read_text(encoding="utf-8")
    original_owner = owner_path.read_text(encoding="utf-8")
    updated_variables = patch_variables(original_variables, api_id, api_hash)
    updated_owner = patch_build_config_owner(original_owner)

    # Compute both transformations before mutating either file so owner drift fails closed.
    variables_path.write_text(updated_variables, encoding="utf-8")
    owner_path.write_text(updated_owner, encoding="utf-8")

    print("[Jerkgram Telegram API] approved credentials injected into active BuildConfig owner")


if __name__ == "__main__":
    main()
