#!/usr/bin/env python3

from pathlib import Path
import importlib.util


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_PATH = SCRIPT_DIR / "apply_jerkgram_build140_download_boost1.py"

spec = importlib.util.spec_from_file_location("jerkgram_download_boost1", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("[Build140 Download Boost2] unable to load base patcher")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

RAW_PENDING = "maxPendingParts: 6,"
PATCHED_PENDING = "maxPendingParts: jerkgramDownloadMaxPendingParts(6),"
EXPECTED_PENDING_OWNERS = 4

SELECTOR_RENDERER = "        case let .selector(_, _, title, value):"
STYLE_PREVIEW_RENDERER = "        case let .stylePreview(_, _, value):"
BOOST_RENDERER = "        case let .downloadBoost(_, _, title, value):"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build140 Download Boost2] " + message)


def patch_fetch_v2(text: str) -> str:
    if base.FETCH_MARKER in text:
        require(text.count(base.FETCH_MARKER) == 1, "Fetch marker count")
        require(
            text.count(PATCHED_PENDING) == EXPECTED_PENDING_OWNERS,
            f"patched pending owners: expected {EXPECTED_PENDING_OWNERS}, found {text.count(PATCHED_PENDING)}",
        )
        require(RAW_PENDING not in text, "stock pending owner survived patched source")
        require(
            "self.defaultPartSize = jerkgramDownloadPartSize(512 * 1024, fileSize: self.size)" in text,
            "story part-size hook missing from patched source",
        )
        require(
            "self.defaultPartSize = jerkgramDownloadPartSize(128 * 1024, fileSize: self.size)" in text,
            "normal part-size hook missing from patched source",
        )
        require("self.cdnPartSize = 128 * 1024" in text, "CDN stock part size missing")
        return text

    require("import Foundation" in text, "FetchV2 Foundation import missing")
    anchor = "private let possiblePartLengths:"
    anchor_index = text.find(anchor)
    require(anchor_index >= 0, "FetchV2 possiblePartLengths anchor missing")

    # The helper is identical to v1; only the owner topology is corrected here.
    text = text[:anchor_index] + base.FETCH_HELPER + text[anchor_index:]
    text = base.replace_once(
        text,
        "self.defaultPartSize = 512 * 1024",
        "self.defaultPartSize = jerkgramDownloadPartSize(512 * 1024, fileSize: self.size)",
        "story part size",
    )
    text = base.replace_once(
        text,
        "self.defaultPartSize = 128 * 1024",
        "self.defaultPartSize = jerkgramDownloadPartSize(128 * 1024, fileSize: self.size)",
        "default part size",
    )

    raw_count = text.count(RAW_PENDING)
    require(
        raw_count == EXPECTED_PENDING_OWNERS,
        f"pending parts: expected {EXPECTED_PENDING_OWNERS} anchors, found {raw_count}",
    )
    text = text.replace(RAW_PENDING, PATCHED_PENDING)

    require(text.count(PATCHED_PENDING) == EXPECTED_PENDING_OWNERS, "pending owners were not all patched")
    require(RAW_PENDING not in text, "stock pending owner survived replacement")
    require("self.cdnPartSize = 128 * 1024" in text, "CDN part size changed/missing")
    return text


def patch_download_boost_renderer(text: str) -> str:
    if BOOST_RENDERER in text:
        require(text.count(BOOST_RENDERER) == 1, "download boost renderer duplicated")
        return text

    require(text.count(SELECTOR_RENDERER) == 1, f"selector renderer: expected one owner, found {text.count(SELECTOR_RENDERER)}")
    selector_start = text.find(SELECTOR_RENDERER)
    preview_start = text.find("\n" + STYLE_PREVIEW_RENDERER, selector_start)
    require(preview_start >= 0, "stylePreview boundary missing after selector renderer")

    selector_block = text[selector_start:preview_start]
    require("arguments.openSendTextStyle()" in selector_block, "selector renderer lost send-style action owner")
    require("GhostBaseSettingsEntryTag.sendTextStyle" in selector_block, "selector renderer lost send-style tag owner")

    boost_block = '''
        case let .downloadBoost(_, _, title, value):
            return ItemListDisclosureItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: title,
                label: value,
                labelStyle: .text,
                sectionId: self.section,
                style: .blocks,
                disclosureStyle: .arrow,
                action: {
                    arguments.openDownloadBoost()
                },
                tag: GhostBaseSettingsEntryTag.downloadBoost
            )
'''
    result = text[:preview_start] + boost_block + text[preview_start:]
    require(result.count(BOOST_RENDERER) == 1, "download boost renderer insertion failed")
    return result


def patch_settings_text(text: str) -> str:
    # Boost1 owns the established settings topology. Intercept only its stale
    # exact-string renderer replacement and bind that one operation semantically
    # to the live selector -> stylePreview boundary.
    original_replace_once = base.replace_once

    def replace_once_with_live_renderer(current: str, old: str, new: str, label: str) -> str:
        if label == "download boost item renderer":
            return patch_download_boost_renderer(current)
        return original_replace_once(current, old, new, label)

    base.replace_once = replace_once_with_live_renderer
    try:
        return base.patch_settings_text(text)
    finally:
        base.replace_once = original_replace_once


def main() -> None:
    for path in (base.FETCH, base.SETTINGS, base.STRINGS):
        require(path.is_file(), "missing source file: " + str(path))

    fetch = patch_fetch_v2(base.FETCH.read_text(encoding="utf-8"))
    settings = patch_settings_text(base.SETTINGS.read_text(encoding="utf-8"))
    strings = base.patch_strings_text(base.STRINGS.read_text(encoding="utf-8"))

    base.FETCH.write_text(fetch, encoding="utf-8")
    base.SETTINGS.write_text(settings, encoding="utf-8")
    base.STRINGS.write_text(strings, encoding="utf-8")

    print("[Build140 Download Boost2] SOURCE PATCHED")
    print("[Build140 Download Boost2] FetchV2 four-owner topology: 4 -> 4; CDN chunk size preserved")
    print("[Build140 Download Boost2] Settings renderer: semantic selector -> stylePreview binding")


if __name__ == "__main__":
    main()
