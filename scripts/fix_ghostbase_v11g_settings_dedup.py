#!/usr/bin/env python3

import os
import re
from pathlib import Path


SOURCE_ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        "/root/gb_builder/work/swiftgram-src",
    )
)

TARGET = (
    SOURCE_ROOT
    / "submodules/SettingsUI/Sources/GhostBase/"
      "GhostBaseSettingsController.swift"
)

PROPERTY_NAMES = (
    "glassEnabled",
    "profileAvatarBlur",
    "profileBlurTint",
    "profileBlurReduced",
)


def matching_paren(text: str, opening: int) -> int:
    depth = 0
    in_string = False
    escaped = False

    for index in range(opening, len(text)):
        char = text[index]

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
                return index

    raise RuntimeError("matching closing parenthesis not found")


def split_top_level_arguments(body: str) -> list[str]:
    result: list[str] = []
    start = 0
    paren = 0
    bracket = 0
    brace = 0
    in_string = False
    escaped = False

    for index, char in enumerate(body):
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
            paren += 1
        elif char == ")":
            paren -= 1
        elif char == "[":
            bracket += 1
        elif char == "]":
            bracket -= 1
        elif char == "{":
            brace += 1
        elif char == "}":
            brace -= 1
        elif (
            char == ","
            and paren == 0
            and bracket == 0
            and brace == 0
        ):
            result.append(body[start:index])
            start = index + 1

    tail = body[start:]
    if tail.strip():
        result.append(tail)

    return result


def argument_label(argument: str) -> str | None:
    match = re.match(
        r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:",
        argument,
    )
    return match.group(1) if match else None


text = TARGET.read_text(encoding="utf-8")

# ------------------------------------------------------------
# 1. Оставляем ровно одно stored property каждого типа.
# ------------------------------------------------------------
lines = text.splitlines(keepends=True)
seen_properties: set[str] = set()
output_lines: list[str] = []

for line in lines:
    stripped = line.strip()
    matched = None

    for name in PROPERTY_NAMES:
        if stripped == f"var {name}: Bool":
            matched = name
            break

    if matched is None:
        output_lines.append(line)
    elif matched not in seen_properties:
        seen_properties.add(matched)
        output_lines.append(line)
    else:
        print(
            f"[V11G SETTINGS FIX] removed duplicate property: "
            f"{matched}"
        )

missing = [
    name for name in PROPERTY_NAMES
    if name not in seen_properties
]
if missing:
    raise RuntimeError(
        "missing stored properties: " + ", ".join(missing)
    )

text = "".join(output_lines)

# ------------------------------------------------------------
# 2. Разбираем весь GhostBaseSettingsState(...) в load().
# ------------------------------------------------------------
load_marker = (
    "    static func load() -> GhostBaseSettingsState {"
)
call_marker = "return GhostBaseSettingsState("

load_start = text.find(load_marker)
if load_start < 0:
    raise RuntimeError("load() not found")

call_start = text.find(call_marker, load_start)
if call_start < 0:
    raise RuntimeError("GhostBaseSettingsState constructor not found")

opening = call_start + len(call_marker) - 1
closing = matching_paren(text, opening)

body = text[opening + 1:closing]
arguments = split_top_level_arguments(body)

seen_labels: set[str] = set()
clean_arguments: list[str] = []

for argument in arguments:
    label = argument_label(argument)

    if label is None:
        if argument.strip():
            clean_arguments.append(argument)
        continue

    if label in seen_labels:
        print(
            f"[V11G SETTINGS FIX] removed duplicate "
            f"constructor argument: {label}"
        )
        continue

    seen_labels.add(label)
    clean_arguments.append(argument)

for name in PROPERTY_NAMES:
    if name not in seen_labels:
        raise RuntimeError(
            f"required constructor argument missing: {name}"
        )

# Нормализуем только разделители между уже готовыми аргументами.
normalized = []
for argument in clean_arguments:
    stripped = argument.strip()
    if stripped:
        normalized.append("            " + stripped)

new_body = "\n" + ",\n".join(normalized) + "\n        "

text = (
    text[:opening + 1]
    + new_body
    + text[closing:]
)

# ------------------------------------------------------------
# 3. Удаляем неиспользуемую локальную переменную секции.
# ------------------------------------------------------------
text = text.replace(
    "    let profile = "
    "GhostBaseSettingsSection.profileMetrics.rawValue\n",
    "",
)

# ------------------------------------------------------------
# 4. Финальная структурная проверка.
# ------------------------------------------------------------
for name in PROPERTY_NAMES:
    property_count = len(
        re.findall(
            rf"(?m)^\s*var {re.escape(name)}: Bool\s*$",
            text,
        )
    )
    if property_count != 1:
        raise RuntimeError(
            f"{name} property count={property_count}"
        )

new_call_start = text.find(call_marker, load_start)
new_opening = new_call_start + len(call_marker) - 1
new_closing = matching_paren(text, new_opening)
new_body_check = text[new_opening + 1:new_closing]
new_arguments = split_top_level_arguments(new_body_check)

label_counts: dict[str, int] = {}
for argument in new_arguments:
    label = argument_label(argument)
    if label is not None:
        label_counts[label] = label_counts.get(label, 0) + 1

duplicates = {
    label: count
    for label, count in label_counts.items()
    if count != 1
}
if duplicates:
    raise RuntimeError(
        f"constructor labels are not unique: {duplicates}"
    )

TARGET.write_text(text, encoding="utf-8")

print(f"[V11G SETTINGS FIX] repaired {TARGET}")
print(
    f"[V11G SETTINGS FIX] constructor arguments="
    f"{len(label_counts)}"
)
