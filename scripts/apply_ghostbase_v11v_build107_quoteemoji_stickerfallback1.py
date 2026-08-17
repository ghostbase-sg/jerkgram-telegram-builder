#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src",
)).resolve()

CONVERSION = (
    ROOT
    / "submodules/TextFormat/Sources/"
    "ChatInputContentConversion.swift"
)

CHAT_TEXT = (
    ROOT
    / "submodules/ChatPresentationInterfaceState/Sources/"
    "ChatTextFormat.swift"
)

ENQUEUE = (
    ROOT
    / "submodules/TelegramCore/Sources/PendingMessages/"
    "EnqueueMessage.swift"
)

for path in (CONVERSION, CHAT_TEXT, ENQUEUE):
    if not path.is_file():
        raise RuntimeError(
            f"[V11V] missing source: {path}"
        )

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

if (
    QUOTE_MARKER in conversion
    and STICKER_MARKER in enqueue
):
    print("[V11V] BUILD107 already materialized")
    raise SystemExit(0)


def once(text, old, new, label):
    count = text.count(old)

    if count != 1:
        raise RuntimeError(
            f"[V11V] {label}: "
            f"expected exactly 1 anchor, found {count}"
        )

    return text.replace(old, new, 1)


# ============================================================
# EXACT POST-V11U PRECONDITIONS
# ============================================================

for proof in (
    "GhostBase v1.1U BUILD106_CUSTOM_EMOJI_QUOTE1",
    "else if key == ChatTextInputAttributes.customEmoji",
):
    if proof not in chat_text:
        raise RuntimeError(
            "[V11V] post-V11U ChatTextFormat "
            f"prerequisite missing: {proof}"
        )

for proof in (
    "GhostBase v1.1U BUILD106_FINAL1",
    "GhostBase v1.1U BUILD106_STICKER_RECOVERY1",
    "GhostBase v1.1U BUILD106_ALBUM_RECOVERY1",
    "GhostBase v1.1U BUILD106_PORTABLE_AUTHOR1",
):
    if proof not in enqueue:
        raise RuntimeError(
            "[V11V] post-V11U EnqueueMessage "
            f"prerequisite missing: {proof}"
        )


# ============================================================
# A. PREMIUM / CUSTOM EMOJI INSIDE QUOTE
#
# V11U already fixes:
#
#   select Premium emoji -> Quote
#
# by preserving ChatTextInputAttributes.customEmoji.
#
# Remaining runtime bug is the reverse projection of an
# expanded structured blockQuote:
#
#   bq.content.plainText
#
# That deliberately throws away customEmoji(fileId/file/
# enableAnimation).
#
# Project the structured content recursively instead.
# ============================================================

old_projection = (
    "                result.append("
    "NSAttributedString(string: bq.content.plainText))\n"
)

new_projection = '''                // MARK: GhostBase v1.1V BUILD107_BLOCKQUOTE_CUSTOM_EMOJI1
                // Preserve the semantic ChatInputRun attributes of the
                // quote body. Flattening through .plainText turns a
                // Premium/custom emoji into its Unicode fallback.
                result.append(attributedString(from: bq.content))
'''

conversion = once(
    conversion,
    old_projection,
    new_projection,
    "expanded blockQuote semantic projection",
)


# ============================================================
# B. REMOVE BUILD106 NATIVE STICKER RECOVERY
#
# Restore the Build105 policy:
#
# deleted sticker -> no reconstructed media
#                 -> textual portable quote label "Стикер"
#
# Also undo the three sticker-specific cache extensions that
# V11U introduced.
# ============================================================

build106_mime = '''                case "video/mp4":
                    ext = "mp4"
                case "video/webm":
                    ext = "webm"
                case "application/x-tgsticker":
                    ext = "tgs"
                case "image/webp":
                    ext = "webp"
                case "audio/ogg", "audio/opus":
                    ext = "ogg"
                case "audio/mpeg":
                    ext = "mp3"
                case "image/gif":
                    ext = "gif"
                default:
                    break
'''

build105_mime = '''                case "video/mp4":
                    ext = "mp4"
                case "audio/ogg", "audio/opus":
                    ext = "ogg"
                case "audio/mpeg":
                    ext = "mp3"
                case "image/gif":
                    ext = "gif"
                default:
                    break
'''

enqueue = once(
    enqueue,
    build106_mime,
    build105_mime,
    "restore Build105 deleted-file mime policy",
)

build106_sticker = '''    // MARK: GhostBase v1.1U BUILD106_STICKER_RECOVERY1
    // Keep TelegramMediaFile mimeType + attributes.
    //
    // Official pending upload maps
    // .Sticker / .Animated / .Video
    // back to the appropriate document attributes.

'''

build107_sticker = '''    // MARK: GhostBase v1.1V BUILD107_STICKER_TEXT_FALLBACK1
    // Deleted stickers intentionally remain textual portable
    // replies. Do not reconstruct/reupload the sticker itself.
    if let file = media as? TelegramMediaFile, file.isSticker {
        return nil
    }

'''

enqueue = once(
    enqueue,
    build106_sticker,
    build107_sticker,
    "restore sticker textual fallback",
)


# ============================================================
# FINAL PROOFS BEFORE WRITE
# ============================================================

proofs = [
    (
        "quote marker",
        QUOTE_MARKER in conversion,
    ),
    (
        "plainText projection removed",
        old_projection not in conversion,
    ),
    (
        "semantic quote projection",
        (
            "result.append("
            "attributedString(from: bq.content))"
        )
        in conversion,
    ),
    (
        "V11U customEmoji preservation retained",
        (
            "GhostBase v1.1U "
            "BUILD106_CUSTOM_EMOJI_QUOTE1"
        )
        in chat_text,
    ),
    (
        "customEmoji branch retained",
        (
            "else if key == "
            "ChatTextInputAttributes.customEmoji"
        )
        in chat_text,
    ),
    (
        "Build107 sticker fallback",
        STICKER_MARKER in enqueue,
    ),
    (
        "sticker hard rejection restored",
        '''if let file = media as? TelegramMediaFile, file.isSticker {
        return nil
    }'''
        in enqueue,
    ),
    (
        "Build106 sticker recovery removed",
        "BUILD106_STICKER_RECOVERY1"
        not in enqueue,
    ),
    (
        "TGS extension removed",
        'case "application/x-tgsticker":'
        not in enqueue,
    ),
    (
        "WebP extension removed",
        'case "image/webp":'
        not in enqueue,
    ),
    (
        "WebM extension removed",
        'case "video/webm":'
        not in enqueue,
    ),
    (
        "textual sticker label retained",
        'return "Стикер"'
        in enqueue,
    ),
    (
        "Build106 core retained",
        "GhostBase v1.1U BUILD106_FINAL1"
        in enqueue,
    ),
    (
        "album retained",
        "BUILD106_ALBUM_RECOVERY1"
        in enqueue,
    ),
    (
        "portable author retained",
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
# WRITE ONLY AFTER EVERYTHING MATCHES
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
    "[V11V] Premium/custom emoji: "
    "semantic expanded-quote projection"
)
print(
    "[V11V] Deleted sticker: "
    'text fallback "Стикер" restored'
)
print(
    "[V11V] Build106 albums/author/media core untouched"
)
