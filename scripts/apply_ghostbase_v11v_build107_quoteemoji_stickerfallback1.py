#!/usr/bin/env python3
from pathlib import Path
import os
import re

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src",
)).resolve()

CONVERSION = ROOT / (
    "submodules/TextFormat/Sources/"
    "ChatInputContentConversion.swift"
)

CHAT_TEXT = ROOT / (
    "submodules/ChatPresentationInterfaceState/Sources/"
    "ChatTextFormat.swift"
)

ENQUEUE = ROOT / (
    "submodules/TelegramCore/Sources/PendingMessages/"
    "EnqueueMessage.swift"
)

for path in (CONVERSION, CHAT_TEXT, ENQUEUE):
    if not path.is_file():
        raise RuntimeError(f"[V11V] missing source: {path}")

conversion = CONVERSION.read_text(encoding="utf-8")
chat_text = CHAT_TEXT.read_text(encoding="utf-8")
enqueue = ENQUEUE.read_text(encoding="utf-8")

QUOTE_MARKER = (
    "GhostBase v1.1V "
    "BUILD107_BLOCKQUOTE_CUSTOM_EMOJI1"
)

STICKER_MARKER = (
    "GhostBase v1.1V "
    "BUILD107_STICKER_TEXT_FALLBACK1"
)

BUILD106_STICKER_MARKER = (
    "GhostBase v1.1U "
    "BUILD106_STICKER_RECOVERY1"
)


# ============================================================
# POST-BUILD106 PRECONDITIONS
# ============================================================

for proof in (
    "GhostBase v1.1U BUILD106_CUSTOM_EMOJI_QUOTE1",
    "else if key == ChatTextInputAttributes.customEmoji",
):
    if proof not in chat_text:
        raise RuntimeError(
            "[V11V] ChatTextFormat post-V11U "
            f"prerequisite missing: {proof}"
        )

for proof in (
    "GhostBase v1.1U BUILD106_FINAL1",
    "GhostBase v1.1U BUILD106_ALBUM_RECOVERY1",
    "GhostBase v1.1U BUILD106_PORTABLE_AUTHOR1",
):
    if proof not in enqueue:
        raise RuntimeError(
            "[V11V] EnqueueMessage post-V11U "
            f"prerequisite missing: {proof}"
        )


# ============================================================
# A. PREMIUM / CUSTOM EMOJI INSIDE EXPANDED QUOTE
#
# V11U already preserves customEmoji when selected text becomes
# a quote. Remaining bug is bq.content.plainText during reverse
# projection of an expanded structured quote.
# ============================================================

if QUOTE_MARKER not in conversion:
    old = (
        "result.append("
        "NSAttributedString(string: bq.content.plainText))"
    )

    if conversion.count(old) != 1:
        raise RuntimeError(
            "[V11V] expanded blockQuote plainText owner: "
            f"expected 1, found {conversion.count(old)}"
        )

    new = '''// MARK: GhostBase v1.1V BUILD107_BLOCKQUOTE_CUSTOM_EMOJI1
                // Keep structured inline attributes here.
                // .plainText destroys Premium/custom emoji metadata.
                result.append(attributedString(from: bq.content))'''

    conversion = conversion.replace(
        old,
        new,
        1,
    )


# ============================================================
# B. DELETE BUILD106 NATIVE STICKER RECOVERY
#
# Do NOT depend on exact comment wording.
#
# Find BUILD106 marker in its actual materialized source,
# consume the consecutive comment/blank region, then replace
# it with the Build107 hard rejection.
#
# Result:
# deleted sticker -> reconstructedMedia nil -> "Стикер"
# ============================================================

if STICKER_MARKER not in enqueue:
    lines = enqueue.splitlines(keepends=True)

    marker_index = None

    for i, line in enumerate(lines):
        if BUILD106_STICKER_MARKER in line:
            marker_index = i
            break

    if marker_index is None:
        raise RuntimeError(
            "[V11V] BUILD106 sticker marker not found"
        )

    end = marker_index + 1

    while end < len(lines):
        stripped = lines[end].strip()

        if stripped == "" or stripped.startswith("//"):
            end += 1
            continue

        break

    replacement = [
        "    // MARK: GhostBase v1.1V "
        "BUILD107_STICKER_TEXT_FALLBACK1\n",
        "    // Deleted stickers intentionally remain textual "
        "portable replies.\n",
        "    // Do not reconstruct or reupload sticker media.\n",
        "    if let file = media as? TelegramMediaFile, "
        "file.isSticker {\n",
        "        return nil\n",
        "    }\n",
        "\n",
    ]

    lines[marker_index:end] = replacement
    enqueue = "".join(lines)


