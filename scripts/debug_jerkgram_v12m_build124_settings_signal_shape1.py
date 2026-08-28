#!/usr/bin/env python3

from pathlib import Path
import os

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"


def balanced_region(text: str, token: str) -> str:
    start = text.find(token)
    if start < 0:
        raise RuntimeError("[Build124 settings diagnostic] controller missing")
    brace = text.find("{", start)
    depth = 0
    in_string = False
    escaped = False
    for index in range(brace, len(text)):
        ch = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise RuntimeError("[Build124 settings diagnostic] controller unbalanced")


def main() -> None:
    if not TARGET.is_file():
        raise RuntimeError(f"[Build124 settings diagnostic] materialized settings owner missing: {TARGET}")
    region = balanced_region(TARGET.read_text(encoding="utf-8"), "public func ghostBaseSettingsController(")
    needles = (
        "statePromise",
        "stateValue",
        "Signal<",
        "let signal",
        "combineLatest",
        "ItemListController",
        "controller =",
        "return controller",
        "|>",
    )
    print("[Build124 settings diagnostic] BEGIN")
    for number, raw in enumerate(region.splitlines(), 1):
        line = raw.strip()
        if any(needle in line for needle in needles):
            print(f"[Build124 settings diagnostic] {number}: {line}")
    print("[Build124 settings diagnostic] END")


if __name__ == "__main__":
    main()
