#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))
dry_run = os.environ.get("GHOSTBASE_DRY_RUN") == "1"

path = root / "submodules/TelegramApi/Sources/Api42.swift"

if not path.is_file():
    raise SystemExit(f"missing source: {path}")

text = path.read_text(encoding="utf-8")

old = '("botAuthToken", ConstructorParameterDescription(botAuthToken))'
new = '("botAuthToken", ConstructorParameterDescription("[REDACTED]"))'

if new in text:
    print("[v1.0Y] token metadata already redacted")
elif old not in text:
    raise SystemExit("importBotAuthorization token anchor not found")
elif dry_run:
    print(f"[DRY RUN] would redact token metadata in {path}")
else:
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("[v1.0Y] token metadata redacted")
