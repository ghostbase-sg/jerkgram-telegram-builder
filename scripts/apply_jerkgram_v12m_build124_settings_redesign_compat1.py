#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

PAGE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_SETTINGS_PAGE_SUMMARY1"
COMPAT_MARKER = "// MARK: Jerkgram v1.2M BUILD124_SETTINGS_REDESIGN_COMPAT1"

PAGE_SUMMARIES = {
    "home": "strings.build124HomeSummary(state.profileEnabled, state.glassEnabled, state.localStarsEnabled)",
    "ghostMode": "strings.build124GhostSummary(state.readMessages, state.typingActions, state.presence, state.scheduledSend)",
    "messages": "strings.build124MessagesSummary(state.saveDeleted, state.saveEditHistory, state.preserveDeletedMedia)",
    "protectedContent": "strings.build124ProtectedSummary(state.protectedEnabled, state.oneTimeSave)",
    "mediaStories": "strings.build124MediaSummary(state.oneTimeSave, state.storySave)",
    "appearance": "strings.build124AppearanceSummary(state.glassEnabled, state.showRamUnderClock, state.messageSeconds)",
    "debugResearch": "strings.build124DiagnosticsSummary",
    "about": "strings.build124AboutSummary",
}


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 settings redesign compat] " + message)


def block_bounds(text: str, signature: str) -> tuple[int, int]:
    start = text.find(signature)
    require(start >= 0, "block missing: " + signature)
    brace = text.find("{", start)
    require(brace >= 0, "opening brace missing: " + signature)
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
                return start, index + 1
    raise RuntimeError("[Build124 settings redesign compat] unbalanced block: " + signature)


def patch_page(block: str, expression: str, page: str) -> str:
    if PAGE_MARKER in block:
        return block

    # Final Build123 pages frequently build an initially empty mutable entries
    # array and append rows conditionally. Put the summary in that same native
    # array instead of forcing the older literal-array representation.
    mutable = re.search(
        r'(?m)^(?P<indent>[ \t]*)var\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*\[[^\n]+\])?\s*=\s*\[\s*\]\s*$',
        block,
    )
    if mutable is not None:
        indent = mutable.group("indent")
        name = mutable.group("name")
        insertion = (
            mutable.group(0)
            + "\n"
            + indent + PAGE_MARKER + "\n"
            + indent + name + ".append(.info(-1, " + expression + "))"
        )
        return block[:mutable.start()] + insertion + block[mutable.end():]

    # Retain compatibility with the older literal-array owner used by the
    # Build124 unit fixture and any page which still returns its entries inline.
    literal = re.search(
        r'(?m)^(?P<indent>[ \t]*)(?:return\s*\[|var\s+[A-Za-z_][A-Za-z0-9_]*(?:\s*:\s*\[[^\]]+\])?\s*=\s*\[)\s*$',
        block,
    )
    require(literal is not None, f"{page}: neither mutable nor literal entries owner found")
    indent = literal.group("indent") + "    "
    insertion = (
        literal.group(0)
        + "\n"
        + indent + PAGE_MARKER + "\n"
        + indent + ".info(-1, " + expression + "),"
    )
    return block[:literal.start()] + insertion + block[literal.end():]


def patch_settings_text(text: str) -> str:
    # Main redesign is intentionally idempotent; if it already completed there
    # is nothing for this compatibility bridge to do.
    if COMPAT_MARKER in text:
        return text

    root_start, root_end = block_bounds(text, "if page == .root {")
    root = text[root_start:root_end]
    require(root.count(".disclosure(") == 9, "root destination topology is not the Build123 contract")
    require(PAGE_MARKER not in root, "summary marker must never enter root Settings")

    for page, expression in PAGE_SUMMARIES.items():
        signature = f"if page == .{page} {{"
        start, end = block_bounds(text, signature)
        block = text[start:end]
        patched = patch_page(block, expression, page)
        require(patched.count(PAGE_MARKER) == 1, f"{page}: summary marker count")
        text = text[:start] + patched + text[end:]

    owner = "private func ghostBaseSettingsEntries("
    owner_index = text.find(owner)
    require(owner_index >= 0, "settings entries owner missing")
    text = text[:owner_index] + COMPAT_MARKER + "\n" + text[owner_index:]

    root_start, root_end = block_bounds(text, "if page == .root {")
    root = text[root_start:root_end]
    require(PAGE_MARKER not in root, "summary marker leaked into root Settings")
    return text


def main() -> None:
    require(SETTINGS.is_file(), f"target missing: {SETTINGS}")
    original = SETTINGS.read_text(encoding="utf-8")
    updated = patch_settings_text(original)
    SETTINGS.write_text(updated, encoding="utf-8")
    print("[Build124 settings redesign compat] GREEN")
    print("[Build124 settings redesign compat] mutable/literal internal page entries normalized without changing root routes")


if __name__ == "__main__":
    main()