# ============================================================
# C. REMOVE THE THREE BUILD106 STICKER-ONLY CACHE EXTENSIONS
#
# Regex is intentionally formatting-tolerant.
# ============================================================

for mime, ext in (
    ("video/webm", "webm"),
    ("application/x-tgsticker", "tgs"),
    ("image/webp", "webp"),
):
    pattern = re.compile(
        rf'(?m)'
        rf'^[ \t]*case "{re.escape(mime)}":[ \t]*\n'
        rf'^[ \t]*ext = "{re.escape(ext)}"[ \t]*\n'
    )

    enqueue, count = pattern.subn(
        "",
        enqueue,
        count=1,
    )

    if count != 1:
        raise RuntimeError(
            f"[V11V] sticker cache case {mime}: "
            f"expected 1, found {count}"
        )


# ============================================================
# FINAL PROOFS
# ============================================================

proofs = [
    (
        "V11U selected-text customEmoji fix retained",
        "GhostBase v1.1U BUILD106_CUSTOM_EMOJI_QUOTE1"
        in chat_text,
    ),

    (
        "V11U customEmoji branch retained",
        (
            "else if key == "
            "ChatTextInputAttributes.customEmoji"
        )
        in chat_text,
    ),

    (
        "Build107 expanded-quote marker",
        QUOTE_MARKER in conversion,
    ),

    (
        "expanded quote no longer uses plainText",
        (
            "NSAttributedString("
            "string: bq.content.plainText)"
        )
        not in conversion,
    ),

    (
        "semantic quote projection exists",
        (
            "result.append("
            "attributedString(from: bq.content))"
        )
        in conversion,
    ),

    (
        "Build107 sticker marker",
        STICKER_MARKER in enqueue,
    ),

    (
        "Build106 sticker marker removed",
        BUILD106_STICKER_MARKER not in enqueue,
    ),

    (
        "sticker hard rejection restored",
        re.search(
            r"if let file = media as\? TelegramMediaFile,"
            r"\s*file\.isSticker\s*\{\s*"
            r"return nil\s*\}",
            enqueue,
            re.S,
        )
        is not None,
    ),

    (
        "TGS cache extension removed",
        'case "application/x-tgsticker":'
        not in enqueue,
    ),

    (
        "WebM cache extension removed",
        'case "video/webm":'
        not in enqueue,
    ),

    (
        "WebP cache extension removed",
        'case "image/webp":'
        not in enqueue,
    ),

    (
        'textual sticker label retained',
        'return "Стикер"'
        in enqueue,
    ),

    (
        "Build106 deleted reply retained",
        "GhostBase v1.1U BUILD106_FINAL1"
        in enqueue,
    ),

    (
        "Build106 album retained",
        "BUILD106_ALBUM_RECOVERY1"
        in enqueue,
    ),

    (
        "Build106 portable author retained",
        "BUILD106_PORTABLE_AUTHOR1"
        in enqueue,
    ),
]

failed = [
    label
    for label, ok in proofs
    if not ok
]

if failed:
    raise RuntimeError(
        "[V11V] final proof failure: "
        + ", ".join(failed)
    )


# ============================================================
# WRITE ONLY AFTER ALL TRANSFORMS PASS
# ============================================================

CONVERSION.write_text(
    conversion,
    encoding="utf-8",
)

ENQUEUE.write_text(
    enqueue,
    encoding="utf-8",
)

print()
print("[V11V] BUILD107 materialized")
print(
    "[V11V] Premium emoji: "
    "semantic expanded-quote projection"
)
print(
    "[V11V] Deleted sticker: "
    '"Стикер" textual fallback restored'
)
print(
    "[V11V] Build106 album/author/reply core retained"
)
