#!/usr/bin/env python3

from pathlib import Path
import os

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"


def balanced_region(text: str, token: str) -> str:
    start = text.find(token)
    if start < 0:
        raise RuntimeError("[Build124 settings diagnostic] block missing: " + token)
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
    raise RuntimeError("[Build124 settings diagnostic] block unbalanced: " + token)


def main() -> None:
    if not TARGET.is_file():
        raise RuntimeError(f"[Build124 settings diagnostic] materialized settings owner missing: {TARGET}")
    text = TARGET.read_text(encoding="utf-8")

    print("[Build124 settings diagnostic] PUBLIC BEGIN")
    public_region = balanced_region(text, "public func ghostBaseSettingsController(")
    for number, raw in enumerate(public_region.splitlines(), 1):
        print(f"[Build124 settings diagnostic] PUBLIC {number}: {raw.strip()}")
    print("[Build124 settings diagnostic] PUBLIC END")

    anchor = "let stateValue = Atomic(value: initialState)"
    pos = text.find(anchor)
    if pos < 0:
        raise RuntimeError("[Build124 settings diagnostic] stateValue owner missing")
    lines = text.splitlines()
    line_index = text[:pos].count("\n")
    start = max(0, line_index - 35)
    end = min(len(lines), line_index + 70)
    print("[Build124 settings diagnostic] STATE OWNER BEGIN")
    for idx in range(start, end):
        print(f"[Build124 settings diagnostic] STATE {idx + 1}: {lines[idx].strip()}")
    print("[Build124 settings diagnostic] STATE OWNER END")


if __name__ == "__main__":
    main()
