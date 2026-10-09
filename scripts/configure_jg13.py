#!/usr/bin/env python3
"""Configure release identity without modifying pinned upstream versions.json."""
from pathlib import Path
import json
import shutil
import apply_jerkgram_build124_telegram_api_credentials1 as credentials
import os

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work/swiftgram-src"


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError(f"Expected one exact identity owner: {old}")
    return text.replace(old, new, 1)


def main():
    config = json.loads((ROOT / "jerkgram-migration.json").read_text())
    p = SOURCE / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
    text = p.read_text()
    for key, old, value in [
        ("displayVersion", "1.0.2", config["product_display_version"]),
        ("technicalVersion", "1.0.2", config["product_technical_version"]),
        ("build", "138", str(config["build_number"])),
        ("telegramBase", "12.9.2", config["upstream_new_version"]),
    ]:
        text = replace_once(text, f'public static let {key} = "{old}"', f'public static let {key} = "{value}"')
    p.write_text(text)
    dst = SOURCE / "build-input/configuration-repository"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(SOURCE / "build-system/example-configuration", dst)
    (dst / "MODULE.bazel").write_text('module(name = "build_configuration", version = "0.0.0")\n')
    p = dst / "variables.bzl"
    text = p.read_text()
    text = replace_once(text, 'telegram_bundle_id = "ph.telegra.Telegraph"', f'telegram_bundle_id = "{config["bundle_id"]}"')
    text += '\ntelegram_bazel_path = "."\ntelegram_use_xcode_managed_codesigning = False\n'
    text = credentials.patch_variables(text, os.environ.get("JERKGRAM_TELEGRAM_API_ID", ""), os.environ.get("JERKGRAM_TELEGRAM_API_HASH", ""))
    p.write_text(text)
    # Generated VersionInfoPlist is the actual owner for both app and extension versions.
    p = SOURCE / "Telegram/BUILD"
    text = p.read_text()
    text = replace_once(text, '<string>$$version</string>', f'<string>{config["bundle_short_version"]}</string>')
    p.write_text(text)
    print(f'Configured Jerkgram {config["product_display_version"]} / Build{config["build_number"]}')


if __name__ == "__main__":
    main()
