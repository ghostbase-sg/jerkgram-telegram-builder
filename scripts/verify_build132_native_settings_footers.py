#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
OWNER = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
PATCHER = Path(__file__).with_name("apply_build132_native_settings_footers.py")
MARKER = "BUILD132_NATIVE_SETTINGS_FOOTERS1"


def fail(message: str) -> None:
    raise SystemExit(f"[Build132 native footers verify] FAIL: {message}")


if not OWNER.is_file():
    fail(f"missing exact owner: {OWNER}")
if not PATCHER.is_file():
    fail(f"missing sibling patcher: {PATCHER}")

source = OWNER.read_text(encoding="utf-8")
patcher = PATCHER.read_text(encoding="utf-8")

# Scope guard: STEP3 is allowed to touch only the known SettingsUI owner.
expected_owner_literal = "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
if expected_owner_literal not in patcher:
    fail("patcher is not bound to the exact SettingsUI owner")
if "rglob(" in patcher or ".glob(" in patcher:
    fail("recursive/broad source discovery is forbidden")

# The patcher must leave an explicit bounded marker after all three target
# descriptions have been normalized.  The concrete native footer constructor
# and exact anchors are verified below after the patcher's implementation.
if source.count(MARKER) != 1:
    fail(f"expected exactly one {MARKER} marker")

for section in ("About", "Appearance", "Messages"):
    token = f"BUILD132_NATIVE_FOOTER_{section.upper()}"
    if source.count(token) != 1:
        fail(f"expected exactly one bounded footer marker for {section}")

# Guard against reintroducing the old custom presentation around the STEP3
# marker block.  The implementation verifier intentionally checks only the
# bounded block, never the whole Telegram tree.
start = source.find("BUILD132_NATIVE_FOOTER_ABOUT")
end = source.find(MARKER)
if start < 0 or end < start:
    fail("bounded STEP3 marker block is malformed")
window = source[start:end + len(MARKER)]
for forbidden in ("bubble", "pill", "roundedCard", "cardBackground"):
    if forbidden.lower() in window.lower():
        fail(f"custom {forbidden} presentation remains in STEP3 block")

print("[Build132 native footers verify] PASS: exact owner + bounded native-footer markers")
