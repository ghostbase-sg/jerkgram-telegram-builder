#!/usr/bin/env python3

import os
from pathlib import Path


SOURCE_ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        "/root/gb_builder/work/swiftgram-src",
    )
)

TARGET = (
    SOURCE_ROOT
    / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
)

text = TARGET.read_text(encoding="utf-8")

property_names = (
    "glassEnabled",
    "profileAvatarBlur",
    "profileBlurTint",
    "profileBlurReduced",
)

# ------------------------------------------------------------
# 1. Оставляем по одному stored property.
# ------------------------------------------------------------
lines = text.splitlines(keepends=True)
seen_properties: set[str] = set()
repaired_lines: list[str] = []

for line in lines:
    stripped = line.strip()

    matched_name = None
    for name in property_names:
        if stripped == f"var {name}: Bool":
            matched_name = name
            break

    if matched_name is None:
        repaired_lines.append(line)
        continue

    if matched_name in seen_properties:
        print(
            f"[V11G SETTINGS FIX] removed duplicate property: "
            f"{matched_name}"
        )
        continue

    seen_properties.add(matched_name)
    repaired_lines.append(line)

missing_properties = [
    name for name in property_names
    if name not in seen_properties
]

if missing_properties:
    raise RuntimeError(
        "missing profile/glass properties: "
        + ", ".join(missing_properties)
    )

text = "".join(repaired_lines)

# ------------------------------------------------------------
# 2. В load() оставляем по одному аргументу каждого имени.
# ------------------------------------------------------------
load_start = text.find(
    "    static func load() -> GhostBaseSettingsState {"
)
save_start = text.find(
    "    func save()",
    load_start,
)

if load_start < 0 or save_start <= load_start:
    raise RuntimeError("GhostBaseSettingsState load() span unavailable")

before_load = text[:load_start]
load_body = text[load_start:save_start]
after_load = text[save_start:]

load_lines = load_body.splitlines(keepends=True)
seen_arguments: set[str] = set()
repaired_load_lines: list[str] = []

for line in load_lines:
    stripped = line.strip()

    matched_name = None
    for name in property_names:
        if stripped.startswith(f"{name}:"):
            matched_name = name
            break

    if matched_name is None:
        repaired_load_lines.append(line)
        continue

    if matched_name in seen_arguments:
        print(
            f"[V11G SETTINGS FIX] removed duplicate load argument: "
            f"{matched_name}"
        )
        continue

    seen_arguments.add(matched_name)
    repaired_load_lines.append(line)

missing_arguments = [
    name for name in property_names
    if name not in seen_arguments
]

if missing_arguments:
    raise RuntimeError(
        "missing load arguments: "
        + ", ".join(missing_arguments)
    )

text = (
    before_load
    + "".join(repaired_load_lines)
    + after_load
)

# ------------------------------------------------------------
# 3. Удаляем старую неиспользуемую локальную переменную.
# ------------------------------------------------------------
unused_profile = (
    "    let profile = "
    "GhostBaseSettingsSection.profileMetrics.rawValue\n"
)

if unused_profile in text:
    text = text.replace(unused_profile, "", 1)
    print(
        "[V11G SETTINGS FIX] removed unused profile section local"
    )

# ------------------------------------------------------------
# 4. Финальные проверки.
# ------------------------------------------------------------
for name in property_names:
    property_count = text.count(f"    var {name}: Bool\n")

    if property_count != 1:
        raise RuntimeError(
            f"{name} property count after repair: "
            f"{property_count}"
        )

final_load = text[
    text.find("    static func load() -> GhostBaseSettingsState {"):
    text.find(
        "    func save()",
        text.find(
            "    static func load() -> GhostBaseSettingsState {"
        ),
    )
]

for name in property_names:
    argument_count = sum(
        1
        for line in final_load.splitlines()
        if line.strip().startswith(f"{name}:")
    )

    if argument_count != 1:
        raise RuntimeError(
            f"{name} load argument count after repair: "
            f"{argument_count}"
        )

TARGET.write_text(text, encoding="utf-8")

print(f"[V11G SETTINGS FIX] repaired {TARGET}")
