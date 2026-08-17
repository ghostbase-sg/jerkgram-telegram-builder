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

conversion = CONVERSION.read_text(
    encoding="utf-8",
    errors="replace",
)

chat_text = CHAT_TEXT.read_text(
    encoding="utf-8",
    errors="replace",
)

enqueue = ENQUEUE.read_text(
    encoding="utf-8",
    errors="replace",
)

passed = []
failed = []


def check(label, ok):
    if ok:
        passed.append(label)
        print("OK   :", label)
    else:
        failed.append(label)
        print("FAIL :", label)


print()
print("============================================================")
print("V11V BUILD107 MATERIALIZED SOURCE VERIFIER")
print("============================================================")

print()
print("--- Premium/custom emoji ---")

check(
    "selected text -> Quote keeps customEmoji",
    (
        "GhostBase v1.1U "
        "BUILD106_CUSTOM_EMOJI_QUOTE1"
    )
    in chat_text
    and
    (
        "else if key == "
        "ChatTextInputAttributes.customEmoji"
    )
    in chat_text,
)

check(
    "Build107 expanded quote marker",
    (
        "GhostBase v1.1V "
        "BUILD107_BLOCKQUOTE_CUSTOM_EMOJI1"
    )
    in conversion,
)

check(
    "expanded quote does not flatten through plainText",
    (
        "NSAttributedString("
        "string: bq.content.plainText)"
    )
    not in conversion,
)

check(
    "expanded quote uses semantic content projection",
    (
        "result.append("
        "attributedString(from: bq.content))"
    )
    in conversion,
)

check(
    "customEmoji projection support exists",
    "ChatTextInputAttributes.customEmoji"
    in conversion,
)


print()
print("--- Deleted sticker ---")

check(
    "Build107 sticker fallback marker",
    (
        "GhostBase v1.1V "
        "BUILD107_STICKER_TEXT_FALLBACK1"
    )
    in enqueue,
)

check(
    "Build106 native sticker marker removed",
    "BUILD106_STICKER_RECOVERY1"
    not in enqueue,
)

check(
    "sticker recovered-media hard rejection",
    re.search(
        r"if let file = media as\? TelegramMediaFile,"
        r"\s*file\.isSticker\s*\{\s*"
        r"return nil\s*\}",
        enqueue,
        re.S,
    )
    is not None,
)

check(
    "TGS/WebM/WebP sticker cache additions removed",
    (
        'case "application/x-tgsticker":'
        not in enqueue
        and
        'case "video/webm":'
        not in enqueue
        and
        'case "image/webp":'
        not in enqueue
    ),
)

check(
    'deleted sticker textual label is "Стикер"',
    'return "Стикер"'
    in enqueue,
)


print()
print("--- Build106 regression guards ---")

for label, proof in (
    (
        "deleted reply V2",
        "GhostBase v1.1U BUILD106_FINAL1",
    ),
    (
        "portable author",
        "BUILD106_PORTABLE_AUTHOR1",
    ),
    (
        "album query",
        "BUILD106_ALBUM_QUERY1",
    ),
    (
        "album recovery",
        "BUILD106_ALBUM_RECOVERY1",
    ),
    (
        "album tail",
        "ghostBaseBuildRecoveredAlbumTail(",
    ),
    (
        "user-attached media priority",
        "userMedia == nil else",
    ),
    (
        "long quote collapse",
        "let collapse = sourceLength > 320",
    ),
    (
        "original quote entities",
        "ghostBaseOriginalQuoteableEntities(",
    ),
):
    check(
        label,
        proof in enqueue,
    )


print()
print("============================================================")
print("V11V BUILD107 RESULT")
print("============================================================")
print("PASS:", len(passed))
print("FAIL:", len(failed))

if failed:
    print()
    print("FAILED:")
    for i, label in enumerate(failed, 1):
        print(f"{i:02d}. {label}")

    raise SystemExit(1)

print()
print("BUILD107 MATERIALIZED SOURCE OK")
print("premium emoji : Quote + inside Quote preserved")
print('deleted sticker: textual fallback "Стикер"')
print("Build106 core : retained")
