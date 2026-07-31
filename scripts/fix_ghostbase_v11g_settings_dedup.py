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

property_block = """    var glassEnabled: Bool
    var profileAvatarBlur: Bool
    var profileBlurTint: Bool
    var profileBlurReduced: Bool
"""

count = text.count(property_block)

if count == 2:
    first = text.find(property_block)
    second = text.find(property_block, first + len(property_block))

    if first < 0 or second < 0:
        raise SystemExit(
            "[V11G SETTINGS FIX] duplicate property block offsets unavailable"
        )

    text = text[:second] + text[second + len(property_block):]
    print("[V11G SETTINGS FIX] removed duplicate profile/glass state properties")
elif count == 1:
    print("[V11G SETTINGS FIX] profile/glass state properties already unique")
else:
    raise SystemExit(
        f"[V11G SETTINGS FIX] unexpected profile/glass property block count: {count}"
    )

unused_profile = (
    "    let profile = GhostBaseSettingsSection.profileMetrics.rawValue\n"
)

profile_decl_count = text.count(unused_profile)

if profile_decl_count == 1:
    text = text.replace(unused_profile, "", 1)
    print("[V11G SETTINGS FIX] removed unused profile section local")
elif profile_decl_count == 0:
    print("[V11G SETTINGS FIX] unused profile section local already absent")
else:
    raise SystemExit(
        f"[V11G SETTINGS FIX] unexpected profile local count: {profile_decl_count}"
    )

if text.count(property_block) != 1:
    raise SystemExit(
        "[V11G SETTINGS FIX] profile/glass properties are not unique after repair"
    )

if unused_profile in text:
    raise SystemExit(
        "[V11G SETTINGS FIX] unused profile section local remains after repair"
    )

TARGET.write_text(text, encoding="utf-8")

print(f"[V11G SETTINGS FIX] repaired {TARGET}")
