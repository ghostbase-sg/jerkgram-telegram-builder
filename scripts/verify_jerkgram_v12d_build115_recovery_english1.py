#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get(
            "GHOSTBASE_SOURCE_ROOT",
            str(Path.cwd())
        )
    )
).resolve()

ENQUEUE = (
    ROOT
    / "submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift"
)

MARKER = (
    "// MARK: Jerkgram v1.2D "
    "BUILD115_RECOVERY_ENGLISH1"
)


def require(value, message):
    if not value:
        raise RuntimeError(
            "[verify Build115 recovery English] "
            + message
        )


def function_region(text, signature):
    start = text.find(signature)
    require(start >= 0, "function missing: " + signature)

    brace = text.find("{", start)
    require(brace >= 0, "function brace missing")

    depth = 0
    in_string = False
    escaped = False

    for index in range(brace, len(text)):
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
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]

    raise RuntimeError(
        "[verify Build115 recovery English] "
        "function closing brace missing"
    )


require(ENQUEUE.is_file(), "EnqueueMessage.swift missing")
text = ENQUEUE.read_text(encoding="utf-8")

media_region = function_region(
    text,
    "private func ghostBaseDeletedMediaLabel("
)
quote_region = function_region(
    text,
    "private func ghostBaseQuoteBody("
)
resolver_region = function_region(
    text,
    "private func ghostBaseResolveDeletedReplies("
)

require(media_region.count(MARKER) == 1, "marker count != 1")

expected = (
    'return "Album"',
    'return "Poll"',
    'return "📍 Location"',
    'return "👤 Contact"',
    'return "🎲 Dice"',
    'return "Task List"',
    'return "📷 Photo"',
    'return "Sticker"',
    'return "🎙 Voice Message"',
    'return "🎥 Video Message"',
    'return "GIF"',
    'return "🎬 Video"',
    'return "🎵 Audio"',
    'return "📎 File: \\(name)"',
    'return "📎 File"',
    'return "Attachment"',
)

for token in expected:
    require(
        token in media_region,
        "English recovery label missing: " + token
    )

require(
    'ghostBaseDeletedMediaLabel(source) ?? "Deleted Message"'
    in quote_region,
    "Deleted Message fallback not canonical English"
)
require(
    resolver_region.count('"User"') >= 2,
    "unknown-author fallback not canonical English"
)

for label, region in (
    ("media label", media_region),
    ("quote body", quote_region),
    ("reply resolver", resolver_region),
):
    require(
        re.search(r"[А-Яа-яЁё]", region) is None,
        "Cyrillic survived in recovery owner: " + label
    )

# The Build107 sticker safety decision remains untouched here. This overlay
# changes only portable user-facing text; native sticker recovery is audited
# separately before any renderer change.
require(
    "BUILD107_STICKER_TEXT_FALLBACK1" in text,
    "Build107 sticker fallback prerequisite missing"
)
require(
    re.search(
        r"if let file = media as\? TelegramMediaFile,"
        r"\s*file\.isSticker\s*\{\s*return nil\s*\}",
        text,
        re.S,
    ) is not None,
    "Build107 sticker hard rejection changed unexpectedly"
)

print("[verify Build115 recovery English] GREEN")
print("[verify Build115 recovery English] portable media labels are English canonical")
print("[verify Build115 recovery English] deleted fallback + unknown author are English canonical")
print("[verify Build115 recovery English] no Cyrillic remains in portable recovery owners")
print("[verify Build115 recovery English] sticker renderer policy intentionally unchanged")
