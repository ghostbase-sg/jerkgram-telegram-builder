#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

OWNER = Path("submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift")
MARKER = "// BUILD132_NATIVE_SETTINGS_FOOTERS1"
TARGET_PAGES = ("about", "appearance", "messages")


def fail(message: str) -> None:
    print(f"[build132-native-footers] FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def require_target_info(source: str, page: str) -> None:
    token = f".{page}"
    positions = [m.start() for m in re.finditer(re.escape(token), source)]
    if not positions:
        fail(f"missing settings page token: {token}")

    # The page enum token can also occur in navigation wiring.  Require at
    # least one bounded occurrence whose local page-entry region contains the
    # semantic .info footer entry used by this controller.
    for pos in positions:
        start = max(0, pos - 500)
        end = min(len(source), pos + 3500)
        window = source[start:end]
        if ".info(" in window:
            return
    fail(f"{page} page has no bounded .info footer entry")


def canonicalize_info_renderer(source: str) -> tuple[str, bool]:
    pattern = re.compile(
        r"(?m)^(?P<indent>[ \t]*)case let \.info\(_, text\):[ \t]*$"
    )
    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        fail(f"expected exactly one .info renderer case, found {len(matches)}")

    match = matches[0]
    indent = match.group("indent")
    body_start = match.start()
    search_from = match.end()

    # Bound replacement to this switch case only.  Stop at the next sibling
    # case or at the switch-closing brace; never rewrite the surrounding enum.
    sibling_case = re.compile(
        rf"(?m)^{re.escape(indent)}case\s+"
    ).search(source, search_from)
    closing_brace = re.compile(
        rf"(?m)^{re.escape(indent)}\}}[ \t]*$"
    ).search(source, search_from)

    candidates = [
        m.start() for m in (sibling_case, closing_brace) if m is not None
    ]
    if not candidates:
        fail("could not bound .info renderer case")
    body_end = min(candidates)

    canonical = (
        f"{indent}case let .info(_, text):\n"
        f"{indent}    {MARKER}\n"
        f"{indent}    return ItemListTextItem(\n"
        f"{indent}        presentationData: presentationData,\n"
        f"{indent}        text: .plain(text),\n"
        f"{indent}        sectionId: self.section\n"
        f"{indent}    )\n"
    )

    current = source[body_start:body_end]
    if current == canonical:
        return source, False

    return source[:body_start] + canonical + source[body_end:], True


def verify_result(source: str) -> None:
    if source.count(MARKER) != 1:
        fail(f"expected exactly one marker {MARKER}")

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


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: apply_build132_native_settings_footers.py <materialized-source-root>")

    root = Path(sys.argv[1]).expanduser().resolve()
    if not root.is_dir():
        fail(f"not a directory: {root}")

    owner = root / OWNER
    if not owner.is_file():
        fail(f"missing exact owner: {OWNER}")

    original = owner.read_text(encoding="utf-8")
    for page in TARGET_PAGES:
        require_target_info(original, page)

    patched, changed = canonicalize_info_renderer(original)
    verify_result(patched)

    if changed:
        owner.write_text(patched, encoding="utf-8")
        print("[build132-native-footers] patched")
    else:
        print("[build132-native-footers] already applied")
    print(f"  owner: {OWNER}")
    print("  pages: About, Appearance, Messages")
    print("  renderer: ItemListTextItem / .plain")


if __name__ == "__main__":
    main()
