#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramCore/Sources/TelegramEngine/Peers/TelegramEnginePeers.swift"
if not path.is_file():
    raise SystemExit(f"[V10ZG PROFILEINTEL2 cleanup] missing source: {path}")

text = path.read_text(encoding="utf-8")
marker = "// MARK: GhostBase v1.0ZG PROFILEINTEL2 no-change events are report-only"
phrase = "Изменений с прошлого снимка нет"


def find_balanced_call(source: str, phrase_index: int) -> tuple[int, int] | None:
    start = source.rfind("events.append(", max(0, phrase_index - 2000), phrase_index)
    if start == -1:
        return None
    open_index = source.find("(", start)
    depth = 0
    in_string = False
    escaped = False
    for index in range(open_index, len(source)):
        char = source[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                end = index + 1
                while end < len(source) and source[end] in " \t":
                    end += 1
                if end < len(source) and source[end] == ";":
                    end += 1
                if end < len(source) and source[end] == "\r":
                    end += 1
                if end < len(source) and source[end] == "\n":
                    end += 1
                if start <= phrase_index < end:
                    return start, end
                return None
    return None


if marker not in text:
    phrase_positions = []
    offset = 0
    while True:
        index = text.find(phrase, offset)
        if index == -1:
            break
        phrase_positions.append(index)
        offset = index + len(phrase)

    removable = []
    for position in phrase_positions:
        span = find_balanced_call(text, position)
        if span is not None and span not in removable:
            removable.append(span)

    if len(removable) > 1:
        raise SystemExit(
            f"[V10ZG PROFILEINTEL2 cleanup] ambiguous no-change event calls: {len(removable)}"
        )

    if removable:
        start, end = removable[0]
        indent_start = text.rfind("\n", 0, start) + 1
        indent = text[indent_start:start]
        replacement = (
            f"{indent}{marker}\n"
            f"{indent}// The current report may say that nothing changed, but the timeline stays clean.\n"
        )
        text = text[:indent_start] + replacement + text[end:]
    else:
        # PROFILEINTEL2 may already have stopped persisting this status. Keep a proof marker
        # without altering behavior.
        insert_at = 0
        while text.startswith("import ", insert_at):
            newline = text.find("\n", insert_at)
            if newline == -1:
                break
            insert_at = newline + 1
        text = text[:insert_at] + "\n" + marker + "\n" + text[insert_at:]

    path.write_text(text, encoding="utf-8")

text = path.read_text(encoding="utf-8")
if marker not in text:
    raise SystemExit("[V10ZG PROFILEINTEL2 cleanup] marker missing")
for position in [i for i in range(len(text)) if text.startswith(phrase, i)]:
    if find_balanced_call(text, position) is not None:
        raise SystemExit("[V10ZG PROFILEINTEL2 cleanup] no-change timeline append remains")

print("[V10ZG] PROFILEINTEL2 cleanup applied")
print("[V10ZG] no-change status is not persisted as a history event")
