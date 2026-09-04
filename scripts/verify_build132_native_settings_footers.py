#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
OWNER_REL = Path("submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift")
OWNER = ROOT / OWNER_REL
PATCHER = Path(__file__).with_name("apply_build132_native_settings_footers.py")
MARKER = "// BUILD132_NATIVE_SETTINGS_FOOTERS1"
TARGET_PAGES = ("about", "appearance", "messages")


def fail(message: str) -> None:
    raise SystemExit(f"[Build132 native footers verify] FAIL: {message}")


def require_target_info(source: str, page: str) -> None:
    token = f".{page}"
    positions = [m.start() for m in re.finditer(re.escape(token), source)]
    if not positions:
        fail(f"missing settings page token: {token}")
    for pos in positions:
        window = source[max(0, pos - 500): min(len(source), pos + 3500)]
        if ".info(" in window:
            return
    fail(f"{page} page has no bounded .info footer entry")


if not OWNER.is_file():
    fail(f"missing exact owner: {OWNER_REL}")
if not PATCHER.is_file():
    fail(f"missing sibling patcher: {PATCHER}")

source = OWNER.read_text(encoding="utf-8")
patcher = PATCHER.read_text(encoding="utf-8")

expected_owner_literal = str(OWNER_REL)
if expected_owner_literal not in patcher:
    fail("patcher is not bound to the exact SettingsUI owner")
if "rglob(" in patcher or ".glob(" in patcher:
    fail("recursive/broad source discovery is forbidden")
if "GhostBaseSettingsController.swift" not in patcher:
    fail("patcher owner guard missing")

if source.count(MARKER) != 1:
    fail(f"expected exactly one {MARKER} marker")

for page in TARGET_PAGES:
    require_target_info(source, page)

marker_pos = source.find(MARKER)
window = source[max(0, marker_pos - 300): marker_pos + 700]
required = (
    "case let .info(_, text):",
    "return ItemListTextItem(",
    "presentationData: presentationData",
    "text: .plain(text)",
    "sectionId: self.section",
)
for needle in required:
    if needle not in window:
        fail(f"native .info renderer missing: {needle}")

for forbidden in (
    "ItemListDisclosureItem(",
    "roundedCard",
    "cardBackground",
    "systemStyle: .glass",
):
    if forbidden in window:
        fail(f"custom/card presentation remains in .info renderer: {forbidden}")

# Static patcher contract: target only the shared semantic info renderer and
# the three named page contexts. This catches accidental broad settings edits.
for needle in (
    'TARGET_PAGES = ("about", "appearance", "messages")',
    "canonicalize_info_renderer",
    "case let .info(_, text):",
    "ItemListTextItem(",
    "text: .plain(text)",
):
    if needle not in patcher:
        fail(f"patcher contract missing: {needle}")

print(
    "[Build132 native footers verify] PASS: About/Appearance/Messages use "
    "native ItemListTextItem footer renderer"
)
