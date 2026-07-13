#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / (
    "work/swiftgram-src/submodules/SettingsUI/Sources/"
    "GhostBase/GhostBaseSettingsController.swift"
)

text = FILE.read_text()

if "Version: v1.0W" in text:
    print("[v1.0W metadata] already applied")
elif "Version: v1.0U" in text:
    FILE.write_text(text.replace(
        "Version: v1.0U",
        "Version: v1.0W",
        1
    ))
    print("[v1.0W metadata] version updated")
else:
    raise RuntimeError("[v1.0W metadata] version anchor missing")
